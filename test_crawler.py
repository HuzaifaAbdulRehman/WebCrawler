"""
Quick test script to verify the crawler works with books.toscrape.com
"""
from SearchEngine import SearchEngine

# Create search engine with books.toscrape.com
search_engine = SearchEngine("http://books.toscrape.com")
search_engine.set_page_limit(5)
search_engine.set_stop_words("Input/stopwords.txt")
search_engine.set_thesaurus("Input/thesaurus.csv")

print("Testing crawler with http://books.toscrape.com")
print("Page limit: 5")
print("\nStarting crawl...\n")

# Run the crawl
search_engine.crawl()

print("\n" + "="*70)
print("CRAWL COMPLETE!")
print("="*70)
print(f"Pages crawled: {search_engine.num_pages_crawled}")
print(f"Pages indexed: {search_engine.num_pages_indexed}")
print(f"Unique terms found: {len(search_engine.all_terms) if search_engine.all_terms else 0}")

if search_engine.num_pages_indexed > 0:
    print("\n[SUCCESS] The crawler is working correctly!")
else:
    print("\n[FAILURE] No pages were indexed.")
