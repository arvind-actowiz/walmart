from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.database import DatabaseManager
from core.config import DB_CONFIG
from core.driver_setup import get_driver
from bs4 import BeautifulSoup
import json
import re
import urllib


def extract_size(title):
    # Patterns to match common size formats (oz, fl oz, lb, etc.)
    patterns = [
        r'(\d+\.?\d*)\s*(?:fl\s*)?oz',  # matches "6 oz", "15.8 oz", "17 fl oz"
        r'(\d+)\s*lb',                   # matches "2 lb"
        r'(\d+)\s*g',                    # matches "500 g"
        r'(\d+)\s*ml',                   # matches "250 ml"
        r'(\d+)\s*l',                    # matches "1 l"
        r'Pack of (\d+)',                # matches "Pack of 4"
    ]

    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(0)

    return ''


def fill_product_data(pd: dict) -> dict:
    """Fill product_data dictionary with information from pageContext"""
    product_data = {
        "item_id": None,
        "upc": None,
        "product_id": None,
        "url": "",
        "name": "",
        "categories": [],
        "image": "",
        "store_id": None,
        "store_location": "",
        "price": None,
        "mrp": None,
        "discount": None,
        "availability": "",
        "keyword": "",
        "size": ""
    }

    # Fill in the fields
    product_data["item_id"] = pd['usItemId']
    product_data["upc"] = pd["upc"]
    product_data["product_id"] = pd["id"]
    product_data["name"] = pd["name"]    

    for category in pd['category']['path']:
        product_data["categories"].append(category['name'].strip())

    product_data['image'] = pd['imageInfo']['thumbnailUrl']
    product_data['store_id'] = pd['location']['storeIds'][0]
    product_data['store_location'] = pd['location']['city']
    product_data['price'] = pd['priceInfo']['currentPrice']['priceString']
    try:
        product_data['mrp'] = pd['priceInfo']['wasPrice']['priceString']
    except:
        product_data['mrp'] = pd['priceInfo']['currentPrice']['priceString']

    product_data['availability'] = pd['shippingOption']['availabilityStatus']
    # Extract name from size since there isn't any specific field for size
    product_data['size'] = extract_size(pd['name'])

    return product_data


def scrape_product_details(product_url):
    driver = get_driver(headless=True)

    try:
        print("Opening: ", product_url)
        driver.get(product_url)

        page_source = driver.page_source

        soup = BeautifulSoup(page_source, 'html.parser')

        next_data_script = json.loads(soup.find('script', {'id': '__NEXT_DATA__'}).text)

        product_source_data = next_data_script['props']['pageProps']['initialData']['data']['product']

        product_data = fill_product_data(product_source_data)
        product_data['url'] = product_url

        print(product_data)

        driver.close()
        del driver

        return product_data
    except Exception as e:
        print("Error occured while scraping product details")
        print(e)

        driver.close()
        del driver

        raise e


def scrape_products(search_keyword):
    """Scrapes subcategory for each given category page URL."""
    search_url = generate_search_url(search_keyword)

    # --- Open URL and look for last page number ---
    driver = get_driver(headless=True)
    print("Opening: ", search_url)
    driver.get(search_url)

    last_page_number = get_last_page_number(driver)

    print("Total pages available: ", last_page_number)

    driver.close()
    del driver
    # -----

    products = []

    for page_nu in range(1, last_page_number):
        search_url = generate_search_url(search_keyword) + "&page=" + str(page_nu)

        # There's a reason mentioned below why we've to create new window always for a URL
        driver = get_driver(headless=True)
        print("Opening: ", search_url)
        driver.get(search_url)
        wait = WebDriverWait(driver, 10)

        # Get all the products anchor tags
        product_elements = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='item-stack']"))
        ).find_elements(By.TAG_NAME, "a")

        print(f"Total products found on page {page_nu}: {len(product_elements)}")

        for product in product_elements:
            products.append({
                "product_name": product.text,
                "product_url": product.get_attribute('href')
            })
        
        driver.close()
        del driver

    return products


def generate_search_url(query):
    # Encode the query string to be URL-safe
    encoded_query = urllib.parse.quote_plus(query)
    # Construct the Walmart search URL
    url = f"https://www.walmart.com/search?q={encoded_query}"
    return url


def get_last_page_number(driver):
    """
    Get last page number from pagination elements.
    """
    try:
        # Wait for the pagination element to be present
        pagination = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.list.flex.items-center.justify-center.pa0"))
        )
        
        # Find all page number elements
        page_items = pagination.find_elements(By.CSS_SELECTOR, "li a[data-automation-id='page-number'], li div")
        
        # Extract the last page number
        last_page = 1
        for item in reversed(page_items):
            if item.text.isdigit():
                last_page = int(item.text)
                break
        return last_page
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    keyword_to_search = "bread italian"

    # PS: Opening URLs in current window's tab yields captcha, to deal with it, we'll open URLs in whole new chrome instance repteadly
    with DatabaseManager(DB_CONFIG) as db:
        products = scrape_products(keyword_to_search)

        print(f"Total products to scrape: {len(products)}")

        for product in products:
            if db.check_if_product_exists(product['product_url']):
                print(f"Product with URL: {product['product_url']} exists in database, hence skipping.")
                continue

            try:
                product_details = scrape_product_details(product['product_url'])

                # Insert each product individually -> REMOVE LATER
                db.insert_products([product_details])
            except Exception:
                pass
