"""
Integration example showing how to use RealTimeSearch with other AI services
in the Examify AI-Powered Exam Preparation App.
"""

import asyncio
from typing import Dict, List, Any
from RealTimeSearch import create_real_time_agent


class ExamPrepAIAgent:
    """
    Enhanced AI agent that combines real-time search with exam preparation features.
    """
    
    def __init__(self, serpapi_key: str = None):
        """Initialize the enhanced AI agent with real-time search capabilities."""
        self.search_agent = create_real_time_agent(api_key=serpapi_key)
        
    async def get_comprehensive_study_materials(self, 
                                              topic: str, 
                                              subject: str = None,
                                              difficulty_level: str = "intermediate") -> Dict[str, Any]:
        """
        Get comprehensive study materials for a topic including:
        - Academic sources
        - Latest developments
        - Video tutorials
        - Practice problems
        """
        
        # Enhanced query based on difficulty level
        difficulty_keywords = {
            "beginner": "introduction basics fundamentals",
            "intermediate": "explained concepts tutorial",
            "advanced": "advanced complex in-depth analysis"
        }
        
        enhanced_topic = f"{topic} {difficulty_keywords.get(difficulty_level, '')}"
        if subject:
            enhanced_topic = f"{subject} {enhanced_topic}"
        
        # Perform multiple searches concurrently
        search_tasks = [
            # Academic research papers
            self.search_agent.search_real_time_async(
                query=enhanced_topic,
                search_type="academic",
                num_results=10
            ),
            
            # Video tutorials
            self.search_agent.search_real_time_async(
                query=f"{enhanced_topic} tutorial explanation",
                search_type="videos",
                num_results=8
            ),
            
            # Latest news and developments
            self.search_agent.get_latest_news(
                topic=topic,
                hours_back=168  # Last week
            ),
            
            # General educational resources
            self.search_agent.search_real_time_async(
                query=f"{enhanced_topic} study guide notes",
                search_type="general",
                num_results=15
            )
        ]
        
        # Wait for all searches to complete
        academic_results, video_results, news_results, general_results = await asyncio.gather(*search_tasks)
        
        return {
            "topic": topic,
            "subject": subject,
            "difficulty_level": difficulty_level,
            "academic_sources": academic_results.get("results", []),
            "video_tutorials": video_results.get("results", []),
            "latest_news": news_results.get("results", []),
            "study_guides": general_results.get("results", []),
            "total_resources": (
                len(academic_results.get("results", [])) +
                len(video_results.get("results", [])) +
                len(news_results.get("results", [])) +
                len(general_results.get("results", []))
            )
        }
    
    async def solve_exam_problem(self, problem: str, subject: str = None) -> Dict[str, Any]:
        """
        Get comprehensive solutions for exam problems.
        """
        
        # Search for academic solutions
        academic_solutions = self.search_agent.search_academic_solutions(
            problem=problem,
            subject=subject
        )
        
        # Search for step-by-step tutorials
        tutorial_search = await self.search_agent.search_real_time_async(
            query=f"{problem} step by step solution method",
            search_type="general",
            num_results=10
        )
        
        # Search for similar problems
        similar_problems = await self.search_agent.search_real_time_async(
            query=f"similar problems like {problem} examples",
            search_type="general",
            num_results=8
        )
        
        return {
            "problem": problem,
            "subject": subject,
            "academic_solutions": academic_solutions.get("academic_sources", []),
            "web_explanations": academic_solutions.get("web_explanations", []),
            "video_tutorials": academic_solutions.get("video_tutorials", []),
            "tutorial_guides": tutorial_search.get("results", []),
            "similar_problems": similar_problems.get("results", []),
            "solution_sources": academic_solutions.get("total_sources", 0)
        }
    
    async def get_exam_prep_strategy(self, exam_type: str, time_remaining: str) -> Dict[str, Any]:
        """
        Get personalized exam preparation strategies.
        """
        
        strategy_query = f"{exam_type} exam preparation strategy {time_remaining}"
        
        # Search for preparation strategies
        strategies = await self.search_agent.search_real_time_async(
            query=strategy_query,
            search_type="general",
            num_results=12
        )
        
        # Search for recent tips and techniques
        recent_tips = self.search_agent.get_latest_news(
            topic=f"{exam_type} exam tips preparation",
            hours_back=720  # Last month
        )
        
        # Search for study schedules
        study_schedules = await self.search_agent.search_real_time_async(
            query=f"{exam_type} study schedule {time_remaining} plan",
            search_type="general",
            num_results=8
        )
        
        return {
            "exam_type": exam_type,
            "time_remaining": time_remaining,
            "preparation_strategies": strategies.get("results", []),
            "recent_tips": recent_tips.get("results", []),
            "study_schedules": study_schedules.get("results", []),
            "total_resources": (
                len(strategies.get("results", [])) +
                len(recent_tips.get("results", [])) +
                len(study_schedules.get("results", []))
            )
        }
    
    async def get_current_trends(self, subject: str) -> Dict[str, Any]:
        """
        Get current trends and developments in a subject area.
        """
        
        # Latest research trends
        research_trends = await self.search_agent.search_real_time_async(
            query=f"{subject} latest research trends 2024 2025",
            search_type="academic",
            num_results=10
        )
        
        # Industry news
        industry_news = self.search_agent.get_latest_news(
            topic=f"{subject} industry developments",
            hours_back=168  # Last week
        )
        
        # Emerging technologies
        tech_trends = await self.search_agent.search_real_time_async(
            query=f"{subject} emerging technologies innovations",
            search_type="general",
            num_results=10
        )
        
        return {
            "subject": subject,
            "research_trends": research_trends.get("results", []),
            "industry_news": industry_news.get("results", []),
            "technology_trends": tech_trends.get("results", []),
            "last_updated": industry_news.get("timestamp", "")
        }


