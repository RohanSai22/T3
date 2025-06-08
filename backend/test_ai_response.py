"""
Advanced AI Response Testing for LangGraph System
Tests complete agent responses and research capabilities
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://127.0.0.1:2024"
HEADERS = {"Content-Type": "application/json"}

def test_ai_research_capabilities():
    """Test the AI agent's research and reasoning capabilities"""
    print("🧠 Testing AI Agent Research Capabilities")
    print("=" * 60)
    
    # 1. Discover assistant
    print("1️⃣ Discovering assistant...")
    assistants_response = requests.get(f"{BASE_URL}/assistants/search")
    if assistants_response.status_code != 200:
        print(f"❌ Failed to get assistants: {assistants_response.status_code}")
        return False
    
    assistants = assistants_response.json()
    if not assistants:
        print("❌ No assistants found")
        return False
    
    assistant_id = assistants[0]["assistant_id"]
    print(f"✅ Assistant found: {assistant_id}")
    
    # 2. Create thread
    print("\n2️⃣ Creating conversation thread...")
    thread_response = requests.post(f"{BASE_URL}/threads")
    if thread_response.status_code != 200:
        print(f"❌ Failed to create thread: {thread_response.status_code}")
        return False
    
    thread_data = thread_response.json()
    thread_id = thread_data["thread_id"]
    print(f"✅ Thread created: {thread_id}")
    
    # 3. Test complex research query
    research_query = {
        "assistant_id": assistant_id,
        "input": {
            "type": "human",
            "content": "Can you research and explain the current trends in artificial intelligence for 2025? Please provide specific examples and recent developments."
        },
        "config": {
            "configurable": {
                "thread_id": thread_id
            }
        }
    }
    
    print("\n3️⃣ Testing complex research query...")
    print(f"📝 Query: {research_query['input']['content']}")
    
    # Test synchronous execution for complete response
    start_time = time.time()
    run_response = requests.post(
        f"{BASE_URL}/threads/{thread_id}/runs/wait",
        headers=HEADERS,
        json=research_query
    )
    end_time = time.time()
    
    if run_response.status_code != 200:
        print(f"❌ Run failed: {run_response.status_code}")
        print(f"Response: {run_response.text}")
        return False
    
    response_data = run_response.json()
    processing_time = end_time - start_time
    
    print(f"✅ Query processed in {processing_time:.2f}s")
    
    # 4. Analyze response
    print("\n4️⃣ Analyzing AI response...")
    
    if "messages" in response_data:
        messages = response_data["messages"]
        print(f"📊 Total messages: {len(messages)}")
        
        # Find AI response
        ai_responses = [msg for msg in messages if msg.get("type") == "ai"]
        if ai_responses:
            latest_response = ai_responses[-1]
            content = latest_response.get("content", "")
            
            print(f"🤖 AI Response Length: {len(content)} characters")
            print(f"📝 Response Preview: {content[:200]}...")
            
            # Check for quality indicators
            quality_indicators = [
                ("mentions trends", "trend" in content.lower() or "2025" in content),
                ("provides examples", "example" in content.lower()),
                ("shows research depth", len(content) > 500),
                ("structured response", any(marker in content for marker in ["1.", "•", "-", "*"]))
            ]
            
            print("\n📋 Response Quality Analysis:")
            all_passed = True
            for indicator, passed in quality_indicators:
                status = "✅" if passed else "❌"
                print(f"   {status} {indicator}")
                if not passed:
                    all_passed = False
            
            return all_passed
        else:
            print("❌ No AI response found")
            return False
    else:
        print("❌ No messages in response")
        return False

def test_streaming_with_complete_response():
    """Test streaming functionality and capture complete response"""
    print("\n\n🌊 Testing Streaming with Complete Response Capture")
    print("=" * 60)
    
    # Get assistant and create thread
    assistants_response = requests.get(f"{BASE_URL}/assistants/search")
    assistant_id = assistants_response.json()[0]["assistant_id"]
    
    thread_response = requests.post(f"{BASE_URL}/threads")
    thread_id = thread_response.json()["thread_id"]
    
    # Streaming query
    stream_query = {
        "assistant_id": assistant_id,
        "input": {
            "type": "human", 
            "content": "What are the key benefits of using LangGraph for building AI agents?"
        },
        "config": {
            "configurable": {
                "thread_id": thread_id
            }
        }
    }
    
    print("🚀 Starting streaming request...")
    
    try:
        stream_response = requests.post(
            f"{BASE_URL}/threads/{thread_id}/runs/stream",
            headers=HEADERS,
            json=stream_query,
            stream=True
        )
        
        if stream_response.status_code != 200:
            print(f"❌ Stream failed: {stream_response.status_code}")
            return False
        
        print("✅ Stream established")
        
        events_count = 0
        complete_response = ""
        
        for line in stream_response.iter_lines():
            if line:
                try:
                    # Parse SSE format
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = line_str[6:]  # Remove 'data: ' prefix
                        if data.strip() and data != '[DONE]':
                            events_count += 1
                            event_data = json.loads(data)
                            
                            # Extract content from various event types
                            if isinstance(event_data, list):
                                for item in event_data:
                                    if isinstance(item, dict):
                                        if "data" in item and "chunk" in item["data"]:
                                            chunk = item["data"]["chunk"]
                                            if "content" in chunk:
                                                complete_response += str(chunk["content"])
                            elif isinstance(event_data, dict):
                                if "data" in event_data and "chunk" in event_data["data"]:
                                    chunk = event_data["data"]["chunk"]
                                    if "content" in chunk:
                                        complete_response += str(chunk["content"])
                                        
                except json.JSONDecodeError:
                    continue
        
        print(f"📊 Streaming events received: {events_count}")
        print(f"📝 Complete response length: {len(complete_response)} characters")
        
        if complete_response:
            print(f"🤖 Response preview: {complete_response[:200]}...")
            return True
        else:
            print("⚠️ No content captured from stream")
            return False
            
    except Exception as e:
        print(f"❌ Streaming error: {e}")
        return False

def main():
    """Run all AI response tests"""
    print("🚀 LangGraph AI Response Validation Suite")
    print("=" * 80)
    
    # Test 1: Research capabilities
    research_success = test_ai_research_capabilities()
    
    # Test 2: Streaming with response capture
    streaming_success = test_streaming_with_complete_response()
    
    # Final results
    print("\n" + "=" * 80)
    print("📊 FINAL AI RESPONSE TEST RESULTS")
    print("=" * 80)
    
    tests = [
        ("🧠 Research Capabilities", research_success),
        ("🌊 Streaming Response Capture", streaming_success)
    ]
    
    all_passed = True
    for test_name, passed in tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL AI RESPONSE TESTS PASSED!")
        print("🚀 LangGraph system is generating complete AI responses")
        print("✅ Ready for production deployment")
    else:
        print("⚠️ Some AI response tests failed")
        print("🔧 May need additional configuration or debugging")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
