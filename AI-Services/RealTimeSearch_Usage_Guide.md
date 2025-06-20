# RealTimeSearch Agent - Usage Guide

The `RealTimeSearch` class provides a comprehensive real-time search agent specifically designed for educational applications. It leverages SerpAPI to deliver fresh, relevant academic content and solutions.

## Features

### 🔍 **Multiple Search Types**
- **Academic Search**: Scholarly articles and research papers via Google Scholar
- **News Search**: Latest developments and current events
- **General Search**: Web results with educational content prioritization
- **Image Search**: Visual learning materials and diagrams
- **Video Search**: Educational tutorials and explanations via YouTube

### ⚡ **Performance Features**
- **Async Support**: Non-blocking searches for better performance
- **Batch Processing**: Multiple searches simultaneously
- **Intelligent Caching**: TTL-based caching with configurable duration
- **Educational Filtering**: Prioritizes content from educational domains

### 🎯 **Educational Focus**
- **Problem Solving**: Specialized search for academic problems
- **Multiple Sources**: Combines academic, web, and video resources
- **Subject-Specific**: Enhanced searches by academic subject
- **Recent Content**: Time-filtered searches for latest information

## Installation

### 1. Install Dependencies

```bash
pip install serpapi aiohttp cachetools requests pytz
```

Or add to your `requirements.txt`:
```
serpapi==0.2.0
aiohttp==3.10.12
cachetools==5.5.2
requests==2.32.4
pytz==2025.2
```

### 2. Get SerpAPI Key

