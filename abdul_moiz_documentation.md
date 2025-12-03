# Viva Quick Reference: Core Networking & Search Algorithms
## Abdul Moiz Hossain (23K-0553) | CS3001 Computer Networks

---

## 1. Quick Overview

**My Role:** I built the **core networking stack** (HTTP/HTTPS, TCP/IP, DNS) and **search algorithms** (BFS crawling, TF-IDF, Cosine Similarity) that form the foundation of the web crawler.

**System Flow I Control:**
```
Seed URL → DNS Resolution → TCP Connection → HTTP GET → BFS Traversal → Index → TF-IDF → Search Results
   │              │               │              │            │           │        │           │
   └──────────────┴───────────────┴──────────────┴────────────┴───────────┴────────┴───────────┘
                              ALL HANDLED BY MY COMPONENTS
```

**Data Flow:**
```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌───────────────┐
│ URL Input   │───►│ HTTP Client  │───►│ BFS Crawler     │───►│ Search Engine │
│             │    │ (urllib)     │    │ (FIFO Queue)    │    │ (TF-IDF)      │
└─────────────┘    └──────────────┘    └─────────────────┘    └───────────────┘
```

---

## 2. Code Location Map

### Feature 1: HTTP/HTTPS Protocol Implementation
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Location** | Line 188 (inside `crawl()`) |
| **Code** |
```python
# Line 188: HTTP GET Request - Application Layer
handle = urllib.request.urlopen(current_page)

# Line 195: Read HTTP Response Body
current_content = str(handle.read())
```
| **Libraries** | `urllib.request`, `urllib.error` (Lines 11, 15) |
| **CN Concept** | Application Layer (OSI Layer 7) - HTTP/1.1 protocol |
| **Integrates with** | Huzaifa's BeautifulSoup parser receives `current_content` |

---

### Feature 2: TCP/IP Socket Communication
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` (via urllib) |
| **Location** | Implicit in Line 188 |
| **How it works** |
```python
# urllib.request.urlopen() internally:
# 1. Creates TCP socket: socket.socket(AF_INET, SOCK_STREAM)
# 2. Three-way handshake: SYN → SYN-ACK → ACK
# 3. Sends HTTP request over TCP stream
# 4. Receives response segments
# 5. Closes connection (FIN-ACK)
```
| **Ports** | HTTP → 80, HTTPS → 443 (automatic) |
| **CN Concept** | Transport Layer (OSI Layer 4) - Reliable delivery via TCP |

---

### Feature 3: DNS Resolution Handler
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` (via urllib) |
| **Location** | Implicit in Line 188 |
| **How it works** |
```python
# When urlopen("http://books.toscrape.com/") is called:
# 1. urllib extracts hostname: "books.toscrape.com"
# 2. Calls socket.getaddrinfo("books.toscrape.com", 80)
# 3. OS performs DNS lookup (recursive query)
# 4. Returns IP: 51.77.156.129
# 5. TCP connection made to resolved IP
```
| **CN Concept** | Application/Network Layer - Domain name to IP translation |

---

### Feature 4: Breadth-First Search Crawler
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Function** | `crawl()` |
| **Lines** | 165-273 |
```python
# Line 172: Initialize frontier with seed URL
self.url_frontier.append(self.seed_url + "/")

# Line 178: BFS loop condition
while self.url_frontier and (self.page_limit is None or
                              self.num_pages_indexed < self.page_limit):

    # Line 180: DEQUEUE from front (FIFO = BFS)
    current_page = self.url_frontier.pop(0)

    # Line 188: HTTP GET (fetch page)
    handle = urllib.request.urlopen(current_page)

    # Lines 242-259: Extract links and ENQUEUE to back
    for link in soup.find_all('a'):
        current_url = link.get('href')
        # ... validation ...
        self.url_frontier.append(current_url)  # Line 259
```
| **Data Structure** | FIFO Queue (`list` with `append()` and `pop(0)`) |
| **CN Concept** | Graph traversal algorithm for web graph |

---

