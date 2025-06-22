import os
import json
import asyncio
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.core.cache import cache
import openai
import google.generativeai as genai
from PIL import Image
import io
import base64

# OCR imports (with fallback)
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    pytesseract = None

# Import our existing AI services
try:
    from RealTimeSearch import RealTimeSearch
except ImportError:
    RealTimeSearch = None

try:
    from Rag import RagProcessor
except ImportError:
    RagProcessor = None

# Import models
from AItutor.models import (
    Question, PastQuestion, Quiz, QuizQuestion, 
    DifficultyAnalysis, OnlineSource, EmbeddingVector,
    QuizCustomization, UserPerformanceAnalytics
)
from student.models import User, Course

logger = logging.getLogger(__name__)


@dataclass
class QuestionGenerationConfig:
    """Configuration for AI question generation"""
    primary_model: str = "gemini-pro"
    fallback_model: str = "gpt-4o-mini" 
    difficulty_levels: List[str] = None
    question_types: List[str] = None
    max_questions_per_request: int = 10
    include_explanations: bool = True
    generate_distractors: bool = True
    estimate_solve_time: bool = True
    
    def __post_init__(self):
        if self.difficulty_levels is None:
            self.difficulty_levels = ['beginner', 'intermediate', 'advanced', 'expert']
        if self.question_types is None:
            self.question_types = ['multiple_choice', 'true_false', 'short_answer', 'essay']


