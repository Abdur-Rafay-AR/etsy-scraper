from requests.exceptions import RequestException
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import cloudscraper
import json
import csv
import time
import random
import logging
import os
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger()

page_num = 0

options = uc.ChromeOptions()

    # General options
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")
options.add_argument("--disable-infobars")

profile_path = os.path.join(os.getcwd(), "User Data")
os.makedirs(profile_path, exist_ok=True)

# User profile settings
options.add_argument("--user-data-dir=" + profile_path)
options.add_argument("--profile-directory=Profile sel")

driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 10)

url = "https://app.everbee.io/"
driver.get(url)

# Wait for page to load fully
time.sleep(2)  # Adjust as needed or use WebDriverWait for better control

# Get cookies and convert to dictionary
cookies_list = driver.get_cookies()
cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies_list}

# print(cookies_dict) 

# Print or use the cookies dictionary
everBeeToken = cookies_dict.get('everbeeToken')

if everBeeToken:
    logger.info("EverBee token retrieved successfully.")
else:
    input("Not logged in to everbee. Please login manually and then press enter...")
    cookies_list = driver.get_cookies()
    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies_list}

# Print or use the cookies dictionary
everBeeToken = cookies_dict.get('everbeeToken')

# Initialize the scraper
scraper = cloudscraper.CloudScraper()  # Returns a requests.Session object

# Define headers for the requests
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'dnt': '1',
    'downlink': '10',
    'dpr': '1.25',
    'ect': '4g',
    'priority': 'u=0, i',
    'rtt': '150',
    'sec-ch-dpr': '1.25',
    'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    'sec-ch-ua-arch': '"x86"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version-list': '"Chromium";v="136.0.7103.92", "Google Chrome";v="136.0.7103.92", "Not.A/Brand";v="99.0.0.0"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"15.0.0"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'sec-gpc': '1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
}

def get_links_from_page(page,base_url):
    soup = BeautifulSoup(page, "lxml")
    links = []
    for link in soup.find_all('a', href=True):
        # print(link)
        href = link['href']
        if href.startswith('http'):
            links.append(href)
        else:
            if base_url:
                full_url = base_url + href
                links.append(full_url)
    return links

def make_request_with_retry(url, max_retries=5, initial_delay=120, headers=None, is_json=False):
    """Make a request with retry logic for handling rate limits"""
    retry_count = 0
    delay = initial_delay

    while retry_count < max_retries:
        try:
            logger.info(f"Requesting: {url}")
            response = scraper.get(url, headers=headers)
            
            # Check if we've been rate limited
            if "too many requests" in response.text.lower() or response.status_code == 429:
                retry_count += 1
                wait_time = delay + random.uniform(5, 20)  # Reduced randomness
                logger.warning(f"Rate limited. Retry {retry_count}/{max_retries}. Waiting {wait_time:.2f} seconds.")
                time.sleep(wait_time)
                delay *= 1.5  # Exponential backoff
                continue
            
            try:
                return response.json()
            except Exception as e:
                return response
            
        except RequestException as e:
            retry_count += 1
            wait_time = delay + random.uniform(5, 20)
            logger.error(f"Request error: {e}. Retry {retry_count}/{max_retries}. Waiting {wait_time:.2f} seconds.")
            time.sleep(wait_time)
            delay *= 1.5
    
    logger.error(f"Failed to get {url} after {max_retries} retries")
    raise Exception(f"Failed to get {url} after {max_retries} retries")

def extract_deepest_urls(data):
    results = {}
    
    # Process each main category
    for main_category in data:
        category_name = main_category["category"]
        results[category_name] = []
        
        # Find all deepest URLs in this main category
        find_deepest_urls(main_category, results[category_name])
    
    return results

def find_deepest_urls(category, result_list):
    # If this category has no subcategories or empty subcategories, it's a leaf node
    if "subcategories" not in category or not category["subcategories"]:
        result_list.append({
            "name": category.get("name", category.get("category", "")),
            "url": category["url"]
        })
    else:
        # If it has subcategories, recursively search them
        for subcategory in category["subcategories"]:
            find_deepest_urls(subcategory, result_list)

# Load the JSON data
with open("category_m.json", "r") as file:
    json_data = json.load(file)

# Extract the deepest URLs
deepest_urls_by_category = extract_deepest_urls(json_data)

# Flatten the deepest URLs into a single list for processing
urls_json = []
for category, url_list in deepest_urls_by_category.items():
    for url_info in url_list:
        if "url" in url_info:
            urls_json.append(url_info["url"])

