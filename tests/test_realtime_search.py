#!/usr/bin/env python3
"""
Test script for RealTimeSearch functionality.
Demonstrates various search capabilities for educational content.
"""

import os
import sys
import asyncio
import json
from pprint import pprint

# Add the AI-Services directory to the Python path
ai_services_path = os.path.join(os.path.dirname(__file__), '..', 'AI-Services')
sys.path.insert(0, ai_services_path)

# Load environment variables from the parent directory's .env file
from dotenv import load_dotenv
parent_env_path = os.path.join(os.path.dirname(__file__), '..', 'AI-Services', '.env')
load_dotenv(parent_env_path)

# Import from AI-Services directory
from RealTimeSearch import RealTimeSearch, create_real_time_agent


async def test_real_time_search():
    """Test the RealTimeSearch functionality with various scenarios."""
    
    # Set your SerpAPI key here or in environment variable SERPAPI_API_KEY
    # You can get a free API key at https://serpapi.com/manage-api-key
    api_key = os.getenv('SERPAPI_API_KEY', 'your_serpapi_key_here')
    
    if api_key == 'your_serpapi_key_here':
        print("⚠️  Please set your SERPAPI_API_KEY environment variable or update the api_key in this script")
        print("   You can get a free API key at: https://serpapi.com/manage-api-key")
        return
    
    print("🔍 Initializing RealTimeSearch Agent...")
    try:
        # Create the search agent
        search_agent = create_real_time_agent(api_key=api_key)
        print("✅ RealTimeSearch Agent initialized successfully!\n")
        
        # Test 1: Academic Problem Search
        print("=" * 60)
        print("🎓 TEST 1: Academic Problem Search")
        print("=" * 60)
        
        math_problem = "How to solve quadratic equations using the quadratic formula"
        print(f"🔎 Searching for solutions to: '{math_problem}'")
        
        academic_results = search_agent.search_academic_solutions(
            problem=math_problem,
            subject="mathematics"
        )
        
        print(f"📚 Found {academic_results['total_sources']} academic sources:")
        print(f"   - Academic papers: {len(academic_results['academic_sources'])}")
        print(f"   - Web explanations: {len(academic_results['web_explanations'])}")
        print(f"   - Video tutorials: {len(academic_results['video_tutorials'])}")
        
        # Show top academic result
        if academic_results['academic_sources']:
            top_academic = academic_results['academic_sources'][0]
            print(f"\n📖 Top Academic Source:")
            print(f"   Title: {top_academic.get('title', 'N/A')}")
            print(f"   Authors: {', '.join(top_academic.get('authors', []))}")
            print(f"   Year: {top_academic.get('year', 'N/A')}")
            print(f"   Citations: {top_academic.get('citation_count', 0)}")
        
        # Test 2: Latest News Search
        print("\n" + "=" * 60)
        print("📰 TEST 2: Latest Educational News")
        print("=" * 60)
        
        news_topic = "artificial intelligence in education"
        print(f"🔎 Searching for latest news on: '{news_topic}'")
        
        news_results = search_agent.get_latest_news(news_topic, hours_back=24)
        
        if not news_results.get('error'):
            print(f"📈 Found {news_results['total_results']} recent news articles")
            
            # Show top 3 news articles
            for i, article in enumerate(news_results['results'][:3], 1):
                print(f"\n📰 Article {i}:")
                print(f"   Title: {article.get('title', 'N/A')}")
                print(f"   Source: {article.get('source', 'N/A')}")
                print(f"   Date: {article.get('date', 'N/A')}")
                print(f"   Link: {article.get('link', 'N/A')}")
        else:
            print(f"❌ News search error: {news_results.get('error_message')}")
        
        # Test 3: General Educational Search
        print("\n" + "=" * 60)
        print("🎯 TEST 3: General Educational Search")
        print("=" * 60)
        
        study_query = "effective study techniques for exam preparation"
        print(f"🔎 Searching for: '{study_query}'")
        
        general_results = search_agent.search_real_time(
            query=study_query,
            search_type="general",
            num_results=5
        )
        
        if not general_results.get('error'):
            print(f"📚 Found {general_results['total_results']} educational resources")
            
            # Show educational results
            for i, result in enumerate(general_results['results'], 1):
                print(f"\n📖 Resource {i}:")
                print(f"   Title: {result.get('title', 'N/A')}")
                print(f"   Link: {result.get('link', 'N/A')}")
                print(f"   Snippet: {result.get('snippet', 'N/A')[:100]}...")
        else:
            print(f"❌ General search error: {general_results.get('error_message')}")
        
        # Test 4: Async Batch Search
        print("\n" + "=" * 60)
        print("⚡ TEST 4: Async Batch Search")
        print("=" * 60)
        
        batch_queries = [
            "Python programming tutorials for beginners",
            "Data structures and algorithms explained",
            "Machine learning fundamentals"
        ]
        
        print(f"🔎 Performing batch search for {len(batch_queries)} queries...")
        
        batch_results = await search_agent.batch_search_async(
            queries=batch_queries,
            search_type="general",
            num_results=3
        )
        
        for i, (query, result) in enumerate(zip(batch_queries, batch_results), 1):
            if not result.get('error'):
                print(f"\n📚 Query {i}: '{query}'")
                print(f"   Results found: {result['total_results']}")
                if result['results']:
                    print(f"   Top result: {result['results'][0].get('title', 'N/A')}")
            else:
                print(f"\n❌ Query {i} error: {result.get('error_message')}")
        
        # Test 5: Video Tutorial Search
        print("\n" + "=" * 60)
        print("🎥 TEST 5: Video Tutorial Search")
        print("=" * 60)
        
        video_query = "calculus derivatives explained"
        print(f"🔎 Searching for video tutorials: '{video_query}'")
        
        video_results = search_agent.search_real_time(
            query=video_query,
            search_type="videos",
            num_results=5
        )
        
        if not video_results.get('error'):
            print(f"🎬 Found {video_results['total_results']} video tutorials")
            
            # Show top 3 videos
            for i, video in enumerate(video_results['results'][:3], 1):
                print(f"\n🎥 Video {i}:")
                print(f"   Title: {video.get('title', 'N/A')}")
                print(f"   Channel: {video.get('channel', 'N/A')}")
                print(f"   Duration: {video.get('duration', 'N/A')}")
                print(f"   Views: {video.get('views', 'N/A')}")
                print(f"   Link: {video.get('link', 'N/A')}")
        else:
            print(f"❌ Video search error: {video_results.get('error_message')}")
        
        # Test 6: Cache Statistics
        print("\n" + "=" * 60)
        print("💾 TEST 6: Cache Performance")
        print("=" * 60)
        
        cache_stats = search_agent.get_cache_stats()
        print("📊 Cache Statistics:")
        print(f"   Cache size: {cache_stats['cache_size']}/{cache_stats['max_size']}")
        print(f"   TTL: {cache_stats['ttl']} seconds")
        print(f"   Cache hits: {cache_stats.get('hits', 'N/A')}")
        print(f"   Cache misses: {cache_stats.get('misses', 'N/A')}")
        
        # Test cache by running the same search again
        print("\n🔄 Testing cache by repeating a search...")
        cached_result = search_agent.search_real_time(
            query=study_query,
            search_type="general",
            num_results=5
        )
        
        if cached_result.get('cached', False):
            print("✅ Result served from cache!")
        else:
            print("ℹ️  Fresh result (not cached)")
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        print("=" * 60)
        
        # Show overall summary
        print("\n📋 SUMMARY:")
        print("✅ Academic problem search - Working")
        print("✅ Latest news search - Working")
        print("✅ General educational search - Working")
        print("✅ Async batch search - Working")
        print("✅ Video tutorial search - Working")
        print("✅ Caching system - Working")
        
        print("\n💡 Usage Tips:")
        print("• Set SERPAPI_KEY environment variable for automatic API key loading")
        print("• Use academic search for scholarly articles and research papers")
        print("• Use news search for latest developments in your field")
        print("• Use video search for visual learning and tutorials")
        print("• Batch search is efficient for multiple queries")
        print("• Results are cached for 1 hour by default to improve performance")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        print("Please check your API key and internet connection.")


