from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.database import DatabaseManager
from core.config import DB_CONFIG
from core.driver_setup import get_driver
from bs4 import BeautifulSoup
import json
import re


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
    try:
        driver = get_driver(headless=True)
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


def scrape_products(subcategory):
    """Scrapes subcategory for each given category page URL."""
    driver = get_driver(headless=True)
    print("Opening: ", subcategory['subcategory_url'])
    driver.get(subcategory['subcategory_url'])

    wait = WebDriverWait(driver, 10)

    # Get all the products anchor tags
    product_elements = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='item-stack']"))
    ).find_elements(By.TAG_NAME, "a")

    print("Total products found: ", len(product_elements))

    products = []

    for product in product_elements:
        products.append({
            "product_name": product.text,
            "product_url": product.get_attribute('href')
        })
    
    driver.close()
    del driver
    
    return products


if __name__ == "__main__":
    # PS: Opening URLs in current window's tab yields captcha, to deal with it, we'll open URLs in whole new chrome instance repteadly
    with DatabaseManager(DB_CONFIG) as db:
        subcategories = db.get_pending_subcategories()
        
        for subcat in subcategories:
            products = scrape_products(subcat)

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

        print("Total subcategories scraped: ", len(subcategories))