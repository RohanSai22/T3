"""
Simple test to see the actual AI response content
"""

import requests
import json

BASE_URL = "http://127.0.0.1:2024"

def test_ai_response_content():
    print("🤖 Testing AI Response Content")
    print("=" * 50)
    
    # 1. Create thread
    thread_response = requests.post(f"{BASE_URL}/threads")
    thread_id = thread_response.json()["thread_id"]
    print(f"📝 Thread: {thread_id}")
    
    # 2. Send message and wait for complete response
    message = {
        "input": {
            "type": "human",
            "content": "What are the main benefits of using LangGraph? Please provide a detailed explanation."
        }
    }
    
    print("\n💭 Sending query and waiting for response...")
    response = requests.post(
        f"{BASE_URL}/threads/{thread_id}/runs/wait",
        headers={"Content-Type": "application/json"},
        json=message
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Response received!")
        
        if "messages" in data:
            messages = data["messages"]
            print(f"\n📊 Total messages: {len(messages)}")
            
            for i, msg in enumerate(messages):
                msg_type = msg.get("type", "unknown")
                content = msg.get("content", "")
                print(f"\n📩 Message {i+1} ({msg_type}):")
                if content:
                    if len(content) > 300:
                        print(f"   {content[:300]}...")
                        print(f"   [Total length: {len(content)} characters]")
                    else:
                        print(f"   {content}")
                else:
                    print("   [No content]")
        else:
            print("⚠️ No messages found in response")
            print(f"Response keys: {list(data.keys())}")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_ai_response_content()
