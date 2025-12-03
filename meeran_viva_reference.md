# Viva Quick Reference: Protocol Compliance & Resource Management
## Meeran Uz Zaman (23K-0039) | CS3001 Computer Networks

---

## 1. Quick Overview

**My Role:** I ensure the crawler is **ethical, robust, and efficient** by implementing:
- **Protocol Compliance:** robots.txt (RFC 9309), URL validation (RFC 3986)
- **Error Handling:** HTTP status codes, network failures
- **Resource Management:** Page limits, domain scope, stopword filtering

**Protection Layer:**
```
                    ┌─────────────────────────────────────┐
                    │     MEERAN'S PROTECTION LAYER       │
                    ├─────────────────────────────────────┤
   Incoming URL ───►│ robots.txt │ URL Valid │ In Scope? │───► Abdul Moiz's
                    │  Check     │  (RFC3986)│  (Domain) │     HTTP Client
                    └─────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │         ERROR HANDLING            │
                    │  HTTP 4xx │ HTTP 5xx │ Timeouts  │
                    └───────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │       RESOURCE MANAGEMENT         │
                    │ Page Limit │ Stopwords │ Stats   │
                    └───────────────────────────────────┘
```

---

## 2. Code Location Map

### Feature 1: Robots.txt Protocol Parser (RFC 9309)
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Function** | `get_robots_txt()` |
| **Lines** | 71-98 |
```python
# Lines 71-76: Fetch and parse robots.txt
def get_robots_txt(self):
    result_data_set = {"Disallowed": [], "Allowed": []}
    try:
        result = urllib.request.urlopen(self.seed_url + "/robots.txt").read()

# Lines 79-87: Parse Allow/Disallow rules
for line in result.decode("utf-8").split('\n'):
    if line.startswith("Allow"):
        result_data_set["Allowed"].append(
            self.seed_url + line.split(": ")[1].split('\r')[0])
    elif line.startswith("Disallow"):
        result_data_set["Disallowed"].append(
            self.seed_url + line.split(": ")[1].split('\r')[0])
```
| **RFC** | RFC 9309 - Robots Exclusion Protocol |
| **Integrates with** | Abdul Moiz's crawl() checks `self.robots_txt["Disallowed"]` at Line 185 |

---

### Feature 2: HTTP Status Code Processor
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Location** | Lines 186-194 (inside `crawl()`) |
```python
# Lines 186-188: Attempt HTTP request
try:
    handle = urllib.request.urlopen(current_page)

# Lines 190-193: Handle HTTP errors (4xx, 5xx)
except urllib.error.HTTPError as e:
    if current_page not in self.broken_urls and current_page is not None:
        self.broken_urls.append(current_page)

# Line 194-195: Success path (2xx)
else:
    current_content = str(handle.read())
```
| **Codes Handled** | 2xx (success), 4xx (client error), 5xx (server error) |
| **CN Concept** | Application layer protocol response handling |

---

### Feature 3: HTTP Error Handler
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Lines** | 89-96 (robots.txt errors), 191-193 (crawl errors) |
```python
# Lines 89-96: Graceful robots.txt error handling
except urllib.error.HTTPError as e:
    if e.code == 404:
        print("Note: No robots.txt found. Proceeding with no restrictions.")
    else:
        print(f"Warning: Could not fetch robots.txt (HTTP {e.code})...")
except Exception as e:
    print(f"Warning: Error reading robots.txt: {e}...")

# Lines 191-193: Crawl error handling
except urllib.error.HTTPError as e:
    if current_page not in self.broken_urls:
        self.broken_urls.append(current_page)
```
| **CN Concept** | Network fault tolerance - graceful degradation |

---

### Feature 4: URL Validation System (RFC 3986)
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Function** | `url_is_valid()` |
| **Lines** | 124-134 |
```python
def url_is_valid(self, url_string):
    pattern = re.compile(
        r'^(?:http|ftp)s?://'                    # Scheme (http/https/ftp)
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+' # Domain
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'   # TLD
        r'localhost|'                             # Localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'   # IPv4
        r'(?::\d+)?'                              # Port (optional)
        r'(?:/?|[/?]\S+)$',                       # Path
        re.IGNORECASE)
    return bool(pattern.match(url_string))
```
| **RFC** | RFC 3986 - URI Generic Syntax |
| **Used at** | Line 252 before adding URL to frontier |

