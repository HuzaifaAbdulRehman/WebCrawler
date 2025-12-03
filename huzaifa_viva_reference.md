# Viva Quick Reference: Content Processing Pipeline
## Huzaifa Abdul Rehman (23K-0782) | CS3001 Computer Networks

---

## 1. Quick Overview

**My Role:** I handle everything that happens AFTER Abdul Moiz's HTTP client fetches a page and BEFORE the search results are returned. This includes parsing HTML responses, extracting text/links, tokenizing content, building the searchable index, and processing user queries.

**Data Flow I Control:**
```
HTTP Response → HTML Parser → Content Extractor → Tokenizer → Stemmer → TF Matrix → Query Processor → Results
      │              │              │               │            │           │            │            │
      └──────────────┴──────────────┴───────────────┴────────────┴───────────┴────────────┴────────────┘
                                    ALL HANDLED BY MY COMPONENTS
```

**System Integration:**
```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌───────────────┐
│ Abdul Moiz  │───►│ My HTML      │───►│ My Indexer      │───►│ My Query      │
│ HTTP Client │    │ Parser       │    │ (TF Matrix)     │    │ Processor     │
└─────────────┘    └──────────────┘    └─────────────────┘    └───────────────┘
```

---

## 2. Code Location Map

### Feature 1: Connection Timeout Manager
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Location** | Lines 186-193 |
| **Code** |
```python
# Lines 186-193: HTTP request with error handling
try:
    handle = urllib.request.urlopen(current_page)  # May timeout
except urllib.error.HTTPError as e:
    if current_page not in self.broken_urls and current_page is not None:
        self.broken_urls.append(current_page)  # Track failed URLs
```
| **CN Concept** | Network reliability - graceful handling of failed connections (4xx/5xx errors) |
| **Integrates with** | Abdul Moiz's TCP/IP layer provides the connection |

---

### Feature 2: HTML Parser (BeautifulSoup)
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Location** | Line 198 |
| **Import** | `from bs4 import BeautifulSoup` (Line 12) |
```python
# Line 198: Parse HTTP response body into DOM tree
soup = BeautifulSoup(current_content, "lxml")

# Line 201: Extract page title from <title> tag
current_title = str(soup.title.string) if soup.title is not None else current_page.replace(pwd, '')
```
| **Parser Used** | `lxml` - fast and tolerant of malformed HTML |
| **CN Concept** | Application layer data parsing - interprets HTTP response body (HTML) |
| **Integrates with** | Abdul Moiz's HTTP GET provides `current_content` |

---

### Feature 3: Link Discovery & Extraction
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Location** | Lines 242-266 |
```python
# Lines 242-244: Find all <a> tags with href attributes
for link in soup.find_all('a'):
    current_url = link.get('href')

# Lines 247-249: Convert relative URLs to absolute (RFC 3986)
if current_url is not None and pwd not in current_url:
    current_url = urllib.parse.urljoin(pwd, current_url)

# Lines 255-259: Add valid, unvisited URLs to frontier
if self.url_is_within_scope(current_url) and current_url not in self.url_frontier:
    if current_url not in self.visited_urls.keys():
        self.url_frontier.append(current_url)
```
| **CN Concept** | Web graph traversal - discovers edges (hyperlinks) in the web graph |
| **Integrates with** | Abdul Moiz's URL Frontier receives extracted links for BFS traversal |

---

### Feature 4: Content Extractor
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Location** | Lines 216-223 |
```python
# Line 217: Remove title tag to avoid duplication
[s.extract() for s in soup('title')]

# Line 220: Extract visible text, convert to lowercase
formatted_content = codecs.escape_decode(
    bytes(soup.get_text().lower(), "utf-8")
)[0].decode("utf-8", errors='replace')
```
| **Key Method** | `soup.get_text()` - strips all HTML tags |
| **CN Concept** | Data extraction from application layer payload - separates content from markup |
| **Integrates with** | Meeran's stopword filtering cleans extracted text |

---