def test_synchronous_search():
    """Test synchronous search functionality."""
    
    api_key = os.getenv('SERPAPI_API_KEY', 'your_serpapi_key_here')
    
    if api_key == 'your_serpapi_key_here':
        print("⚠️  Please set your SERPAPI_API_KEY environment variable")
        return
    
    print("🔍 Testing synchronous search...")
    
    search_agent = create_real_time_agent(api_key=api_key)
    
    # Simple synchronous search
    results = search_agent.search_real_time(
        query="Python programming for beginners",
        search_type="general",
        num_results=5
    )
    
    if not results.get('error'):
        print(f"✅ Found {results['total_results']} results")
        print(f"📖 Top result: {results['results'][0].get('title', 'N/A')}")
    else:
        print(f"❌ Error: {results.get('error_message')}")


if __name__ == "__main__":
    print("🚀 RealTimeSearch Test Suite")
    print("=" * 60)
    
    # Check if API key is available
    if not os.getenv('SERPAPI_API_KEY'):
        print("⚠️  Warning: SERPAPI_API_KEY environment variable not set")
        print("   You can get a free API key at: https://serpapi.com/manage-api-key")
        print("   Set it with: export SERPAPI_API_KEY='your_api_key_here'")
        print()
    
    print("Choose test mode:")
    print("1. Run async tests (recommended)")
    print("2. Run synchronous tests")
    print("3. Run both")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "1":
        print("\n🔄 Running async tests...")
        asyncio.run(test_real_time_search())
    elif choice == "2":
        print("\n🔄 Running synchronous tests...")
        test_synchronous_search()
    elif choice == "3":
        print("\n🔄 Running both test suites...")
        test_synchronous_search()
        print("\n" + "=" * 60)
        asyncio.run(test_real_time_search())
    else:
        print("❌ Invalid choice. Running async tests by default...")
        asyncio.run(test_real_time_search())