---

### Feature 5: Domain Scope Controller
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Function** | `url_is_within_scope()` |
| **Lines** | 147-148 |
```python
# Line 147-148: Check if URL belongs to seed domain
def url_is_within_scope(self, url_string):
    return self.seed_url in url_string

# Line 25: Domain extraction from seed URL
self.domain_url = "/".join(self.seed_url.split("/")[:3])
# Example: "http://books.toscrape.com/page" → "http://books.toscrape.com"
```
| **Used at** | Lines 255, 261 in crawl() |
| **CN Concept** | Prevents crawler from leaving target domain |

---

### Feature 6: Page Limit Enforcer
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Setter** | `set_page_limit()` Lines 100-101 |
| **Check** | Line 178 |
```python
# Lines 100-101: Set maximum pages to crawl
def set_page_limit(self, limit):
    self.page_limit = int(limit)

# Line 178: Enforce limit in crawl loop
while self.url_frontier and (self.page_limit is None or
                              self.num_pages_indexed < self.page_limit):

# Line 239: Increment counter after successful index
self.num_pages_indexed += 1
```
| **Default** | 15 pages (SearchEngine.py Line 414) |
| **CN Concept** | Resource management - prevents runaway crawler |

---

### Feature 7: Stopword Filter
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Loader** | `set_stop_words()` Lines 104-118 |
| **Usage** | Line 229-230 |
```python
# Lines 104-110: Load stopwords from file
def set_stop_words(self, filepath):
    try:
        with open(filepath, "r") as stop_words_file:
            stop_words = stop_words_file.readlines()
        self.stop_words = [x.strip() for x in stop_words]

# Lines 229-230: Filter during document processing
self.doc_words[current_doc_id] = [w for w in content_words
    if w not in self.stop_words and self.word_is_valid(w)]
```
| **Source File** | `Input/stopwords.txt` (150+ words) |
| **Integrates with** | Huzaifa's tokenizer output |

---

### Feature 8: Word Validator
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Function** | `word_is_valid()` |
| **Lines** | 141-144 |
```python
def word_is_valid(self, word):
    # Word must: start with letter, end with letter/digit
    pattern = re.compile(r'^[a-zA-z](\S*)[a-zA-z0-9]$')
    return bool(pattern.match(word))

# Valid:   "python", "web-crawler", "http3"
# Invalid: "123abc", "-word", "a", ".test"
```
| **Used at** | Line 230 during content processing |
| **CN Concept** | Data quality - filters noise from indexed content |

---

### Feature 9: CSV Data Exporter
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` Lines 302-316, `SearchEngine.py` Lines 320-322 |
| **Function** | `print_frequency_matrix()` |
```python
# WebCrawler.py Lines 302-316
def print_frequency_matrix(self):
    output_string = ","
    # Create header: ,Doc0,Doc1,Doc2,...
    for i in range(len(self.doc_words.keys())):
        output_string += "Doc" + str(i) + ","
    output_string += "\n"

    # Add matrix rows: term,freq0,freq1,freq2,...
    for i in range(len(self.frequency_matrix)):
        output_string += self.all_terms[i] + "," + \
            ",".join([str(i) for i in self.frequency_matrix[i]]) + "\n"
    return output_string

# SearchEngine.py Lines 320-322: Write to file
f = open("Output/tf_matrix.csv", "w")
f.write(search_engine.print_frequency_matrix())
f.close()
```
| **Output** | `Output/tf_matrix.csv` |

---

### Feature 10: Statistics Reporter
| Item | Details |
|------|---------|
| **File** | `WebCrawler.py` |
| **Function** | `__str__()` Lines 50-65 |
| **Counters** | Lines 37-38 |
```python
# Lines 37-38: Counter initialization
self.num_pages_crawled = 0  # Valid pages visited
self.num_pages_indexed = 0  # Pages with words stored