### Feature 5: Text Tokenizer
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Location** | Lines 223-230 |
```python
# Line 223: Remove punctuation and split into words
content_words = list(re.sub('[' + string.punctuation + ']', '', formatted_content).split())

# Line 226: Remove 'b' prefix from bytes conversion
content_words[0] = content_words[0][1:]

# Lines 229-230: Filter valid words, remove stopwords
self.doc_words[current_doc_id] = [w for w in content_words
    if w not in self.stop_words and self.word_is_valid(w)]
```
| **Regex Pattern** | `'[' + string.punctuation + ']'` removes: `!"#$%&'()*+,-./:;<=>?@[\]^_{|}~` |
| **CN Concept** | Data preprocessing - transforms raw network data into searchable tokens |

---

### Feature 6: Visited URL Tracker (Hash-based)
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Declaration** | Line 31 |
| **Insert** | Line 207 |
| **Lookup** | Line 258 |
```python
# Line 31: Dictionary for O(1) lookup (hash table)
self.visited_urls = {}  # {URL: (Title, DocumentID)}

# Line 207: Mark URL as visited after successful fetch
self.visited_urls[current_page] = (current_title, current_doc_id)

# Line 258: Check before adding to queue (prevents duplicates)
if current_url not in self.visited_urls.keys():
    self.url_frontier.append(current_url)
```
| **Time Complexity** | O(1) average for lookup/insert (Python dict = hash table) |
| **CN Concept** | Efficient URL deduplication prevents redundant network requests |

---

### Feature 7: Porter Stemmer Integration (NLTK)
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` Lines 282-298, `SearchEngine.py` Lines 188-189 |
| **Import** | `from nltk.stem import PorterStemmer` (Line 19) |
```python
# WebCrawler.py Line 282: Initialize stemmer for indexing
stemmer = PorterStemmer()

# WebCrawler.py Line 285: Stem all terms for index
self.all_terms = list(set([stemmer.stem(word)
    for word_list in self.doc_words.values() for word in word_list]))

# SearchEngine.py Lines 188-189: Stem query terms
stemmer = PorterStemmer()
query = [stemmer.stem(q) for q in query]
```
| **Examples** | `running→run`, `jumps→jump`, `happily→happili`, `connection→connect` |
| **CN Concept** | Data normalization - improves search recall across morphological variants |

---

### Feature 8: Term Frequency Matrix Builder
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` Lines 279-300, `SearchEngine.py` Lines 131-135 |
| **Function** | `build_frequency_matrix()` |
```python
# WebCrawler.py Lines 288-300: Build term-document matrix
self.frequency_matrix = [[] for i in self.all_terms]  # Row per term

for term in range(len(self.all_terms)):
    frequency_count = []
    for word_list in self.doc_words.values():
        stemmed_word_list = [stemmer.stem(word) for word in word_list]
        frequency_count.append(stemmed_word_list.count(self.all_terms[term]))
    self.frequency_matrix[term] = frequency_count

# SearchEngine.py Lines 134-135: Calculate document frequency for IDF
self.N = len(self.frequency_matrix[0])  # Total documents
self.df = [sum(row) for row in self.frequency_matrix]  # Doc freq per term
```
| **Data Structure** | 2D list: `frequency_matrix[term_index][doc_index] = count` |
| **CN Concept** | Inverted index structure for efficient information retrieval |

---