### Feature 5: URL Frontier Queue Manager
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Declaration** | Line 30 |
| **Operations** | Lines 172, 180, 259 |
```python
# Line 30: Initialize empty frontier
self.url_frontier = []

# Line 172: Enqueue seed URL
self.url_frontier.append(self.seed_url + "/")

# Line 180: Dequeue from front (FIFO)
current_page = self.url_frontier.pop(0)

# Line 259: Enqueue discovered links to back
self.url_frontier.append(current_url)
```
| **FIFO Guarantee** | `append()` adds to back, `pop(0)` removes from front |
| **CN Concept** | BFS requires FIFO queue for level-order traversal |

---

### Feature 6: URL Normalization Algorithm
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Location** | Line 249 (inside `crawl()`) |
| **Library** | `urllib.parse` (Line 15) |
```python
# Line 247-249: Convert relative URL to absolute
if current_url is not None and pwd not in current_url:
    current_url = urllib.parse.urljoin(pwd, current_url)

# Examples:
# urljoin("http://example.com/dir/", "page.html")
#   → "http://example.com/dir/page.html"
# urljoin("http://example.com/dir/", "../other.html")
#   → "http://example.com/other.html"
```
| **RFC** | RFC 3986 - URI Generic Syntax |
| **CN Concept** | Standardizes URLs for consistent HTTP requests |

---

### Feature 7: SHA-256 Content Hasher
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Location** | Line 204 |
| **Library** | `hashlib` (Line 16) |
```python
# Line 204: Generate SHA-256 hash of page content
current_doc_id = hashlib.sha256(current_content.encode("utf-8")).hexdigest()

# Output: 64-character hex string (256 bits)
# Example: "a7f3d8c2e1b4a9f6c3d2e1b4a9f6c3d2..."
```
| **Properties** | Deterministic, fixed-size output, collision-resistant |
| **CN Concept** | Cryptographic fingerprinting for content identification |

---

### Feature 8: Duplicate Detection System
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Data Structures** | Lines 44-47 |
| **Check** | Line 236 |
```python
# Lines 44-47: Data structures for duplicate tracking
self.duplicate_urls = {}  # {doc_id: [URLs producing same content]}
self.doc_urls = {}        # {doc_id: first_URL}
self.doc_titles = {}      # {doc_id: title}
self.doc_words = {}       # {doc_id: [words]}

# Line 236: Check if content already indexed
if current_doc_id not in self.doc_urls:
    self.doc_urls[current_doc_id] = current_page  # First URL wins
    # ... index content ...
```
| **Algorithm** | Hash content → Check if hash exists → Skip if duplicate |
| **CN Concept** | Prevents redundant indexing of identical content |

---

### Feature 9: TF-IDF Calculator
| Item | Details |
|------|---------|
| **File** | `SearchEngine.py` |
| **Function** | `tf_idf()` |
| **Lines** | 137-147 |
```python
# Lines 137-147: TF-IDF Weight Calculation
def tf_idf(self, doc):
    w = []
    for d in range(len(doc)):
        if doc[d] > 0:
            # Logarithmic TF × IDF
            w.append(
                (1 + math.log10(doc[d])) *      # Log TF
                math.log10(self.N / self.df[d]) # IDF
            )
        else:
            w.append(0)
    return w
```
| **Formula** | `TF-IDF = (1 + log₁₀(tf)) × log₁₀(N / df)` |
| **CN Concept** | Information retrieval - term importance weighting |

---

### Feature 10: Cosine Similarity Engine
| Item | Details |
|------|---------|
| **File** | `SearchEngine.py` |
| **Functions** | `cosine_similarity()` Lines 149-160, `normalize_list()` Lines 120-128 |
```python
# Lines 120-128: L2 Normalization
def normalize_list(self, input_list):
    l_norm = math.sqrt(sum([l**2 for l in input_list]))
    if l_norm > 0:
        input_list = [l/l_norm for l in input_list]
    return input_list

# Lines 149-160: Cosine Similarity
def cosine_similarity(self, query, doc):
    q_prime = self.tf_idf(query)           # TF-IDF weight query
    d_prime = self.tf_idf(doc)             # TF-IDF weight doc
    q_prime = self.normalize_list(q_prime) # Normalize to unit vector
    d_prime = self.normalize_list(d_prime)
    # Dot product of unit vectors = cosine similarity
    return sum([q_prime[i] * d_prime[i] for i in range(len(q_prime))])
```
| **Formula** | `cos(θ) = (Q · D) / (||Q|| × ||D||)` |
| **Range** | [0, 1] where 1 = identical, 0 = no similarity |

---