# Lines 50-65: Statistics report
def __str__(self):
    report = "\nPages crawled: " + str(self.num_pages_crawled) \
           + "\nPages indexed: " + str(self.num_pages_indexed) \
           + "\nVisited URLs: " + str(len(self.visited_urls)) \
           + "\n\nOutgoing URLs: " + "\n  +  ".join(self.outgoing_urls) \
           + "\n\nBroken URLs: " + "\n  +  ".join(self.broken_urls) \
           + "\n\nGraphic URLs: " + "\n  +  ".join(self.graphic_urls) \
           + "\n\nDuplicate URLs:\n"
```
| **Metrics Tracked** | pages_crawled, pages_indexed, visited, outgoing, broken, graphic, duplicates |

---

## 3. Integration Points

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      INTEGRATION FLOW DIAGRAM                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  MEERAN (Compliance)              ABDUL MOIZ (Network)                  │
│                                                                          │
│  ┌──────────────────┐             ┌──────────────────┐                  │
│  │ robots.txt Parse │────────────►│ Disallow Check   │                  │
│  │ (Line 71-98)     │   blocks    │ (Line 185)       │                  │
│  └──────────────────┘             └──────────────────┘                  │
│                                                                          │
│  ┌──────────────────┐             ┌──────────────────┐                  │
│  │ url_is_valid()   │────────────►│ URL Frontier     │                  │
│  │ (Line 124)       │   filters   │ (Line 252)       │                  │
│  └──────────────────┘             └──────────────────┘                  │
│                                                                          │
│  ┌──────────────────┐             ┌──────────────────┐                  │
│  │ url_is_within_   │────────────►│ Scope Gate       │                  │
│  │ scope() (L147)   │   gates     │ (Line 255)       │                  │
│  └──────────────────┘             └──────────────────┘                  │
│                                                                          │
│  ┌──────────────────┐             ┌──────────────────┐                  │
│  │ HTTP Error       │◄────────────│ urlopen()        │                  │
│  │ Handler (L191)   │   catches   │ (Line 188)       │                  │
│  └──────────────────┘             └──────────────────┘                  │
│                                                                          │
│  MEERAN (Filters)                 HUZAIFA (Processing)                  │
│                                                                          │
│  ┌──────────────────┐             ┌──────────────────┐                  │
│  │ Stopword Filter  │◄────────────│ Tokenizer Output │                  │
│  │ (Line 229)       │   cleans    │ (Line 223)       │                  │
│  └──────────────────┘             └──────────────────┘                  │
│                                                                          │
│  ┌──────────────────┐             ┌──────────────────┐                  │
│  │ word_is_valid()  │────────────►│ doc_words Dict   │                  │
│  │ (Line 141)       │   filters   │ (Line 229)       │                  │
│  └──────────────────┘             └──────────────────┘                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Key Integration Calls

| My Function | Called From | Purpose |
|-------------|-------------|---------|
| `get_robots_txt()` | `crawl()` Line 167 | Initialize before crawling |
| `url_is_valid()` | `crawl()` Line 252 | Validate before queuing |
| `url_is_within_scope()` | `crawl()` Line 255 | Prevent off-domain crawl |
| Stopword check | `crawl()` Line 229 | Clean indexed content |
| `word_is_valid()` | `crawl()` Line 230 | Validate each word |
| `print_frequency_matrix()` | `SearchEngine` Line 321 | Export results |

---

## 4. Key Implementations

### 4.1 Robots.txt Parser (RFC 9309) - CRITICAL

**Location:** `WebCrawler.py`, `get_robots_txt()`, Lines 71-98

**How It Works:**
```python
# Step 1: Fetch robots.txt (Line 76)
result = urllib.request.urlopen(self.seed_url + "/robots.txt").read()

# Step 2: Parse each line (Lines 79-87)
for line in result.decode("utf-8").split('\n'):
    if line.startswith("Allow"):
        result_data_set["Allowed"].append(parsed_url)
    elif line.startswith("Disallow"):
        result_data_set["Disallowed"].append(parsed_url)

