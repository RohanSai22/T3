import requests
import os
import time
import uuid

# BASE_URL can be overridden by an environment variable
BASE_URL = os.getenv("LANGGRAPH_BASE_URL", "http://127.0.0.1:2024")
ASSISTANT_ID = "" # Will be fetched

def fetch_assistant_id():
    """Fetches the first available assistant_id."""
    global ASSISTANT_ID
    if ASSISTANT_ID:
        return ASSISTANT_ID
    try:
        response = requests.post(f"{BASE_URL}/assistants/search", json={}, timeout=10)
        response.raise_for_status()
        assistants = response.json()
        if assistants and isinstance(assistants, list) and assistants[0].get("assistant_id"):
            ASSISTANT_ID = assistants[0]["assistant_id"]
            print(f"Fetched Assistant ID: {ASSISTANT_ID}")
            return ASSISTANT_ID
        else:
            raise ValueError("No assistants found or unexpected response format.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching assistant ID: {e}")
        # Fallback or re-raise, depending on how critical this is.
        # For now, let's use a default if fetching fails, assuming one might be registered.
        ASSISTANT_ID = "agent"
        print(f"Using default Assistant ID: {ASSISTANT_ID}")
        return ASSISTANT_ID
    except Exception as e:
        print(f"An unexpected error occurred while fetching assistant ID: {e}")
        ASSISTANT_ID = "agent"
        print(f"Using default Assistant ID due to unexpected error: {ASSISTANT_ID}")
        return ASSISTANT_ID


def run_test_query(thread_id: str, assistant_id: str, query: str, config: dict = None):
    """Helper function to run a query and get the final AI response."""
    payload = {
        "assistant_id": assistant_id,
        "input": {"messages": [{"type": "human", "content": query}]},
    }
    if config:
        payload.update(config)

    # Use the /wait endpoint for simplicity in testing final output
    response = requests.post(
        f"{BASE_URL}/threads/{thread_id}/runs/wait",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=300 # Increased timeout for potentially long research
    )
    response.raise_for_status() # Will raise an exception for 4xx/5xx status codes
    return response.json()

def test_health_check():
    """Test if the server is running and API docs are accessible."""
    print("\n--- Test: Server Health Check ---")
    response = requests.get(f"{BASE_URL}/docs", timeout=10)
    assert response.status_code == 200, f"Health check failed: API docs not accessible (status {response.status_code})"
    print("Health check: PASSED")

def test_simple_query_normal_mode():
    """Test a simple query in Normal research mode."""
    print("\n--- Test: Simple Query (Normal Mode) ---")
    assistant_id = fetch_assistant_id()
    thread_id = str(uuid.uuid4()) # Create a new thread ID for each test run

    query = "What is the capital of France?"

    start_time = time.time()
    result = run_test_query(thread_id, assistant_id, query)
    end_time = time.time()

    print(f"Query processed in {end_time - start_time:.2f}s")

    assert "messages" in result, "Response JSON does not contain 'messages'"
    messages = result["messages"]
    assert isinstance(messages, list), "'messages' is not a list"

    ai_messages = [msg for msg in messages if msg.get("type") == "ai"]
    assert len(ai_messages) > 0, "No AI message found in the response"

    last_ai_message_content = ai_messages[-1].get("content")
    assert last_ai_message_content, "AI message content is empty"
    assert isinstance(last_ai_message_content, str), "AI message content is not a string"
    print(f"AI Response (Normal Mode): {last_ai_message_content[:150]}...")
    print("Simple Query (Normal Mode): PASSED")

def test_deep_research_query():
    """Test a query that should invoke Deep Research mode and potentially E2B."""
    print("\n--- Test: Deep Research Query ---")
    assistant_id = fetch_assistant_id()
    thread_id = str(uuid.uuid4())

    # This query is more likely to trigger E2B if configured for deep research
    query = "What were the main developments in LangGraph framework in the last month? Summarize them."

    # Configuration for Deep Research mode
    config_payload = {"configurable": {"assistant_id": assistant_id, "research_effort": "Deep Research"}}

    start_time = time.time()
    result = run_test_query(thread_id, assistant_id, query, config=config_payload)
    end_time = time.time()

    print(f"Query processed in {end_time - start_time:.2f}s")

    assert "messages" in result, "Response JSON does not contain 'messages'"
    messages = result["messages"]
    assert isinstance(messages, list), "'messages' is not a list"

    ai_messages = [msg for msg in messages if msg.get("type") == "ai"]
    assert len(ai_messages) > 0, "No AI message found in the response"

    last_ai_message_content = ai_messages[-1].get("content")
    assert last_ai_message_content, "AI message content is empty"
    assert isinstance(last_ai_message_content, str), "AI message content is not a string"
    print(f"AI Response (Deep Research): {last_ai_message_content[:150]}...")

    # Check for e2b_artifacts_data - it should be present, even if empty
    assert "e2b_artifacts_data" in result, "Response JSON does not contain 'e2b_artifacts_data'"
    if result.get("e2b_artifacts_data"):
        print(f"E2B Artifacts found: {len(result['e2b_artifacts_data'])}")
    else:
        print("E2B Artifacts: None produced (as expected for some queries or if E2B is disabled/errors).")

    print("Deep Research Query: PASSED")

def main():
    """Run all tests."""
    print("🚀 Starting LangGraph Backend Comprehensive Tests 🚀")
    print(f"Targeting BASE_URL: {BASE_URL}")

    all_passed = True
    tests_to_run = [
        test_health_check,
        test_simple_query_normal_mode,
        test_deep_research_query,
    ]

    for test_func in tests_to_run:
        try:
            test_func()
        except AssertionError as e:
            print(f"🛑 TEST FAILED: {test_func.__name__} - {e}")
            all_passed = False
        except requests.exceptions.HTTPError as e:
            print(f"🛑 TEST FAILED (HTTP Error): {test_func.__name__} - {e.response.status_code} - {e.response.text}")
            all_passed = False
        except Exception as e:
            print(f"🛑 TEST FAILED (Unexpected Error): {test_func.__name__} - {type(e).__name__}: {e}")
            all_passed = False
            import traceback
            traceback.print_exc() # Print full traceback for unexpected errors

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉🎉🎉 ALL TESTS PASSED! LangGraph backend appears healthy. 🎉🎉🎉")
    else:
        print("❌❌❌ SOME TESTS FAILED. Please review the output above. ❌❌❌")
    print("=" * 60)

if __name__ == "__main__":
    main()
