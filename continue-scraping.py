#!/usr/bin/env python3
"""
Continue scraping from the current browser session
"""
import os
import sys

# Add the current directory to path so we can import our scraper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_auto_save_books import BookScraper

def continue_scraping():
    """Continue scraping from where we left off"""
    print("🔄 Continuing chapter scraping...")
    
    # Use the same configuration as main
    start_url = "https://www.bilibili.com/opus/763979363954720774?spm_id_from=333.1387.0.0"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_directory = os.path.join(current_dir, "OVERLORD")
    
    # Create scraper instance
    scraper = BookScraper(start_url, output_directory)
    
    # Setup driver
    if not scraper.setup_driver():
        print("❌ Failed to setup driver")
        return
    
    print("\n📋 Instructions:")
    print("1. Navigate to the NEXT chapter you want to scrape in the browser")
    print("2. Make sure you can see the chapter content")
    print("3. Press Enter here to continue automatic scraping")
    
    # Navigate to starting point
    print(f"🌐 Opening: {start_url}")
    scraper.driver.get(start_url)
    
    input("\n⏸️  PRESS ENTER when you're on the chapter you want to continue from...")
    
    # Continue scraping from current page
    try:
        current_url = scraper.driver.current_url
        print(f"\n🚀 Continuing to scrape from: {current_url}")
        
        # Check how many chapters we already have
        existing_files = [f for f in os.listdir(output_directory) if f.startswith("chapter_x") and f.endswith(".txt")]
        scraper.chapter_count = len(existing_files)
        print(f"📊 Found {scraper.chapter_count} existing chapters, continuing from chapter {scraper.chapter_count + 1}")
        
        while current_url:
            print(f"\n📄 Chapter {scraper.chapter_count + 1}: {current_url}")
            
            # Extract chapter content
            title, content = scraper.get_current_chapter_content()
            
            if title and content:
                if scraper.save_chapter(title, content):
                    print(f"  ✓ Successfully processed chapter: {title}")
                else:
                    print(f"  ✗ Failed to save chapter: {title}")
                    break
            else:
                print("  ✗ Failed to extract chapter content")
                break
            
            # Find next chapter
            print("  🔍 Looking for next chapter...")
            next_url = scraper.find_next_chapter_link()
            
            if next_url:
                from urllib.parse import urljoin
                # Convert relative URL to absolute if needed
                if not next_url.startswith('http'):
                    next_url = urljoin(current_url, next_url)
                current_url = next_url
                print(f"  ➡️  Next chapter found: {next_url}")
                
                # Navigate to next chapter
                scraper.driver.get(current_url)
                import time
                time.sleep(3)
            else:
                print("  🏁 No more chapters found. Scraping complete!")
                break
        
        print(f"\n🎉 Scraping completed! Total chapters saved: {scraper.chapter_count}")
        print("\n📋 Browser will remain open for you to review.")
        
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    continue_scraping()