# Step 3: Return dictionary
return result_data_set  # {"Disallowed": [...], "Allowed": [...]}
```

**Enforcement in crawl() - Line 185:**
```python
# Before fetching any page, check robots.txt
pwd = "/".join(current_page.split("/")[:-1]) + "/"
if pwd not in self.robots_txt["Disallowed"]:
    # Proceed with crawling
else:
    print("Not allowed: " + current_page)  # Line 273
```

**Missing robots.txt Handling - Lines 89-96:**
```python
except urllib.error.HTTPError as e:
    if e.code == 404:
        print("Note: No robots.txt found. Proceeding with no restrictions.")
```

---

### 4.2 HTTP Status Code Handler

**Location:** `WebCrawler.py`, Lines 186-194

| Status | Handling | Code Location |
|--------|----------|---------------|
| **2xx Success** | Process content | Line 194-195 (`else:` block) |
| **4xx Client Error** | Add to broken_urls | Lines 191-193 |
| **5xx Server Error** | Add to broken_urls | Lines 191-193 |

```python
try:
    handle = urllib.request.urlopen(current_page)  # Line 188
except urllib.error.HTTPError as e:                # Line 191
    # 4xx and 5xx errors caught here
    self.broken_urls.append(current_page)          # Line 193
else:
    # 2xx success - process content
    current_content = str(handle.read())           # Line 195
```

**Note:** Redirects (3xx) are handled automatically by urllib.

---

### 4.3 URL Validation (RFC 3986)

**Location:** `WebCrawler.py`, Lines 124-134

**Regex Pattern Breakdown:**
```python
pattern = re.compile(
    r'^(?:http|ftp)s?://'      # Scheme: http, https, ftp, ftps
    r'(?:'
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+' # Subdomain.domain
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)'         # TLD (.com, .co.uk)
        r'|localhost'                                  # OR localhost
        r'|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'        # OR IPv4
    r')'
    r'(?::\d+)?'               # Optional port (:8080)
    r'(?:/?|[/?]\S+)$',        # Path (/page?q=1)
    re.IGNORECASE
)
```

**Valid URLs:**
- `http://example.com`
- `https://sub.domain.co.uk:8080/path?query=1`
- `http://192.168.1.1/page`
- `http://localhost:3000`

**Invalid URLs:**
- `example.com` (no scheme)
- `ftp://` (no host)
- `http://` (incomplete)

---

### 4.4 Domain Scope Controller

**Location:** `WebCrawler.py`, Lines 25, 147-148, 255, 261

```python
# Line 25: Extract domain from seed URL
self.domain_url = "/".join(self.seed_url.split("/")[:3])
# "http://books.toscrape.com/catalogue/page" → "http://books.toscrape.com"

# Lines 147-148: Scope check function
def url_is_within_scope(self, url_string):
    return self.seed_url in url_string

# Line 255: Gate in-scope URLs to frontier
if self.url_is_within_scope(current_url) and current_url not in self.url_frontier:
    self.url_frontier.append(current_url)

# Lines 261-262: Track out-of-scope URLs separately
elif not self.url_is_within_scope(current_url):
    self.outgoing_urls.append(current_url)
```

---

### 4.5 Page Limit Enforcer

**Location:** `WebCrawler.py`, Lines 100-101, 178, 239

```python
# Lines 100-101: Setter
def set_page_limit(self, limit):
    self.page_limit = int(limit)

# Line 178: Enforcement in main loop
while self.url_frontier and \
      (self.page_limit is None or self.num_pages_indexed < self.page_limit):

# Line 239: Counter increment after indexing
self.num_pages_indexed += 1
```

**Flow:**
```
Start → Check: num_pages_indexed < page_limit?
          │
          ├─ Yes → Continue crawling
          │
          └─ No → Exit loop (Line 178 condition fails)
```

---

### 4.6 Stopword Filter

**Location:** `WebCrawler.py`, Lines 104-118, 229-230