### Feature 11: Relevance Ranking System
| Item | Details |
|------|---------|
| **File** | `SearchEngine.py` |
| **Function** | `process_query()` |
| **Lines** | 170-229 |
```python
# Lines 170-229: Complete Query Processing & Ranking
def process_query(self, user_query, k=6, query_expanded=False):
    # Line 172: Initialize scores
    scores = {doc_id: 0 for doc_id in self.doc_titles.keys()}

    # Lines 175-178: Title match bonus (+0.25)
    for t in self.doc_titles.keys():
        if query_terms in title:
            scores[t] = 0.25

    # Lines 201-202: Calculate cosine similarity
    for i, (doc_id, score) in enumerate(scores.items()):
        scores[doc_id] += self.cosine_similarity(query, docs[i])

    # Line 205: Sort by score descending
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Line 229: Return top K results
    return results[:k]
```
| **Output** | `[[score, title, URL, preview], ...]` |

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
│  ABDUL MOIZ (Networking)              MEERAN (Compliance)               │
│                                                                          │
│  ┌──────────────────┐                 ┌──────────────────┐              │
│  │ Before urlopen() │◄────────────────│ robots.txt check │              │
│  │ (Line 185)       │  allow/deny     │ (Line 185)       │              │
│  └──────────────────┘                 └──────────────────┘              │
│                                                                          │
│  ┌──────────────────┐                 ┌──────────────────┐              │
│  │ Before enqueue   │◄────────────────│ url_is_valid()   │              │
│  │ (Line 252)       │  validation     │ (Line 252)       │              │
│  └──────────────────┘                 └──────────────────┘              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Function Call Chain

| My Function | Calls | From |
|-------------|-------|------|
| `crawl()` Line 188 | `urlopen()` | Abdul Moiz |
| Response → | `BeautifulSoup()` Line 198 | Huzaifa |
| `BeautifulSoup` → | `find_all('a')` Line 242 | Huzaifa |
| Links → | `url_is_valid()` Line 252 | Meeran |
| Valid URLs → | `url_frontier.append()` Line 259 | Abdul Moiz |

---

## 4. Key Algorithm Implementations

### 4.1 BFS Crawling Algorithm (CRITICAL)

**Location:** `WebCrawler.py`, `crawl()`, Lines 165-273

**Step-by-Step BFS Loop:**

```python
# STEP 1: Initialize (Line 172)
self.url_frontier.append(self.seed_url + "/")

# STEP 2: Main BFS Loop (Lines 178-273)
while self.url_frontier and self.num_pages_indexed < self.page_limit:

    # STEP 3: Dequeue front URL - FIFO ensures BFS (Line 180)
    current_page = self.url_frontier.pop(0)

    # STEP 4: Check robots.txt via Meeran's code (Line 185)
    if pwd not in self.robots_txt["Disallowed"]:

        # STEP 5: HTTP GET Request (Line 188)
        handle = urllib.request.urlopen(current_page)
        current_content = str(handle.read())

        # STEP 6: Generate content hash for duplicate detection (Line 204)
        current_doc_id = hashlib.sha256(current_content.encode()).hexdigest()

        # STEP 7: Mark as visited (Line 207)
        self.visited_urls[current_page] = (current_title, current_doc_id)

        # STEP 8: Extract and enqueue links (Lines 242-259)
        for link in soup.find_all('a'):
            current_url = urllib.parse.urljoin(pwd, link.get('href'))

            if (self.url_is_valid(current_url) and
                self.url_is_within_scope(current_url) and
                current_url not in self.visited_urls):

                self.url_frontier.append(current_url)  # Enqueue to back
```

**Why BFS over DFS?**
| BFS | DFS |
|-----|-----|
| Level-by-level traversal | Deep before wide |
| Important pages found early | May miss shallow important pages |
| FIFO queue | LIFO stack |
| ✅ Better for web crawling | ❌ Gets stuck in deep branches |

---

### 4.2 HTTP Implementation

**Location:** `WebCrawler.py`, Lines 186-195

```python
# Lines 186-195: HTTP GET with error handling
try:
    handle = urllib.request.urlopen(current_page)  # HTTP GET
except urllib.error.HTTPError as e:
    self.broken_urls.append(current_page)  # Track failed URLs
else:
    current_content = str(handle.read())  # Read response body
```

