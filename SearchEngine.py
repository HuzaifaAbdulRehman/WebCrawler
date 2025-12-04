from WebCrawler import WebCrawler                        # Parent class with crawling functionality
import pickle                                            # Serialization - saves/loads index to/from disk
import sys                                               # System utilities for max integer in clustering
import argparse                                          # Command-line argument parsing (-u, -p, -s, -t flags)
import numpy as np                                       # Matrix operations for document clustering
import random                                            # Random sampling to select cluster leaders
from sklearn.metrics.pairwise import euclidean_distances # Distance calculation between document vectors
from nltk.stem import PorterStemmer                      # Stemming for query processing (search -> search)
import math                                              # Logarithms and square root for TF-IDF calculation
import csv                                               # CSV parsing for thesaurus file
from textwrap import wrap                                # Text wrapping for displaying search result snippets


class SearchEngine(WebCrawler):
    def __init__(self, seed_url):
        super().__init__(seed_url)
        self.thesaurus = None
        self.thesaurus_file = None
        self.clusters = None  # Leader-follower clustering: {leader_doc: [(follower, distance)]}
        self.N = None  # Total number of documents in collection
        self.df = None  # Document frequency for each term (how many docs contain it)

    def set_thesaurus(self, thesaurus_file):
        """Load word synonyms from CSV file for query expansion when results are sparse"""
        thesaurus = {}

        try:
            with open(thesaurus_file) as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                    word = row[0]
                    alternatives = row[1:]
                    thesaurus[word] = alternatives

            self.thesaurus = thesaurus
            self.thesaurus_file = thesaurus_file

        except IOError as e:
            print("Error opening" + thesaurus_file + " error({0}): {1}".format(e.errno, e.strerror))
        except ValueError:
            print("Error opening" + thesaurus_file + ": Data is not correctly formatted. See README.")
        except:
            print("Error opening" + thesaurus_file + "Unexpected error:", sys.exc_info()[0])
            raise

    def load_index(self, filename="Output/exported_index.obj"):
        """Restore previously built index from disk using pickle deserialization"""
        try:
            f = open(filename, "rb")
        except IOError:
            print("Error opening index file: " + filename)
            return 0

        tmp_dict = pickle.load(f)
        f.close()

        self.__dict__.update(tmp_dict)
        print("Index successfully imported from disk.")

    def save_index(self, filename="Output/exported_index.obj"):
        """Persist current index to disk so we don't have to re-crawl next time"""
        f = open(filename, 'wb')
        pickle.dump(self.__dict__, f)
        f.close()

    def validate_query(self, query):
        for q in query.split():
            if self.word_is_valid(q) is not True:
                return False
        return True

    def cluster_docs(self, k=5):
        """
        K-means style clustering using leader-follower algorithm
        Randomly select k documents as leaders, assign others to nearest leader
        based on Euclidean distance in the term frequency space

        Useful for finding similar documents and organizing search results
        """
        # Use np.array instead of deprecated np.matrix for NumPy 2.x compatibility
        X = np.array([list(x) for x in zip(*self.frequency_matrix)])

        # Min-max normalization to scale all values between 0 and 1
        X_max, X_min = X.max(), X.min()
        if X_max - X_min > 0:
            X = (X - X_min) / (X_max - X_min)
        else:
            X = np.zeros_like(X)

        if len(X) < k:
            print("Warning: not enough documents to pick " + str(k) + " leaders.")
            k = int(len(X) / 2)
            print("Clustering around " + str(k) + " leaders.")

        leader_indices = random.sample(range(0, len(X)), k)
        follower_indices = list(set([i for i in range(len(X))]) - set(leader_indices))

        clusters = {l: [] for l in leader_indices}

        # Assign each follower to its closest leader using Euclidean distance
        for f in follower_indices:
            min_dist = sys.maxsize
            min_dist_index = -1

            for l in leader_indices:
                # Reshape to 2D arrays as required by euclidean_distances
                cur_dist = euclidean_distances(X[f].reshape(1, -1), X[l].reshape(1, -1))[0][0]
                if cur_dist < min_dist:
                    min_dist = cur_dist
                    min_dist_index = l

            clusters[min_dist_index].append((f, min_dist))

        self.clusters = clusters

    def normalize_list(self, input_list):
        """
        Convert vector to unit length for cosine similarity
        Divides each element by the L2 norm (Euclidean length)
        This removes document length bias from relevance scoring
        """
        l_norm = math.sqrt(sum([l**2 for l in input_list]))

        if l_norm > 0:
            input_list = [l/l_norm for l in input_list]
        return input_list

    def build_frequency_matrix(self):
        """Extend parent method to also compute corpus statistics needed for TF-IDF"""
        super().build_frequency_matrix()

        self.N = len(self.frequency_matrix[0])  # Total documents
        self.df = [sum(row) for row in self.frequency_matrix]  # Docs containing each term

    def tf_idf(self, doc):
        """
        Calculate TF-IDF weight for document/query vector

        TF (Term Frequency): 1 + log10(count) - dampens impact of repeated terms
        IDF (Inverse Document Frequency): log10(N/df) - rare terms get higher weight

        Combined: frequent terms in few docs score highest
        """
        w = []

        for d in range(len(doc)):
            if doc[d] > 0:
                # Logarithmic TF prevents long documents from dominating
                # IDF boosts discriminative terms that appear in fewer documents
                w.append((1 + math.log10(doc[d])) * math.log10(self.N / self.df[d]))
            else:
                w.append(0)

        return w

    def cosine_similarity(self, query, doc):
        """
        Measure angle between query and document vectors in term space

        Result ranges from 0 (orthogonal/unrelated) to 1 (identical direction)
        Independent of vector magnitude - focuses purely on term distribution

        Formula: cos(θ) = (q · d) / (|q| × |d|)
        """
        q_prime = self.tf_idf(query)
        d_prime = self.tf_idf(doc)

        q_prime = self.normalize_list(q_prime)
        d_prime = self.normalize_list(d_prime)

        # Dot product of normalized vectors equals cosine of angle between them
        return sum([q_prime[i] * d_prime[i] for i in range(len(q_prime))])

    def process_query(self, user_query, k=6, query_expanded=False):
        """
        Main search function: convert user query to ranked document list

        Pipeline:
        1. Tokenize and stem query terms
        2. Remove stopwords and unknown terms
        3. Convert to term frequency vector
        4. Calculate cosine similarity with each document
        5. Boost score if query terms appear in title
        6. If too few results, expand query using thesaurus synonyms

        Returns top k results as [[score, title, URL, snippet]]
        """
        scores = {doc_id: 0 for doc_id in self.doc_titles.keys()}

        # Title boost: documents with query terms in title get relevance bonus
        for t in self.doc_titles.keys():
            cur_title = self.doc_titles[t].lower()
            if len(set(user_query.split()).intersection(cur_title.split())) > 0:
                scores[t] = 0.25

        query = user_query
        query = query.split()

        query = [q for q in query if q not in self.stop_words]

        # Stem query terms to match how documents were indexed
        stemmer = PorterStemmer()
        query = [stemmer.stem(q) for q in query]

        # Discard terms not in our vocabulary (they can't match anything)
        query = [q for q in query if q in self.all_terms]

        # Build query vector: count of each term in the query
        query = [query.count(term) for term in self.all_terms]

        # Transpose matrix to get document vectors (columns become rows)
        docs = [list(x) for x in zip(*self.frequency_matrix)]

        for i, (doc_id, score) in enumerate(scores.items()):
            scores[doc_id] += self.cosine_similarity(query, docs[i])

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Build result list with score, title, URL path, and preview snippet
        results = [['%06.4f' % score, self.doc_titles[doc_id], self.doc_urls[doc_id].replace(self.domain_url, ''),
                    " ".join(self.doc_words[doc_id][:20])] for doc_id, score in sorted_scores if score > 0]

        # Query expansion: if results are sparse, add synonyms and try again
        if len(results) < k/2 and query_expanded is False:
            print("Less than K/2 results. Performing thesaurus expansion...")

            query = user_query.split()

            for term in query:
                if term in self.thesaurus:
                    query += [syn for syn in self.thesaurus[term] if syn not in query]

            # Recursive call with expanded query (flag prevents infinite recursion)
            return self.process_query(" ".join(query), k, True)

        return results[:k]

    def display_clusters(self):
        if self.clusters is not None:
            for leader, followers in self.clusters.items():
                print("Doc" + str(leader) + ":", end="")

                if len(followers) == 0:
                    print("\tNo followers", end="")
                print()

                for follower in followers:
                    print("\t\t+ Doc" + str(follower[0]) + " (Distance: " + str(follower[1]) + ")")
                print()
        else:
            print("Documents not yet clustered.")

    def show_main_menu(self):
        self.print_divider()
        print("|    Web Crawler & Search Engine System                             |\n"
              "|    CS3001 - Computer Networks Project                             |\n"
              "|                                                                    |\n"
              "|    [0] Exit                                                        |\n"
              "|    [1] Build Index                                                 |\n"
              "|    [2] Search Documents                                            |")
        self.print_divider()

    def print_divider(self):
        [print("-", end="") for x in range(70)]
        print()

    def display_menu(self):
        """Interactive CLI menu for crawling websites and searching indexed content"""
        run_program = True

        while run_program:
            self.show_main_menu()

            main_menu_input = "-1"
            while main_menu_input.isdigit() is False or int(main_menu_input) not in range(0, 3):
                main_menu_input = input("Please select an option: ")
            self.print_divider()

            if int(main_menu_input) == 1:
                if self.clusters is not None:
                    print("Index has already been built. \nYou'll need to restart the program to build a new one.")

                else:
                    import_input = "-1"
                    while import_input != "y" and import_input != "n":
                        import_input = input("Would you like to import the index from disk? (y/n) ").lower()

                    if import_input == "y":
                        self.load_index()

                    else:
                        print("\nSeed URL: " + self.seed_url)
                        print("Page limit: " + str(self.page_limit))
                        print("Stop words: " + str(self.stop_words_file))
                        print("Thesaurus: " + str(self.thesaurus_file))

                        print("\nBeginning crawling...\n")
                        search_engine.crawl()
                        print("\nIndex built.")
                        self.print_divider()

                        info_input = "-1"
                        while info_input != "y" and info_input != "n":
                            info_input = input("Would you like to see info about the pages crawled? (y/n) ").lower()

                        if info_input == "y":
                            search_engine.produce_duplicates()
                            print(search_engine)

                        self.print_divider()
                        print("Building Term Frequency matrix...", end="")
                        sys.stdout.flush()

                        search_engine.build_frequency_matrix()
                        print(" Done.")

                        f = open("Output/tf_matrix.csv", "w")
                        f.write(search_engine.print_frequency_matrix())
                        f.close()
                        print("\n\nComplete frequency matrix has been exported to Output/tf_matrix.csv")
                        self.print_divider()

                        tf_input = "-1"
                        while tf_input != "y" and tf_input != "n":
                            tf_input = input("\nWould you like to see the most frequent terms? (y/n) ").lower()

                        if tf_input == "y":
                            self.print_divider()
                            print("Most Common Stemmed Terms:\n")
                            print("{: <15} {: >25} {: >25}".format("Term", "Term Frequency", "Document Frequency"))
                            print("{: <15} {: >25} {: >25}".format("----", "--------------", "------------------"))
                            count = 1
                            for i, j, k in search_engine.n_most_common(20):
                                print("{: <15} {: >25} {: >25}".format((str(count) + ". " + i), j, k))
                                count += 1

                        self.print_divider()

                        print("\nBeginning clustering...")
                        try:
                            self.cluster_docs()

                            c_input = "-1"
                            while c_input != "y" and c_input != "n":
                                c_input = input("\nDocuments clustered. Would you like to see their clustering? (y/n) ").lower()

                            if c_input == "y":
                                self.print_divider()
                                self.display_clusters()
                        except (TypeError, KeyError) as e:
                            print(f"Clustering skipped due to compatibility issue with newer NumPy/scikit-learn versions.")
                            print("(This is optional - search functionality still works!)")

                        b_input = "-1"
                        while b_input != "y" and b_input != "n":
                            b_input = input("\nWould you like to export this index to disk? (y/n) ").lower()

                        if b_input == "y":
                            self.save_index()
                            print("Exported to Output/exported_index.obj.")

            elif int(main_menu_input) == 2:
                if len(self.visited_urls) == 0:
                    print("You must build the index first.")
                else:
                    while True:
                        query_input = input("\nPlease enter a query or \"stop\": ")

                        if self.validate_query(query_input):
                            if "stop" in query_input:
                                run_program = False
                                break

                            else:
                                results = self.process_query(query_input)
                                self.print_divider()

                                if len(results) > 0:
                                    for i in range(len(results)):
                                        print(str(i+1) + ".\t[" + str(results[i][0]) + "]  " + results[i][1] + " (" + results[i][2] + ")")
                                        print()
                                        print("\t\"" + "\n\t ".join(wrap(results[i][3], 50)) + "\"")
                                        print("\n")
                                else:
                                    print("No results found.")
                                self.print_divider()

                        else:
                            print("Invalid query.")
            else:
                break

        print("\nGoodbye!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Crawler & Search Engine System - CS3001 Computer Networks - FAST NUCES Karachi")
    parser.add_argument("-u", "--url", help="Seed URL to start crawling from. (Default is http://lyle.smu.edu/~fmoore)", required=False, default="http://lyle.smu.edu/~fmoore")
    parser.add_argument("-p", "--pagelimit", help="Maximum number of pages to crawl. (Default is 15 for lightweight performance)", required=False, default="15")
    parser.add_argument("-s", "--stopwords",
                        help="Stop words file: a newline separated list of stop words. (Default is Input/stopwords.txt)", required=False, default="Input/stopwords.txt")
    parser.add_argument("-t", "--thesaurus",
                        help="Thesaurus file: a comma separated list of words and their synonyms. (Default is Input/thesaurus.csv)", required=False, default="Input/thesaurus.csv")

    argument = parser.parse_args()

    search_engine = SearchEngine(argument.url)

    if int(argument.pagelimit) > 1:
        search_engine.set_page_limit(argument.pagelimit)

        if argument.stopwords:
            search_engine.set_stop_words(argument.stopwords)
        if argument.thesaurus:
            search_engine.set_thesaurus(argument.thesaurus)

        search_engine.display_menu()
    else:
        print("Sorry. You must crawl a minimum of 2 pages. Otherwise, why would you need a search engine?")
