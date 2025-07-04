#!/usr/bin/env python3
"""
Translate OVERLORD chapters from Simplified Chinese to Traditional Chinese
and format for iPhone screen reading with parallel processing
"""
import os
import re
import time
import concurrent.futures
from pathlib import Path
from typing import List, Tuple
import opencc

def setup_opencc():
    """Setup OpenCC converter for Simplified to Traditional Chinese"""
    try:
        # s2t = Simplified to Traditional
        converter = opencc.OpenCC('s2t')
        return converter
    except Exception as e:
        print(f"❌ Error setting up OpenCC: {e}")
        print("📋 Please install OpenCC with: pip install opencc-python-reimplemented")
        return None

def format_for_iphone(text: str, max_line_length: int = 35) -> str:
    """
    Format text for iPhone screen reading
    - Optimal line length for iPhone screen
    - Proper paragraph breaks
    - Better readability spacing
    """
    # Split into paragraphs
    paragraphs = text.split('\n\n')
    formatted_paragraphs = []
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
            
        # Clean up the paragraph
        paragraph = paragraph.strip()
        
        # Handle special formatting (titles, separators, etc.)
        if paragraph.startswith('Title:') or paragraph.startswith('標題:'):
            formatted_paragraphs.append(paragraph)
            continue
        
        if paragraph.startswith('='):
            formatted_paragraphs.append(paragraph)
            continue
        
        # For regular text, wrap lines appropriately
        words = paragraph.replace('\n', ' ').split()
        current_line = ""
        formatted_lines = []
        
        for word in words:
            # Check if adding this word would exceed line length
            if len(current_line + word) > max_line_length:
                if current_line:
                    formatted_lines.append(current_line.strip())
                    current_line = word + " "
                else:
                    # Word is too long, just add it
                    formatted_lines.append(word)
                    current_line = ""
            else:
                current_line += word + " "
        
        # Add remaining text
        if current_line.strip():
            formatted_lines.append(current_line.strip())
        
        formatted_paragraphs.append('\n'.join(formatted_lines))
    
    # Join paragraphs with double line breaks for better readability
    return '\n\n'.join(formatted_paragraphs)

def translate_chapter(chapter_info: Tuple[str, str, str, opencc.OpenCC]) -> Tuple[str, bool, str]:
    """
    Translate a single chapter file
    Returns: (filename, success, error_message)
    """
    input_path, output_path, filename, converter = chapter_info
    
    try:
        print(f"  📖 Translating: {filename}")
        
        # Read the original file
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Translate content
        translated_content = converter.convert(content)
        
        # Format for iPhone screen
        formatted_content = format_for_iphone(translated_content)
        
        # Save to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        print(f"  ✓ Completed: {filename}")
        return filename, True, ""
        
    except Exception as e:
        error_msg = f"Error translating {filename}: {str(e)}"
        print(f"  ❌ {error_msg}")
        return filename, False, error_msg

def get_chapter_files(input_dir: str) -> List[str]:
    """Get all chapter files from input directory"""
    chapter_files = []
    
    try:
        for filename in os.listdir(input_dir):
            if filename.startswith('chapter_x') and filename.endswith('.txt'):
                chapter_files.append(filename)
        
        # Sort by chapter number
        def extract_chapter_number(filename):
            match = re.search(r'chapter_x(\d+)', filename)
            return int(match.group(1)) if match else 0
        
        chapter_files.sort(key=extract_chapter_number)
        return chapter_files
        
    except Exception as e:
        print(f"❌ Error reading directory {input_dir}: {e}")
        return []