### Feature 9: Query Processor
| Item | Details |
|------|---------|
| **File** | `SearchEngine.py` |
| **Function** | `process_query()` |
| **Lines** | 170-229 |
```python
def process_query(self, user_query, k=6, query_expanded=False):
    # Line 172: Initialize scores for all documents
    scores = {doc_id: 0 for doc_id in self.doc_titles.keys()}

    # Lines 175-178: Title matching bonus (+0.25)
    for t in self.doc_titles.keys():
        if len(set(user_query.split()).intersection(cur_title.split())) > 0:
            scores[t] = 0.25

    # Line 185: Remove stopwords from query
    query = [q for q in query if q not in self.stop_words]

    # Lines 188-189: Porter stemming on query
    stemmer = PorterStemmer()
    query = [stemmer.stem(q) for q in query]

    # Line 195: Convert query to frequency vector
    query = [query.count(term) for term in self.all_terms]

    # Lines 201-202: Calculate cosine similarity for each document
    for i, (doc_id, score) in enumerate(scores.items()):
        scores[doc_id] += self.cosine_similarity(query, docs[i])

    # Line 205: Sort by score descending
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Line 229: Return top K results
    return results[:k]
```
| **Pipeline** | Tokenize → Stopword removal → Stem → Vectorize → Cosine similarity → Rank |
| **CN Concept** | Query-document matching in vector space model |

---

### Feature 10: Thesaurus Query Expansion
| Item | Details |
|------|---------|
| **File** | `SearchEngine.py` |
| **Loader** | Lines 33-53 `set_thesaurus()` |
| **Expansion** | Lines 213-226 |
```python
# Lines 33-44: Load thesaurus from CSV file
def set_thesaurus(self, thesaurus_file):
    with open(thesaurus_file) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            word = row[0]
            alternatives = row[1:]
            thesaurus[word] = alternatives

# Lines 213-226: Expand query if less than K/2 results
if len(results) < k/2 and query_expanded is False:
    print("Less than K/2 results. Performing thesaurus expansion...")
    for term in query:
        if term in self.thesaurus:
            query += [syn for syn in self.thesaurus[term] if syn not in query]
    return self.process_query(" ".join(query), k, True)  # Recursive call
```
| **File Format** | CSV: `word,synonym1,synonym2,synonym3` |
| **CN Concept** | Improves recall by expanding search to semantically related terms |

---

### Feature 11: Pickle Serializer
| Item | Details |
|------|---------|
| **File** | `SearchEngine.py` |
| **Save** | Lines 70-73 |
| **Load** | Lines 56-67 |
```python
# Lines 70-73: Save entire crawler state to disk
def save_index(self, filename="Output/exported_index.obj"):
    f = open(filename, 'wb')
    pickle.dump(self.__dict__, f)  # Serialize all object attributes
    f.close()

# Lines 56-67: Load index from disk (skip re-crawling)
def load_index(self, filename="Output/exported_index.obj"):
    f = open(filename, "rb")
    tmp_dict = pickle.load(f)
    self.__dict__.update(tmp_dict)  # Restore all attributes
    f.close()
```
| **Output File** | `Output/exported_index.obj` |
| **CN Concept** | Persistence layer - saves network crawl results for later use without re-crawling |

---

## 3. Integration Points

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      INTEGRATION FLOW DIAGRAM                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ABDUL MOIZ (Networking)              HUZAIFA (Processing)              │
│                                                                          │
│  ┌──────────────────┐                 ┌──────────────────┐              │
│  │ urlopen()        │────────────────►│ BeautifulSoup    │              │
│  │ (Line 188)       │  HTTP response  │ (Line 198)       │              │
│  └──────────────────┘                 └──────────────────┘              │
│                                                                          │
│  ┌──────────────────┐                 ┌──────────────────┐              │
│  │ url_frontier     │◄────────────────│ soup.find_all()  │              │
│  │ (Line 259)       │  extracted URLs │ (Line 242)       │              │
│  └──────────────────┘                 └──────────────────┘              │
│                                                                          │
│  HUZAIFA (Processing)                 MEERAN (Compliance)               │
│                                                                          │
│  ┌──────────────────┐                 ┌──────────────────┐              │
│  │ Tokenized words  │────────────────►│ Stopword filter  │              │
│  │ (Line 223)       │  raw words      │ (Line 229)       │              │
│  └──────────────────┘                 └──────────────────┘              │
│                                                                          │
│  ┌──────────────────┐                 ┌──────────────────┐              │
│  │ Extracted URLs   │────────────────►│ url_is_valid()   │              │
│  │ (Line 244)       │  for validation │ (Line 252)       │              │
│  └──────────────────┘                 └──────────────────┘              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Function Call Chain