**HTTP Request Generated:**
```
GET /catalogue/page-1.html HTTP/1.1
Host: books.toscrape.com
User-Agent: Python-urllib/3.x
Accept-Encoding: identity
Connection: close
```

---

### 4.3 URL Normalization

**Location:** `WebCrawler.py`, Lines 247-249

```python
# Convert relative to absolute URL
if current_url is not None and pwd not in current_url:
    current_url = urllib.parse.urljoin(pwd, current_url)
```

**Examples:**
| Base URL | Relative | Absolute Result |
|----------|----------|-----------------|
| `http://x.com/dir/` | `page.html` | `http://x.com/dir/page.html` |
| `http://x.com/dir/` | `../other.html` | `http://x.com/other.html` |
| `http://x.com/dir/` | `/root.html` | `http://x.com/root.html` |

---

### 4.4 Duplicate Detection

**Location:** `WebCrawler.py`, Lines 204, 236-237

```python
# Line 204: Hash content
current_doc_id = hashlib.sha256(current_content.encode("utf-8")).hexdigest()

# Lines 236-237: Check and store
if current_doc_id not in self.doc_urls:
    self.doc_urls[current_doc_id] = current_page  # New content
else:
    # Duplicate - different URL, same content
    self.duplicate_urls[current_doc_id].append(current_page)
```

---

### 4.5 TF-IDF Calculation

**Location:** `SearchEngine.py`, Lines 137-147

**Formula:** `TF-IDF(t,d) = (1 + log₁₀(tf)) × log₁₀(N / df)`

```python
def tf_idf(self, doc):
    w = []
    for d in range(len(doc)):
        if doc[d] > 0:
            tf = 1 + math.log10(doc[d])        # Logarithmic TF
            idf = math.log10(self.N / self.df[d])  # IDF
            w.append(tf * idf)
        else:
            w.append(0)
    return w
```

**Example:**
```
Term "crawler" in Doc A:
  - Appears 5 times (tf = 5)
  - Total docs N = 10
  - Appears in 3 docs (df = 3)

TF = 1 + log₁₀(5) = 1.699
IDF = log₁₀(10/3) = 0.523
TF-IDF = 1.699 × 0.523 = 0.889
```

---

### 4.6 Cosine Similarity

**Location:** `SearchEngine.py`, Lines 149-160

```python
def cosine_similarity(self, query, doc):
    # Convert to TF-IDF vectors
    q_prime = self.tf_idf(query)
    d_prime = self.tf_idf(doc)

    # L2 normalize to unit vectors
    q_prime = self.normalize_list(q_prime)
    d_prime = self.normalize_list(d_prime)

    # Dot product = cosine similarity for unit vectors
    return sum([q_prime[i] * d_prime[i] for i in range(len(q_prime))])
```

**Formula:** `cos(θ) = (Q · D) / (||Q|| × ||D||)`

---

### 4.7 Term Frequency Matrix

**Location:** `WebCrawler.py`, `build_frequency_matrix()`, Lines 279-300

```python
def build_frequency_matrix(self):
    stemmer = PorterStemmer()

    # Get all unique stemmed terms
    self.all_terms = list(set([stemmer.stem(word)
        for word_list in self.doc_words.values()
        for word in word_list]))

    # Build matrix: rows = terms, cols = docs
    self.frequency_matrix = [[] for i in self.all_terms]

    for term in range(len(self.all_terms)):
        for word_list in self.doc_words.values():
            stemmed = [stemmer.stem(w) for w in word_list]
            self.frequency_matrix[term].append(
                stemmed.count(self.all_terms[term])
            )
```

**Matrix Structure:**
```
        Doc0  Doc1  Doc2
crawl     5     0     2
web       3     4     0
search    0     2     5
```

---

## 5. Viva Q&A - Code Reference

### Q1: "Explain your HTTP implementation"
**A:** `WebCrawler.py`, Lines 186-195
```python
handle = urllib.request.urlopen(current_page)  # HTTP GET
current_content = str(handle.read())           # Response body
```
**Layers:** Application (HTTP/1.1) → Transport (TCP) → Network (IP)

---

### Q2: "Walk through your BFS algorithm"
**A:** `WebCrawler.py`, `crawl()`, Lines 165-273

