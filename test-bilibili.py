#!/usr/bin/env python3
"""
Minimal test to see what we can extract from the Bilibili page
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_bilibili_access():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        print("Starting Chrome...")
        driver = webdriver.Chrome(options=chrome_options)
        
        url = "https://www.bilibili.com/opus/763979363954720774?spm_id_from=333.1387.0.0"
        print(f"Navigating to: {url}")
        
        driver.get(url)
        print(f"Page title: {driver.title}")
        
        # Wait and see what we got
        time.sleep(5)
        
        # Try to find elements
        print("\nLooking for content elements...")
        
        # Check page source length
        print(f"Page source length: {len(driver.page_source)} characters")
        
        # Try to find the expected selectors
        selectors = [
            ".opus-module-title__text",
            ".opus-module-content", 
            ".opus-collection__content",
            ".opus-collection__item"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"  {selector}: {len(elements)} elements found")
                if elements:
                    print(f"    First element text: {elements[0].text[:100]}...")
            except Exception as e:
                print(f"  {selector}: Error - {e}")
        
        # Save page source for inspection
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("\nPage source saved to page_source.html")
        
        # Wait to see the page
        print("Waiting 10 seconds to observe the page...")
        time.sleep(10)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if driver:
            print("Closing browser...")
            driver.quit()

if __name__ == "__main__":
    test_bilibili_access()
