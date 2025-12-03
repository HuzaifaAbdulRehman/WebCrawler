import urllib.request
from bs4 import BeautifulSoup
import sys
import re
import urllib.parse
import hashlib
import string
import codecs
from nltk.stem import PorterStemmer


class WebCrawler:
    def __init__(self, seed_url):
        self.seed_url = seed_url
        self.domain_url = "/".join(self.seed_url.split("/")[:3])  # Extract base domain like http://example.com
        self.robots_txt = None
        self.stop_words_file = None
        self.page_limit = None
        self.stop_words = []
        self.url_frontier = []  # FIFO queue for BFS traversal - URLs waiting to be crawled
        self.visited_urls = {}  # Tracks what we've seen to avoid infinite loops
        self.outgoing_urls = []
        self.broken_urls = []
        self.graphic_urls = []
        self.all_terms = []
        self.frequency_matrix = []  # Rows = terms, Columns = documents
        self.num_pages_crawled = 0
        self.num_pages_indexed = 0

        """
        These attributes store data only for indexable documents (.txt, .htm, .html, .php)
        We separate this because images/PDFs don't contribute to the search index
        """
        self.duplicate_urls = {}  # SHA-256 hash maps to list of URLs with identical content
        self.doc_urls = {}
        self.doc_titles = {}
        self.doc_words = {}

    def __str__(self):
        """Generate a human-readable crawl report showing statistics and discovered URLs"""
        report = "\nPages crawled: " + str(self.num_pages_crawled) \
                 + "\nPages indexed: " + str(self.num_pages_indexed) \
                 + "\nVisited URLs: " + str(len(self.visited_urls)) \
                 + "\n\nOutgoing URLs: " + "\n  +  " + "\n  +  ".join(self.outgoing_urls) \
                 + "\n\nBroken URLs: " + "\n  +  " + "\n  +  ".join(self.broken_urls) \
                 + "\n\nGraphic URLs: " + "\n  +  " + "\n  +  ".join(self.graphic_urls) \
                 + "\n\nDuplicate URLs:\n"

        for key in range(len(self.duplicate_urls.keys())):
            report += "\t +  Doc" + str(key + 1) + ":\n"
            for val in list(self.duplicate_urls.values())[key]:
                report += "\t\t  +  " + val + "\n"

        return report

    def get_robots_txt(self):
        """
        Fetch and parse robots.txt following RFC 9309 standard
        This tells us which paths we're allowed or forbidden to crawl
        Returns dict with 'Allowed' and 'Disallowed' URL lists
        """
        result_data_set = {"Disallowed": [], "Allowed": []}

        try:
            result = urllib.request.urlopen(self.seed_url + "/robots.txt").read()

            for line in result.decode("utf-8").split('\n'):
                if line.startswith("Allow"):
                    result_data_set["Allowed"].append(
                        self.seed_url + line.split(": ")[1].split('\r')[0]
                    )
                elif line.startswith("Disallow"):
                    result_data_set["Disallowed"].append(
                        self.seed_url + line.split(": ")[1].split('\r')[0]
                    )

        except urllib.error.HTTPError as e:
            if e.code == 404:
                print("Note: No robots.txt found. Proceeding with no restrictions.")
            else:
                print(f"Warning: Could not fetch robots.txt (HTTP {e.code}). Proceeding with no restrictions.")
        except Exception as e:
            print(f"Warning: Error reading robots.txt: {e}. Proceeding with no restrictions.")

        return result_data_set

    def set_page_limit(self, limit):
        self.page_limit = int(limit)

    def set_stop_words(self, filepath):
        """Load stopwords from file - these common words (the, is, a) add noise to search results"""
        try:
            with open(filepath, "r") as stop_words_file:
                stop_words = stop_words_file.readlines()

            self.stop_words = [x.strip() for x in stop_words]
            self.stop_words_file = filepath

        except IOError as e:
            print("Error opening" + filepath + " error({0}): {1}".format(e.errno, e.strerror))
        except ValueError:
            print("Error opening" + filepath + ": Data is not correctly formatted. See README.")
        except:
            print("Error opening" + filepath + "Unexpected error:", sys.exc_info()[0])
            raise

    def url_is_valid(self, url_string):
        """
        Validates URL structure against RFC 3986 using regex
        Checks for proper scheme (http/https), valid domain format, and optional port/path
        """
        pattern = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$',
            re.IGNORECASE)

        return bool(pattern.match(url_string))

    def word_is_valid(self, word):
        """
        A valid word starts with a letter and ends with letter/digit
        This filters out garbage tokens like punctuation-only strings
        """
        pattern = re.compile(r'^[a-zA-z](\S*)[a-zA-z0-9]$')
        return bool(pattern.match(word))

    def url_is_within_scope(self, url_string):
        """Keep crawler focused on the target domain - don't wander off to external sites"""
        return self.seed_url in url_string

    def produce_duplicates(self):
        """
        Group URLs by their content hash (SHA-256)
        If multiple URLs produce the same hash, they have identical content
        Useful for detecting mirrors and avoiding redundant indexing
        """
        duplicates = {}

        for url, (_, docID) in self.visited_urls.items():
            duplicates[docID] = [url] if duplicates.get(docID) is None else duplicates[docID] + [url]

        self.duplicate_urls = {docID: urls for docID, urls in duplicates.items() if len(urls) > 1}

    def crawl(self):
        """
        Core BFS crawling algorithm:
        1. Start with seed URL in queue (frontier)
        2. Pop URL, fetch content via HTTP GET
        3. Parse HTML, extract links, add unvisited ones to queue
        4. Repeat until queue empty or page limit reached

        This breadth-first approach ensures we explore level by level,
        finding pages closer to the seed first
        """
        self.robots_txt = self.get_robots_txt()

        print("robots.txt: " + " ".join("{}{}".format(key, [
            v.replace(self.domain_url, "") for v in val]) for key, val in self.robots_txt.items()) + "\n")

        self.url_frontier.append(self.seed_url + "/")

        while self.url_frontier and (self.page_limit is None or self.num_pages_indexed < self.page_limit):
            current_page = self.url_frontier.pop(0)  # FIFO: first URL in queue gets processed first

            pwd = "/".join(current_page.split("/")[:-1]) + "/"

            if pwd not in self.robots_txt["Disallowed"]:
                try:
                    # HTTP GET request - this is where TCP connection happens under the hood
                    handle = urllib.request.urlopen(current_page)

                except urllib.error.HTTPError as e:
                    # Server returned error (4xx client error, 5xx server error)
                    if current_page not in self.broken_urls and current_page is not None:
                            self.broken_urls.append(current_page)
                else:
                    current_content = str(handle.read())

                    # BeautifulSoup parses raw HTML into navigable DOM tree
                    soup = BeautifulSoup(current_content, "lxml")

                    current_title = str(soup.title.string) if soup.title is not None else current_page.replace(pwd, '')

                    # SHA-256 creates unique fingerprint of page content for duplicate detection
                    current_doc_id = hashlib.sha256(current_content.encode("utf-8")).hexdigest()

                    self.visited_urls[current_page] = (current_title, current_doc_id)
                    self.num_pages_crawled += 1

                    print(str(self.num_pages_crawled) + ". " + "Visiting: " +
                          current_page.replace(self.domain_url, "") + " (" + current_title + ")")

                    # Only index text-based documents, not binaries like PDFs or images
                    if any((current_page.lower().endswith(ext) for ext in ["/", ".html", ".htm", ".php", ".txt"])):

                        [s.extract() for s in soup('title')]

                        # Decode escaped characters and normalize to lowercase for consistent matching
                        formatted_content = codecs.escape_decode(bytes(soup.get_text().lower(), "utf-8"))[0].decode("utf-8", errors='replace')

                        # Tokenize: split text into individual words, strip punctuation
                        content_words = list(re.sub('[' + string.punctuation + ']', '', formatted_content).split())

                        content_words[0] = content_words[0][1:]

                        # Filter out stopwords and invalid tokens to keep only meaningful terms
                        self.doc_words[current_doc_id] = [w for w in content_words
                                                      if w not in self.stop_words and self.word_is_valid(w)]

                        self.doc_titles[current_doc_id] = current_title

                        # Store only first URL for each content hash to avoid duplicate entries
                        if current_doc_id not in self.doc_urls:
                            self.doc_urls[current_doc_id] = current_page

                        self.num_pages_indexed += 1

                        # Extract all hyperlinks from the page to expand our crawl frontier
                        for link in soup.find_all('a'):
                            current_url = link.get('href')

                            # Convert relative URLs (like /page.html) to absolute URLs
                            if current_url is not None and pwd not in current_url:
                                current_url = urllib.parse.urljoin(pwd, current_url)

                            if current_url is not None and self.url_is_valid(current_url):

                                # Add to frontier if within scope and not already queued or visited
                                if self.url_is_within_scope(current_url) and current_url not in self.url_frontier:

                                    if current_url not in self.visited_urls.keys():
                                        self.url_frontier.append(current_url)

                                elif not self.url_is_within_scope(current_url) and current_url not in self.outgoing_urls:
                                    self.outgoing_urls.append(current_url)

                            elif current_url not in self.broken_urls and current_url is not None:
                                self.broken_urls.append(current_url)

                    elif any(current_page.lower().endswith(ext) for ext in [".gif", ".png", ".jpeg", ".jpg"]):
                        self.graphic_urls.append(current_page)

            else:
                print("Not allowed: " + current_page.replace(self.domain_url, ""))

    def build_frequency_matrix(self):
        """
        Construct term-document matrix for TF-IDF calculations
        Each row = one unique stemmed term
        Each column = one document
        Cell value = how many times that term appears in that document

        This matrix is the foundation of our vector space model for search
        """
        if self.doc_words is not None:
            # Porter Stemmer reduces words to root form (running -> run, cats -> cat)
            stemmer = PorterStemmer()

            # Build vocabulary: all unique stemmed terms across all documents
            self.all_terms = list(set([stemmer.stem(word) for word_list in self.doc_words.values() for word in word_list]))
            self.all_terms.sort()

            self.frequency_matrix = [[] for i in self.all_terms]

            # Count term occurrences in each document
            for term in range(len(self.all_terms)):
                frequency_count = []

                for word_list in self.doc_words.values():
                    stemmed_word_list = [stemmer.stem(word) for word in word_list]
                    frequency_count.append(stemmed_word_list.count(self.all_terms[term]))

                self.frequency_matrix[term] = frequency_count

    def print_frequency_matrix(self):
        """Export term-document matrix to CSV format for analysis"""
        output_string = ","

        if self.doc_words is not None:
            for i in range(len(self.doc_words.keys())):
                output_string += "Doc" + str(i) + ","
            output_string += "\n"

            for i in range(len(self.frequency_matrix)):
                output_string += self.all_terms[i] + "," + ",".join([str(i) for i in self.frequency_matrix[i]]) + "\n"

        return output_string

    def n_most_common(self, n):
        """
        Find the N most frequently occurring terms across all documents
        Returns tuples of (term, total_frequency, document_frequency)
        Useful for understanding what topics dominate the crawled content
        """
        term_totals = []
        sorted_terms = self.all_terms
        doc_freqs = []

        for row in self.frequency_matrix:
            term_totals.append(sum(row))
            doc_freqs.append(sum([1 for x in row if x > 0]))

        sorted_terms = [x for _, x in sorted(zip(term_totals, sorted_terms))]
        doc_freqs = [x for _, x in sorted(zip(term_totals, doc_freqs))]
        term_totals.sort()

        return zip(reversed(sorted_terms[-n:]), reversed(term_totals[-n:]), reversed(doc_freqs[-n:]))
