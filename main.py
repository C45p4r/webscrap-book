#!/usr/bin/env python3
"""
Unified Book Processing Workflow
Web scraping, translation, renaming, and indexing all in one place
"""
import os
import re
import time
import shutil
import concurrent.futures
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

# Web scraping imports
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Translation imports
import opencc

class BookProcessor:
    """Main class for book processing workflow"""
    
    def __init__(self, start_url: str, output_dir: str = "OVERLORD"):
        self.start_url = start_url
        self.output_dir = output_dir
        self.traditional_dir = f"{output_dir}_Traditional"
        self.driver = None
        self.chapter_count = 0
        self.converter = None
        
        # Ensure output directories exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(self.traditional_dir, exist_ok=True)
    
    # ===== WEB SCRAPING METHODS =====
    
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
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            print("🔄 Setting up Chrome WebDriver...")
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✓ Chrome WebDriver initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to setup WebDriver: {e}")
            return False
    
    def extract_chinese_text(self, element):
        """Extract Chinese text from web element"""
        try:
            # Get text content
            text = element.text.strip()
            
            # Clean up common web formatting
            text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
            text = text.replace('\n', '\n\n')  # Add paragraph breaks
            
            return text
        except Exception as e:
            print(f"  ⚠️  Error extracting text: {e}")
            return ""
    
    def save_chapter(self, title: str, content: str, chapter_num: int) -> bool:
        """Save chapter content to file"""
        if not title or not content:
            print(f"  ⚠️  Empty title or content for chapter {chapter_num}")
            return False
        
        # Clean filename
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        safe_title = safe_title[:100]  # Limit length
        
        filename = f"chapter_x{chapter_num}.txt"
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
            return None, None
        except NoSuchElementException as e:
            print(f"  ✗ Required element not found: {e}")
            return None, None
    
    def find_next_chapter_link(self):
        """Find the next chapter link in the collection"""
        try:
            print("    🔍 Looking for next chapter...")
            
            # Try to find collection button
            menu_selectors = [
                ".side-toolbar__action.collection",
                "div.side-toolbar__action.collection",
                "[class*='side-toolbar'][class*='collection']"
            ]
            
            menu_button = None
            for selector in menu_selectors:
                try:
                    menu_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if menu_button and menu_button.is_displayed():
                        break
                except:
                    continue
            
            if menu_button:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", menu_button)
                    time.sleep(0.5)
                    menu_button.click()
                    time.sleep(3)
                except:
                    pass
            
            # Look for collection content
            collection_selectors = [
                ".opus-collection__content",
                ".opus-collection__list",
                ".opus-collection",
                "[class*='opus-collection']"
            ]
            
            collection_content = None
            for selector in collection_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            collection_content = element
                            break
                    if collection_content:
                        break
                except:
                    continue
            
            if not collection_content:
                return None
            
            # Find collection items
            item_selectors = [
                ".opus-collection__item",
                "[class*='opus-collection'][class*='item']",
                "li", "a[href*='opus']"
            ]
            
            collection_items = []
            for selector in item_selectors:
                try:
                    items = collection_content.find_elements(By.CSS_SELECTOR, selector)
                    visible_items = [item for item in items if item.is_displayed()]
                    if visible_items:
                        collection_items = visible_items
                        break
                except:
                    continue
            
            if not collection_items:
                return None
            
            # Find active item
            active_index = -1
            current_url = self.driver.current_url
            
            for i, item in enumerate(collection_items):
                try:
                    links = item.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute("href")
                        if href and href in current_url:
                            active_index = i
                            break
                    if active_index >= 0:
                        break
                except:
                    continue
            
            # Get next item
            if active_index + 1 < len(collection_items):
                next_item = collection_items[active_index + 1]
                try:
                    links = next_item.find_elements(By.TAG_NAME, "a")
                    if links:
                        self.driver.execute_script("arguments[0].click();", links[0])
                        time.sleep(3)
                        return self.driver.current_url
                except:
                    pass
            
            return None
            
        except Exception as e:
            print(f"    ✗ Error finding next chapter: {e}")
            return None
    
    def scrape_all_chapters(self):
        """Main scraping method"""
        print("🚀 Starting book scraping process...")
        
        if not self.setup_driver():
            return False
        
        try:
            # Wait for manual CAPTCHA resolution
            self.wait_for_manual_captcha_resolution()
            
            current_url = self.driver.current_url
            self.chapter_count = 0
            
            while True:
                self.chapter_count += 1
                print(f"\n📖 Processing Chapter {self.chapter_count}")
                print(f"🌐 Current URL: {current_url}")
                
                # Get chapter content
                title, content = self.get_current_chapter_content()
                
                if title and content:
                    # Save chapter
                    if self.save_chapter(title, content, self.chapter_count):
                        print(f"  ✓ Chapter {self.chapter_count} saved successfully")
                    else:
                        print(f"  ✗ Failed to save chapter {self.chapter_count}")
                else:
                    print("  ✗ Failed to extract chapter content")
                    break
                
                # Find next chapter
                next_url = self.find_next_chapter_link()
                
                if next_url and next_url != current_url:
                    current_url = next_url
                    print(f"  ➡️  Moving to next chapter")
                    time.sleep(1)
                else:
                    print("  🏁 No more chapters found. Scraping complete!")
                    break
            
            print(f"\n🎉 Scraping completed! Total chapters saved: {self.chapter_count}")
            return True
            
        except Exception as e:
            print(f"\n❌ Error during scraping: {e}")
            return False
    
    # ===== TRANSLATION METHODS =====
    
    def setup_translator(self):
        """Setup OpenCC translator"""
        try:
            # Try different conversion configs
            conversion_configs = ['s2t', 's2tw', 's2hk']
            
            for config in conversion_configs:
                try:
                    converter = opencc.OpenCC(config)
                    test_text = "简体中文测试"
                    converted = converter.convert(test_text)
                    
                    if converted != test_text:
                        print(f"✓ Using OpenCC config: {config}")
                        self.converter = converter
                        return True
                except Exception as e:
                    continue
            
            print("❌ No working OpenCC configuration found")
            return False
            
        except Exception as e:
            print(f"❌ Error setting up translator: {e}")
            return False
    
    def format_for_iphone(self, text: str, max_line_length: int = 35) -> str:
        """Format text for iPhone screen reading"""
        paragraphs = text.split('\n\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            
            paragraph = paragraph.strip()
            
            # Handle special formatting
            if paragraph.startswith(('Title:', '標題:', '=')):
                formatted_paragraphs.append(paragraph)
                continue
            
            # Wrap lines for regular text
            words = paragraph.replace('\n', ' ').split()
            current_line = ""
            formatted_lines = []
            
            for word in words:
                if len(current_line + word) > max_line_length:
                    if current_line:
                        formatted_lines.append(current_line.strip())
                        current_line = word + " "
                    else:
                        formatted_lines.append(word)
                        current_line = ""
                else:
                    current_line += word + " "
            
            if current_line.strip():
                formatted_lines.append(current_line.strip())
            
            formatted_paragraphs.append('\n'.join(formatted_lines))
        
        return '\n\n'.join(formatted_paragraphs)
    
    def translate_chapter(self, chapter_info: Tuple[str, str, str]) -> Tuple[str, bool, str]:
        """Translate a single chapter file"""
        input_path, output_path, filename = chapter_info
        
        try:
            print(f"  📖 Translating: {filename}")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Translate content
            translated_content = self.converter.convert(content)
            
            # Format for iPhone
            formatted_content = self.format_for_iphone(translated_content)
            
            # Save translated file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            print(f"  ✓ Completed: {filename}")
            return filename, True, ""
            
        except Exception as e:
            error_msg = f"Error translating {filename}: {str(e)}"
            print(f"  ❌ {error_msg}")
            return filename, False, error_msg
    
    def translate_all_chapters(self, max_workers: int = 5):
        """Translate all chapters with parallel processing"""
        print(f"🔄 Starting translation process...")
        
        if not self.setup_translator():
            return False
        
        # Get chapter files
        chapter_files = []
        for filename in os.listdir(self.output_dir):
            if filename.startswith('chapter_x') and filename.endswith('.txt'):
                chapter_files.append(filename)
        
        def extract_chapter_number(filename):
            match = re.search(r'chapter_x(\d+)', filename)
            return int(match.group(1)) if match else 0
        
        chapter_files.sort(key=extract_chapter_number)
        
        if not chapter_files:
            print("❌ No chapter files found")
            return False
        
        print(f"📚 Found {len(chapter_files)} chapters to translate")
        
        # Prepare chapter info
        chapter_info_list = []
        for filename in chapter_files:
            input_path = os.path.join(self.output_dir, filename)
            output_path = os.path.join(self.traditional_dir, filename)
            chapter_info_list.append((input_path, output_path, filename))
        
        # Process in parallel
        start_time = time.time()
        success_count = 0
        error_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chapter = {executor.submit(self.translate_chapter, info): info[2] for info in chapter_info_list}
            
            for future in concurrent.futures.as_completed(future_to_chapter):
                filename = future_to_chapter[future]
                try:
                    result_filename, success, error_msg = future.result()
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"  ❌ Exception processing {filename}: {str(e)}")
        
        end_time = time.time()
        print(f"\n📊 Translation completed in {end_time - start_time:.2f} seconds")
        print(f"✓ Successfully translated: {success_count} chapters")
        print(f"❌ Failed translations: {error_count} chapters")
        
        return error_count == 0
    
    # ===== TITLE UPDATE METHODS =====
    
    def update_chapter_titles(self):
        """Update titles in Traditional Chinese chapters"""
        print("📝 Updating chapter titles...")
        
        if not self.converter:
            if not self.setup_translator():
                return False
        
        chapter_files = []
        for filename in os.listdir(self.traditional_dir):
            if filename.startswith('chapter_x') and filename.endswith('.txt'):
                chapter_files.append(filename)
        
        def extract_chapter_number(filename):
            match = re.search(r'chapter_x(\d+)', filename)
            return int(match.group(1)) if match else 0
        
        chapter_files.sort(key=extract_chapter_number)
        updated_count = 0
        
        for filename in chapter_files:
            file_path = os.path.join(self.traditional_dir, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                title_line = lines[0] if lines else ""
                
                if title_line.startswith('Title:'):
                    title_text = title_line[6:].strip()
                    
                    if title_text:
                        translated_title = self.converter.convert(title_text)
                        new_title_line = f"Title: {translated_title}"
                        
                        new_lines = [new_title_line] + lines[1:]
                        new_content = '\n'.join(new_lines)
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        print(f"  ✓ Updated: {filename}")
                        updated_count += 1
                        
            except Exception as e:
                print(f"  ❌ Error processing {filename}: {e}")
        
        print(f"📊 Updated {updated_count} chapter titles")
        return True
    
    # ===== CHAPTER SEQUENCE METHODS =====
    
    def extract_title_from_content(self, content: str) -> Optional[str]:
        """Extract title from file content"""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('Title:'):
                return line[6:].strip()
        return None
    
    def normalize_title_for_comparison(self, title: str) -> str:
        """Normalize title for comparison"""
        if not title:
            return ""
        normalized = re.sub(r'[《》（）\[\]()「」『』【】·\-\s]', '', title)
        return normalized.lower()
    
    def create_chapter_mapping(self):
        """Create mapping between original and traditional chapters"""
        print("🔍 Creating chapter mapping...")
        
        if not os.path.exists(self.output_dir) or not os.path.exists(self.traditional_dir):
            print("❌ Required directories not found")
            return None
        
        # Get original chapters
        original_chapters = []
        for filename in os.listdir(self.output_dir):
            if filename.startswith('chapter_x') and filename.endswith('.txt'):
                match = re.search(r'chapter_x(\d+)', filename)
                if match:
                    chapter_num = int(match.group(1))
                    original_chapters.append((chapter_num, filename))
        
        original_chapters.sort(key=lambda x: x[0])
        
        # Get traditional files
        traditional_files = []
        for filename in os.listdir(self.traditional_dir):
            if filename.endswith('.txt') and not filename.startswith('README'):
                traditional_files.append(filename)
        
        print(f"📚 Found {len(original_chapters)} original and {len(traditional_files)} traditional chapters")
        
        # Create mapping by comparing titles
        mapping = {}
        
        for chapter_num, orig_filename in original_chapters:
            orig_path = os.path.join(self.output_dir, orig_filename)
            
            try:
                with open(orig_path, 'r', encoding='utf-8') as f:
                    orig_content = f.read()
                
                orig_title = self.extract_title_from_content(orig_content)
                if not orig_title:
                    continue
                
                orig_title_norm = self.normalize_title_for_comparison(orig_title)
                
                # Find matching traditional file
                best_match = None
                best_score = 0
                
                for trad_filename in traditional_files:
                    if trad_filename in mapping.values():
                        continue
                    
                    trad_path = os.path.join(self.traditional_dir, trad_filename)
                    
                    try:
                        with open(trad_path, 'r', encoding='utf-8') as f:
                            trad_content = f.read()
                        
                        trad_title = self.extract_title_from_content(trad_content)
                        if not trad_title:
                            continue
                        
                        trad_title_norm = self.normalize_title_for_comparison(trad_title)
                        
                        # Calculate similarity
                        if orig_title_norm in trad_title_norm or trad_title_norm in orig_title_norm:
                            score = len(set(orig_title_norm) & set(trad_title_norm))
                            if score > best_score:
                                best_score = score
                                best_match = trad_filename
                    except:
                        continue
                
                if best_match:
                    mapping[chapter_num] = best_match
                    print(f"  ✓ Ch{chapter_num}: {best_match[:60]}...")
                    
            except Exception as e:
                print(f"  ❌ Error processing {orig_filename}: {e}")
        
        print(f"📊 Successfully mapped {len(mapping)} chapters")
        return mapping
    
    def rename_files_by_mapping(self, mapping: dict):
        """Rename traditional files according to mapping"""
        print("📝 Renaming files according to original order...")
        
        temp_dir = os.path.join(self.traditional_dir, "temp_rename")
        os.makedirs(temp_dir, exist_ok=True)
        
        renamed_count = 0
        
        try:
            # Move files to temp directory with new names
            for chapter_num, old_filename in mapping.items():
                old_path = os.path.join(self.traditional_dir, old_filename)
                
                if os.path.exists(old_path):
                    # Clean filename
                    clean_filename = old_filename
                    if clean_filename.startswith('Ch'):
                        clean_filename = re.sub(r'^Ch\d+\.\s*', '', clean_filename)
                    
                    new_filename = f"Ch{chapter_num}. {clean_filename}"
                    temp_path = os.path.join(temp_dir, new_filename)
                    
                    shutil.move(old_path, temp_path)
                    print(f"  ✓ Ch{chapter_num}: {old_filename[:50]}...")
                    renamed_count += 1
            
            # Move files back
            for filename in os.listdir(temp_dir):
                src = os.path.join(temp_dir, filename)
                dst = os.path.join(self.traditional_dir, filename)
                shutil.move(src, dst)
            
            os.rmdir(temp_dir)
            print(f"✅ Successfully renamed {renamed_count} files")
            
        except Exception as e:
            print(f"❌ Error during renaming: {e}")
            # Cleanup
            if os.path.exists(temp_dir):
                for filename in os.listdir(temp_dir):
                    src = os.path.join(temp_dir, filename)
                    dst = os.path.join(self.traditional_dir, filename)
                    shutil.move(src, dst)
                os.rmdir(temp_dir)
        
        return renamed_count
    
    def fix_chapter_sequence(self):
        """Fix chapter sequence ordering"""
        print("🔄 Fixing chapter sequence...")
        
        mapping = self.create_chapter_mapping()
        if not mapping:
            return False
        
        renamed_count = self.rename_files_by_mapping(mapping)
        return renamed_count > 0
    
    # ===== MAIN WORKFLOW METHODS =====
    
    def create_readme(self):
        """Create README file with processing info"""
        readme_content = f"""# OVERLORD 繁體中文版 - 自動化處理版本

## 📱 iPhone 閱讀優化
- 每行最佳長度：35個字符
- 適合 iPhone 螢幕寬度
- 段落間距優化，提升閱讀體驗

## 🔧 處理流程
1. 網頁爬蟲：自動抓取章節內容
2. 翻譯轉換：簡體中文 → 繁體中文
3. 格式優化：針對手機螢幕優化排版
4. 章節排序：按照原文順序重新編號

## 📚 章節說明
- 原文來源：{self.start_url}
- 總章節數：{self.chapter_count}
- 處理時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 💡 使用說明
1. 建議使用支援繁體中文的閱讀器
2. 調整字體大小至舒適程度
3. 可開啟夜間模式保護眼睛
4. 章節已按順序編號，建議依序閱讀

## 🛠️ 技術細節
- 網頁爬蟲：Selenium + Chrome WebDriver
- 翻譯引擎：OpenCC (簡繁轉換)
- 並行處理：提升處理效率
- 格式優化：iPhone 螢幕適配

生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        readme_path = os.path.join(self.traditional_dir, "README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"📖 Created README: {readme_path}")
    
    def run_full_workflow(self):
        """Run the complete workflow"""
        print("🚀 Starting Complete Book Processing Workflow")
        print("=" * 60)
        
        # Step 1: Web Scraping
        print("\n📊 STEP 1: Web Scraping")
        print("-" * 30)
        if not self.scrape_all_chapters():
            print("❌ Web scraping failed")
            return False
        
        # Step 2: Translation
        print("\n📊 STEP 2: Translation")
        print("-" * 30)
        if not self.translate_all_chapters():
            print("❌ Translation failed")
            return False
        
        # Step 3: Title Updates
        print("\n📊 STEP 3: Title Updates")
        print("-" * 30)
        if not self.update_chapter_titles():
            print("❌ Title updates failed")
            return False
        
        # Step 4: Chapter Sequence Fix
        print("\n📊 STEP 4: Chapter Sequence Fix")
        print("-" * 30)
        if not self.fix_chapter_sequence():
            print("❌ Chapter sequence fix failed")
            return False
        
        # Step 5: Create README
        print("\n📊 STEP 5: Create Documentation")
        print("-" * 30)
        self.create_readme()
        
        print("\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"✅ Total chapters processed: {self.chapter_count}")
        print(f"📁 Original files: {self.output_dir}")
        print(f"📁 Translated files: {self.traditional_dir}")
        print(f"📱 All files optimized for iPhone reading")
        
        return True
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

def main():
    """Main function with interactive menu"""
    print("📚 OVERLORD Book Processing System")
    print("=" * 50)
    
    # Configuration
    start_url = "https://www.bilibili.com/opus/763979363954720774?spm_id_from=333.1387.0.0"
    output_dir = "OVERLORD"
    
    processor = BookProcessor(start_url, output_dir)
    
    while True:
        print("\n📋 Choose an option:")
        print("1. 🔄 Run Full Workflow (Scrape + Translate + Rename + Index)")
        print("2. 🌐 Web Scraping Only")
        print("3. 🔤 Translation Only")
        print("4. 📝 Update Titles Only")
        print("5. 🗂️  Fix Chapter Sequence Only")
        print("6. ❌ Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        try:
            if choice == "1":
                print("\n🚀 Starting Full Workflow...")
                if processor.run_full_workflow():
                    print("✅ Full workflow completed successfully!")
                else:
                    print("❌ Full workflow failed!")
            
            elif choice == "2":
                print("\n🌐 Starting Web Scraping...")
                if processor.scrape_all_chapters():
                    print("✅ Web scraping completed!")
                else:
                    print("❌ Web scraping failed!")
            
            elif choice == "3":
                print("\n🔤 Starting Translation...")
                if processor.translate_all_chapters():
                    print("✅ Translation completed!")
                else:
                    print("❌ Translation failed!")
            
            elif choice == "4":
                print("\n📝 Updating Titles...")
                if processor.update_chapter_titles():
                    print("✅ Title updates completed!")
                else:
                    print("❌ Title updates failed!")
            
            elif choice == "5":
                print("\n🗂️  Fixing Chapter Sequence...")
                if processor.fix_chapter_sequence():
                    print("✅ Chapter sequence fixed!")
                else:
                    print("❌ Chapter sequence fix failed!")
            
            elif choice == "6":
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n⚠️  Operation interrupted by user")
        except Exception as e:
            print(f"❌ An error occurred: {e}")
        
        if choice != "6":
            input("\nPress Enter to continue...")
    
    # Cleanup
    processor.cleanup()

if __name__ == "__main__":
    main()