```python
# Lines 104-110: Load stopwords
def set_stop_words(self, filepath):
    with open(filepath, "r") as stop_words_file:
        stop_words = stop_words_file.readlines()
    self.stop_words = [x.strip() for x in stop_words]

# Lines 229-230: Apply filter
self.doc_words[current_doc_id] = [w for w in content_words
    if w not in self.stop_words and self.word_is_valid(w)]
```

**Stopwords Include:** a, about, an, are, as, at, be, by, for, from, has, have, in, is, it, of, on, or, that, the, to, was, were, will, with...

---

### 4.7 CSV Exporter

**Location:** `WebCrawler.py` Lines 302-316, `SearchEngine.py` Lines 320-322

```python
# WebCrawler.py print_frequency_matrix()
def print_frequency_matrix(self):
    output_string = ","
    for i in range(len(self.doc_words.keys())):
        output_string += "Doc" + str(i) + ","
    output_string += "\n"

    for i in range(len(self.frequency_matrix)):
        output_string += self.all_terms[i] + "," + \
            ",".join([str(j) for j in self.frequency_matrix[i]]) + "\n"
    return output_string

# SearchEngine.py write to file
f = open("Output/tf_matrix.csv", "w")
f.write(search_engine.print_frequency_matrix())
```

**Output Format:**
```csv
,Doc0,Doc1,Doc2
term1,5,2,0
term2,0,3,1
```

---

### 4.8 Statistics Reporter

**Location:** `WebCrawler.py`, Lines 30-38, 50-65

**Counters:**
```python
# Lines 30-38: Data structures
self.url_frontier = []       # Pending URLs
self.visited_urls = {}       # Visited: URL → (title, hash)
self.outgoing_urls = []      # Off-domain links
self.broken_urls = []        # Failed URLs (4xx, 5xx)
self.graphic_urls = []       # Image files
self.num_pages_crawled = 0   # Total pages visited
self.num_pages_indexed = 0   # Pages with content indexed
```

**Report Generation (Lines 50-65):**
```python
def __str__(self):
    report = "\nPages crawled: " + str(self.num_pages_crawled)
    report += "\nPages indexed: " + str(self.num_pages_indexed)
    report += "\nVisited URLs: " + str(len(self.visited_urls))
    report += "\n\nOutgoing URLs: " + "\n  +  ".join(self.outgoing_urls)
    report += "\n\nBroken URLs: " + "\n  +  ".join(self.broken_urls)
    report += "\n\nGraphic URLs: " + "\n  +  ".join(self.graphic_urls)
    return report
```

---

## 5. Viva Q&A - Code Reference

### Q1: "Explain RFC 9309 and show your implementation"
**A:** `WebCrawler.py`, `get_robots_txt()`, Lines 71-98

**RFC 9309** = Robots Exclusion Protocol. Defines how websites communicate crawling permissions.

```python
# Fetch robots.txt
result = urllib.request.urlopen(self.seed_url + "/robots.txt").read()

# Parse Allow/Disallow directives
for line in result.decode("utf-8").split('\n'):
    if line.startswith("Disallow"):
        result_data_set["Disallowed"].append(url)
```
**Why:** Ethical crawling - respect website owner's wishes.

---

### Q2: "How do you handle HTTP 404 errors?"
**A:** `WebCrawler.py`, Lines 191-193

```python
except urllib.error.HTTPError as e:
    if current_page not in self.broken_urls:
        self.broken_urls.append(current_page)
```
**Why:** Don't retry non-existent pages; track for reporting.

---

### Q3: "Show me URL validation regex"
**A:** `WebCrawler.py`, `url_is_valid()`, Lines 124-134

```python
pattern = re.compile(
    r'^(?:http|ftp)s?://'     # Scheme
    r'(?:...domain pattern...)'
    r'(?::\d+)?'              # Port
    r'(?:/?|[/?]\S+)$',       # Path
    re.IGNORECASE)
```
**RFC 3986:** Validates scheme://authority/path?query#fragment structure.

---

