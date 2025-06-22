import os
import json
import logging
import requests
import asyncio
import aiohttp
import hashlib
import re
from datetime import datetime, timedelta
import pytz
from typing import Any, Dict, List, Optional, Union
from cachetools import TTLCache
from langchain.agents import AgentType, initialize_agent
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This is for when a user wants a realtime update on a topic, because since this is a student based app, realtime updates are crucial for studying
class RealTimeSearch:
    """
    Real-time search agent for educational content using SerpAPI.
    Provides real-time information and solutions to academic problems.
    """
    
    def __init__(self, api_key: Optional[str] = None, cache_ttl: int = 3600):
        """
        Initialize the RealTimeSearch agent.
        
        Args:
            api_key: SerpAPI key. If None, will try to get from environment
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.api_key = api_key or os.getenv('SERPAPI_API_KEY')
        if not self.api_key:
            raise ValueError("SerpAPI key is required. Set SERPAPI_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize cache with TTL (Time To Live)
        self.cache = TTLCache(maxsize=1000, ttl=cache_ttl)
        
        # Search endpoints
        self.serpapi_base_url = "https://serpapi.com/search.json"
        
        # Educational search preferences
        self.educational_domains = [
            "edu", "scholar.google.com", "wikipedia.org", "khanacademy.org",
            "coursera.org", "edx.org", "mit.edu", "stanford.edu", "harvard.edu",
            "youtube.com/watch", "arxiv.org", "researchgate.net"
        ]
        
        # Initialize session for reuse
        self.session = requests.Session()
        
        # Timezone for timestamp
        self.timezone = pytz.UTC
        
    def _generate_cache_key(self, query: str, search_type: str = "general", **kwargs) -> str:
        """Generate a unique cache key for the search query."""
        key_data = f"{query}_{search_type}_{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_educational_content(self, url: str, title: str, snippet: str) -> bool:
        """Check if content is educational based on URL, title, and snippet."""
        # Check if URL contains educational domains
        for domain in self.educational_domains:
            if domain in url.lower():
                return True
        
        # Check for educational keywords in title and snippet
        educational_keywords = [
            "tutorial", "learn", "education", "course", "lesson", "study",
            "academic", "research", "university", "college", "textbook",
            "guide", "how to", "explanation", "theory", "concept"
        ]
        
        text_to_check = f"{title} {snippet}".lower()
        return any(keyword in text_to_check for keyword in educational_keywords)
    
    def _filter_educational_results(self, results: List[Dict]) -> List[Dict]:
        """Filter search results to prioritize educational content."""
        educational_results = []
        other_results = []
        
        for result in results:
            url = result.get('link', '')
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            if self._is_educational_content(url, title, snippet):
                educational_results.append(result)
            else:
                other_results.append(result)
        
        # Return educational content first, then other results
        return educational_results + other_results
    
    def search_real_time(self, 
                        query: str, 
                        search_type: str = "general",
                        num_results: int = 10,
                        location: str = "Global",
                        language: str = "en",
                        time_range: str = "all",
                        use_cache: bool = True) -> Dict[str, Any]:
        """
        Perform real-time search using SerpAPI.
        
        Args:
            query: Search query
            search_type: Type of search ('general', 'academic', 'news', 'images', 'videos')
            num_results: Number of results to return
            location: Location for search (e.g., "United States", "Global")
            language: Language code (e.g., "en", "es", "fr")
            time_range: Time range filter ("all", "hour", "day", "week", "month", "year")
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                query, search_type, num_results=num_results, 
                location=location, language=language, time_range=time_range
            )
            
            # Check cache first
            if use_cache and cache_key in self.cache:
                logger.info(f"Returning cached results for query: {query}")
                return self.cache[cache_key]
            
            # Prepare search parameters
            params = {
                'api_key': self.api_key,
                'q': query,
                'num': min(num_results, 100),  # SerpAPI limit
                'hl': language,
                'gl': self._get_country_code(location),
                'no_cache': 'true'  # Get fresh results
            }
            
            # Set search engine and specific parameters based on search type
            if search_type == "academic":
                params['engine'] = 'google_scholar'
                params['as_ylo'] = datetime.now().year - 5  # Last 5 years for academic
            elif search_type == "news":
                params['engine'] = 'google'
                params['tbm'] = 'nws'
                if time_range != "all":
                    params['tbs'] = self._get_time_filter(time_range)
            elif search_type == "images":
                params['engine'] = 'google'
                params['tbm'] = 'isch'
            elif search_type == "videos":
                params['engine'] = 'youtube'
                params['search_query'] = query
            else:  # general search
                params['engine'] = 'google'
                if time_range != "all":
                    params['tbs'] = self._get_time_filter(time_range)
            
            # Make API request
            response = self.session.get(self.serpapi_base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if 'error' in data:
                logger.error(f"SerpAPI error: {data['error']}")
                return self._create_error_response(f"Search API error: {data['error']}")
            
            # Process results based on search type
            processed_results = self._process_search_results(data, search_type)
            
            # Filter for educational content in general searches
            if search_type == "general":
                processed_results['results'] = self._filter_educational_results(
                    processed_results['results']
                )
            
            # Add metadata
            processed_results.update({
                'query': query,
                'search_type': search_type,
                'timestamp': datetime.now(self.timezone).isoformat(),
                'total_results': len(processed_results['results']),
                'location': location,
                'language': language,
                'cached': False
            })
            
            # Cache the results
            if use_cache:
                self.cache[cache_key] = processed_results
            
            logger.info(f"Successfully retrieved {len(processed_results['results'])} results for query: {query}")
            return processed_results
            
        except requests.RequestException as e:
            logger.error(f"Request error during search: {str(e)}")
            return self._create_error_response(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during search: {str(e)}")
            return self._create_error_response(f"Unexpected error: {str(e)}")
    
    async def search_real_time_async(self, 
                                   query: str, 
                                   search_type: str = "general",
                                   num_results: int = 10,
                                   location: str = "Global",
                                   language: str = "en",
                                   time_range: str = "all",
                                   use_cache: bool = True) -> Dict[str, Any]:
        """
        Asynchronous version of real-time search for better performance.
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                query, search_type, num_results=num_results, 
                location=location, language=language, time_range=time_range
            )
            
            # Check cache first
            if use_cache and cache_key in self.cache:
                logger.info(f"Returning cached results for query: {query}")
                return self.cache[cache_key]
            
            # Prepare search parameters
            params = {
                'api_key': self.api_key,
                'q': query,
                'num': min(num_results, 100),
                'hl': language,
                'gl': self._get_country_code(location),
                'no_cache': 'true'
            }
            
            # Set engine based on search type
            if search_type == "academic":
                params['engine'] = 'google_scholar'
                params['as_ylo'] = datetime.now().year - 5
            elif search_type == "news":
                params['engine'] = 'google'
                params['tbm'] = 'nws'
                if time_range != "all":
                    params['tbs'] = self._get_time_filter(time_range)
            elif search_type == "images":
                params['engine'] = 'google'
                params['tbm'] = 'isch'
            elif search_type == "videos":
                params['engine'] = 'youtube'
                params['search_query'] = query
            else:
                params['engine'] = 'google'
                if time_range != "all":
                    params['tbs'] = self._get_time_filter(time_range)
            
            # Make async API request
            async with aiohttp.ClientSession() as session:
                async with session.get(self.serpapi_base_url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            # Check for API errors
            if 'error' in data:
                logger.error(f"SerpAPI error: {data['error']}")
                return self._create_error_response(f"Search API error: {data['error']}")
            
            # Process results
            processed_results = self._process_search_results(data, search_type)
            
            # Filter for educational content in general searches
            if search_type == "general":
                processed_results['results'] = self._filter_educational_results(
                    processed_results['results']
                )
            
            # Add metadata
            processed_results.update({
                'query': query,
                'search_type': search_type,
                'timestamp': datetime.now(self.timezone).isoformat(),
                'total_results': len(processed_results['results']),
                'location': location,
                'language': language,
                'cached': False
            })
            
            # Cache the results
            if use_cache:
                self.cache[cache_key] = processed_results
            
            logger.info(f"Successfully retrieved {len(processed_results['results'])} results for query: {query}")
            return processed_results
            
        except aiohttp.ClientError as e:
            logger.error(f"Async request error during search: {str(e)}")
            return self._create_error_response(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during async search: {str(e)}")
            return self._create_error_response(f"Unexpected error: {str(e)}")
    
    async def batch_search_async(self, queries: List[str], **kwargs) -> List[Dict[str, Any]]:
        """
        Perform multiple searches asynchronously for better performance.
        
        Args:
            queries: List of search queries
            **kwargs: Additional search parameters
            
        Returns:
            List of search results for each query
        """
        tasks = []
        for query in queries:
            task = self.search_real_time_async(query, **kwargs)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in batch search for query {queries[i]}: {str(result)}")
                processed_results.append(
                    self._create_error_response(f"Error: {str(result)}")
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    def search_academic_solutions(self, problem: str, subject: str = None) -> Dict[str, Any]:
        """
        Search for academic solutions and explanations for specific problems.
        
        Args:
            problem: The academic problem or question
            subject: Subject area (e.g., "mathematics", "physics", "chemistry")
            
        Returns:
            Dictionary containing academic solutions and explanations
        """
        # Enhance query for academic content
        enhanced_query = problem
        if subject:
            enhanced_query = f"{subject} {problem}"
        
        # Add academic keywords to improve results
        academic_query = f"{enhanced_query} explanation solution tutorial how to solve"
        
        # Search academic sources
        academic_results = self.search_real_time(
            query=academic_query,
            search_type="academic",
            num_results=15
        )
        
        # Search general web for additional explanations
        general_results = self.search_real_time(
            query=f"{enhanced_query} step by step solution explanation",
            search_type="general",
            num_results=10
        )
        
        # Search for video explanations
        video_results = self.search_real_time(
            query=f"{enhanced_query} tutorial explanation",
            search_type="videos",
            num_results=5
        )
        
        # Combine and structure results
        combined_results = {
            'problem': problem,
            'subject': subject,
            'academic_sources': academic_results.get('results', []),
            'web_explanations': general_results.get('results', []),
            'video_tutorials': video_results.get('results', []),
            'timestamp': datetime.now(self.timezone).isoformat(),
            'total_sources': (
                len(academic_results.get('results', [])) + 
                len(general_results.get('results', [])) + 
                len(video_results.get('results', []))
            )
        }
        
        return combined_results
    
    def get_latest_news(self, topic: str, hours_back: int = 24) -> Dict[str, Any]:
        """
        Get latest news and updates on a specific topic.
        
        Args:
            topic: Topic to search for news
            hours_back: How many hours back to search (default: 24 hours)
            
        Returns:
            Dictionary containing latest news results
        """
        # Determine time range based on hours_back
        if hours_back <= 1:
            time_range = "hour"
        elif hours_back <= 24:
            time_range = "day"
        elif hours_back <= 168:  # 7 days
            time_range = "week"
        else:
            time_range = "month"
        
        return self.search_real_time(
            query=topic,
            search_type="news",
            time_range=time_range,
            num_results=20
        )
    
    def _process_search_results(self, data: Dict, search_type: str) -> Dict[str, Any]:
        """Process raw SerpAPI results based on search type."""
        results = []
        
        if search_type == "academic":
            # Process Google Scholar results
            for result in data.get('organic_results', []):
                results.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'publication_info': result.get('publication_info', {}),
                    'citation_count': result.get('inline_links', {}).get('cited_by', {}).get('total', 0),
                    'authors': result.get('publication_info', {}).get('authors', []),
                    'year': result.get('publication_info', {}).get('year', ''),
                    'type': 'academic'
                })
        
        elif search_type == "news":
            # Process news results
            for result in data.get('news_results', []):
                results.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'source': result.get('source', ''),
                    'date': result.get('date', ''),
                    'thumbnail': result.get('thumbnail', ''),
                    'type': 'news'
                })
        
        elif search_type == "images":
            # Process image results
            for result in data.get('images_results', []):
                results.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'original': result.get('original', ''),
                    'thumbnail': result.get('thumbnail', ''),
                    'source': result.get('source', ''),
                    'type': 'image'
                })
        
        elif search_type == "videos":
            # Process YouTube video results
            for result in data.get('video_results', []):
                results.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'channel': result.get('channel', {}).get('name', ''),
                    'duration': result.get('duration', ''),
                    'views': result.get('views', ''),
                    'published_date': result.get('published_date', ''),
                    'thumbnail': result.get('thumbnail', ''),
                    'type': 'video'
                })
        
        else:  # general search
            # Process general web results
            for result in data.get('organic_results', []):
                results.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'displayed_link': result.get('displayed_link', ''),
                    'favicon': result.get('favicon', ''),
                    'type': 'web'
                })
        
        return {'results': results}
    
    def _get_time_filter(self, time_range: str) -> str:
        """Convert time range to SerpAPI time filter."""
        time_filters = {
            'hour': 'qdr:h',
            'day': 'qdr:d',
            'week': 'qdr:w',
            'month': 'qdr:m',
            'year': 'qdr:y'
        }
        return time_filters.get(time_range, '')
    
    def _get_country_code(self, location: str) -> str:
        """Convert location to country code for SerpAPI."""
        location_codes = {
            'global': 'us',
            'united states': 'us',
            'canada': 'ca',
            'united kingdom': 'uk',
            'germany': 'de',
            'france': 'fr',
            'spain': 'es',
            'italy': 'it',
            'japan': 'jp',
            'china': 'cn',
            'india': 'in',
            'australia': 'au',
            'brazil': 'br',
            'mexico': 'mx'
        }
        return location_codes.get(location.lower(), 'us')
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            'error': True,
            'error_message': error_message,
            'results': [],
            'timestamp': datetime.now(self.timezone).isoformat(),
            'total_results': 0
        }
    
    def clear_cache(self):
        """Clear the search cache."""
        self.cache.clear()
        logger.info("Search cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cache_size': len(self.cache),
            'max_size': self.cache.maxsize,
            'ttl': self.cache.ttl,
            'hits': getattr(self.cache, 'hits', 0),
            'misses': getattr(self.cache, 'misses', 0)
        }


# Example usage and helper functions
def create_real_time_agent(api_key: str = None) -> RealTimeSearch:
    """
    Factory function to create a RealTimeSearch agent.
    
    Args:
        api_key: SerpAPI key (optional, will use environment variable if not provided)
        
    Returns:
        Configured RealTimeSearch instance
    """
    return RealTimeSearch(api_key=api_key)


# Async helper function for running async searches in sync context
def run_async_search(search_agent: RealTimeSearch, query: str, **kwargs) -> Dict[str, Any]:
    """
    Helper function to run async search in synchronous context.
    
    Args:
        search_agent: RealTimeSearch instance
        query: Search query
        **kwargs: Additional search parameters
        
    Returns:
        Search results
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            search_agent.search_real_time_async(query, **kwargs)
        )
    finally:
        loop.close()


# Example usage
if __name__ == "__main__":
    # Initialize the search agent
    agent = create_real_time_agent()
    
    # Example searches
    print("=== Academic Problem Search ===")
    math_problem = agent.search_academic_solutions(
        problem="solve quadratic equation x^2 + 5x + 6 = 0",
        subject="mathematics"
    )
    print(f"Found {math_problem['total_sources']} sources for math problem")
    
    print("\n=== Latest News Search ===")
    latest_ai_news = agent.get_latest_news("artificial intelligence in education")
    print(f"Found {latest_ai_news['total_results']} recent news articles")
    
    print("\n=== General Real-time Search ===")
    study_tips = agent.search_real_time(
        query="effective study techniques for exam preparation",
        search_type="general",
        num_results=10
    )
    print(f"Found {study_tips['total_results']} study resources")
    
    print("\n=== Cache Statistics ===")
    print(agent.get_cache_stats())
