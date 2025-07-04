#!/usr/bin/env python3
"""
Debug OpenCC translation issues
"""
import opencc

def test_opencc_detailed():
    """Test OpenCC with detailed debugging"""
    print("🔍 OpenCC Debug Test")
    print("=" * 40)
    
    # Test different configs
    configs = ['s2t', 's2tw', 's2hk', 's2twp']
    
    test_texts = [
        "简体中文",
        "魔导王的怒火", 
        "这是一个测试",
        "教国覆灭",
        "纳萨力克大坟墓"
    ]
    
    for config in configs:
        print(f"\n📝 Testing config: {config}")
        try:
            converter = opencc.OpenCC(config)
            
            for text in test_texts:
                converted = converter.convert(text)
                changed = "✓" if converted != text else "✗"
                print(f"  {changed} {text} -> {converted}")
                
        except Exception as e:
            print(f"  ❌ Error with {config}: {e}")
    
    print("\n" + "=" * 40)
    print("🔍 Testing with actual chapter content...")
    
    # Test with actual chapter file
    try:
        with open('OVERLORD/chapter_x1.txt', 'r', encoding='utf-8') as f:
            content = f.read()[:500]  # First 500 chars
        
        print(f"Original content sample:\n{content[:200]}...")
        
        converter = opencc.OpenCC('s2t')
        translated = converter.convert(content)
        
        print(f"\nTranslated content sample:\n{translated[:200]}...")
        
        # Check if any characters were actually changed
        changed_chars = sum(1 for a, b in zip(content, translated) if a != b)
        print(f"\nCharacters changed: {changed_chars} out of {len(content)}")
        
        if changed_chars > 0:
            print("✅ Translation is working!")
        else:
            print("❌ No translation occurred - content might already be Traditional Chinese")
            
    except Exception as e:
        print(f"❌ Error testing with chapter file: {e}")

if __name__ == "__main__":
    test_opencc_detailed()
