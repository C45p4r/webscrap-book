#!/usr/bin/env python3
"""
Test the iPhone formatting function
"""
import opencc

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

def test_formatting():
    """Test the formatting and translation"""
    print("🔤 Testing Translation + iPhone Formatting...")
    
    # Read test file
    with open('test_chapter.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Setup converter
    converter = opencc.OpenCC('s2t')
    
    # Translate
    translated = converter.convert(content)
    
    # Format for iPhone
    formatted = format_for_iphone(translated)
    
    # Save result
    with open('test_output.txt', 'w', encoding='utf-8') as f:
        f.write(formatted)
    
    print("✅ Test completed!")
    print("📁 Check 'test_output.txt' to see the result")
    print("\n📱 iPhone Formatting Preview:")
    print("-" * 40)
    print(formatted[:500] + "...")
    print("-" * 40)

if __name__ == "__main__":
    test_formatting()
