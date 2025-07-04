#!/usr/bin/env python3
"""
Simple single-threaded translation test
"""
import opencc
import os

def test_single_translation():
    """Test translating a single chapter"""
    print("🧪 Single Chapter Translation Test")
    print("=" * 40)
    
    # Setup converter
    converter = opencc.OpenCC('s2t')
    
    # Test with first chapter
    input_file = 'OVERLORD/chapter_x1.txt'
    output_file = 'test_translated_chapter.txt'
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    try:
        # Read original
        with open(input_file, 'r', encoding='utf-8') as f:
            original = f.read()
        
        print(f"📖 Original length: {len(original)} characters")
        print(f"📖 Original sample:\n{original[:200]}...")
        
        # Translate
        translated = converter.convert(original)
        
        print(f"\n📝 Translated length: {len(translated)} characters")
        print(f"📝 Translated sample:\n{translated[:200]}...")
        
        # Count changes
        changes = sum(1 for a, b in zip(original, translated) if a != b)
        print(f"\n📊 Characters changed: {changes} out of {len(original)} ({changes/len(original)*100:.1f}%)")
        
        # Save translated version
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(translated)
        
        print(f"✅ Translation saved to: {output_file}")
        
        # Show some specific character changes
        print("\n🔍 Sample character changes:")
        for i, (orig, trans) in enumerate(zip(original, translated)):
            if orig != trans:
                print(f"  Position {i}: '{orig}' -> '{trans}'")
                if i > 10:  # Show first 10 changes
                    break
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_single_translation()
