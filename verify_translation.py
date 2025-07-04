#!/usr/bin/env python3
"""
Compare original and translated files to verify translation worked
"""
import os
import opencc

def compare_translations():
    """Compare original and translated files"""
    print("🔍 Translation Verification Tool")
    print("=" * 50)
    
    original_dir = "OVERLORD"
    translated_dir = "OVERLORD_Traditional"
    
    if not os.path.exists(original_dir):
        print(f"❌ Original directory not found: {original_dir}")
        return
    
    if not os.path.exists(translated_dir):
        print(f"❌ Translated directory not found: {translated_dir}")
        return
    
    # Get chapter files
    original_files = [f for f in os.listdir(original_dir) if f.startswith('chapter_x') and f.endswith('.txt')]
    translated_files = [f for f in os.listdir(translated_dir) if f.startswith('chapter_x') and f.endswith('.txt')]
    
    print(f"📚 Original files: {len(original_files)}")
    print(f"📚 Translated files: {len(translated_files)}")
    
    # Compare first few files
    for filename in original_files[:3]:  # Check first 3 files
        if filename in translated_files:
            original_path = os.path.join(original_dir, filename)
            translated_path = os.path.join(translated_dir, filename)
            
            try:
                with open(original_path, 'r', encoding='utf-8') as f:
                    original = f.read()
                with open(translated_path, 'r', encoding='utf-8') as f:
                    translated = f.read()
                
                # Remove formatting differences for comparison
                orig_clean = original.replace('\n', '').replace(' ', '')
                trans_clean = translated.replace('\n', '').replace(' ', '')
                
                # Count changes
                changes = sum(1 for a, b in zip(orig_clean, trans_clean) if a != b)
                percentage = (changes / len(orig_clean)) * 100 if orig_clean else 0
                
                print(f"\n📄 {filename}:")
                print(f"  Original length: {len(original)} chars")
                print(f"  Translated length: {len(translated)} chars")
                print(f"  Characters changed: {changes} ({percentage:.1f}%)")
                
                if changes > 0:
                    print(f"  ✅ Translation detected")
                    # Show sample changes
                    print(f"  Sample original: {original[:100]}...")
                    print(f"  Sample translated: {translated[:100]}...")
                else:
                    print(f"  ⚠️  No changes detected")
                    
            except Exception as e:
                print(f"  ❌ Error comparing {filename}: {e}")
        else:
            print(f"  ❌ {filename} not found in translated directory")

if __name__ == "__main__":
    compare_translations()