### Q4: "How do you prevent infinite crawling?"
**A:** `WebCrawler.py`, Lines 100-101, 178

```python
# Line 101: Set limit
self.page_limit = int(limit)

# Line 178: Check in loop
while self.url_frontier and self.num_pages_indexed < self.page_limit:
```
**Why:** Resource management - prevents runaway crawler consuming bandwidth.

---

### Q5: "How does robots.txt blocking work?"
**A:** `WebCrawler.py`, Lines 167, 185, 272-273

```python
# Line 167: Fetch robots.txt before crawling
self.robots_txt = self.get_robots_txt()

# Line 185: Check before each fetch
if pwd not in self.robots_txt["Disallowed"]:
    handle = urllib.request.urlopen(current_page)
else:
    print("Not allowed: " + current_page)  # Line 273
```

---

### Q6: "Why filter stopwords?"
**A:** `WebCrawler.py`, Lines 229-230

```python
self.doc_words[current_doc_id] = [w for w in content_words
    if w not in self.stop_words]
```
**Why:**
- Reduces index size (stopwords are 30-50% of text)
- Improves search relevance (stopwords carry no meaning)
- Matches information retrieval best practices

---

### Q7: "How do you keep crawler on the same domain?"
**A:** `WebCrawler.py`, `url_is_within_scope()`, Lines 147-148, 255

```python
def url_is_within_scope(self, url_string):
    return self.seed_url in url_string

# Line 255: Only add in-scope URLs
if self.url_is_within_scope(current_url):
    self.url_frontier.append(current_url)
```
**Why:** Prevents crawler from wandering across the entire internet.

---

### Q8: "What happens if robots.txt doesn't exist?"
**A:** `WebCrawler.py`, Lines 89-92

```python
except urllib.error.HTTPError as e:
    if e.code == 404:
        print("Note: No robots.txt found. Proceeding with no restrictions.")
```
**RFC 9309 compliance:** Missing robots.txt = no restrictions.

---

### Q9: "Show me word validation logic"
**A:** `WebCrawler.py`, `word_is_valid()`, Lines 141-144

```python
def word_is_valid(self, word):
    pattern = re.compile(r'^[a-zA-z](\S*)[a-zA-z0-9]$')
    return bool(pattern.match(word))
```
**Rules:** Must start with letter, end with letter/digit.

---

### Q10: "How do you export crawl data?"
**A:** `WebCrawler.py` Lines 302-316, `SearchEngine.py` Lines 320-322

```python
# Generate CSV string
output = self.print_frequency_matrix()

# Write to file
f = open("Output/tf_matrix.csv", "w")
f.write(output)
```
**Format:** Term-document frequency matrix in CSV.

---

### Q11: "What statistics do you track?"
**A:** `WebCrawler.py`, Lines 37-38, `__str__()` Lines 50-65

| Metric | Variable | Line |
|--------|----------|------|
| Pages crawled | `num_pages_crawled` | 37 |
| Pages indexed | `num_pages_indexed` | 38 |
| Visited URLs | `len(visited_urls)` | 31 |
| Broken URLs | `broken_urls` | 33 |
| Outgoing URLs | `outgoing_urls` | 32 |
| Graphic URLs | `graphic_urls` | 34 |

---

### Q12: "Explain ethical crawling practices in your code"
**A:** Three-layer protection:

1. **RFC 9309 Compliance** (Lines 71-98, 185): Respect robots.txt
2. **Domain Scope** (Lines 147-148): Don't crawl other sites
3. **Page Limits** (Lines 100-101, 178): Don't overload servers

---

## 6. RFC Compliance Summary

### RFC 9309 - Robots Exclusion Protocol

| Requirement | Implementation | Location |
|-------------|----------------|----------|
| Fetch /robots.txt | `urlopen(seed_url + "/robots.txt")` | Line 76 |
| Parse User-agent | Not implemented (assumes `*`) | - |
| Parse Disallow | `line.startswith("Disallow")` | Line 84 |
| Parse Allow | `line.startswith("Allow")` | Line 80 |
| Handle 404 | Return empty restrictions | Lines 89-92 |
| Check before fetch | `if pwd not in Disallowed` | Line 185 |