def get_shop_data(shop_name):
    api_headers = {
        'accept': 'application/json',
        'accept-language': 'en-US,en;q=0.9',
        'origin': 'https://app.everbee.io',
        'priority': 'u=1, i',
        'referer': 'https://app.everbee.io/',
        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'x-access-token': everBeeToken,
    }

    try:
        response = make_request_with_retry(
            f'https://api.everbee.com/shops/{shop_name}', 
            headers=api_headers, 
            is_json=True,
            initial_delay=30  # Reduced from 60
        )
        
        avg_product_price = response.get("average_listing_price", 0)
        monthly_revenue = response.get("revenue_30_days", 0)


        return avg_product_price, monthly_revenue
    except Exception as e:
        logger.error(f"Error fetching shop data for {shop_name}: {e}")
        return 0, 0

def extract_sales_number(shop_soup):

    link_containers = shop_soup.find_all('div', class_=['wt-mb-xs-2', 'wt-text-body-01', 'wt-mr-md-6'])

    urls = []

    if link_containers:
        for container in link_containers:

            link = container.find('a')
            if link:
                url = link.get('href')

                label = link.get('aria-label')
                
                span_text = link.find('span')
                if span_text and span_text.string:
                    label = span_text.string.strip()
                # Add to our results if we found a URL
                if url and label:
                    urls.append(url)
    else:
        print("No divs with the specified class combination found.")

    urls = urls[:-1]
    
    # Extract sales number
    sales_element = shop_soup.select_one('.wt-text-caption.wt-no-wrap')
    if sales_element:
        sales_text = sales_element.text.strip()
        sales_number = int(''.join(filter(str.isdigit, sales_text)))
    else:
        sales_number = 0
        
    return sales_number, urls
def extract_shop_names(response_text):
    soup = BeautifulSoup(response_text, 'lxml')
    script_tags = soup.find_all('script', type='application/ld+json')
    shop_names = set()

    for script in script_tags:
        try:
            data = json.loads(script.text)
            if isinstance(data, dict):
                if data.get('@type') == 'ItemList':
                    items = data.get('itemListElement', [])
                    for item in items:
                        if isinstance(item, dict) and 'brand' in item:
                            brand = item.get('brand', {})
                            if isinstance(brand, dict) and 'name' in brand:
                                shop_names.add(brand['name'])
                elif data.get('@type') == 'Product' and 'brand' in data:
                    brand = data.get('brand', {})
                    if isinstance(brand, dict) and 'name' in brand:
                        shop_names.add(brand['name'])
        except Exception as e:
            print(e)
            input("Error parsing JSON data. Press Enter to continue...")
            continue
    return sorted(shop_names)