| From (Abdul Moiz) | To (Huzaifa) | Location |
|-------------------|--------------|----------|
| `urlopen()` returns content | `BeautifulSoup(content)` | Line 188 → 198 |
| `hashlib.sha256()` returns hash | `visited_urls[url] = (title, hash)` | Line 204 → 207 |

| From (Huzaifa) | To (Abdul Moiz) | Location |
|----------------|-----------------|----------|
| `soup.find_all('a')` extracts links | `url_frontier.append(url)` | Line 242 → 259 |

| From (Huzaifa) | To (Meeran) | Location |
|----------------|-------------|----------|
| Raw word list | Stopword filtering | Line 223 → 229 |
| Extracted URLs | `url_is_valid()` validation | Line 244 → 252 |

---

## 4. Key Algorithms Implementation

### 4.1 Timeout/Error Handling

**Location:** `WebCrawler.py`, Lines 186-193

```python
try:
    handle = urllib.request.urlopen(current_page)  # May hang or fail
except urllib.error.HTTPError as e:
    if current_page not in self.broken_urls:
        self.broken_urls.append(current_page)  # Track failed URLs
```

**Note:** Default urllib timeout is system-dependent. For explicit timeout: `urlopen(url, timeout=10)`

---

### 4.2 Link Extraction Algorithm

**Location:** `WebCrawler.py`, Lines 242-259

```python
for link in soup.find_all('a'):           # Find all anchor tags
    current_url = link.get('href')         # Get href attribute

    # Normalize relative to absolute (RFC 3986)
    current_url = urllib.parse.urljoin(pwd, current_url)

    # Validate before adding to queue
    if (self.url_is_valid(current_url) and
        self.url_is_within_scope(current_url) and
        current_url not in self.visited_urls):
        self.url_frontier.append(current_url)
```

---

### 4.3 Tokenization Regex

**Location:** `WebCrawler.py`, Line 223

```python
# Pattern removes: !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
content_words = list(re.sub('[' + string.punctuation + ']', '', formatted_content).split())
```

---

### 4.4 Porter Stemmer Usage

**Location:** `WebCrawler.py` Line 282, `SearchEngine.py` Line 188

```python
from nltk.stem import PorterStemmer
stemmer = PorterStemmer()
stemmed = stemmer.stem("running")  # Returns "run"
```

**Stemming Examples:**
| Original | Stemmed |
|----------|---------|
| running | run |
| connections | connect |
| jumps | jump |
| happily | happili |

---

### 4.5 Term Frequency Matrix Structure

**Location:** `WebCrawler.py`, Lines 288-300

```python
# frequency_matrix[term_index][doc_index] = count
# Example structure:
#         Doc0  Doc1  Doc2
# crawl     5     0     2
# web       3     4     0
# search    0     2     5
```

---

### 4.6 Query Processing Pipeline

```
User Query: "web crawler"
     │
     ▼ Split (Line 182)
["web", "crawler"]
     │
     ▼ Stopword Removal (Line 185)
["web", "crawler"]  # No stopwords removed
     │
     ▼ Porter Stem (Line 189)
["web", "crawl"]
     │
     ▼ Corpus Filter (Line 192)
["web", "crawl"]  # Keep only indexed terms
     │
     ▼ Vectorize (Line 195)
[0, 0, 1, 0, 0, 1, 0, ...]  # Term frequency vector
     │
     ▼ Cosine Similarity (Line 202)
{doc1: 0.85, doc2: 0.32, doc3: 0.15, ...}
     │
     ▼ Sort & Return Top K (Lines 205, 229)
[("doc1", 0.85), ("doc2", 0.32), ...]
```

---

## 5. Viva Q&A - Code Reference

