#!/usr/bin/env python3
"""
Bilibili-specific scraper that handles the collection structure correctly
"""
import sys
import os
import time
from urllib.parse import urljoin

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    """Setup Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    driver.set_page_load_timeout(60)
    return driver

def extract_text(element):
    """Extract text from element"""
    if not element:
        return ""
    text = element.text
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)

def save_chapter(title, content, chapter_num, output_dir):
    """Save chapter to file"""
    if not title or not content:
        return False
    
    os.makedirs(output_dir, exist_ok=True)
    filename = f"chapter_x{chapter_num}.txt"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\n")
            f.write("=" * 50 + "\n\n")
            f.write(content)
        print(f"✓ Saved: {filename}")
        return True
    except Exception as e:
        print(f"✗ Error saving {filename}: {e}")
        return False

def get_chapter_content(driver):
    """Extract title and content from current page"""
    try:
        print("  📖 Loading chapter content...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".opus-module-content"))
        )
        
        title_element = driver.find_element(By.CSS_SELECTOR, ".opus-module-title__text")
        title = extract_text(title_element)
        
        content_element = driver.find_element(By.CSS_SELECTOR, ".opus-module-content")
        content = extract_text(content_element)
        
        print(f"  ✓ Extracted: {title[:50]}...")
        return title, content
        
    except TimeoutException:
        print("  ✗ Timeout waiting for content")
        page_title = driver.title
        if "验证码" in page_title:
            print("  ⚠️  Hit CAPTCHA page. Please solve it manually.")
            input("  ⏸️  Press Enter after solving CAPTCHA...")
            return get_chapter_content(driver)  # Retry
        return None, None
    except NoSuchElementException as e:
        print(f"  ✗ Element not found: {e}")
        return None, None

def get_collection_links(driver):
    """Get all chapter links from the collection"""
    try:
        print("    🔍 Looking for collection button...")
        
        # First, try to click the collection button to show the collection
        try:
            collection_button = driver.find_element(By.CSS_SELECTOR, ".side-toolbar__action.collection")
            print("    🎯 Found collection button, clicking...")
            driver.execute_script("arguments[0].click();", collection_button)
            time.sleep(3)  # Wait for collection to appear
        except NoSuchElementException:
            print("    ⚠️  Collection button not found, trying to find visible collection...")
        
        # Look for the collection content
        collection_selectors = [
            ".opus-collection__content",
            ".opus-collection",
            "[class*='opus-collection']"
        ]
        
        collection = None
        for selector in collection_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    # Check if it's visible or make it visible
                    if elem.is_displayed():
                        collection = elem
                        print(f"    ✓ Found visible collection: {selector}")
                        break
                    else:
                        # Try to make it visible
                        try:
                            driver.execute_script("""
                                arguments[0].style.display = 'block';
                                arguments[0].style.visibility = 'visible';
                                var parent = arguments[0].parentElement;
                                if (parent) {
                                    parent.style.display = 'block';
                                    parent.style.visibility = 'visible';
                                }
                            """, elem)
                            time.sleep(1)
                            if elem.is_displayed():
                                collection = elem
                                print(f"    ✓ Made collection visible: {selector}")
                                break
                        except:
                            continue
                if collection:
                    break
            except:
                continue
        
        if not collection:
            print("    ❌ Could not find or show collection")
            return []
        
        # Wait a bit more for content to load
        time.sleep(2)
        
        # Find all links in the collection
        all_links = collection.find_elements(By.TAG_NAME, "a")
        print(f"    🔍 Found {len(all_links)} total links in collection")
        
        chapter_links = []
        for i, link in enumerate(all_links):
            try:
                href = link.get_attribute("href")
                text = link.text.strip() if link.text else f"Chapter {i+1}"
                
                # Only include opus links
                if href and "opus" in href:
                    chapter_links.append({
                        'url': href,
                        'text': text,
                        'index': i
                    })
                    print(f"    📄 Chapter {len(chapter_links)}: {text[:50]}")
            except:
                continue
        
        print(f"    ✅ Found {len(chapter_links)} chapter links")
        return chapter_links
        
    except Exception as e:
        print(f"    ✗ Error getting collection links: {e}")
        return []

def scrape_bilibili_book():
    """Main scraping function for Bilibili book collection"""
    print("🔄 Starting Bilibili book scraper...")
    
    # Configuration
    start_url = "https://www.bilibili.com/opus/763979363954720774?spm_id_from=333.1387.0.0"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_directory = os.path.join(current_dir, "OVERLORD")
    
    print(f"📁 Output directory: {output_directory}")
    
    # Check existing chapters
    try:
        existing_files = [f for f in os.listdir(output_directory) 
                         if f.startswith("chapter_x") and f.endswith(".txt")]
        chapter_count = len(existing_files)
        print(f"📊 Found {chapter_count} existing chapters")
    except:
        chapter_count = 0
        print("📊 No existing chapters found")
    
    # Setup driver
    driver = setup_driver()
    
    try:
        print(f"🌐 Opening: {start_url}")
        driver.get(start_url)
        time.sleep(3)
        
        print("\n📋 Manual Setup:")
        print("1. Solve any CAPTCHA if it appears")
        print("2. Make sure you can see the book content")
        print("3. The collection menu should be visible on the right side")
        input("⏸️  Press Enter when ready to start scraping...")
        
        # Try to get all chapter links from the collection
        chapter_links = get_collection_links(driver)
        
        if not chapter_links:
            print("❌ Could not find chapter links! Trying single chapter mode...")
            
            # Fallback: just scrape the current chapter
            title, content = get_chapter_content(driver)
            if title and content:
                chapter_num = chapter_count + 1
                if save_chapter(title, content, chapter_num, output_directory):
                    print(f"✓ Saved single chapter: {title}")
                    chapter_count += 1
            
        else:
            print(f"\n🚀 Starting to scrape {len(chapter_links)} chapters...")
            
            for i, chapter_info in enumerate(chapter_links):
                chapter_num = chapter_count + i + 1
                print(f"\n📄 Chapter {chapter_num}: {chapter_info['text']}")
                
                # Navigate to chapter
                print(f"  🌐 Navigating to: {chapter_info['url']}")
                driver.get(chapter_info['url'])
                time.sleep(3)
                
                # Extract content
                title, content = get_chapter_content(driver)
                
                if title and content:
                    if save_chapter(title, content, chapter_num, output_directory):
                        print(f"  ✓ Successfully processed: {title}")
                    else:
                        print(f"  ✗ Failed to save: {title}")
                else:
                    print(f"  ✗ Failed to extract content from: {chapter_info['url']}")
                    continue
                
                # Small delay between chapters
                time.sleep(2)
        
        print(f"\n🎉 Scraping completed! Total chapters processed: {chapter_count}")
        print("📋 Browser will remain open for review")
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    scrape_bilibili_book()