def write_to_backup_csv(shop_data,backup_file='shop_data.csv'):
    """Write a single shop data row to a backup CSV file"""
    file_exists = os.path.isfile(backup_file)
    
    with open(backup_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write header if file doesn't exist
        if not file_exists:
            writer.writerow(['Shop Name', 'Shop URL', 'Sales Number', 'Average Product Price', 'Monthly Revenue', 'Phone', 'Email'])
        
        # Write the shop data
        writer.writerow(shop_data)
        
def load_from_backup_csv(backup_file='shop_data.csv'):
    """Load already processed shop data from backup CSV"""
    processed_shops = set()

    try:
    
        if os.path.isfile(backup_file):
            with open(backup_file, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    if row and len(row) > 0:
                        processed_shops.add(row[0])  # Add shop name to processed set
            
            logger.info(f"Loaded {len(processed_shops)} already processed shops from backup")

    except Exception as e:
        print(e)
    
    return processed_shops

def scrape_contact_info(urls):
    
    

    # scraper = cloudscraper.CloudScraper()

    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = phone_pattern = r'\+\d{1,3}(?:[\s\-]?\d{2,4}){3,5}'

    links = []
    emails = []
    phone_numbers = []

    for url in urls:

        if "etsy" in url:
            continue

        if "instagram" in url:
            driver.get(url)


            _emails = re.findall(email_pattern, driver.page_source)
            _phones = re.findall(phone_pattern, driver.page_source)

            phone_numbers.extend([''.join(t).strip() for t in _phones if any(t)])

            emails.extend(_emails)
            try:    
                wait.until(EC.visibility_of_element_located((
                    By.CSS_SELECTOR, '._ap3a _aaco _aacw _aacz _aada _aade'.replace(" ", ".")
                ))).click()

                element = wait.until(EC.visibility_of_element_located((
                    By.CSS_SELECTOR, '.x1n2onr6 xzkaem6'.replace(" ", ".")
                ))).find_elements(By.CSS_SELECTOR, ".x1lliihq x193iq5w x6ikm8r x10wlt62 xlyipyv xuxw1ft".replace(" ", "."))
            except:
                element = driver.find_elements(By.CSS_SELECTOR, 'x1lliihq x193iq5w x6ikm8r x10wlt62 xlyipyv xuxw1ft'.replace(" ", "."))
            
            links.extend(["https://"+x.text if "." in x.text and not x.text.startswith("http") else x.text for x in element if "." in x.text and "etsy" not in x.text])

        elif "facebook" in url:
            driver.get(url)


            _emails = re.findall(email_pattern, driver.page_source)
            _phones = re.findall(phone_pattern, driver.page_source)

            phone_numbers.extend([''.join(t).strip() for t in _phones if any(t)])

            emails.extend(_emails)
            
            wait.until(EC.visibility_of_element_located((
                By.CSS_SELECTOR, '.x9f619 x1ja2u2z x78zum5 x2lah0s x1n2onr6 x1qughib x1qjc9v5 xozqiw3 x1q0g3np x1pi30zi x1swvt13 xyamay9 xykv574 xbmpl8g x4cne27 xifccgj'.replace(" ", ".")
            )))

            element = driver.find_elements(By.CSS_SELECTOR, ".x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen xo1l8bm x1qq9wsj x1yc453h".replace(" ", "."))

            links.extend(["https://"+x.text if "." in x.text and not x.text.startswith("http") else x.text for x in element if "." in x.text and "etsy" not in x.text])


        elif "pinterest" in url:
            driver.get(url)

            _emails = re.findall(email_pattern, driver.page_source)
            _phones = re.findall(phone_pattern, driver.page_source)

            phone_numbers.extend([''.join(t).strip() for t in _phones if any(t)])

            emails.extend(_emails)
            try:    
                wait.until(
                    EC.presence_of_element_located((By.XPATH, "//span[text()='more']"))
                ).click()

                element = driver.find_elements(By.CSS_SELECTOR, ".X8m zDA IZT eSP dyH llN Kv8".replace(" ", "."))
            except:
                element = driver.find_elements(By.CSS_SELECTOR, "Jea jX8 zI7 iyn Hsu".replace(" ", "."))

            links.extend(["https://"+x.text if "." in x.text and not x.text.startswith("http") else x.text for x in element if "." in x.text and "etsy" not in x.text])
            
        elif "x.com" in url:
            driver.get(url)

            _emails = re.findall(email_pattern, driver.page_source)
            _phones = re.findall(phone_pattern, driver.page_source)

            phone_numbers.extend([''.join(t).strip() for t in _phones if any(t)])

            emails.extend(_emails)

            try:    

                element = driver.find_elements(By.CSS_SELECTOR, "css-175oi2r r-1adg3ll r-6gpygo".replace(" ", "."))
            except:
                pass
            links.extend(["https://"+x.text if "." in x.text and not x.text.startswith("http") else x.text for x in element if "." in x.text and "etsy" not in x.text])
                        
        elif "tiktok" in url:
            continue       
        else:
            r = scraper.get(url)
            soup = BeautifulSoup(r.text, "lxml")
            if "facebook.com/tr" in r.text:
                continue
            links2 = [x['href'] if x['href'].startswith("http") else url+x['href'] for x in soup.findAll("a") if x.get("href") != None and ("contact" in x['href'] or "about" in x['href'])]
            links.extend(links2)

            _emails = re.findall(email_pattern, driver.page_source)
            _phones = re.findall(phone_pattern, driver.page_source)

            phone_numbers.extend([''.join(t).strip() for t in _phones if any(t)])

        if len(emails):
            break

    checkedUrls = []
    
    while len(links) and not len(emails):
        if not len(emails) and len(links):
            for link in links:
                
                r = scraper.get(link)
                soup = BeautifulSoup(r.text, "lxml")

                linksTemp = [x['href'] for x in soup.findAll("a") if x.get("href") != None and ("contact" in x['href'] or "about" in x['href']) and link not in x['href']]
                linksTemp = [x for x in linksTemp if x not in checkedUrls]
                checkedUrls.extend(linksTemp)
                linksTemp = [x if x.startswith("http") else link+x for x in linksTemp]

                _emails = re.findall(email_pattern, soup.text)
                _phones = re.findall(phone_pattern, soup.text)

                phone_numbers.extend([''.join(t).strip() for t in _phones if any(t)])
                emails.extend(_emails)
                
                if len(emails):
                    break

                if len(linksTemp):
                    links = linksTemp

            if not len(linksTemp):
                break

    emails = list(set(emails))
    phone_numbers = list(set(phone_numbers))

    # driver.quit()
    res = {
        "phone": ", ".join(phone_numbers).strip(),
        "email": ", ".join(emails).strip(),
    }
    return res

def main(choice):
    global page_num
    try:
        backup_file = "shop_data.csv"

        # Load already processed shops from backup
        processed_shops = load_from_backup_csv(backup_file)
        
        # Open a CSV file to store the data
        with open('shop_data.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Shop Name', 'Shop URL', 'Sales Number', 'Average Product Price', 'Monthly Revenue', 'Phone', 'Email'])

            # Process each URL from the deep category extraction
            for url_index, url in enumerate(urls_json):

                try:
                    logger.info(f"Processing category URL {url_index+1}/{len(urls_json)}: {url}")

                    while True:
                        try:   
                            page_num += 1
                            if "?page=" not in url:
                                url = url+f"?page={page_num}"
                            # Fetch the page for this category URL with retry logic
                            response = make_request_with_retry(url, headers=headers)
                            
                            # Extract shop names from this page
                            shop_names = extract_shop_names(response.text)
                            logger.info(f"Found {len(shop_names)} shops in category URL: {url}")
                            
                            # Iterate through the shop names and fetch sales data
                            for index, shop_name in enumerate(shop_names):
                                try:
                                    # Skip if already processed
                                    if shop_name in processed_shops:
                                        logger.info(f"Skipping already processed shop: {shop_name}")
                                        continue

                                    shop_url = f'https://www.etsy.com/shop/{shop_name}'
                                    logger.info(f"Processing shop {index+1}/{len(shop_names)} from URL {url_index+1}/{len(urls_json)}: {shop_name}")
                                
                                    # Reduced random delay between requests
                                    time.sleep(random.uniform(1, 3))
                                    
                                    avg_product_price, monthly_revenue = get_shop_data(shop_name)
                                    
                                    # Skip if monthly revenue is less than 5000
                                    if monthly_revenue < 5000:
                                        continue

                                    time.sleep(random.uniform(1, 3))
                                    
                                    shop_response = make_request_with_retry(shop_url, headers=headers)
                                    shop_soup = BeautifulSoup(shop_response.content, 'lxml')

                                    sales_number, extracted_urls = extract_sales_number(shop_soup)

                                    contact_info = scrape_contact_info(extracted_urls)
                                    if contact_info['email'] == "your-email@example.com":
                                        continue
                                    # Prepare shop data row with contact info and without category URL
                                    shop_data_row = [
                                        shop_name, 
                                        shop_url, 
                                        sales_number, 
                                        avg_product_price, 
                                        monthly_revenue, 
                                        contact_info['phone'], 
                                        contact_info['email']
                                    ]
                                    print(shop_data_row)
                                    if choice == "1":
                                        if contact_info['email'] ==  "":
                                            continue
                                    elif choice == "2":
                                        if contact_info['phone'] ==  "":
                                            continue
                                    elif choice == "3":
                                        if contact_info['phone'] == "" or contact_info['email'] == "":
                                            continue
                                    elif choice == "4":
                                        if contact_info['phone'] == "" and contact_info['email'] == "":
                                            continue

                                    # Write shop details to the main CSV file
                                    writer.writerow(shop_data_row)
                                    
                                    # Write to backup CSV after each shop is processed
                                    write_to_backup_csv(shop_data_row,backup_file)
                                    
                                    # Add to processed shops
                                    processed_shops.add(shop_name)
                                    
                                    logger.info(f"Successfully processed {shop_name}")
                                    
                                    # Reduced break every 5 shops
                                    if (index + 1) % 5 == 0:
                                        wait_time = random.uniform(3, 8)
                                        logger.info(f"Taking a break for {wait_time:.2f} seconds after processing 5 shops")
                                        time.sleep(wait_time)
                                        
                                except Exception as e:
                                    logger.error(f"Error processing shop {shop_name}: {e}")
                                    with open ('unprocessed_shops.txt', 'a') as file:
                                        file.write(f"{shop_name}\n")
                                    pass
                            
                            # Reduced break after processing all shops from one category URL
                            category_wait_time = random.uniform(10, 20)
                            logger.info(f"Taking a longer break for {category_wait_time:.2f} seconds after processing URL: {url}")
                            time.sleep(category_wait_time)

                        except RequestException as e:
                            print("No more pages to process for this URL:",e)
                            page_num = 0
                            break    

                except Exception as e:
                    logger.error(f"Error processing category URL {url}: {e}")
                    
        
        logger.info("Scraping completed successfully")
        
    except Exception as e:
        logger.error(f"Main process error: {str(e)}")
        print(f"Main process error: {str(e)}")

if __name__ == "__main__":
    print("===================================")
    print("          Etsy Scraper Menu        ")
    print("===================================")
    print("Etsy Scraper:")
    print("1. Extract if email")
    print("2. Extract if phone number")
    print("3. Extract if email and phone number")
    print("4. Extract if email or phone number")
    print("===================================")
    choice = input("Enter your choice (1-4): ")

    main(choice)