### Q1: "Show me where you handle connection timeouts/errors"
**A:** `WebCrawler.py`, Lines 186-193
```python
try:
    handle = urllib.request.urlopen(current_page)
except urllib.error.HTTPError as e:
    self.broken_urls.append(current_page)
```
**Why:** Prevents crawler crash on network failures; maintains reliability.

---

### Q2: "How do you extract links from HTML?"
**A:** `WebCrawler.py`, Lines 242-259
```python
for link in soup.find_all('a'):
    current_url = link.get('href')
```
**Why:** BeautifulSoup parses DOM tree; `find_all('a')` finds all anchor elements.

---

### Q3: "Why BeautifulSoup instead of regex for HTML parsing?"
**A:** Regex cannot handle:
- Nested tags: `<div><a href="x"><span>text</span></a></div>`
- Malformed HTML: Missing closing tags
- Varying attribute orders: `<a href="x" class="y">` vs `<a class="y" href="x">`

BeautifulSoup builds a parse tree that handles all edge cases.
```python
# BeautifulSoup handles both:
soup.find_all('a')  # Works regardless of attribute order
```

---

### Q4: "Where is the visited URL tracker? What's its time complexity?"
**A:** `WebCrawler.py`, Line 31 (declaration), Line 207 (insert), Line 258 (lookup)
```python
self.visited_urls = {}  # Python dict = hash table
# O(1) average for insert and lookup
```
**Why:** Hash-based set prevents O(n) linear search through visited URLs.

---

### Q5: "Explain Porter Stemming. Where is it implemented?"
**A:** `WebCrawler.py` Line 282, `SearchEngine.py` Line 188
```python
stemmer = PorterStemmer()
stemmer.stem("running")  # → "run"
```
**Algorithm:** Rule-based suffix stripping (removes -ing, -ed, -ly, etc.)
**Why:** "running" and "run" should match the same documents.

---

### Q6: "What's the structure of your term-document matrix?"
**A:** `WebCrawler.py`, Lines 288-300
```python
self.frequency_matrix[term_index][doc_index] = count
# 2D list: rows = terms, columns = documents
```
**Why:** Enables efficient TF-IDF calculation and cosine similarity.

---

### Q7: "Why Pickle instead of JSON for serialization?"
**A:** `SearchEngine.py`, Lines 70-73
```python
pickle.dump(self.__dict__, f)  # Serializes entire object state
```

| Pickle | JSON |
|--------|------|
| Binary, compact | Text, human-readable |
| Preserves Python objects | Requires type conversion |
| Handles numpy arrays | Cannot serialize numpy |
| Faster for complex data | Slower, more overhead |

**Why:** Need to preserve exact Python object state (PorterStemmer instance, numpy arrays, nested dicts).

---

### Q8: "How does thesaurus expansion work?"
**A:** `SearchEngine.py`, Lines 213-226
```python
if len(results) < k/2:  # Fewer than expected results
    for term in query:
        if term in self.thesaurus:
            query += self.thesaurus[term]  # Add synonyms
    return self.process_query(query, k, True)  # Re-search recursively
```
**Why:** Improves recall when exact terms don't match documents.

---

### Q9: "How do you handle relative vs absolute URLs?"
**A:** `WebCrawler.py`, Lines 247-249
```python
if current_url is not None and pwd not in current_url:
    current_url = urllib.parse.urljoin(pwd, current_url)
```
**Examples:**
- `urljoin("http://x.com/dir/", "../page")` → `"http://x.com/page"`
- `urljoin("http://x.com/dir/", "page.html")` → `"http://x.com/dir/page.html"`

---

### Q10: "Walk through the query processing pipeline"
**A:** `SearchEngine.py`, `process_query()` method, Lines 170-229

1. **Line 182:** Tokenize query → `["web", "crawler"]`
2. **Line 185:** Remove stopwords → `["web", "crawler"]`
3. **Line 189:** Porter stem → `["web", "crawl"]`
4. **Line 192:** Filter to corpus terms → `["web", "crawl"]`
5. **Line 195:** Convert to frequency vector → `[0, 0, 1, 0, 1, ...]`
6. **Line 202:** Calculate cosine similarity for each doc
7. **Line 205:** Sort by score descending
8. **Line 229:** Return top K results