### RFC 3986 - URI Generic Syntax

| Component | Regex Pattern | Line |
|-----------|---------------|------|
| Scheme | `^(?:http|ftp)s?://` | 126 |
| Host (domain) | `[A-Z0-9](?:[A-Z0-9-]{0,61}...` | 127-128 |
| Host (IP) | `\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}` | 129 |
| Port | `(?::\d+)?` | 130 |
| Path | `(?:/?|[/?]\S+)$` | 131 |

### HTTP Status Codes (RFC 7231)

| Code Class | Meaning | Handling | Location |
|------------|---------|----------|----------|
| 2xx | Success | Process content | Line 194-195 |
| 3xx | Redirect | Automatic (urllib) | - |
| 4xx | Client Error | Add to broken_urls | Line 193 |
| 5xx | Server Error | Add to broken_urls | Line 193 |

---

## 7. CN Concepts Summary

| Concept | My Implementation | Location |
|---------|-------------------|----------|
| **Application Layer Protocol** | HTTP status handling | Lines 186-194 |
| **Protocol Standards** | RFC 9309 (robots.txt) | Lines 71-98 |
| **Protocol Standards** | RFC 3986 (URI syntax) | Lines 124-134 |
| **Network Fault Tolerance** | Error handling, broken URL tracking | Lines 89-96, 191-193 |
| **Resource Management** | Page limit enforcement | Lines 100-101, 178 |
| **Ethical Crawling** | robots.txt respect | Lines 185, 272-273 |
| **Data Quality** | Stopword filtering, word validation | Lines 141-144, 229-230 |
| **Persistence** | CSV export for analysis | Lines 302-316 |

---

## 8. Edge Case Handling

| Edge Case | Handled At | Code |
|-----------|------------|------|
| **Missing robots.txt** | Lines 89-92 | `if e.code == 404: print("No robots.txt...")` |
| **Invalid URLs** | Lines 124-134, 252 | `if self.url_is_valid(url)` |
| **HTTP 4xx errors** | Lines 191-193 | `self.broken_urls.append(current_page)` |
| **HTTP 5xx errors** | Lines 191-193 | `self.broken_urls.append(current_page)` |
| **Off-domain URLs** | Lines 255, 261-262 | `self.outgoing_urls.append(current_url)` |
| **Duplicate URLs** | Line 258 | `if current_url not in self.visited_urls` |
| **Empty content** | Line 195 | `current_content = str(handle.read())` |
| **Missing title** | Line 201 | `if soup.title is not None else filename` |
| **Graphic files** | Lines 269-270 | `self.graphic_urls.append(current_page)` |
| **robots.txt fetch error** | Lines 95-96 | `except Exception as e: print(...)` |

---

## Quick Reference Card

```
┌────────────────────────────────────────────────────────────────┐
│                    MEERAN'S CODE LOCATIONS                     │
├────────────────────────────────────────────────────────────────┤
│ robots.txt Parser        WebCrawler.py:71-98                  │
│ robots.txt Enforcement   WebCrawler.py:185                    │
│ HTTP Error Handler       WebCrawler.py:191-193                │
│ URL Validator (RFC3986)  WebCrawler.py:124-134                │
│ Domain Scope Check       WebCrawler.py:147-148                │
│ Page Limit Setter        WebCrawler.py:100-101                │
│ Page Limit Check         WebCrawler.py:178                    │
│ Stopword Loader          WebCrawler.py:104-118                │
│ Stopword Filter          WebCrawler.py:229-230                │
│ Word Validator           WebCrawler.py:141-144                │
│ CSV Exporter             WebCrawler.py:302-316                │
│ Statistics Reporter      WebCrawler.py:50-65                  │
│ Counters                 WebCrawler.py:37-38                  │
└────────────────────────────────────────────────────────────────┘
```

---

*Concise Viva Reference - Meeran Uz Zaman (23K-0039)*
*CS3001 Computer Networks | December 2025*
