import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options

def get_driver(headless=True):
    """Initialize and configure undetected Chrome WebDriver"""
    options = Options()
    
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--allow-redirects")
    
    # Initialize undetected-chromedriver
    driver = uc.Chrome(
        options=options,
        headless=headless,
    )
    
    driver.implicitly_wait(10)
    return driver