1. Sign up at [SerpAPI](https://serpapi.com/manage-api-key)
2. Get your free API key (100 searches/month)
3. Set environment variable:
   ```bash
   export SERPAPI_KEY="your_api_key_here"
   ```

## Basic Usage

### Initialize the Agent

```python
from RealTimeSearch import create_real_time_agent

# Method 1: Using environment variable
agent = create_real_time_agent()

# Method 2: Direct API key
agent = create_real_time_agent(api_key="your_api_key_here")
```

### Simple Search

```python
# Basic search
results = agent.search_real_time(
    query="machine learning algorithms explained",
    search_type="general",
    num_results=10
)

print(f"Found {results['total_results']} results")
for result in results['results']:
    print(f"- {result['title']}: {result['link']}")
```

## Advanced Usage Examples

### 1. Academic Problem Solving

```python
# Search for solutions to a specific academic problem
math_solutions = agent.search_academic_solutions(
    problem="solve differential equations using separation of variables",
    subject="mathematics"
)

print(f"Academic Sources: {len(math_solutions['academic_sources'])}")
print(f"Web Explanations: {len(math_solutions['web_explanations'])}")
print(f"Video Tutorials: {len(math_solutions['video_tutorials'])}")

# Access results
for source in math_solutions['academic_sources'][:3]:
    print(f"📚 {source['title']}")
    print(f"   Authors: {', '.join(source['authors'])}")
    print(f"   Citations: {source['citation_count']}")
    print(f"   Link: {source['link']}\n")
```

### 2. Latest Educational News

```python
# Get recent news in your field
ai_news = agent.get_latest_news(
    topic="artificial intelligence in education",
    hours_back=24  # Last 24 hours
)

for article in ai_news['results'][:5]:
    print(f"📰 {article['title']}")
    print(f"   Source: {article['source']}")
    print(f"   Date: {article['date']}")
    print(f"   Link: {article['link']}\n")
```

### 3. Video Tutorials

```python
# Find educational videos
video_results = agent.search_real_time(
    query="organic chemistry mechanisms explained",
    search_type="videos",
    num_results=10
)

for video in video_results['results']:
    print(f"🎥 {video['title']}")
    print(f"   Channel: {video['channel']}")
    print(f"   Duration: {video['duration']}")
    print(f"   Views: {video['views']}")
    print(f"   Link: {video['link']}\n")
```

### 4. Async Batch Search

```python
import asyncio

async def search_multiple_topics():
    topics = [
        "quantum physics fundamentals",
        "organic chemistry reactions",
        "calculus integration techniques",
        "data structures algorithms"
    ]
    
    # Search all topics simultaneously
    results = await agent.batch_search_async(
        queries=topics,
        search_type="general",
        num_results=5
    )
    
    for topic, result in zip(topics, results):
        if not result.get('error'):
            print(f"📚 {topic}: {result['total_results']} results")
        else:
            print(f"❌ {topic}: {result['error_message']}")

# Run async search
asyncio.run(search_multiple_topics())
```

### 5. Subject-Specific Searches

```python
# Physics problem
physics_help = agent.search_academic_solutions(
    problem="calculate momentum and energy in relativistic collisions",
    subject="physics"
)

# Chemistry problem
chemistry_help = agent.search_academic_solutions(
    problem="predict products of organic synthesis reactions",
    subject="chemistry"
)

# Computer Science problem
cs_help = agent.search_academic_solutions(
    problem="implement binary search tree with balancing",
    subject="computer science"
)
```

## Search Types and Parameters

### Search Types

| Type | Description | Best For |
|------|-------------|----------|
| `"general"` | Web search with educational filtering | General learning resources |
| `"academic"` | Google Scholar search | Research papers, citations |
| `"news"` | Recent news articles | Current developments |
| `"images"` | Image search | Diagrams, visual aids |
| `"videos"` | YouTube search | Tutorials, explanations |

### Parameters

```python
results = agent.search_real_time(
    query="your search query",
    search_type="general",  # See table above
    num_results=10,         # Number of results (1-100)
    location="Global",      # Search location
    language="en",          # Language code
    time_range="all",       # "hour", "day", "week", "month", "year"
    use_cache=True          # Use cached results if available
)
```

## Caching System

The agent includes intelligent caching to improve performance and reduce API calls:

```python
# Check cache statistics
cache_stats = agent.get_cache_stats()
print(f"Cache size: {cache_stats['cache_size']}")
print(f"Cache hits: {cache_stats['hits']}")
print(f"Cache misses: {cache_stats['misses']}")

# Clear cache if needed
agent.clear_cache()

# Disable cache for fresh results
fresh_results = agent.search_real_time(
    query="latest AI developments",
    use_cache=False
)
```

## Error Handling

```python
results = agent.search_real_time(query="your query")

if results.get('error'):
    print(f"Search failed: {results['error_message']}")
else:
    print(f"Success! Found {results['total_results']} results")
    # Process results...
```

## Integration with Django/FastAPI

### Django Integration

```python
# views.py
from django.http import JsonResponse
from .ai_services import RealTimeSearch

def search_academic_content(request):
    query = request.GET.get('q', '')
    subject = request.GET.get('subject', '')
    
    agent = RealTimeSearch()
    results = agent.search_academic_solutions(
        problem=query,
        subject=subject
    )
    
    return JsonResponse({
        'status': 'success',
        'total_sources': results['total_sources'],
        'academic_sources': results['academic_sources'][:10],
        'video_tutorials': results['video_tutorials'][:5]
    })
```

### FastAPI Integration

```python
# main.py
from fastapi import FastAPI, Query
from .ai_services import RealTimeSearch

app = FastAPI()
search_agent = RealTimeSearch()

@app.get("/search/academic")
async def search_academic(
    q: str = Query(..., description="Search query"),
    subject: str = Query(None, description="Academic subject")
):
    results = await search_agent.search_real_time_async(
        query=f"{subject} {q}" if subject else q,
        search_type="academic",
        num_results=20
    )
    
    return {
        "query": q,
        "subject": subject,
        "results": results['results'],
        "total": results['total_results']
    }
```

## Best Practices

### 1. API Key Management
```python
# Use environment variables
import os
api_key = os.getenv('SERPAPI_KEY')

# Never hardcode API keys in source code
# ❌ DON'T DO THIS
agent = RealTimeSearch(api_key="abc123...")

# ✅ DO THIS
agent = RealTimeSearch()  # Uses environment variable
```

### 2. Efficient Caching
```python
# Use longer cache for stable content
agent = RealTimeSearch(cache_ttl=3600)  # 1 hour

# Use shorter cache for frequently changing content
news_agent = RealTimeSearch(cache_ttl=600)  # 10 minutes
```

### 3. Batch Processing
```python
# For multiple searches, use batch processing
queries = ["topic1", "topic2", "topic3"]
results = await agent.batch_search_async(queries)

# Instead of individual searches
# ❌ Less efficient
for query in queries:
    result = agent.search_real_time(query)
```

### 4. Error Handling
```python
try:
    results = agent.search_real_time("complex query")
    if results.get('error'):
        # Handle API errors
        print(f"API Error: {results['error_message']}")
    else:
        # Process successful results
        process_results(results['results'])
except Exception as e:
    # Handle network or other errors
    print(f"Network Error: {str(e)}")
```

## Rate Limits and Costs

### SerpAPI Limits
- **Free Plan**: 100 searches/month
- **Paid Plans**: Higher limits available
- **Rate Limiting**: Built-in handling

### Cost Optimization
1. **Use Caching**: Reduces redundant API calls
2. **Batch Searches**: More efficient for multiple queries
3. **Filter Results**: Request only needed number of results
4. **Subject Filtering**: More targeted searches

## Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   ValueError: SerpAPI key is required
   ```
   **Solution**: Set `SERPAPI_KEY` environment variable

2. **Network Timeout**
   ```
   NetworkError: Request timeout
   ```
   **Solution**: Check internet connection, retry search

3. **Empty Results**
   ```
   {'results': [], 'total_results': 0}
   ```
   **Solution**: Try different keywords, broader search terms

4. **Rate Limit Exceeded**
   ```
   {'error': 'Rate limit exceeded'}
   ```
   **Solution**: Wait and retry, upgrade API plan if needed

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed request/response information
agent = RealTimeSearch()
results = agent.search_real_time("test query")
```

## Examples for Different Subjects

### Mathematics
```python
math_problems = [
    "solve linear algebra eigenvalue problems",
    "calculus optimization techniques",
    "statistics hypothesis testing methods",
    "number theory prime factorization"
]

for problem in math_problems:
    results = agent.search_academic_solutions(problem, "mathematics")
    print(f"Math Problem: {problem}")
    print(f"Found {results['total_sources']} resources\n")
```

### Science
```python
science_topics = [
    "CRISPR gene editing mechanisms",
    "quantum entanglement experiments",
    "organic synthesis reaction pathways",
    "climate change modeling techniques"
]

for topic in science_topics:
    # Get latest research
    academic = agent.search_real_time(topic, "academic", num_results=5)
    # Get news updates
    news = agent.get_latest_news(topic, hours_back=168)  # Last week
    
    print(f"Topic: {topic}")
    print(f"Academic papers: {academic['total_results']}")
    print(f"Recent news: {news['total_results']}\n")
```

This comprehensive real-time search agent will significantly enhance your AI-powered exam preparation app by providing students with up-to-date, relevant educational content and solutions to their academic problems.
