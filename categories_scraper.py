from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.database import DatabaseManager
from core.config import DB_CONFIG
from core.driver_setup import get_driver

def scrape_subcategories(category_name, category_url):
    """Scrapes subcategory for each given category page URL."""
    driver = get_driver(headless=True)
    print("Opening: ", category_url)
    driver.get(category_url)

    wait = WebDriverWait(driver, 10)

    # Get all the subcategory anchor tags
    try:
        subcat_elements= wait.until(
            EC.visibility_of_element_located((By.ID, "Hubspokes4orNxMGrid"))
        ).find_elements(By.TAG_NAME, "a")
    except Exception:
        # Check if it's a product page
        try:
            driver.find_element(By.CSS_SELECTOR, "[data-testid='item-stack']")
            return [{
                "category_name": category_name,
                "category_url": category_url,
                "subcategory_name": category_name,
                "subcategory_url": category_url
            }]
        except Exception:
            raise

    print("Total subcategories found: ", len(subcat_elements))

    subcategories = []

    for subcat_a in subcat_elements:
        subcategories.append({
            "category_name": category_name,
            "category_url": category_url,
            "subcategory_name": subcat_a.text,
            "subcategory_url": subcat_a.get_attribute('href')
        })
    
    driver.close()
    del driver
    
    return subcategories


def scrape_categories():
    """Scrape category names and URLs from Kroger's homepage"""
    page_url = "https://www.walmart.com/cp/food/976759"
    driver = get_driver(headless=True)
    try:
        # Open URL in current tab
        driver.get(page_url)

        wait = WebDriverWait(driver, 10)  # 10 second timeout

        # Get all the category divs
        category_elements= wait.until(
            EC.visibility_of_element_located((By.ID, "Hubspokes4orNxMGrid"))
        ).find_elements(By.TAG_NAME, "a")[:-2]  # slice last two, since they contain irrelevant categories

        print("Total Grocery categories found: ", len(category_elements))

        categories = []

        for cat_a in category_elements:
            category = {
                "category_name": cat_a.text,
                "category_url": cat_a.get_attribute('href')
            }

            categories.append(category)
        
        return categories

    finally:
        driver.close()
        del driver

if __name__ == "__main__":
    # PS: Opening URLs in current window's tab yields captcha, to deal with it, we'll open URLs in whole new chrome instance repteadly
    with DatabaseManager(DB_CONFIG) as db:
        categories = scrape_categories()
        
        for cat in categories:
            subcategories = scrape_subcategories(cat['category_name'], cat['category_url'])
            db.insert_subcategories(subcategories)

        print("Total categories scraped: ", len(categories))