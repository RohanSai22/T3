#!/usr/bin/env python3
"""
Simple test script to verify the backend API is working correctly.
"""
import requests
import json

# Test basic API connectivity
def test_api_connectivity():
    """Test if the API is accessible."""
    try:
        response = requests.get("http://127.0.0.1:2024/docs")
        print(f"✅ API Docs accessible: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ API not accessible: {e}")
        return False

# Test assistant list endpoint
def test_assistants_endpoint():
    """Test the assistants endpoint."""
    try:
        response = requests.get("http://127.0.0.1:2024/assistants")
        print(f"✅ Assistants endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Available assistants: {len(data)}")
            if data:
                print(f"🤖 First assistant: {data[0].get('assistant_id', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ Assistants endpoint error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing LangGraph API Backend")
    print("=" * 40)
    
    api_ok = test_api_connectivity()
    if api_ok:
        test_assistants_endpoint()
    
    print("\n✨ Test completed!")
