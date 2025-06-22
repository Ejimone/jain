export const API_BASE_URL = 'https://b5ef-2401-4900-91d1-ac9e-e5b8-224f-9528-f33e.ngrok-free.app/api/v1';

export const API_ENDPOINTS = {
  // Authentication
  REGISTER: '/students/auth/register/',
  LOGIN: '/students/auth/login/',
  LOGOUT: '/students/auth/logout/',
  PROFILE: '/students/profile/',
  
  // Academic Data
  REGIONS: '/students/regions/',
  DEPARTMENTS: '/students/departments/',
  COURSES: '/students/courses/',
  DASHBOARD: '/students/dashboard/',
  
  // Content
  QUESTIONS: '/content/questions/',
  STUDY_MATERIALS: '/content/study-materials/',
  CONTENT_STATS: '/content/stats/',
  
  // AI Tutor
  GENERATE_AI_QUESTIONS: '/ai-tutor/questions/generate_ai_questions/',
  UPLOAD_IMAGE: '/ai-tutor/questions/upload_image/',
  QUIZZES: '/ai-tutor/quizzes/',
  QUIZ_SESSIONS: '/ai-tutor/quiz-sessions/',
  AI_ANALYTICS: '/ai-tutor/analytics/',
  
  // AI Services
  MATH_SOLVE: '/services/math/solve/',
  IMAGE_ANALYZE: '/services/image/analyze/',
  DOCUMENT_PROCESS: '/services/document/process/',
  SERVICE_HEALTH: '/services/health/',
  
  // Recommendations
  CONTENT_RECOMMENDATIONS: '/recommendations/content/',
  STUDY_RECOMMENDATIONS: '/recommendations/study/',
  PERSONALIZED_RECOMMENDATIONS: '/recommendations/personalized/',
};

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
}; 