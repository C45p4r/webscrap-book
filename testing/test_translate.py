#!/usr/bin/env python3
"""
Test script to verify OpenCC translation works
"""
import opencc

def test_translation():
    """Test basic translation functionality"""
    print("🔤 Testing OpenCC Translation...")
    
    # Setup converter
    converter = opencc.OpenCC('s2t')  # Simplified to Traditional
    
    # Test text
    simplified_text = "这是一个测试文本，用于验证简体中文到繁体中文的转换。"
    traditional_text = converter.convert(simplified_text)
    
    print(f"Original (Simplified): {simplified_text}")
    print(f"Translated (Traditional): {traditional_text}")
    
    # Test with OVERLORD sample
    sample_text = "魔导王的怒火"
    translated_sample = converter.convert(sample_text)
    
    print(f"\nSample Translation:")
    print(f"Original: {sample_text}")
    print(f"Translated: {translated_sample}")
    
    print("\n✅ OpenCC translation test successful!")

if __name__ == "__main__":
    test_translation()