class AIQuizEngine:
    """
    Comprehensive AI-powered quiz and question generation system
    Integrates with existing RealTimeSearch and Rag services
    """
    
    def __init__(self):
        """Initialize the AI Quiz Engine with necessary services"""
        self.config = QuestionGenerationConfig()
        
        # Initialize AI models
        self.ai_models_available = self._setup_ai_models()
        
        # Initialize existing services
        try:
            self.real_time_search = RealTimeSearch()
        except Exception as e:
            logger.warning(f"RealTimeSearch not available: {e}")
            self.real_time_search = None
            
        try:
            self.rag_processor = RagProcessor()
        except Exception as e:
            logger.warning(f"RagProcessor not available: {e}")
            self.rag_processor = None
        
        # OCR setup
        self.ocr_enabled = OCR_AVAILABLE
        
    def _setup_ai_models(self):
        """Setup AI models with proper authentication"""
        try:
            # Get AI config from Django settings
            ai_config = getattr(settings, 'AI_SERVICES_CONFIG', {})
            
            # OpenAI setup
            openai_key = ai_config.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
            if openai_key:
                # Store the key for later use - new OpenAI client doesn't use global api_key
                self.openai_api_key = openai_key
                logger.info("OpenAI API initialized")
            else:
                logger.warning("OpenAI API key not found")
                self.openai_api_key = None
            
            # Google Gemini setup
            gemini_key = ai_config.get('GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if gemini_key:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name
                self.gemini_vision_model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name
                logger.info("Gemini API initialized")
            else:
                logger.warning("Gemini API key not found")
            
            # Check if at least one AI service is available
            if self.openai_api_key or gemini_key:
                logger.info("AI models initialized successfully")
                return True
            else:
                logger.error("No AI API keys found - AI features will be disabled")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            return False
    
    async def generate_quiz(
        self, 
        user: User,
        course: Course = None,
        topics: List[str] = None,
        difficulty: str = 'intermediate',
        num_questions: int = 10,
        question_types: List[str] = None,
        include_past_questions: bool = True,
        include_ai_generated: bool = True,
        use_real_time_sources: bool = False
    ) -> Quiz:
        """
        Generate a comprehensive quiz based on user preferences and AI analysis
        
        Args:
            user: User requesting the quiz
            course: Target course (optional)
            topics: List of topics to cover
            difficulty: Target difficulty level
            num_questions: Number of questions
            question_types: Types of questions to include
            include_past_questions: Include past exam questions
            include_ai_generated: Include AI-generated questions
            use_real_time_sources: Use real-time web sources
            
        Returns:
            Generated Quiz object
        """
        try:
            logger.info(f"Generating quiz for user {user.username} with {num_questions} questions")
            
            # Get user preferences
            user_prefs = await self._get_user_preferences(user)
            
            # Create quiz object
            quiz = Quiz.objects.create(
                title=f"AI Generated Quiz - {course.name if course else 'Multi-subject'}",
                description=f"Auto-generated quiz covering {', '.join(topics) if topics else 'various topics'}",
                course=course,
                quiz_type='mixed' if not course else 'topic_review',
                created_by=user,
                target_difficulty=difficulty,
                estimated_duration=num_questions * 2,  # 2 minutes per question estimate
                settings={
                    'topics': topics or [],
                    'difficulty': difficulty,
                    'question_types': question_types or user_prefs.preferred_question_types,
                    'include_past_questions': include_past_questions,
                    'include_ai_generated': include_ai_generated,
                    'use_real_time_sources': use_real_time_sources
                }
            )
            
            # Generate questions using multiple strategies
            questions = []
            
            # Strategy 1: Past questions (if enabled)
            if include_past_questions:
                past_questions = await self._get_past_questions(
                    course=course,
                    topics=topics,
                    difficulty=difficulty,
                    max_count=max(1, num_questions // 3)
                )
                questions.extend(past_questions)
            
            # Strategy 2: AI-generated questions (if enabled)
            if include_ai_generated:
                remaining_count = num_questions - len(questions)
                if remaining_count > 0:
                    ai_questions = await self._generate_ai_questions(
                        course=course,
                        topics=topics,
                        difficulty=difficulty,
                        question_types=question_types,
                        count=remaining_count,
                        use_real_time=use_real_time_sources
                    )
                    questions.extend(ai_questions)
            
            # Strategy 3: Fill remaining with mixed sources
            remaining_count = num_questions - len(questions)
            if remaining_count > 0:
                mixed_questions = await self._generate_mixed_questions(
                    course=course,
                    topics=topics,
                    difficulty=difficulty,
                    count=remaining_count
                )
                questions.extend(mixed_questions)
            
            # Add questions to quiz
            for order, question in enumerate(questions[:num_questions], 1):
                QuizQuestion.objects.create(
                    quiz=quiz,
                    question=question,
                    order=order,
                    points=1,
                    time_limit_seconds=await self._estimate_question_time(question)
                )
            
            # Update quiz metadata
            quiz.total_questions = quiz.questions.count()
            quiz.total_points = quiz.quiz_questions.aggregate(
                Sum('points')
            )['points__sum'] or 0
            quiz.save()
            
            logger.info(f"Quiz generated successfully with {quiz.total_questions} questions")
            return quiz
            
        except Exception as e:
            logger.error(f"Failed to generate quiz: {e}")
            raise
    
    async def _get_user_preferences(self, user: User) -> QuizCustomization:
        """Get or create user quiz preferences"""
        prefs, created = QuizCustomization.objects.get_or_create(
            user=user,
            defaults={
                'default_num_questions': 10,
                'default_difficulty': 'intermediate',
                'preferred_question_types': ['multiple_choice', 'short_answer'],
                'include_past_questions': True,
                'include_ai_generated': True
            }
        )
        return prefs
    
    async def _get_past_questions(
        self, 
        course: Course = None, 
        topics: List[str] = None,
        difficulty: str = 'intermediate',
        max_count: int = 5
    ) -> List[Question]:
        """Retrieve relevant past questions from database"""
        try:
            queryset = Question.objects.filter(
                source_type='past_exam',
                difficulty_level=difficulty
            )
            
            if course:
                queryset = queryset.filter(course=course)
            
            if topics:
                # Filter by topics (stored as JSON field)
                for topic in topics:
                    queryset = queryset.filter(topics__contains=topic)
            
            # Get verified past questions first
            past_questions = list(queryset.filter(
                past_question_info__is_verified=True
            )[:max_count//2])
            
            # Fill remaining with unverified but high-rated questions
            if len(past_questions) < max_count:
                remaining = max_count - len(past_questions)
                additional = list(queryset.filter(
                    average_rating__gte=4.0
                ).exclude(id__in=[q.id for q in past_questions])[:remaining])
                past_questions.extend(additional)
            
            logger.info(f"Retrieved {len(past_questions)} past questions")
            return past_questions
            
        except Exception as e:
            logger.error(f"Failed to retrieve past questions: {e}")
            return []
    
    async def _generate_ai_questions(
        self,
        course: Course = None,
        topics: List[str] = None,
        difficulty: str = 'intermediate',
        question_types: List[str] = None,
        count: int = 5,
        use_real_time: bool = False
    ) -> List[Dict[str, Any]]:
        """Generate question data using AI models (returns data, not Django models)"""
        try:
            questions_data = []
            
            # Prepare context for AI generation
            context = await self._prepare_generation_context(
                course=course,
                topics=topics,
                use_real_time=use_real_time
            )
            
            # Generate questions in batches
            batch_size = min(5, count)
            for i in range(0, count, batch_size):
                batch_count = min(batch_size, count - i)
                
                batch_questions_data = await self._generate_question_batch_data(
                    context=context,
                    difficulty=difficulty,
                    question_types=question_types,
                    count=batch_count
                )
                questions_data.extend(batch_questions_data)
            
            logger.info(f"Generated {len(questions_data)} AI question data objects")
            return questions_data
            
        except Exception as e:
            logger.error(f"Failed to generate AI questions: {e}")
            return []
    
    async def _prepare_generation_context(
        self,
        course: Course = None,
        topics: List[str] = None,
        use_real_time: bool = False
    ) -> Dict[str, Any]:
        """Prepare context for AI question generation"""
        context = {
            'course_info': {},
            'topic_info': [],
            'real_time_info': [],
            'existing_questions': []
        }
        
        try:
            # Course context
            if course:
                context['course_info'] = {
                    'name': course.name,
                    'code': course.code,
                    'description': course.description,
                    'department': course.department.name if course.department else '',
                }
            
            # Topic context using RAG
            if topics:
                for topic in topics:
                    topic_docs = await self.rag_processor.search_documents(
                        query=topic,
                        course=course.code if course else None
                    )
                    context['topic_info'].append({
                        'topic': topic,
                        'documents': topic_docs[:3]  # Top 3 relevant documents
                    })
            
            # Real-time context (if enabled)
            if use_real_time and topics:
                for topic in topics[:2]:  # Limit to avoid API limits
                    search_query = f"{topic} {course.name if course else ''} practice questions"
                    real_time_results = await self.real_time_search.search(
                        query=search_query,
                        num_results=3
                    )
                    context['real_time_info'].extend(real_time_results)
            
            # Existing questions for diversity
            if course:
                existing = Question.objects.filter(course=course)[:10]
                context['existing_questions'] = [
                    {'title': q.title, 'type': q.question_type} for q in existing
                ]
            
        except Exception as e:
            logger.warning(f"Failed to prepare some context: {e}")
        
        return context
    
    async def _generate_question_batch_data(
        self,
        context: Dict[str, Any],
        difficulty: str,
        question_types: List[str],
        count: int
    ) -> List[Dict[str, Any]]:
        """Generate a batch of question data using AI (returns data, not Django models)"""
        try:
            # Prepare prompt
            prompt = self._build_generation_prompt(
                context=context,
                difficulty=difficulty,
                question_types=question_types,
                count=count
            )
            
            # Try primary model (Gemini)
            try:
                response = await self._generate_with_gemini(prompt)
                questions_data = self._parse_ai_response(response)
            except Exception as e:
                logger.warning(f"Gemini generation failed: {e}, trying OpenAI")
                # Fallback to OpenAI
                response = await self._generate_with_openai(prompt)
                questions_data = self._parse_ai_response(response)
            
            # Add course info to each question data
            for q_data in questions_data[:count]:
                q_data['course_info'] = context.get('course_info', {})
                q_data['source_type'] = 'ai_generated'
                q_data['source_reference'] = f"Generated by AI on {datetime.now(timezone.utc).isoformat()}"
                # Ensure we have the required fields
                q_data.setdefault('tags', ['ai-generated'])
                q_data.setdefault('topics', [])
            
            return questions_data[:count]
            
        except Exception as e:
            logger.error(f"Failed to generate question batch data: {e}")
            return []

    async def _generate_question_batch(
        self,
        context: Dict[str, Any],
        difficulty: str,
        question_types: List[str],
        count: int
    ) -> List[Question]:
        """Generate a batch of questions using AI"""
        try:
            # Prepare prompt
            prompt = self._build_generation_prompt(
                context=context,
                difficulty=difficulty,
                question_types=question_types,
                count=count
            )
            
            # Try primary model (Gemini)
            try:
                response = await self._generate_with_gemini(prompt)
                questions_data = self._parse_ai_response(response)
            except Exception as e:
                logger.warning(f"Gemini generation failed: {e}, trying OpenAI")
                # Fallback to OpenAI
                response = await self._generate_with_openai(prompt)
                questions_data = self._parse_ai_response(response)
            
            # Create Question objects
            questions = []
            for q_data in questions_data[:count]:
                question = await self._create_question_from_ai_data(q_data, context)
                if question:
                    questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to generate question batch: {e}")
            return []
    
    def _build_generation_prompt(
        self,
        context: Dict[str, Any],
        difficulty: str,
        question_types: List[str],
        count: int
    ) -> str:
        """Build comprehensive prompt for AI question generation"""
        
        prompt = f"""
You are an expert educational content creator. Generate {count} high-quality exam questions based on the following requirements:

DIFFICULTY LEVEL: {difficulty}
QUESTION TYPES: {', '.join(question_types) if question_types else 'any appropriate type'}

CONTEXT INFORMATION:
{self._format_context_for_prompt(context)}

REQUIREMENTS:
1. Questions must be academically rigorous and appropriate for {difficulty} level
2. Include clear, unambiguous questions with definitive answers
3. For multiple choice: provide 4 options with only one correct answer
4. Include detailed explanations for answers
5. Estimate solving time based on complexity
6. Ensure questions test understanding, not just memorization
7. Avoid questions similar to existing ones provided in context

RESPONSE FORMAT (JSON):
{{
    "questions": [
        {{
            "title": "Brief question title/topic",
            "question_text": "Full question text",
            "question_type": "multiple_choice|true_false|short_answer|essay|fill_blank|numerical|code",
            "difficulty_level": "{difficulty}",
            "correct_answer": "Correct answer",
            "answer_options": {{"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}},
            "answer_explanation": "Detailed explanation of why this is correct",
            "topics": ["topic1", "topic2"],
            "estimated_solve_time": 120,
            "complexity_analysis": {{
                "conceptual_complexity": 0.7,
                "computational_complexity": 0.5,
                "cognitive_load": 0.6
            }}
        }}
    ]
}}

Generate exactly {count} questions now:
"""
        return prompt
    
    def _format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format context information for AI prompt"""
        formatted = []
        
        if context['course_info']:
            course = context['course_info']
            formatted.append(f"COURSE: {course['name']} ({course['code']})")
            if course['description']:
                formatted.append(f"DESCRIPTION: {course['description']}")
        
        if context['topic_info']:
            formatted.append("\\nTOPICS TO COVER:")
            for topic_data in context['topic_info']:
                formatted.append(f"- {topic_data['topic']}")
        
        if context['real_time_info']:
            formatted.append("\\nCURRENT/TRENDING INFORMATION:")
            for info in context['real_time_info'][:3]:
                formatted.append(f"- {info.get('title', '')} ({info.get('source', '')})")
        
        if context['existing_questions']:
            formatted.append("\\nEXISTING QUESTIONS (avoid similar topics):")
            for eq in context['existing_questions'][:5]:
                formatted.append(f"- {eq['title']} ({eq['type']})")
        
        return "\\n".join(formatted)
    
    async def _generate_with_gemini(self, prompt: str) -> str:
        """Generate content using Google Gemini"""
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise
    
    async def _generate_with_openai(self, prompt: str) -> str:
        """Generate content using OpenAI"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response and extract question data"""
        try:
            # Clean response and extract JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:-3]
            elif response.startswith('```'):
                response = response[3:-3]
            
            data = json.loads(response)
            return data.get('questions', [])
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            # Try to extract questions manually if JSON parsing fails
            return self._manual_parse_response(response)
    
    def _manual_parse_response(self, response: str) -> List[Dict[str, Any]]:
        """Manually parse AI response when JSON parsing fails"""
        # Implementation for manual parsing as fallback
        # This would involve regex patterns to extract question components
        logger.warning("Using manual parsing - may be less reliable")
        return []
    
    async def _create_question_from_ai_data(
        self, 
        q_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Optional[Question]:
        """Create Question object from AI-generated data"""
        try:
            # Extract course from context
            course = None
            if context['course_info']:
                course = Course.objects.filter(
                    code=context['course_info']['code']
                ).first()
            
            # Create question
            question = Question.objects.create(
                title=q_data.get('title', '')[:500],
                question_text=q_data.get('question_text', ''),
                question_type=q_data.get('question_type', 'multiple_choice'),
                correct_answer=q_data.get('correct_answer', ''),
                answer_options=q_data.get('answer_options', {}),
                answer_explanation=q_data.get('answer_explanation', ''),
                difficulty_level=q_data.get('difficulty_level', 'intermediate'),
                estimated_solve_time=q_data.get('estimated_solve_time', 120),
                course=course,
                topics=q_data.get('topics', []),
                tags=q_data.get('tags', ['ai-generated']),
                source_type='ai_generated',
                source_reference=f"Generated by AI on {datetime.now(timezone.utc).isoformat()}",
                created_by=None  # AI-generated questions don't have a human creator
            )
            
            # Create difficulty analysis
            if q_data.get('complexity_analysis'):
                complexity = q_data['complexity_analysis']
                DifficultyAnalysis.objects.create(
                    question=question,
                    conceptual_complexity=complexity.get('conceptual_complexity', 0.5),
                    computational_complexity=complexity.get('computational_complexity', 0.5),
                    cognitive_load=complexity.get('cognitive_load', 0.5),
                    estimated_solve_time=q_data.get('estimated_solve_time', 120),
                    analysis_model='gemini-pro',
                    analysis_confidence=0.8
                )
            
            # Generate embeddings for the question
            await self._generate_question_embeddings(question)
            
            return question
            
        except Exception as e:
            logger.error(f"Failed to create question from AI data: {e}")
            return None
    
    async def _generate_mixed_questions(
        self,
        course: Course = None,
        topics: List[str] = None,
        difficulty: str = 'intermediate',
        count: int = 5
    ) -> List[Question]:
        """Generate questions from mixed sources as fallback"""
        questions = []
        
        # Try to get from existing high-rated questions
        try:
            queryset = Question.objects.filter(
                average_rating__gte=4.0,
                difficulty_level=difficulty
            )
            
            if course:
                queryset = queryset.filter(course=course)
            
            existing_questions = list(queryset[:count])
            questions.extend(existing_questions)
            
        except Exception as e:
            logger.error(f"Failed to get mixed questions: {e}")
        
        return questions
    
    async def _estimate_question_time(self, question: Question) -> int:
        """Estimate time needed to solve a question"""
        base_time = question.estimated_solve_time
        
        # Adjust based on question type
        type_multipliers = {
            'multiple_choice': 1.0,
            'true_false': 0.5,
            'short_answer': 1.5,
            'essay': 3.0,
            'fill_blank': 0.8,
            'numerical': 1.2,
            'code': 2.5
        }
        
        multiplier = type_multipliers.get(question.question_type, 1.0)
        estimated_time = int(base_time * multiplier)
        
        return max(30, min(600, estimated_time))  # Between 30 seconds and 10 minutes
    
    async def _generate_question_embeddings(self, question: Question):
        """Generate and store embeddings for question search and similarity"""
        try:
            # Prepare different content combinations for embedding
            content_variants = [
                ('question_answer', f"{question.question_text}\\n\\nAnswer: {question.correct_answer}"),
                ('question_only', question.question_text),
                ('answer_only', question.correct_answer),
            ]
            
            if question.answer_explanation:
                content_variants.append(('explanation', question.answer_explanation))
            
            # Generate embeddings for each variant
            for content_type, content_text in content_variants:
                # Create content hash for deduplication
                content_hash = hashlib.sha256(content_text.encode()).hexdigest()
                
                # Check if embedding already exists
                if not EmbeddingVector.objects.filter(
                    question=question, 
                    content_type=content_type
                ).exists():
                    # Generate embedding using OpenAI
                    embedding = await self._get_text_embedding(content_text)
                    
                    if embedding:
                        EmbeddingVector.objects.create(
                            question=question,
                            content_type=content_type,
                            vector_data=embedding,
                            vector_model='text-embedding-3-small',
                            vector_dimension=len(embedding),
                            content_hash=content_hash
                        )
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings for question {question.id}: {e}")
    
    async def _get_text_embedding(self, text: str) -> Optional[List[float]]:
        """Get text embedding using OpenAI"""
        try:
            response = await openai.Embedding.acreate(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to get text embedding: {e}")
            return None
    
    async def process_image_upload(
        self, 
        image_file, 
        user: User,
        course: Course = None,
        extract_text: bool = True
    ) -> Dict[str, Any]:
        """
        Process uploaded images with OCR and AI analysis
        
        Args:
            image_file: Uploaded image file
            user: User uploading the image
            course: Associated course
            extract_text: Whether to perform OCR
            
        Returns:
            Dictionary with extracted text, questions, and metadata
        """
        try:
            result = {
                'extracted_text': '',
                'questions_found': [],
                'ai_analysis': {},
                'success': False,
                'error': None
            }
            
            # Read and process image
            image = Image.open(image_file)
            
            # Perform OCR if requested
            if extract_text and OCR_AVAILABLE:
                try:
                    extracted_text = pytesseract.image_to_string(image)
                    result['extracted_text'] = extracted_text.strip()
                except Exception as e:
                    logger.warning(f"OCR failed: {e}")
                    result['extracted_text'] = ""
            elif extract_text and not OCR_AVAILABLE:
                logger.warning("OCR requested but pytesseract not available")
                result['extracted_text'] = "OCR not available - install pytesseract"
            
            # AI analysis using Gemini Vision
            try:
                # Convert image to base64 for Gemini
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_data = base64.b64encode(buffered.getvalue()).decode()
                
                analysis_prompt = """
                Analyze this image which appears to contain educational content (possibly exam questions, study materials, or academic content).
                
                Please provide:
                1. What type of educational content this appears to be
                2. Subject/topic identification
                3. Any questions visible in the image
                4. Difficulty level assessment
                5. Key concepts covered
                
                Format response as JSON:
                {
                    "content_type": "exam_questions|study_notes|textbook_page|worksheet|other",
                    "subject_area": "identified subject",
                    "topics": ["topic1", "topic2"],
                    "questions_detected": [
                        {
                            "question_text": "extracted question",
                            "question_type": "type",
                            "answer_visible": true/false
                        }
                    ],
                    "difficulty_level": "beginner|intermediate|advanced",
                    "key_concepts": ["concept1", "concept2"]
                }
                """
                
                # Use Gemini Vision model
                ai_response = self.gemini_vision_model.generate_content([
                    analysis_prompt,
                    {"mime_type": "image/png", "data": img_data}
                ])
                
                ai_analysis = self._parse_ai_response(ai_response.text)
                result['ai_analysis'] = ai_analysis[0] if ai_analysis else {}
                
            except Exception as e:
                logger.error(f"AI image analysis failed: {e}")
                result['ai_analysis'] = {}
            
            # Extract questions if found
            if result['ai_analysis'].get('questions_detected'):
                questions = []
                for q_data in result['ai_analysis']['questions_detected']:
                    # Create question object (similar to AI generation)
                    question_data = {
                        'title': f"Extracted from image: {q_data.get('question_text', '')[:50]}...",
                        'question_text': q_data.get('question_text', ''),
                        'question_type': q_data.get('question_type', 'short_answer'),
                        'difficulty_level': result['ai_analysis'].get('difficulty_level', 'intermediate'),
                        'topics': result['ai_analysis'].get('topics', []),
                        'source_type': 'user_uploaded',
                        'extracted_from_image': True
                    }
                    
                    question = await self._create_question_from_ai_data(
                        question_data, 
                        {'course_info': {'code': course.code} if course else {}}
                    )
                    
                    if question:
                        questions.append(question)
                
                result['questions_found'] = questions
            
            result['success'] = True
            return result
            
        except Exception as e:
            logger.error(f"Failed to process image upload: {e}")
            result['error'] = str(e)
            return result
    
    async def analyze_user_performance(self, user: User, course: Course = None) -> Dict[str, Any]:
        """
        Analyze user performance and provide recommendations
        
        Args:
            user: User to analyze
            course: Specific course (optional)
            
        Returns:
            Dictionary with performance analysis and recommendations
        """
        try:
            # Get performance data
            analytics_query = UserPerformanceAnalytics.objects.filter(user=user)
            if course:
                analytics_query = analytics_query.filter(course=course)
            
            recent_analytics = analytics_query.order_by('-period_end')[:5]
            
            if not recent_analytics:
                return {
                    'success': False,
                    'message': 'Insufficient performance data',
                    'recommendations': ['Take more quizzes to generate performance insights']
                }
            
            # Aggregate performance metrics
            total_attempted = sum(a.total_questions_attempted for a in recent_analytics)
            total_correct = sum(a.total_questions_correct for a in recent_analytics)
            total_time = sum(a.total_time_spent_minutes for a in recent_analytics)
            
            accuracy = (total_correct / total_attempted * 100) if total_attempted > 0 else 0
            avg_time_per_question = (total_time / total_attempted) if total_attempted > 0 else 0
            
            # Analyze trends
            accuracy_trend = self._calculate_trend([a.accuracy_percentage for a in recent_analytics])
            improvement_rate = sum(a.improvement_rate for a in recent_analytics) / len(recent_analytics)
            
            # Identify strengths and weaknesses
            all_weak_topics = []
            all_strong_topics = []
            for analytics in recent_analytics:
                all_weak_topics.extend(analytics.weak_topics)
                all_strong_topics.extend(analytics.strong_topics)
            
            # Count topic frequencies
            weak_topic_counts = {}
            strong_topic_counts = {}
            
            for topic in all_weak_topics:
                weak_topic_counts[topic] = weak_topic_counts.get(topic, 0) + 1
            
            for topic in all_strong_topics:
                strong_topic_counts[topic] = strong_topic_counts.get(topic, 0) + 1
            
            # Generate recommendations using AI
            recommendations = await self._generate_performance_recommendations(
                user=user,
                accuracy=accuracy,
                weak_topics=list(weak_topic_counts.keys()),
                strong_topics=list(strong_topic_counts.keys()),
                improvement_rate=improvement_rate,
                course=course
            )
            
            return {
                'success': True,
                'overall_accuracy': round(accuracy, 2),
                'total_questions_attempted': total_attempted,
                'average_time_per_question': round(avg_time_per_question, 2),
                'accuracy_trend': accuracy_trend,
                'improvement_rate': round(improvement_rate, 3),
                'weak_topics': sorted(weak_topic_counts.keys(), key=weak_topic_counts.get, reverse=True)[:5],
                'strong_topics': sorted(strong_topic_counts.keys(), key=strong_topic_counts.get, reverse=True)[:5],
                'recommendations': recommendations,
                'detailed_analytics': [
                    {
                        'period': f"{a.period_start} to {a.period_end}",
                        'accuracy': a.accuracy_percentage,
                        'questions_attempted': a.total_questions_attempted,
                        'time_spent': a.total_time_spent_minutes
                    } for a in recent_analytics
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze user performance: {e}")
            return {
                'success': False,
                'error': str(e),
                'recommendations': ['Unable to analyze performance at this time']
            }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values"""
        if len(values) < 2:
            return 'insufficient_data'
        
        recent_avg = sum(values[:2]) / 2  # Most recent 2 periods
        older_avg = sum(values[2:]) / len(values[2:]) if len(values) > 2 else recent_avg
        
        if recent_avg > older_avg * 1.05:
            return 'improving'
        elif recent_avg < older_avg * 0.95:
            return 'declining'
        else:
            return 'stable'
    
    async def _generate_performance_recommendations(
        self,
        user: User,
        accuracy: float,
        weak_topics: List[str],
        strong_topics: List[str],
        improvement_rate: float,
        course: Course = None
    ) -> List[str]:
        """Generate AI-powered performance recommendations"""
        try:
            prompt = f"""
            Generate personalized study recommendations for a student based on their performance data:
            
            PERFORMANCE METRICS:
            - Overall Accuracy: {accuracy:.1f}%
            - Improvement Rate: {improvement_rate:.3f}
            - Weak Topics: {', '.join(weak_topics[:5])}
            - Strong Topics: {', '.join(strong_topics[:5])}
            - Course: {course.name if course else 'Multiple courses'}
            
            Generate 5-7 specific, actionable recommendations to help the student improve.
            Focus on:
            1. Addressing weak areas
            2. Building on strengths
            3. Study strategies
            4. Time management
            5. Practice suggestions
            
            Format as a JSON array of strings:
            ["recommendation 1", "recommendation 2", ...]
            """
            
            response = await self._generate_with_gemini(prompt)
            recommendations = json.loads(response)
            
            if isinstance(recommendations, list):
                return recommendations[:7]  # Limit to 7 recommendations
            else:
                return ["Focus on practicing weak topics", "Continue building on your strengths"]
                
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return [
                "Review and practice questions in your weak topic areas",
                "Continue practicing your strong topics to maintain proficiency",
                "Take regular practice quizzes to track improvement",
                "Focus on understanding concepts rather than memorization"
            ]


# Initialize global instance with error handling
try:
    ai_quiz_engine = AIQuizEngine()
    logger.info("AI Quiz Engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AI Quiz Engine: {e}")
    ai_quiz_engine = None