1. **Line 172:** Initialize queue `url_frontier.append(seed_url)`
2. **Line 178:** Loop while queue not empty
3. **Line 180:** Dequeue front `current_page = url_frontier.pop(0)`
4. **Line 207:** Mark visited `visited_urls[url] = (title, hash)`
5. **Line 188:** HTTP GET request
6. **Line 242:** Extract links `soup.find_all('a')`
7. **Line 259:** Enqueue to back `url_frontier.append(url)`

---

### Q3: "How does DNS resolution work in your crawler?"
**A:** `WebCrawler.py`, Line 188 (implicit in urllib)
```python
urllib.request.urlopen("http://books.toscrape.com/")
# Internally calls socket.getaddrinfo("books.toscrape.com", 80)
# Returns IP: 51.77.156.129
```
**Process:** Local cache → Recursive resolver → Root → TLD → Authoritative NS

---

### Q4: "Show URL normalization"
**A:** `WebCrawler.py`, Lines 247-249
```python
current_url = urllib.parse.urljoin(pwd, current_url)
```
**RFC 3986:** Converts relative references to absolute URIs.

---

### Q5: "Why SHA-256 over MD5?"
**A:** `WebCrawler.py`, Line 204
```python
doc_id = hashlib.sha256(content.encode()).hexdigest()
```
| SHA-256 | MD5 |
|---------|-----|
| 256-bit output | 128-bit output |
| No known collisions | Collision attacks exist |
| NIST approved | Deprecated |

---

### Q6: "Explain TF-IDF formula"
**A:** `SearchEngine.py`, Lines 137-147
```python
tf = 1 + math.log10(doc[d])           # Logarithmic TF
idf = math.log10(self.N / self.df[d]) # Inverse Document Frequency
weight = tf * idf
```
**Formula:** `w(t,d) = (1 + log₁₀(tf)) × log₁₀(N/df)`

---

### Q7: "Why cosine similarity over Euclidean distance?"
**A:** `SearchEngine.py`, Lines 149-160

| Cosine | Euclidean |
|--------|-----------|
| Measures angle (direction) | Measures distance |
| Length-independent | Biased by document length |
| Range [0,1] | Unbounded |
| ✅ Better for text | ❌ Long docs always different |

---

### Q8: "How do you prevent duplicate crawling?"
**A:** Two mechanisms:

1. **URL-based:** `WebCrawler.py`, Line 258
```python
if current_url not in self.visited_urls.keys():
    self.url_frontier.append(current_url)
```

2. **Content-based:** `WebCrawler.py`, Lines 204, 236
```python
doc_id = hashlib.sha256(content.encode()).hexdigest()
if doc_id not in self.doc_urls:  # New content
```

---

### Q9: "Explain the TCP three-way handshake"
**A:** Implicit in `WebCrawler.py`, Line 188

```
Crawler                         Server
   │──── SYN (seq=x) ──────────►│
   │◄─── SYN-ACK (seq=y,ack=x+1)│
   │──── ACK (ack=y+1) ────────►│
   │     Connection Established  │
   │──── HTTP GET ─────────────►│
```

---

### Q10: "What OSI layers does your code touch?"
**A:**

| Layer | Protocol | My Code Location |
|-------|----------|------------------|
| Application | HTTP | `WebCrawler.py:188` |
| Transport | TCP | Implicit in urllib |
| Network | IP, DNS | Implicit in urllib |

---

### Q11: "Why BFS instead of DFS for web crawling?"
**A:** `WebCrawler.py`, Lines 172, 180, 259

**BFS (FIFO Queue):** Important pages near homepage are crawled first.
**DFS (LIFO Stack):** Would go deep into irrelevant branches first.

```python
url_frontier.append(url)   # Enqueue to BACK
url_frontier.pop(0)        # Dequeue from FRONT = FIFO = BFS
```

---

### Q12: "How is the ranking score calculated?"
**A:** `SearchEngine.py`, `process_query()`, Lines 170-229

```python
# Base score from cosine similarity
scores[doc_id] = self.cosine_similarity(query, doc)

# Title match bonus (+0.25)
if query_terms in title:
    scores[doc_id] += 0.25

# Sort descending
sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

---

### Q13: "Show visited URL tracking"
**A:** `WebCrawler.py`, Lines 31, 207, 258

```python
# Line 31: Hash table declaration
self.visited_urls = {}  # {URL: (title, doc_id)}

