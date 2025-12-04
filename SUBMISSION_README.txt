================================================================================
           WEB CRAWLER & SEARCH ENGINE SYSTEM
           CS3001 - Computer Networks Project
           FAST School of Computing, NUCES Karachi
           Fall 2025
================================================================================

TEAM MEMBERS
------------
- Huzaifa Abdul Rehman (23K-0782)
- Meeran uz Zaman (23K-0039)
- Abdul Moiz Hossain (23K-0553)


PROJECT STRUCTURE
-----------------
Web-Crawler/
├── SearchEngine.py          # Main program (search engine + crawler)
├── WebCrawler.py           # Core web crawler module
├── test_crawler.py         # Quick testing script
├── setup.py                # Installation configuration
├── README.md               # Complete project documentation
├── SUBMISSION_README.txt   # This file
├── .gitignore             # Git ignore rules
├── Input/
│   ├── stopwords.txt       # Stop words list
│   └── thesaurus.csv       # Query expansion thesaurus
└── Output/
    └── README.txt          # Output directory description


HOW TO RUN
----------
1. Install Python 3.9+ (tested with Python 3.13)

2. Install dependencies:
   pip install beautifulsoup4 lxml scikit-learn nltk numpy

3. Download NLTK data:
   python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"

4. Run the program:
   python SearchEngine.py

   OR with custom parameters:
   python SearchEngine.py -u "http://books.toscrape.com" -p 10


QUICK TEST
----------
To verify the crawler works:
   python test_crawler.py

This will crawl 5 pages from books.toscrape.com and verify functionality.


NETWORKING FEATURES IMPLEMENTED
--------------------------------
1. HTTP/HTTPS Protocol Implementation
   - HTTP GET requests via urllib
   - HTTP status code handling (200, 404, 403, 500)
   - Request/response cycle management

2. Robots.txt Protocol (RFC 9309)
   - Fetch and parse robots.txt files
   - Enforce Allow/Disallow rules
   - Ethical crawling compliance

3. URL Handling (RFC 3986)
   - URL normalization (relative to absolute)
   - URL validation with regex
   - Scheme, host, port, path parsing

4. Network Error Handling
   - HTTP error exception handling
   - Timeout management
   - Graceful degradation

5. Client-Server Architecture
   - HTTP client implementation
   - Request-response model
   - Stateless connection management


SEARCH ENGINE FEATURES
-----------------------
- BFS (Breadth-First Search) crawling algorithm
- SHA-256 content hashing for duplicate detection
- TF-IDF (Term Frequency-Inverse Document Frequency) ranking
- Cosine similarity for document relevance
- Porter Stemming for word normalization
- Thesaurus-based query expansion
- BeautifulSoup HTML parsing
- Pickle serialization for index persistence


RECOMMENDED TEST WEBSITES
--------------------------
1. http://books.toscrape.com (Best for demo)
2. http://quotes.toscrape.com
3. http://example.com


DOCUMENTATION
-------------
For complete documentation, see README.md


================================================================================
Built for CS3001 - Computer Networks
FAST School of Computing, NUCES Karachi
================================================================================
