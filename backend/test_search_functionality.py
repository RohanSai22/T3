#!/usr/bin/env python3
"""
Test script to verify the enhanced Google search functionality
"""
import sys
import os

import src.agent.graph as graph_module
from googlesearch import search as google_search_lib

def test_url_filtering():
    """Test URL filtering functionality"""
    print("🔍 Testing URL filtering...")
    
    # Sample URLs for testing
    test_urls = [
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "https://www.python.org/",
        "https://docs.python.org/3/",
        "https://www.youtube.com/watch?v=python",
        "https://stackoverflow.com/questions/tagged/python",
        "https://realpython.com/python-basics/",
        "https://github.com/python/cpython"
    ]
    query = "Python programming language"
    filtered = graph_module.filter_urls(test_urls, query, max_results=3)
    
    print(f"✅ Original URLs: {len(test_urls)}")
    print(f"✅ Filtered URLs: {len(filtered)}")
    print(f"📋 Top filtered URLs:")
    for i, url in enumerate(filtered, 1):
        print(f"   {i}. {url}")
    
    return len(filtered) > 0

def test_webpage_data_fetch():
    """Test webpage data fetching"""
    print("\n📄 Testing webpage data fetching...")
    
    test_url = "https://httpbin.org/json"  # Simple JSON endpoint for testing
    try:
        data = graph_module.fetch_webpage_data(test_url, timeout=5)
        print(f"✅ Status: {data['status']}")
        print(f"✅ Title: {data['title'][:50]}...")
        print(f"✅ Content length: {len(data['content'])} characters")
        return data['status'] == 'success'
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_google_search_integration():
    """Test Google search integration"""
    print("\n🔍 Testing Google Search integration...")
    
    try:
        # Simple search query
        query = "Python programming"
        results = list(google_search_lib(query, num=3, lang="en", pause=1.0))
        
        print(f"✅ Google search returned {len(results)} results")
        if results:
            print("📋 Sample results:")
            for i, url in enumerate(results[:2], 1):
                print(f"   {i}. {url}")
        
        return len(results) > 0
    except Exception as e:
        print(f"❌ Google search error: {e}")
        return False

def test_complete_pipeline():
    """Test the complete search and scrape pipeline"""
    print("\n🔄 Testing complete search pipeline...")
    
    try:
        query = "Python programming tutorial"
        
        # Get search results
        search_urls = list(google_search_lib(query, num=5, lang="en", pause=1.0))
        if search_urls:
            # Process with our pipeline
            top_pages = graph_module.get_top_k_webpages_info(search_urls, query, k=2)
            
            print(f"✅ Found {len(search_urls)} search results")
            print(f"✅ Successfully processed {len(top_pages)} pages")
            
            for i, page in enumerate(top_pages, 1):
                print(f"   {i}. {page['title'][:50]}...")
                print(f"      Status: {page['status']}")
                print(f"      Content: {len(page['content'])} chars")
            
            return len(top_pages) > 0
        else:
            print("❌ No search results found")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Enhanced Google Search Functionality")
    print("=" * 50)
    
    tests = [
        ("URL Filtering", test_url_filtering),
        ("Webpage Data Fetch", test_webpage_data_fetch),
        ("Google Search Integration", test_google_search_integration),
        ("Complete Pipeline", test_complete_pipeline)
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
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced search functionality is working.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
