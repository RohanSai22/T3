#!/usr/bin/env python3
"""
Debug test to see the actual content of streaming events.
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:2024"

def debug_streaming_events():
    """Debug streaming events by showing their full content."""
    print("🔍 Debug Streaming Events")
    print("=" * 50)
    
    try:
        # Get assistant
        response = requests.post(f"{BASE_URL}/assistants/search", json={})
        if response.status_code == 200:
            assistants = response.json()
            assistant_id = assistants[0]["assistant_id"] if assistants else "agent"
            print(f"🤖 Using assistant: {assistant_id}")
        else:
            assistant_id = "agent"
            print(f"🤖 Fallback to: {assistant_id}")
        
        # Create thread
        thread_response = requests.post(f"{BASE_URL}/threads")
        if thread_response.status_code != 200:
            print(f"❌ Failed to create thread: {thread_response.status_code}")
            return False
            
        thread_data = thread_response.json()
        thread_id = thread_data["thread_id"]
        print(f"📝 Created thread: {thread_id}")
        
        # Submit simple query
        query_payload = {
            "messages": [
                {
                    "type": "human",
                    "content": "Hello! What is 2+2?",
                    "id": str(int(time.time()))
                }
            ]
        }
        
        print(f"🚀 Submitting simple query...")
        
        # Start a run with streaming
        run_response = requests.post(
            f"{BASE_URL}/threads/{thread_id}/runs/stream",
            json={
                "assistant_id": assistant_id,
                "input": query_payload,
                "stream_mode": ["values", "updates", "debug"]
            },
            headers={"Content-Type": "application/json"},
            stream=True
        )
        
        if run_response.status_code != 200:
            print(f"❌ Failed to start run: {run_response.status_code}")
            print(f"Response: {run_response.text}")
            return False
        
        print(f"✅ Run started successfully: {run_response.status_code}")
        print("📊 Processing streaming events with full content...")
        
        event_count = 0
        for line in run_response.iter_lines():
            if line:
                try:
                    if line.startswith(b"data: "):
                        data = line[6:].decode('utf-8')
                        if data.strip() and data != "[DONE]":
                            event = json.loads(data)
                            event_count += 1
                            
                            print(f"\n📩 Event {event_count}:")
                            print(f"   Type: {type(event).__name__}")
                            
                            if isinstance(event, list):
                                print(f"   Length: {len(event)}")
                                for i, item in enumerate(event):
                                    print(f"   [{i}]: {type(item).__name__}")
                                    if isinstance(item, dict):
                                        print(f"        Keys: {list(item.keys())}")
                                        if 'event' in item:
                                            print(f"        Event: {item['event']}")
                                        if 'data' in item:
                                            print(f"        Data: {str(item['data'])[:100]}...")
                            elif isinstance(event, dict):
                                print(f"   Keys: {list(event.keys())}")
                                if 'event' in event:
                                    print(f"   Event: {event['event']}")
                                if 'data' in event:
                                    print(f"   Data: {str(event['data'])[:100]}...")
                            
                            # Stop after 5 events for debugging
                            if event_count >= 5:
                                print("\n🛑 Stopping after 5 events for debugging")
                                break
                                
                except json.JSONDecodeError as jde:
                    print(f"⚠️ JSON decode error: {jde}")
                    print(f"   Raw data: {data[:100]}...")
                    continue
                except Exception as e:
                    print(f"⚠️ Error processing event: {e}")
                    continue
        
        print(f"\n✅ Processed {event_count} events successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in debug test: {e}")
        return False

if __name__ == "__main__":
    success = debug_streaming_events()
    print("\n" + "=" * 50)
    if success:
        print("🎉 Debug test completed!")
    else:
        print("💥 Debug test failed!")
