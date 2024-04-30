import re
import time

from urllib.parse import urlparse, urljoin

import nltk
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from collections import Counter


def scraper(url, resp):
    links = extract_next_links(url, resp)
    unique_page_count = count_unique_pages(links)
    subdomains_count = count_subdomains(links)
    longest_page, max_word_count, tokens = largest_page(links)
    fifty_common_words = common_words(tokens)

    print(f"There are {unique_page_count} unique pages.")
    print(f"The longest page in terms of words is {longest_page}, with {max_word_count} words.")
    print("The 50 most common words in the entire set of pages are: ", fifty_common_words)
    print(f"There are {subdomains_count} subdomains in the ics.uci.edu domain")

    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    extracted_urls = []
    # Check if the response is valid
    if resp.status != 200 or (is_valid(resp.url) == False):
        # Print out the error message
        print("Error:", resp.status, resp.error)
        return []
    else:
        if (not is_dead_url(resp) and
                not detect_and_avoid_large_files(resp) and
                not detect_and_avoid_infinite_traps(resp) and
                not detect_and_avoid_repeated_patterns(resp.url)):
            try:
                check_politeness(url)

                # Parse the content and extract links
                parsed_content = parse_content(resp.raw_response.content)

                # Identify high textual information content
                if check_content_length(parsed_content):
                    # Get URLs
                    urls = get_all_hyperlinks(parsed_content)

                    # Normalize and filter the URLs
                    for extracted_url in urls:
                        normalized_url = normalize_url(url, extracted_url)
                        if should_follow_url(normalized_url):
                            extracted_urls.append(normalized_url)

                    # Return the parsed content
                    return extracted_urls

            except Exception as e:
                print("Error:", e)
                return []
        else:
            return []

def is_dead_url(resp):
    if len(resp.raw_response.content) == 0:
        return True
    else:
        return False


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        elif not re.match(
                r".*.(ics|cs|informatics|stat)"
                + r".uci.edu$", parsed.hostname.lower()):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def parse_content(content):
    # Parse the HTML content using BeautifulSoup
    parsed_content = BeautifulSoup(content, 'html.parser')
    return parsed_content

def get_all_hyperlinks(parsed_content):
    extracted_urls = []
    for link in parsed_content.find_all('a', href = True):
        href = link.get('href')
        extracted_urls.append(href)
    return extracted_urls

def normalize_url(base_url, extracted_url):
    # Resolve relative URLs to absolute URLs
    absolute_url = urljoin(base_url, extracted_url)
    # Remove fragments
    parsed_url = urlparse(absolute_url)
    normalized_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
    return normalized_url

def should_follow_url(url):
    parsed_url = urlparse(url)
    # Follow only URLs that start with "http" or "https"
    return parsed_url.scheme in {"http", "https"} # to be adjusted if there are specific requirements added

def count_unique_pages(crawled_urls):
    '''How many unique pages did you find?'''
    unique_urls = set() # Use a set to store unique URLs
    for url in crawled_urls:
        # Remove fragment part from the URL
        url_without_fragment = url.split("#")[0]
        unique_urls.add(url_without_fragment)

    return len(unique_urls)

def largest_page(pages):
    '''What is the longest page in terms of the number of words?'''
    max_words = 0
    longest_page = None
    tokens = []

    for page in pages:
        # Extract text
        text = page.get_text(separator=' ')
        # Tokenize the text to count words
        num_words = len(nltk.word_tokenize(text)) # count the number of words
        # Save all words in a list
        tokens.append(nltk.word_tokenize(text))
        # Update if the current page is larger
        if num_words > max_words:
            max_words = num_words
            longest_page = page

    return longest_page, max_words, tokens

def common_words(tokens):
    '''What are the 50 most common words?'''
    # Remove punctuation
    tokens = [word.lower() for word in tokens if word.isalnum()]
    # Remove English stop words
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word not in stop_words]
    # Count word frequencies
    word_freq = Counter(filtered_tokens)
    # Find the 50 most common words
    most_common_words = word_freq.most_common(50)

    return most_common_words

def count_subdomains(crawled_urls):
    '''How many subdomains did you find in the ics.uci.edu domain?'''
    subdomain_count = 0 # initialize the subdomain_count
    for url in crawled_urls: # iterate through the parameters
        parsed_url = urlparse(url)
        seperated_subdomain = parsed_url.netloc # .netloc is to get the net location of the subdomain
        domain_parts = seperated_subdomain.split(".") # split the domain by parts
        if len(domain_parts) > 2 and domain_parts[-2] == "uci" and domain_parts[-1] == "edu": # making sure that's a subdomain
            subdomain_count += 1 # increment the count

    return subdomain_count

def detect_and_avoid_large_files(resp):
    '''Detect and avoid crawling very large files, especially if they have low information value'''
    max_file_size = 10 * 1024 * 1024 #set the max file size to 10MB
    url_content_length = len(resp.raw_response.content)
    if url_content_length > max_file_size:
        return True
    return False

def detect_and_avoid_infinite_traps(resp):
    '''Detect and avoid infinite traps'''
    # Store urls in a dict
    visited_urls = {}
    url = resp.url
    # Check visited time
    if url in visited_urls:
        visited_urls[url] += 1
        # Consider the url an infinite trap if visit count exceeds three times
        if visited_urls[url] >= 3:
            return True
    else:
        # Add the URL to visited_urls dict
        visited_urls[url] = 1

    # Check response time
    start_time = time.time()
    # Consider the url an infinite trap if wait more than 20 secs
    while time.time() - start_time < 20:
        if resp.status == 200:
            return False
    return True

def detect_and_avoid_repeated_patterns(url):
    '''You should write simple automatic trap detection systems based on repeated URL patterns'''
    # Store patterns in a set
    url_patterns = set()
    # If the same URL pattern appears more than once we will say it is a trap
    if url in url_patterns:
        return True
    else:
        url_patterns.add(url)
        return False

last_time_visit = {}
def check_politeness(url, delay=0.5):
    domain = url.netloc # uci.edu
    current_time = time.time()
    if domain in last_time_visit: # check if domain has been visited before.
        time_since_last_visit = current_time - last_time_visit[domain]
        if time_since_last_visit < delay:    # if last vist  less than the required politeness, should wait
            time_to_wait = delay - time_since_last_visit
            time.sleep(time_to_wait)    # wait for politeness
    last_time_visit[domain] = time.time() # store the last time vist again



# Crawl all pages with high textual information content
def check_content_length(parsed_content):
    '''1) We decided 300 tokens for the minimum amount of text a
          page should contain to be considered valuable.'''
    text = parsed_content.get_text(separator = ' ') # Extract content
    num_words = len(nltk.word_tokenize(text))  # Count the number of words
    if num_words > 300:
        return True
    return False