# Line 207: Mark as visited
self.visited_urls[current_page] = (current_title, current_doc_id)

# Line 258: Check before enqueuing
if current_url not in self.visited_urls.keys():
```
**Complexity:** O(1) lookup using hash table.

---

### Q14: "How do you handle HTTP errors?"
**A:** `WebCrawler.py`, Lines 191-193

```python
except urllib.error.HTTPError as e:
    if current_page not in self.broken_urls:
        self.broken_urls.append(current_page)
```
Integrates with Meeran's error tracking system.

---

### Q15: "Explain L2 normalization for vectors"
**A:** `SearchEngine.py`, Lines 120-128

```python
def normalize_list(self, input_list):
    l_norm = math.sqrt(sum([l**2 for l in input_list]))
    return [l/l_norm for l in input_list]
```
**Purpose:** Converts vector to unit length so cosine = dot product.

---

## 6. Protocol & RFC Details

| Protocol/RFC | Implementation | Location |
|--------------|----------------|----------|
| **HTTP/1.1** | `urlopen()` GET requests | `WebCrawler.py:188` |
| **RFC 3986** | `urljoin()` URL normalization | `WebCrawler.py:249` |
| **TCP/IP** | Implicit socket handling | via urllib |
| **DNS** | Automatic resolution | via urllib |
| **SHA-256** | Content hashing | `WebCrawler.py:204` |

---

## 7. CN Concepts Summary

| Concept | My Implementation | Location |
|---------|-------------------|----------|
| **Application Layer** | HTTP GET requests | `WebCrawler.py:188` |
| **Transport Layer** | TCP via urllib | Implicit |
| **Network Layer** | IP, DNS resolution | Implicit |
| **BFS Algorithm** | FIFO queue traversal | `WebCrawler.py:172,180,259` |
| **Hash Tables** | Visited URL tracking | `WebCrawler.py:31` |
| **Cryptographic Hash** | SHA-256 fingerprinting | `WebCrawler.py:204` |
| **Vector Space Model** | TF-IDF + Cosine | `SearchEngine.py:137-160` |
| **Information Retrieval** | Relevance ranking | `SearchEngine.py:170-229` |

---

## 8. Edge Cases & Error Handling

| Edge Case | Handled At | Code |
|-----------|------------|------|
| **HTTP 4xx/5xx** | Lines 191-193 | `self.broken_urls.append(current_page)` |
| **Infinite loop** | Line 178 | `self.num_pages_indexed < self.page_limit` |
| **Duplicate content** | Lines 204, 236 | SHA-256 hash comparison |
| **Duplicate URLs** | Line 258 | `if url not in visited_urls` |
| **Relative URLs** | Line 249 | `urljoin(pwd, current_url)` |
| **robots.txt denial** | Line 185 | `if pwd not in robots_txt["Disallowed"]` |

---

## Quick Reference Card

```
┌────────────────────────────────────────────────────────────────┐
│                  ABDUL MOIZ'S CODE LOCATIONS                   │
├────────────────────────────────────────────────────────────────┤
│ HTTP GET Request         WebCrawler.py:188                    │
│ TCP/IP + DNS             WebCrawler.py:188 (implicit)         │
│ BFS Loop                 WebCrawler.py:165-273                │
│ URL Frontier Init        WebCrawler.py:172                    │
│ URL Dequeue (FIFO)       WebCrawler.py:180                    │
│ URL Enqueue              WebCrawler.py:259                    │
│ URL Normalization        WebCrawler.py:249                    │
│ SHA-256 Hash             WebCrawler.py:204                    │
│ Duplicate Check          WebCrawler.py:236, 258               │
│ Visited Tracking         WebCrawler.py:31, 207                │
│ TF-IDF Calculator        SearchEngine.py:137-147              │
│ L2 Normalization         SearchEngine.py:120-128              │
│ Cosine Similarity        SearchEngine.py:149-160              │
│ Query Processor          SearchEngine.py:170-229              │
│ TF Matrix Builder        WebCrawler.py:279-300                │
│ HTTP Error Handler       WebCrawler.py:191-193                │
└────────────────────────────────────────────────────────────────┘
```

---

*Concise Viva Reference - Abdul Moiz Hossain (23K-0553)*
*CS3001 Computer Networks | December 2025*
