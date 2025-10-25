#!/usr/bin/env python3
"""
Test script to verify video creator integration
"""

def test_imports():
    """Test that all imports work correctly"""
    try:
        from video_creator import create_video, list_available_topics, list_available_audio_topics
        print("✅ Video creator imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_available_topics():
    """Test listing available topics"""
    try:
        from video_creator import list_available_topics, list_available_audio_topics
        
        image_topics = list_available_topics()
        audio_topics = list_available_audio_topics()
        
        print(f"✅ Found {len(image_topics)} image topics: {image_topics}")
        print(f"✅ Found {len(audio_topics)} audio topics: {audio_topics}")
        return True
    except Exception as e:
        print(f"❌ Topic listing error: {e}")
        return False

def main():
    print("🧪 Testing Video Creator Integration")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        return False
    
    # Test topic listing
    if not test_available_topics():
        return False
    
    print("\n🎉 All tests passed! Video creator integration is working.")
    return True

if __name__ == "__main__":
    main()
