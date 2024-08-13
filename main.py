import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import os
import random
import time
import logging
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(filename='web_scraper_errors.log', level=logging.ERROR, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Function to generate URLs
def url_get(x):
    return f'https://zoma.to/r/{x}'

urls = [url_get(x) for x in range(7500, 100000)]

# Function to validate URLs
def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

# Function to process each URL
def process_url(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
    retries = 3
    backoff_factor = 2  # Exponential backoff factor

    if not is_valid_url(url):
        logging.error(f"Invalid URL: {url}")
        return url, None, None

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.title.text.strip() if soup.title else 'No Title'
                
                # Find phone numbers
                phone_number_tags = soup.find_all('p', attrs={'color': '#FF7E8B'})
                phone_numbers = [tag.text.strip() for tag in phone_number_tags if tag.text.strip()]

                if phone_numbers:
                    return url, title, phone_numbers
                else:
                    print(f"No phone number found for {url}")
                    return url, title, []
            else:
                print(f"Failed to retrieve {url}, status code: {response.status_code}")
        except requests.RequestException as e:
            logging.error(f"Error with {url} on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                sleep_time = backoff_factor ** attempt
                time.sleep(sleep_time + random.uniform(0, 1))  # Exponential backoff with jitter
    return url, None, None  # Return None values if all retries fail

# Main logic to run the processing in parallel and write results to a CSV
def main():
    filename = 'webpage_data.csv'
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        if not file_exists:
            csvwriter.writerow(['URL', 'Title', 'Phone Number'])

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(process_url, url): url for url in urls}
            for future in as_completed(future_to_url):
                try:
                    url, title, phone_numbers = future.result()
                    if title and phone_numbers:
                        for number in phone_numbers:
                            csvwriter.writerow([url, title, number])
                        print(f"Data for {url} appended to {filename}")
                    else:
                        print(f"No data found for {url}")
                except Exception as e:
                    logging.error(f"Error processing {future_to_url[future]}: {e}")

if __name__ == "__main__":
    main()
