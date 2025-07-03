import requests
from bs4 import BeautifulSoup
import os
import time
import re
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class BookScraper:
    def __init__(self, start_url, output_dir):
        self.start_url = start_url
        self.output_dir = output_dir
        self.driver = None
        self.chapter_count = 0
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent to appear more like a real browser
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Add window size for better compatibility
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Remove problematic options that might interfere with the site
        # chrome_options.add_argument("--disable-javascript")  # Keep JS enabled for Bilibili
        
        try:
            print("🔄 Setting up Chrome WebDriver...")
            
            # Use system Chrome driver (works better on this system)
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✓ Chrome WebDriver initialized successfully")
            
            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(60)  # Longer timeout for initial load
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to setup Chrome driver: {e}")
            print("Please ensure:")
            print("  1. Chrome browser is installed")
            print("  2. Chrome browser is updated to the latest version")
            print("  3. ChromeDriver is in your PATH or system")
            return False
    
    def clean_filename(self, filename):
        """Clean filename to remove invalid characters"""
        # Remove HTML tags if any
        filename = re.sub(r'<[^>]+>', '', filename)
        # Remove invalid filename characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace multiple spaces with single space
        filename = re.sub(r'\s+', ' ', filename.strip())
        return filename
    
    def extract_chinese_text(self, element):
        """Extract only Chinese text from an element, removing HTML tags"""
        if not element:
            return ""
        
        # Get text content from Selenium WebElement
        text = element.text
        
        # Remove extra whitespace and empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        return cleaned_text
    
    def save_chapter(self, title, content):
        """Save chapter content to a text file"""
        if not title or not content:
            print("Warning: Empty title or content, skipping...")
            return False
        
        self.chapter_count += 1
        
        # Use the format specified in prompt.md: chapter_x<chapter_number>.txt
        filename = f"chapter_x{self.chapter_count}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\n")
                f.write("=" * 50 + "\n\n")
                f.write(content)
            
            print(f"✓ Saved: {filename}")
            return True
        except Exception as e:
            print(f"✗ Error saving file {filename}: {e}")
            return False
    
    def wait_for_manual_captcha_resolution(self):
        """Wait for user to manually resolve CAPTCHA and reach the book page"""
        print("\n🤖 CAPTCHA Detection & Manual Resolution")
        print("=" * 50)
        print("📋 Instructions:")
        print("1. A Chrome browser window will open")
        print("2. If you see a CAPTCHA page (验证码), please solve it manually")
        print("3. Navigate to the book chapter if needed")
        print("4. Once you can see the book content, come back here and press Enter")
        print("=" * 50)
        
        # Navigate to the starting URL
        print(f"🌐 Opening: {self.start_url}")
        self.driver.get(self.start_url)
        
        # Wait for user confirmation
        input("\n⏸️  PRESS ENTER when you have solved any CAPTCHA and can see the book content...")
        
        print("✅ Proceeding with automatic chapter extraction...")
        return True
    def get_current_chapter_content(self):
        """Extract title and content from current page"""
        try:
            # Wait for content to load with longer timeout
            print("  📖 Loading chapter content...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".opus-module-content"))
            )
            
            # Extract title
            title_element = self.driver.find_element(By.CSS_SELECTOR, ".opus-module-title__text")
            title = self.extract_chinese_text(title_element)
            
            # Extract content
            content_element = self.driver.find_element(By.CSS_SELECTOR, ".opus-module-content")
            content = self.extract_chinese_text(content_element)
            
            print(f"  ✓ Extracted: {title[:50]}...")
            return title, content
            
        except TimeoutException:
            print("  ✗ Timeout waiting for page content to load")
            print("  🔍 Let me check what's on the page...")
            # Check if we hit another CAPTCHA or different page
            page_title = self.driver.title
            print(f"  📄 Current page title: {page_title}")
            if "验证码" in page_title:
                print("  ⚠️  Hit another CAPTCHA page. You may need to solve it manually.")
                input("  ⏸️  Press Enter after solving CAPTCHA...")
                return self.get_current_chapter_content()  # Retry
            return None, None
        except NoSuchElementException as e:
            print(f"  ✗ Required element not found: {e}")
            return None, None
    
    def find_next_chapter_link(self):
        """Find the next chapter link in the collection"""
        try:
            print("    🔍 Looking for the specific Bilibili collection button...")
            
            # First, try to find the exact Bilibili collection button
            menu_button = None
            bilibili_selectors = [
                # Exact selector for Bilibili collection button
                ".side-toolbar__action.collection",
                "div.side-toolbar__action.collection",
                # Fallback selectors in case of slight variations
                "[class*='side-toolbar'][class*='collection']",
                ".side-toolbar__action:has(.side-toolbar__action__text:contains('目录'))",
                # XPath for the exact structure
                "//div[contains(@class, 'side-toolbar__action') and contains(@class, 'collection')]",
                "//div[contains(@class, 'side-toolbar__action__text') and text()='目录']/parent::div"
            ]
            
            for selector in bilibili_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath selector
                        menu_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        # CSS selector
                        menu_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if menu_button and menu_button.is_displayed():
                        print(f"    ✓ Found Bilibili collection button with selector: {selector}")
                        break
                except (NoSuchElementException, Exception):
                    continue
            
            # If the exact button wasn't found, try broader search
            if not menu_button:
                print("    🔍 Exact button not found, trying broader search...")
                try:
                    # Look for any element containing the text "目录"
                    xpath = "//div[contains(text(), '目录')] | //div[contains(@class, 'collection')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Check if this element looks like a clickable button
                            tag = element.tag_name.lower()
                            classes = element.get_attribute("class") or ""
                            if any(keyword in classes.lower() for keyword in ['action', 'button', 'clickable', 'toolbar']):
                                menu_button = element
                                print(f"    ✓ Found collection element by broader search")
                                break
                except Exception as e:
                    print(f"    ⚠️  Broader search failed: {e}")
            
            # If no specific menu button found, try to find clickable elements with relevant text
            if not menu_button:
                print("    🔍 No standard menu button found, searching for clickable text elements...")
                try:
                    # Look for any clickable element that might contain menu-related text
                    all_clickables = self.driver.find_elements(By.CSS_SELECTOR, "button, div[role='button'], span[role='button'], a, div[onclick], span[onclick]")
                    for element in all_clickables:
                        try:
                            text = element.text.strip()
                            if any(keyword in text for keyword in ['目录', '章节', '列表', '菜单', 'Menu', 'List', 'Index']):
                                menu_button = element
                                print(f"    ✓ Found menu element by text: '{text}'")
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"    ⚠️  Error searching for text-based menu: {e}")
            
            # Try to click the menu button to activate side menu
            if menu_button:
                try:
                    print("    👆 Clicking collection button to activate chapter menu...")
                    
                    # Scroll element into view first
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", menu_button)
                    time.sleep(0.5)
                    
                    # Try multiple click methods
                    try:
                        menu_button.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", menu_button)
                    
                    time.sleep(3)  # Wait longer for menu to expand
                    print("    ✓ Collection button clicked, chapter menu should now be visible")
                except Exception as e:
                    print(f"    ⚠️  Could not click collection button: {e}")
            else:
                print("    ⚠️  No collection button found, chapter menu might already be visible...")
            
            # Now try to find the chapter list/collection content after activating menu
            print("    🔍 Searching for chapter collection content...")
            
            # Wait a bit more for dynamic content to load
            time.sleep(2)
            
            # Try multiple possible selectors for the collection/chapter list (prioritize Bilibili-specific ones)
            collection_selectors = [
                # Bilibili-specific selectors (highest priority)
                ".opus-collection__content",
                ".opus-collection__list",
                ".opus-collection",
                "[class*='opus-collection'][class*='content']",
                "[class*='opus-collection'][class*='list']",
                "[class*='opus-collection']",
                # General collection selectors
                "[class*='collection'][class*='content']",
                "[class*='collection'][class*='list']",
                "[class*='collection']",
                # Chapter/episode list selectors
                "[class*='chapter'][class*='list']",
                "[class*='chapter'][class*='menu']",
                "[class*='episode'][class*='list']",
                # Menu/navigation selectors
                "[class*='side'][class*='menu']",
                "[class*='side'][class*='panel']",
                "[class*='nav'][class*='menu']",
                "[class*='nav'][class*='panel']",
                # Generic list containers (last resort)
                "ul[class*='list']",
                "div[class*='list']"
            ]
            
            collection_content = None
            for selector in collection_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    # Filter for visible elements
                    for element in elements:
                        if element.is_displayed():
                            collection_content = element
                            print(f"    ✓ Found visible collection with selector: {selector}")
                            break
                    if collection_content:
                        break
                except:
                    continue
            
            if not collection_content:
                print("    ❌ Could not find any visible collection element after menu activation")
                print("    🔍 Let me search for any navigation elements...")
                
                # Fallback: look for any visible navigation-like elements
                try:
                    nav_elements = self.driver.find_elements(By.CSS_SELECTOR, "nav, [role='navigation'], [class*='nav'], [class*='menu'], ul, ol")
                    for nav in nav_elements:
                        if nav.is_displayed() and nav.find_elements(By.TAG_NAME, "a"):
                            collection_content = nav
                            print(f"    ✓ Using navigation element as collection")
                            break
                except:
                    pass
                
                if not collection_content:
                    return None
            
            # Try multiple possible selectors for collection items (prioritize Bilibili-specific ones)
            item_selectors = [
                # Bilibili-specific item selectors (highest priority)
                ".opus-collection__item",
                "[class*='opus-collection'][class*='item']",
                "[class*='opus-item']",
                # General collection item selectors
                "[class*='collection-item']",
                "[class*='collection'][class*='item']",
                "[class*='chapter-item']",
                "[class*='episode-item']",
                # Generic item selectors
                "[class*='item']",
                "li", "a[href*='opus']",  # Look for list items or opus links
                # Fallback: any clickable elements in collection
                "a", "div[onclick]", "span[onclick]"
            ]
            
            collection_items = []
            for selector in item_selectors:
                try:
                    items = collection_content.find_elements(By.CSS_SELECTOR, selector)
                    # Filter for visible and potentially clickable items
                    visible_items = [item for item in items if item.is_displayed()]
                    if visible_items:
                        collection_items = visible_items
                        print(f"    ✓ Found {len(visible_items)} visible items with selector: {selector}")
                        break
                except:
                    continue
            
            if not collection_items:
                print("    ❌ No collection items found with any selector")
                # Let's try to find any clickable elements in the collection
                try:
                    all_links = collection_content.find_elements(By.TAG_NAME, "a")
                    print(f"    � Found {len(all_links)} links in collection")
                    for i, link in enumerate(all_links):
                        href = link.get_attribute("href")
                        text = link.text[:50] if link.text else "No text"
                        print(f"      Link {i}: {href} - {text}")
                        if href and "opus" in href:
                            print(f"    ✅ Found opus link: {href}")
                            return href
                except:
                    pass
                return None
            
            # Debug: Print all items and their classes
            for i, item in enumerate(collection_items):
                item_class = item.get_attribute("class")
                try:
                    item_text = item.text[:30].replace('\n', ' ') if item.text else "No text"
                except:
                    item_text = "No text"
                print(f"      Item {i}: class='{item_class}' text='{item_text}'")
            
            # Find the currently active item or determine next chapter to click
            active_item = None
            active_index = -1
            
            # Method 1: Look for items with "active" class
            for i, item in enumerate(collection_items):
                item_class = item.get_attribute("class") or ""
                if "active" in item_class.lower() or "current" in item_class.lower() or "selected" in item_class.lower():
                    active_item = item
                    active_index = i
                    print(f"    ✓ Found active item at index {i} (class: {item_class})")
                    break
            
            # Method 2: If no active item found, look for items that match current URL
            if active_item is None and collection_items:
                current_url = self.driver.current_url
                print(f"    🔍 No active class found, comparing URLs with current: {current_url}")
                
                for i, item in enumerate(collection_items):
                    try:
                        # Look for links in the item
                        links = item.find_elements(By.TAG_NAME, "a")
                        for link in links:
                            href = link.get_attribute("href")
                            if href and href in current_url:
                                active_item = item
                                active_index = i
                                print(f"    ✓ Found current chapter item at index {i} by URL match")
                                break
                        if active_item:
                            break
                    except:
                        continue
            
            # Method 3: If still no active item, assume we want the first non-clicked item
            if active_item is None and collection_items:
                print(f"    ⚠️  Could not find active item, will try clicking items sequentially")
                
                # Try clicking the first few items to find one that works
                for i, item in enumerate(collection_items[:3]):  # Try first 3 items
                    try:
                        print(f"    👆 Trying to click item at index {i}")
                        
                        # Look for links in the item and click the first one
                        links = item.find_elements(By.TAG_NAME, "a")
                        if links:
                            current_url_before = self.driver.current_url
                            self.driver.execute_script("arguments[0].click();", links[0])
                            time.sleep(3)
                            new_url = self.driver.current_url
                            
                            # Check if URL changed (navigation successful)
                            if new_url != current_url_before:
                                print(f"    ✅ Successfully navigated to: {new_url}")
                                return new_url
                            else:
                                print(f"    ⚠️  Click didn't change URL, trying next item...")
                        else:
                            # Try clicking the item itself
                            current_url_before = self.driver.current_url
                            self.driver.execute_script("arguments[0].click();", item)
                            time.sleep(3)
                            new_url = self.driver.current_url
                            
                            if new_url != current_url_before:
                                print(f"    ✅ Successfully navigated to: {new_url}")
                                return new_url
                                
                    except Exception as e:
                        print(f"    ✗ Failed to click item {i}: {e}")
                        continue
                
                print("    ❌ Could not click any chapter items")
                return None
            
            # Get the next item (right below the active one)
            if active_index + 1 < len(collection_items):
                next_item = collection_items[active_index + 1]
                print(f"    🎯 Found next item at index {active_index + 1}")
                
                # Instead of getting the URL, click the next item directly
                try:
                    # Try to find a clickable link in the next item
                    links = next_item.find_elements(By.TAG_NAME, "a")
                    if links:
                        next_link = links[0]  # Use the first link found
                        print(f"    👆 Clicking next chapter link...")
                        
                        # Use JavaScript click to ensure it works
                        self.driver.execute_script("arguments[0].click();", next_link)
                        time.sleep(3)  # Wait for navigation
                        
                        # Return the current URL after navigation
                        new_url = self.driver.current_url
                        print(f"    ✅ Successfully navigated to: {new_url}")
                        return new_url
                    else:
                        # Try clicking the item itself if no links found
                        print(f"    👆 No links found, trying to click the item directly...")
                        self.driver.execute_script("arguments[0].click();", next_item)
                        time.sleep(3)
                        
                        new_url = self.driver.current_url
                        print(f"    ✅ Successfully navigated to: {new_url}")
                        return new_url
                        
                except Exception as e:
                    print(f"    ✗ Failed to click next chapter: {e}")
                    return None
            else:
                print("    🏁 Already at the last chapter")
                return None
                
        except NoSuchElementException as e:
            print(f"    ✗ Collection elements not found: {e}")
            print("    🔍 Let me check what's available on the page...")
            
            # Debug: Check what elements are actually on the page
            try:
                # Look for any elements that might be related to chapters/collection
                opus_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='opus']")
                print(f"    📋 Found {len(opus_elements)} elements with 'opus' in class name")
                for elem in opus_elements[:10]:  # Show first 10
                    class_name = elem.get_attribute('class')
                    print(f"      - {elem.tag_name}.{class_name}")
                
                # Look specifically for navigation elements
                nav_elements = self.driver.find_elements(By.CSS_SELECTOR, "nav, [class*='nav'], [class*='menu'], [class*='list']")
                print(f"    📋 Found {len(nav_elements)} potential navigation elements")
                for elem in nav_elements[:5]:
                    class_name = elem.get_attribute('class')
                    print(f"      - {elem.tag_name}.{class_name}")
                    
            except Exception as debug_e:
                print(f"    ⚠️  Debug failed: {debug_e}")
            
            return None
    
    def activate_side_menu(self):
        """Try to activate any hidden side menu or chapter list"""
        print("    🔍 Attempting to activate side menu/chapter list...")
        
        # Try various approaches to activate hidden menus
        activation_strategies = [
            # Strategy 1: Look for menu/directory buttons
            {
                "name": "Directory/Menu buttons",
                "selectors": [
                    "[class*='directory']", "[class*='catalog']", "[class*='index']",
                    "[title*='目录']", "[title*='章节']", "[title*='列表']",
                    "button:contains('目录')", "button:contains('章节')", 
                    "*[text()='目录']", "*[text()='章节']", "*[text()='列表']"
                ]
            },
            # Strategy 2: Look for collection-related elements
            {
                "name": "Collection elements",
                "selectors": [
                    "[class*='collection'][class*='header']",
                    "[class*='collection'][class*='toggle']",
                    "[class*='collection'][class*='button']",
                    ".opus-collection__header"
                ]
            },
            # Strategy 3: Look for navigation toggles
            {
                "name": "Navigation toggles",
                "selectors": [
                    "[class*='nav'][class*='toggle']",
                    "[class*='menu'][class*='toggle']",
                    "[class*='sidebar'][class*='toggle']",
                    "[role='button'][aria-label*='menu']",
                    "[role='button'][aria-label*='目录']"
                ]
            },
            # Strategy 4: Look for hamburger menus or icon buttons
            {
                "name": "Icon/Hamburger menus",
                "selectors": [
                    ".icon-menu", ".icon-list", ".icon-bars",
                    "[class*='hamburger']", "[class*='burger']",
                    "button[class*='icon']", "span[class*='icon']"
                ]
            }
        ]
        
        for strategy in activation_strategies:
            print(f"    🎯 Trying strategy: {strategy['name']}")
            
            for selector in strategy['selectors']:
                try:
                    if selector.startswith("*[text()=") or selector.startswith("button:contains("):
                        # Handle XPath-style selectors for text content
                        if "目录" in selector:
                            xpath = f"//*[contains(text(), '目录')]"
                        elif "章节" in selector:
                            xpath = f"//*[contains(text(), '章节')]"
                        elif "列表" in selector:
                            xpath = f"//*[contains(text(), '列表')]"
                        else:
                            continue
                        
                        elements = self.driver.find_elements(By.XPATH, xpath)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            try:
                                print(f"    👆 Clicking menu element: {selector}")
                                # Scroll into view and click
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.5)
                                
                                # Try regular click first, then JavaScript click
                                try:
                                    element.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", element)
                                
                                time.sleep(2)  # Wait for menu to appear
                                print(f"    ✅ Successfully clicked menu element")
                                return True
                                
                            except Exception as e:
                                print(f"    ⚠️  Failed to click element: {e}")
                                continue
                                
                except Exception as e:
                    continue
        
        print("    ⚠️  No menu activation elements found - menu might already be visible")
        return False

    def scrape_all_chapters(self):
        """Main method to scrape all chapters"""
        if not self.setup_driver():
            return False
        
        try:
            # First, handle the initial CAPTCHA
            if not self.wait_for_manual_captcha_resolution():
                return False
            
            # Now start with the current page (should be the first chapter)
            current_url = self.driver.current_url
            # Remove chapter limit - scrape until no more chapters found
            
            print(f"\n🚀 Starting to scrape chapters...")
            print("📋 Will continue until no more chapters are found...")
            
            while current_url:
                print(f"\n📄 Chapter {self.chapter_count + 1}: {current_url}")
                
                # For the first chapter, we're already on the page
                # For subsequent chapters, navigation is handled by find_next_chapter_link()
                
                # Extract chapter content
                title, content = self.get_current_chapter_content()
                
                if title and content:
                    if self.save_chapter(title, content):
                        print(f"  ✓ Successfully processed chapter: {title}")
                    else:
                        print(f"  ✗ Failed to save chapter: {title}")
                        break
                else:
                    print("  ✗ Failed to extract chapter content")
                    print("  🔍 This might be the end of available chapters")
                    break
                
                # Find next chapter (this will also navigate to it)
                print("  🔍 Looking for next chapter...")
                next_url = self.find_next_chapter_link()
                
                if next_url and next_url != current_url:
                    current_url = next_url
                    print(f"  ➡️  Moved to next chapter: {next_url}")
                    
                    # Small wait between chapters to be respectful
                    time.sleep(1)
                else:
                    print("  🏁 No more chapters found. Scraping complete!")
                    break
            
            print(f"\n🎉 Scraping completed! Total chapters saved: {self.chapter_count}")
            
            # Don't close browser automatically - let user close it
            print("\n📋 Browser will remain open for you to review.")
            print("   You can close it manually when done.")
            
            return True
            
        except KeyboardInterrupt:
            print("\n⚠️  Scraping interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ An error occurred during scraping: {e}")
            import traceback
            traceback.print_exc()
            return False
        # Note: NOT closing the driver automatically

def main():
    # Configuration - Use OVERLORD folder as specified in prompt.md
    start_url = "https://www.bilibili.com/opus/763979363954720774?spm_id_from=333.1387.0.0"
    # Use the OVERLORD folder in the current workspace
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_directory = os.path.join(current_dir, "OVERLORD")
    
    print("Book Scraper Starting...")
    print(f"Starting URL: {start_url}")
    print(f"Output Directory: {output_directory}")
    
    # Create scraper instance
    scraper = BookScraper(start_url, output_directory)
    
    # Start scraping
    success = scraper.scrape_all_chapters()
    
    if success:
        print("\n✓ Scraping completed successfully!")
        print(f"✓ Files saved in: {output_directory}")
    else:
        print("\n✗ Scraping failed or was interrupted.")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()