---

### Q11: "How do you extract text content from HTML?"
**A:** `WebCrawler.py`, Line 220
```python
formatted_content = codecs.escape_decode(
    bytes(soup.get_text().lower(), "utf-8")
)[0].decode("utf-8", errors='replace')
```
**Why:** `soup.get_text()` strips all HTML tags, keeping only visible text.

---

### Q12: "What validation do you perform on extracted URLs?"
**A:** `WebCrawler.py`, Lines 252-258
```python
if self.url_is_valid(current_url):          # Regex validation (Meeran)
    if self.url_is_within_scope(current_url):  # Same domain check (Meeran)
        if current_url not in self.visited_urls:  # Not visited (Huzaifa)
            self.url_frontier.append(current_url)
```

---

## 6. CN Concepts Summary

| Concept | My Implementation | Location |
|---------|-------------------|----------|
| **Application Layer** | HTTP response parsing (BeautifulSoup) | Line 198 |
| **Content-Type Handling** | Check file extensions (.html, .php, .txt) | Line 214 |
| **Network Reliability** | HTTP error handling, broken URL tracking | Lines 191-193 |
| **Data Serialization** | Pickle for persisting crawl data | Lines 70-73 |
| **Hash Tables** | O(1) visited URL lookup | Lines 31, 258 |
| **Queues (BFS)** | URL frontier for breadth-first traversal | Line 30 |
| **URL Standards** | RFC 3986 compliant normalization | Line 249 |
| **Information Retrieval** | TF matrix, query processing | Lines 279-300 |

---

## 7. Troubleshooting Reference

| Issue | Handled At | Code |
|-------|------------|------|
| **Malformed HTML** | Line 198 | `BeautifulSoup(content, "lxml")` - lxml is tolerant |
| **Relative URLs** | Lines 247-249 | `urllib.parse.urljoin(pwd, current_url)` |
| **Empty responses** | Line 195 | Check `current_content` before parsing |
| **Unicode errors** | Line 220 | `decode("utf-8", errors='replace')` |
| **Missing title tag** | Line 201 | Fallback: `current_page.replace(pwd, '')` |
| **HTTP 404/500** | Lines 191-193 | Add to `broken_urls` list |
| **Invalid words** | Lines 229-230 | `word_is_valid()` regex filter |
| **Stopwords** | Line 229 | Filter against `self.stop_words` list |
| **Duplicate URLs** | Line 258 | Check `visited_urls` before enqueuing |

---

## Quick Reference Card

```
┌────────────────────────────────────────────────────────────────┐
│                    HUZAIFA'S CODE LOCATIONS                    │
├────────────────────────────────────────────────────────────────┤
│ HTTP Error Handler       WebCrawler.py:186-193                │
│ BeautifulSoup Parser     WebCrawler.py:198                    │
│ Title Extraction         WebCrawler.py:201                    │
│ Content Extraction       WebCrawler.py:216-223                │
│ Link Extraction          WebCrawler.py:242-259                │
│ Tokenization             WebCrawler.py:223                    │
│ Visited URL Tracker      WebCrawler.py:31, 207, 258           │
│ Porter Stemmer           WebCrawler.py:282, SearchEngine:188  │
│ TF Matrix Builder        WebCrawler.py:279-300                │
│ Doc Frequency Calc       SearchEngine.py:131-135              │
│ Query Processor          SearchEngine.py:170-229              │
│ Thesaurus Loader         SearchEngine.py:33-53                │
│ Thesaurus Expansion      SearchEngine.py:213-226              │
│ Pickle Save              SearchEngine.py:70-73                │
│ Pickle Load              SearchEngine.py:56-67                │
└────────────────────────────────────────────────────────────────┘
```

---

*Concise Viva Reference - Huzaifa Abdul Rehman (23K-0782)*
*CS3001 Computer Networks | December 2025*