def translate_all_chapters(input_dir: str, output_dir: str, max_workers: int = 5):
    """
    Translate all chapters with parallel processing
    """
    print(f"🔄 Starting translation process...")
    print(f"📁 Input directory: {input_dir}")
    print(f"📁 Output directory: {output_dir}")
    print(f"⚡ Max workers: {max_workers}")
    
    # Setup OpenCC converter
    converter = setup_opencc()
    if not converter:
        return False
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all chapter files
    chapter_files = get_chapter_files(input_dir)
    
    if not chapter_files:
        print("❌ No chapter files found in input directory")
        return False
    
    print(f"📚 Found {len(chapter_files)} chapters to translate")
    
    # Prepare chapter info for parallel processing
    chapter_info_list = []
    for filename in chapter_files:
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        chapter_info_list.append((input_path, output_path, filename, converter))
    
    # Process chapters in parallel
    start_time = time.time()
    success_count = 0
    error_count = 0
    errors = []
    
    print(f"\n🚀 Starting parallel translation with {max_workers} workers...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_chapter = {executor.submit(translate_chapter, info): info[2] for info in chapter_info_list}
        
        # Process completed tasks
        for future in concurrent.futures.as_completed(future_to_chapter):
            filename = future_to_chapter[future]
            try:
                result_filename, success, error_msg = future.result()
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(error_msg)
            except Exception as e:
                error_count += 1
                error_msg = f"Exception processing {filename}: {str(e)}"
                errors.append(error_msg)
                print(f"  ❌ {error_msg}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Print summary
    print(f"\n" + "="*50)
    print(f"📊 Translation Summary")
    print(f"="*50)
    print(f"✓ Successfully translated: {success_count} chapters")
    print(f"❌ Failed translations: {error_count} chapters")
    print(f"⏱️  Total time: {total_time:.2f} seconds")
    print(f"📱 All files formatted for iPhone screen")
    print(f"📁 Output saved to: {output_dir}")
    
    if errors:
        print(f"\n❌ Errors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    return error_count == 0

def create_reading_info():
    """Create a readme file with information about the translated files"""
    info_content = """# OVERLORD 繁體中文版 - iPhone 優化版

## 📱 iPhone 閱讀優化
- 每行最佳長度：35個字符
- 適合 iPhone 螢幕寬度
- 段落間距優化，提升閱讀體驗
- 支援夜間模式閱讀

## 📚 章節說明
- 原文：簡體中文
- 翻譯：繁體中文
- 格式：針對手機螢幕優化

## 🔧 翻譯技術
- 使用 OpenCC 進行簡繁轉換
- 並行處理提升轉換速度
- 保持原文格式和結構

## 💡 閱讀建議
1. 建議使用支援繁體中文的閱讀器
2. 調整字體大小至舒適程度
3. 可開啟夜間模式保護眼睛
4. 章節按順序編號，建議依序閱讀

生成時間：{timestamp}
"""
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return info_content.format(timestamp=timestamp)

def main():
    """Main function"""
    print("🔤 OVERLORD 章節翻譯工具")
    print("📱 簡體中文 → 繁體中文 + iPhone 格式優化")
    print("="*50)
    
    # Configuration
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_directory = os.path.join(current_dir, "OVERLORD")
    output_directory = os.path.join(current_dir, "OVERLORD_Traditional")
    
    # Check if input directory exists
    if not os.path.exists(input_directory):
        print(f"❌ Input directory not found: {input_directory}")
        print("📋 Please make sure the OVERLORD folder exists with chapter files")
        input("\nPress Enter to exit...")
        return
    
    # Check if OpenCC is available
    try:
        import opencc
        print("✓ OpenCC library found")
    except ImportError:
        print("❌ OpenCC library not found")
        print("📋 Please install it with: pip install opencc-python-reimplemented")
        input("\nPress Enter to exit...")
        return
    
    # Show configuration
    print(f"📁 Input:  {input_directory}")
    print(f"📁 Output: {output_directory}")
    print(f"⚡ Workers: 5 (parallel processing)")
    print(f"📱 Format: iPhone optimized (35 chars per line)")
    
    # Confirm start
    response = input("\n🚀 Start translation? (y/n): ").lower().strip()
    if response != 'y':
        print("❌ Translation cancelled")
        return
    
    # Start translation
    success = translate_all_chapters(input_directory, output_directory, max_workers=5)
    
    if success:
        # Create reading info file
        info_content = create_reading_info()
        info_path = os.path.join(output_directory, "README.md")
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(info_content)
        
        print(f"\n🎉 Translation completed successfully!")
        print(f"📱 All files are now optimized for iPhone reading")
        print(f"📖 Check {info_path} for reading instructions")
    else:
        print(f"\n❌ Translation completed with some errors")
        print(f"📋 Check the error messages above for details")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
