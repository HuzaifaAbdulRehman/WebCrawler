from setuptools import setup

setup(
    name='Web-Crawler-Search-Engine',
    version='2.0',
    packages=[],
    url='https://github.com/HuzaifaAbdulRehman/WebCrawler',
    license='Educational Project',
    author='Huzaifa Abdul Rehman, Meeran uz Zaman, Abdul Moiz Hossain',
    author_email='23k0782@nu.edu.pk',
    description='Intelligent Web Crawler and Search Engine - CS3001 Computer Networks Project',
    long_description='A comprehensive web crawler and search engine implementing HTTP/HTTPS protocols, '
                     'robots.txt compliance, TF-IDF ranking, and network data management.',
    install_requires=[
        'beautifulsoup4>=4.9.0',
        'lxml>=4.6.0',
        'nltk>=3.5',
        'scikit-learn>=0.24.0',
        'numpy>=1.19.0',
        'bs4'
    ],
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Education',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: System :: Networking',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    keywords='web-crawler search-engine http network protocols tfidf nlp',
)
