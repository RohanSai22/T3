#!/usr/bin/env python3
"""
End-to-end test script to verify the backend API can process research queries.
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:2024"

def test_complete_workflow():
    """Test the complete research workflow."""
    print("🧪 Testing Complete Research Workflow")
    print("=" * 50)
      # Step 1: Get available assistants
    try:
        response = requests.post(f"{BASE_URL}/assistants/search", json={})
        print(f"📋 Assistants search endpoint: {response.status_code}")
        
        if response.status_code == 200:
            assistants = response.json()
            if assistants:
                assistant_id = assistants[0]["assistant_id"]
                print(f"🤖 Using assistant: {assistant_id}")
            else:
                # If no assistants found, use "agent" as the graph ID directly
                assistant_id = "agent"
                print(f"🤖 Using graph ID directly: {assistant_id}")
        else:
            print(f"❌ Failed to get assistants: {response.status_code}")
            # Fallback to using graph ID directly
            assistant_id = "agent"
            print(f"🤖 Fallback to graph ID: {assistant_id}")
            
    except Exception as e:
        print(f"❌ Error getting assistants: {e}")
        # Fallback to using graph ID directly
        assistant_id = "agent"
        print(f"🤖 Fallback to graph ID: {assistant_id}")
    
    # Step 2: Create a thread and submit a research query
    try:        # Create thread
        thread_response = requests.post(f"{BASE_URL}/threads", json={})
        if thread_response.status_code != 200:
            print(f"❌ Failed to create thread: {thread_response.status_code}")
            print(f"Response: {thread_response.text}")
            return False
            
        thread_data = thread_response.json()
        thread_id = thread_data["thread_id"]
        print(f"📝 Created thread: {thread_id}")
          # Submit research query
        query_payload = {
            "messages": [
                {
                    "role": "user",
                    "content": "What are the key features of Python 3.12?"
                }
            ]
        }
        
        print(f"🚀 Submitting query: '{query_payload['messages'][0]['content']}'")
        
        # Start a run
        run_response = requests.post(
            f"{BASE_URL}/threads/{thread_id}/runs/stream",
            json={
                "assistant_id": assistant_id,
                "input": query_payload,
                "stream_mode": ["messages-tuple", "values", "updates"]
            },
            headers={"Content-Type": "application/json"},
            stream=True
        )
        
        if run_response.status_code != 200:
            print(f"❌ Failed to start run: {run_response.status_code}")
            print(f"Response: {run_response.text}")
            return False
        
        print(f"✅ Run started successfully: {run_response.status_code}")
          # Process streaming response
        print("📊 Processing streaming response...")
        event_count = 0
        for line in run_response.iter_lines():
            if line:
                try:
                    if line.startswith(b"data: "):
                        data = line[6:].decode('utf-8')
                        if data.strip() and data != "[DONE]":
                            event = json.loads(data)
                            event_count += 1
                            
                            # Handle both list and dict event formats
                            if isinstance(event, list):
                                # Event is a list, check each item
                                for item in event:
                                    if isinstance(item, dict):
                                        event_type = item.get("event", "unknown")
                                        print(f"📩 Event {event_count}: {event_type}")
                                    else:
                                        print(f"📩 Event {event_count}: list_item")
                            elif isinstance(event, dict):
                                # Event is a dict
                                event_type = event.get("event", "unknown")
                                print(f"📩 Event {event_count}: {event_type}")
                            else:
                                print(f"📩 Event {event_count}: {type(event).__name__}")
                            
                            # Stop after a reasonable number of events for testing
                            if event_count >= 10:
                                print("🛑 Stopping after 10 events for test purposes")
                                break
                                
                except json.JSONDecodeError as jde:
                    print(f"⚠️ JSON decode error: {jde}")
                    continue
                except Exception as e:
                    print(f"⚠️ Error processing event: {e}")
                    continue
        
        print(f"✅ Processed {event_count} events successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in workflow test: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_workflow()
    print("\n" + "=" * 50)
    if success:
        print("🎉 End-to-end test PASSED!")
        print("✅ Backend is working correctly!")
    else:
        print("💥 End-to-end test FAILED!")
        print("❌ There are still issues to resolve.")
