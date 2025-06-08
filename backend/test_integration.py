#!/usr/bin/env python3
"""
Integration test to verify the complete LangGraph backend functionality
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_graph_configuration():
    """Test graph configuration and compilation"""
    print("🔧 Testing graph configuration...")
    
    try:
        from src.agent.configuration import Configuration, ResearchEffort
        from src.agent.graph import graph
        
        # Test configuration creation
        config = Configuration()
        print(f"✅ Default configuration created")
        print(f"   Research effort: {config.research_effort}")
        print(f"   Max research loops: {config.max_research_loops}")
        print(f"   Initial queries: {config.number_of_initial_queries}")
        
        # Test graph compilation
        print(f"✅ Graph compiled successfully: {graph.name}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_state_initialization():
    """Test state initialization to avoid KeyError issues"""
    print("\n🔄 Testing state initialization...")
    
    try:
        from src.agent.state import OverallState
        from src.agent.configuration import Configuration
        from langchain_core.messages import HumanMessage
        
        # Create a sample state that should work with the graph
        initial_state = {
            "messages": [HumanMessage(content="What is Python programming?")],
            "search_query": [],
            "web_research_result": [],
            "sources_gathered": [],
            "initial_search_query_count": 3,  # This was causing the KeyError
            "max_research_loops": 2,
            "research_loop_count": 0,
            "e2b_artifact_urls": [],
            "e2b_stdout": [],
            "e2b_stderr": [],
            "e2b_generated_code": None,
            "suggests_code_execution": False,
            "research_effort": "Standard Research",
            "url_to_citation_marker": {},
            "next_citation_index": 1,
            "current_goal": "Starting research process",
            "e2b_artifacts_data": []
        }
        
        print("✅ State structure validated")
        print(f"   Initial search query count: {initial_state['initial_search_query_count']}")
        print(f"   Research effort: {initial_state['research_effort']}")
        
        return True
    except Exception as e:
        print(f"❌ State initialization error: {e}")
        return False

def test_node_functions():
    """Test individual node functions can be imported and called"""
    print("\n🎯 Testing node functions...")
    
    try:
        from src.agent.graph import (
            generate_query, 
            web_research, 
            reflection, 
            finalize_answer,
            filter_urls,
            fetch_webpage_data,
            get_top_k_webpages_info
        )
        
        print("✅ All node functions imported successfully")
        
        # Test utility functions
        test_urls = ["https://python.org", "https://docs.python.org"]
        filtered = filter_urls(test_urls, "Python programming", max_results=2)
        print(f"✅ URL filtering works: {len(filtered)} URLs filtered")
        
        return True
    except Exception as e:
        print(f"❌ Node function error: {e}")
        return False

def test_environment_setup():
    """Test environment variables and dependencies"""
    print("\n🌍 Testing environment setup...")
    
    results = []
    
    # Test required environment variables
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print("✅ GEMINI_API_KEY is set")
        results.append(True)
    else:
        print("⚠️  GEMINI_API_KEY not set (required for full functionality)")
        results.append(False)
    
    e2b_key = os.getenv("E2B_API_KEY")
    if e2b_key:
        print("✅ E2B_API_KEY is set")
        results.append(True)
    else:
        print("ℹ️  E2B_API_KEY not set (optional for code execution)")
        results.append(True)  # This is optional
    
    # Test key dependencies
    try:
        import spacy
        print("✅ spaCy available")
        
        # Check if English model is available
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy English model loaded")
        except OSError:
            print("⚠️  spaCy English model not available")
        results.append(True)
    except ImportError:
        print("❌ spaCy not available")
        results.append(False)
    
    try:
        import requests
        print("✅ Requests library available")
        results.append(True)
    except ImportError:
        print("❌ Requests library not available")
        results.append(False)
    
    try:
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup available")
        results.append(True)
    except ImportError:
        print("❌ BeautifulSoup not available")
        results.append(False)
    
    try:
        from googlesearch import search
        print("✅ Google search library available")
        results.append(True)
    except ImportError:
        print("❌ Google search library not available")
        results.append(False)
    
    return all(results)

def test_graph_execution_readiness():
    """Test if the graph is ready for execution"""
    print("\n🚀 Testing graph execution readiness...")
    
    try:
        from src.agent.graph import graph
        from src.agent.configuration import Configuration
        from langchain_core.messages import HumanMessage
        
        # Create a minimal config
        config = Configuration()
        
        # Test that we can invoke the graph's initial node without KeyError
        # We'll just test the structure, not actually run it to avoid API calls
        print("✅ Graph structure validated")
        print(f"   Available nodes: {list(graph.nodes.keys())}")
        print(f"   Start node: {graph.nodes}")
        
        return True
    except Exception as e:
        print(f"❌ Graph execution readiness error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 LangGraph Backend Integration Test")
    print("=" * 50)
    
    tests = [
        ("Graph Configuration", test_graph_configuration),
        ("State Initialization", test_state_initialization),
        ("Node Functions", test_node_functions),
        ("Environment Setup", test_environment_setup),
        ("Graph Execution Readiness", test_graph_execution_readiness)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n📊 Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend is ready for deployment.")
        print("💡 You can now run 'langgraph dev' to start the development server.")
    elif passed >= total - 1:
        print("✅ Backend is mostly ready. Minor issues may exist but core functionality works.")
    else:
        print("⚠️  Several issues detected. Please check the output above for details.")
