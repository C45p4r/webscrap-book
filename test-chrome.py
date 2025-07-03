#!/usr/bin/env python3
"""
Test Chrome WebDriver setup
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def test_chrome_driver():
    print("Testing Chrome WebDriver setup...")
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        print("1. Trying with webdriver-manager...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✓ webdriver-manager approach successful!")
        
        print("2. Testing navigation...")
        driver.get("https://www.google.com")
        print(f"✓ Successfully navigated to Google. Title: {driver.title}")
        
        driver.quit()
        print("✓ Chrome WebDriver test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ webdriver-manager approach failed: {e}")
        
        try:
            print("3. Trying system Chrome driver...")
            driver = webdriver.Chrome(options=chrome_options)
            print("✓ System Chrome driver approach successful!")
            
            print("4. Testing navigation...")
            driver.get("https://www.google.com")
            print(f"✓ Successfully navigated to Google. Title: {driver.title}")
            
            driver.quit()
            print("✓ Chrome WebDriver test completed successfully!")
            return True
            
        except Exception as e2:
            print(f"✗ System Chrome driver approach failed: {e2}")
            print("\nTroubleshooting tips:")
            print("1. Make sure Google Chrome is installed")
            print("2. Check if Chrome is up to date")
            print("3. Try restarting your computer")
            print("4. Check your antivirus software settings")
            return False

if __name__ == "__main__":
    test_chrome_driver()