# Example usage functions for integration with Django/FastAPI

async def example_comprehensive_study_session():
    """Example of a comprehensive study session."""
    
    agent = ExamPrepAIAgent()
    
    # Student wants to study machine learning
    topic = "neural networks and deep learning"
    subject = "computer science"
    
    print(f"🎓 Starting comprehensive study session: {topic}")
    
    # Get all study materials
    materials = await agent.get_comprehensive_study_materials(
        topic=topic,
        subject=subject,
        difficulty_level="intermediate"
    )
    
    print(f"📚 Found {materials['total_resources']} total resources:")
    print(f"   - Academic papers: {len(materials['academic_sources'])}")
    print(f"   - Video tutorials: {len(materials['video_tutorials'])}")
    print(f"   - Study guides: {len(materials['study_guides'])}")
    print(f"   - Latest news: {len(materials['latest_news'])}")
    
    return materials


async def example_problem_solving_session():
    """Example of solving a specific exam problem."""
    
    agent = ExamPrepAIAgent()
    
    # Student has a specific problem
    problem = "implement backpropagation algorithm for neural networks"
    subject = "machine learning"
    
    print(f"🔍 Solving problem: {problem}")
    
    # Get comprehensive solutions
    solutions = await agent.solve_exam_problem(
        problem=problem,
        subject=subject
    )
    
    print(f"💡 Found {solutions['solution_sources']} solution sources:")
    print(f"   - Academic solutions: {len(solutions['academic_solutions'])}")
    print(f"   - Web explanations: {len(solutions['web_explanations'])}")
    print(f"   - Video tutorials: {len(solutions['video_tutorials'])}")
    print(f"   - Tutorial guides: {len(solutions['tutorial_guides'])}")
    print(f"   - Similar problems: {len(solutions['similar_problems'])}")
    
    return solutions


async def example_exam_preparation():
    """Example of exam preparation planning."""
    
    agent = ExamPrepAIAgent()
    
    # Student preparing for specific exam
    exam_type = "software engineering certification"
    time_remaining = "2 weeks"
    
    print(f"📅 Planning exam preparation: {exam_type} in {time_remaining}")
    
    # Get preparation strategy
    strategy = await agent.get_exam_prep_strategy(
        exam_type=exam_type,
        time_remaining=time_remaining
    )
    
    print(f"📋 Found {strategy['total_resources']} strategy resources:")
    print(f"   - Preparation strategies: {len(strategy['preparation_strategies'])}")
    print(f"   - Recent tips: {len(strategy['recent_tips'])}")
    print(f"   - Study schedules: {len(strategy['study_schedules'])}")
    
    return strategy


# Django view example
def django_search_view_example():
    """Example Django view using the enhanced AI agent."""
    
    from django.http import JsonResponse
    import asyncio
    
    def search_study_materials(request):
        topic = request.GET.get('topic', '')
        subject = request.GET.get('subject', '')
        difficulty = request.GET.get('difficulty', 'intermediate')
        
        if not topic:
            return JsonResponse({'error': 'Topic is required'}, status=400)
        
        async def get_materials():
            agent = ExamPrepAIAgent()
            return await agent.get_comprehensive_study_materials(
                topic=topic,
                subject=subject,
                difficulty_level=difficulty
            )
        
        # Run async function in sync context
        materials = asyncio.run(get_materials())
        
        return JsonResponse({
            'status': 'success',
            'materials': materials
        })


# FastAPI endpoint example
def fastapi_endpoint_example():
    """Example FastAPI endpoint using the enhanced AI agent."""
    
    from fastapi import FastAPI, Query
    
    app = FastAPI()
    
    @app.get("/api/study-materials")
    async def get_study_materials(
        topic: str = Query(..., description="Study topic"),
        subject: str = Query(None, description="Academic subject"),
        difficulty: str = Query("intermediate", description="Difficulty level")
    ):
        agent = ExamPrepAIAgent()
        
        materials = await agent.get_comprehensive_study_materials(
            topic=topic,
            subject=subject,
            difficulty_level=difficulty
        )
        
        return {
            "status": "success",
            "data": materials
        }
    
    @app.get("/api/solve-problem")
    async def solve_problem(
        problem: str = Query(..., description="Problem to solve"),
        subject: str = Query(None, description="Academic subject")
    ):
        agent = ExamPrepAIAgent()
        
        solutions = await agent.solve_exam_problem(
            problem=problem,
            subject=subject
        )
        
        return {
            "status": "success",
            "data": solutions
        }


if __name__ == "__main__":
    print("🚀 Running ExamPrepAIAgent examples...")
    
    async def run_all_examples():
        print("\n1. Comprehensive Study Session")
        await example_comprehensive_study_session()
        
        print("\n2. Problem Solving Session")
        await example_problem_solving_session()
        
        print("\n3. Exam Preparation Planning")
        await example_exam_preparation()
        
        print("\n✅ All examples completed!")
    
    asyncio.run(run_all_examples())
