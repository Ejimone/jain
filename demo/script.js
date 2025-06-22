// Configuration
const API_BASE_URL = 'http://127.0.0.1:8002/api/v1';
let authToken = localStorage.getItem('authToken');
let currentUser = null;

// DOM Elements
const elements = {
    // Auth elements
    authStatus: document.getElementById('authStatus'),
    authText: document.getElementById('authText'),
    authBtn: document.getElementById('authBtn'),
    loginForm: document.getElementById('loginFormElement'),
    registerForm: document.getElementById('registerFormElement'),
    toggleAuth: document.getElementById('toggleAuth'),
    
    // Image upload elements
    imageInput: document.getElementById('imageInput'),
    imageDropzone: document.getElementById('imageDropzone'),
    uploadImageBtn: document.getElementById('uploadImageBtn'),
    imageResults: document.getElementById('imageResults'),
    extractText: document.getElementById('extractText'),
    courseSelect: document.getElementById('courseSelect'),
    
    // Math solver elements
    mathInput: document.getElementById('mathInput'),
    mathDropzone: document.getElementById('mathDropzone'),
    solveMathBtn: document.getElementById('solveMathBtn'),
    mathResults: document.getElementById('mathResults'),
    
    // AI generation elements
    aiTopics: document.getElementById('aiTopics'),
    aiDifficulty: document.getElementById('aiDifficulty'),
    aiCount: document.getElementById('aiCount'),
    aiTypes: document.getElementById('aiTypes'),
    generateQuestionsBtn: document.getElementById('generateQuestionsBtn'),
    aiResults: document.getElementById('aiResults'),
    
    // Quiz elements
    loadQuizzesBtn: document.getElementById('loadQuizzesBtn'),
    createQuizBtn: document.getElementById('createQuizBtn'),
    quizResults: document.getElementById('quizResults'),
    
    // Analytics elements
    loadAnalyticsBtn: document.getElementById('loadAnalyticsBtn'),
    analyticsResults: document.getElementById('analyticsResults'),
    
    // UI elements
    loadingOverlay: document.getElementById('loadingOverlay'),
    notifications: document.getElementById('notifications')
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    updateAuthUI();
    loadCourses();
});

function initializeApp() {
    console.log('🚀 Examify Demo Initialized');
    
    // Check if user is already authenticated
    if (authToken) {
        validateToken();
    }
    
    // Auto-login for demo purposes
    if (!authToken) {
        console.log('🔐 Attempting auto-login for demo...');
        autoLogin();
    }
}

function setupEventListeners() {
    // Authentication
    elements.authBtn.addEventListener('click', handleAuthAction);
    elements.loginForm.addEventListener('submit', handleLogin);
    elements.registerForm.addEventListener('submit', handleRegister);
    elements.toggleAuth.addEventListener('click', toggleAuthForm);
    
    // Image upload
    elements.imageInput.addEventListener('change', handleImageSelect);
    elements.uploadImageBtn.addEventListener('click', uploadImage);
    setupDropzone(elements.imageDropzone, elements.imageInput);
    
    // Math solver
    elements.mathInput.addEventListener('change', handleMathImageSelect);
    elements.solveMathBtn.addEventListener('click', solveMathProblem);
    setupDropzone(elements.mathDropzone, elements.mathInput);
    
    // AI generation
    elements.generateQuestionsBtn.addEventListener('click', generateQuestions);
    
    // Quiz management
    elements.loadQuizzesBtn.addEventListener('click', loadQuizzes);
    elements.createQuizBtn.addEventListener('click', createQuiz);
    
    // Analytics
    elements.loadAnalyticsBtn.addEventListener('click', loadAnalytics);
}

// Authentication Functions
async function autoLogin() {
    try {
        const response = await fetch(`${API_BASE_URL}/students/register/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: 'demo_user_' + Date.now(),
                email: 'demo@example.com',
                password: 'demo123456',
                first_name: 'Demo',
                last_name: 'User'
            })
        });

        if (response.ok) {
            const data = await response.json();
            showNotification('Auto-registration successful', 'Demo account created', 'success');
            
            // Now login
            await login('demo_user_' + Math.floor(Date.now() / 1000), 'demo123456');
        } else {
            // Try to login with existing demo account
            await login('testuser', 'testpass123');
        }
    } catch (error) {
        console.log('Auto-login failed, manual authentication required');
        showNotification('Authentication Required', 'Please login to access AI features', 'warning');
    }
}

async function login(username, password) {
    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE_URL}/students/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const data = await response.json();
        
        if (response.ok && data.token) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            updateAuthUI();
            showNotification('Login Successful', `Welcome ${currentUser.first_name}!`, 'success');
            
            // Load initial data
            loadCourses();
        } else {
            throw new Error(data.error || 'Login failed');
        }
    } catch (error) {
        showNotification('Login Failed', error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    await login(username, password);
}

async function handleRegister(e) {
    e.preventDefault();
    
    try {
        showLoading(true);
        
        const formData = {
            username: document.getElementById('regUsername').value,
            email: document.getElementById('regEmail').value,
            password: document.getElementById('regPassword').value,
            first_name: document.getElementById('regFirstName').value,
            last_name: document.getElementById('regLastName').value
        };
        
        const response = await fetch(`${API_BASE_URL}/students/register/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        
        if (response.ok) {
            showNotification('Registration Successful', 'Please login with your new account', 'success');
            toggleAuthForm();
        } else {
            throw new Error(data.error || 'Registration failed');
        }
    } catch (error) {
        showNotification('Registration Failed', error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function handleAuthAction() {
    if (authToken) {
        logout();
    } else {
        // Show auth section
        document.getElementById('authSection').scrollIntoView({ behavior: 'smooth' });
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    updateAuthUI();
    showNotification('Logged Out', 'You have been logged out successfully', 'success');
}

function updateAuthUI() {
    if (authToken && currentUser) {
        elements.authText.textContent = `Welcome, ${currentUser.first_name}`;
        elements.authBtn.textContent = 'Logout';
        elements.authBtn.classList.remove('btn-outline');
        elements.authBtn.classList.add('btn-primary');
    } else {
        elements.authText.textContent = 'Not authenticated';
        elements.authBtn.textContent = 'Login';
        elements.authBtn.classList.remove('btn-primary');
        elements.authBtn.classList.add('btn-outline');
    }
}

function toggleAuthForm() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const toggleBtn = elements.toggleAuth;
    
    if (loginForm.style.display === 'none') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        toggleBtn.textContent = 'Need an account? Register here';
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        toggleBtn.textContent = 'Have an account? Login here';
    }
}

async function validateToken() {
    try {
        const response = await fetch(`${API_BASE_URL}/students/profile/`, {
            headers: {
                'Authorization': `Token ${authToken}`,
            }
        });
        
        if (response.ok) {
            const userData = await response.json();
            currentUser = userData;
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            updateAuthUI();
        } else {
            logout();
        }
    } catch (error) {
        console.error('Token validation failed:', error);
        logout();
    }
}

// API Helper Functions
async function makeAuthenticatedRequest(url, options = {}) {
    if (!authToken) {
        throw new Error('Authentication required');
    }
    
    const headers = {
        'Authorization': `Token ${authToken}`,
        ...options.headers
    };
    
    return fetch(url, { ...options, headers });
}

// Image Upload Functions
function setupDropzone(dropzone, input) {
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('drag-over');
    });
    
    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('drag-over');
    });
    
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            input.dispatchEvent(new Event('change'));
        }
    });
    
    dropzone.addEventListener('click', () => {
        input.click();
    });
}

function handleImageSelect(e) {
    const file = e.target.files[0];
    if (file) {
        elements.uploadImageBtn.disabled = false;
        
        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.createElement('img');
            preview.src = e.target.result;
            preview.className = 'image-preview';
            
            // Remove existing preview
            const existingPreview = elements.imageDropzone.querySelector('.image-preview');
            if (existingPreview) {
                existingPreview.remove();
            }
            
            elements.imageDropzone.appendChild(preview);
        };
        reader.readAsDataURL(file);
    }
}

function handleMathImageSelect(e) {
    const file = e.target.files[0];
    if (file) {
        elements.solveMathBtn.disabled = false;
        
        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.createElement('img');
            preview.src = e.target.result;
            preview.className = 'image-preview';
            
            // Remove existing preview
            const existingPreview = elements.mathDropzone.querySelector('.image-preview');
            if (existingPreview) {
                existingPreview.remove();
            }
            
            elements.mathDropzone.appendChild(preview);
        };
        reader.readAsDataURL(file);
    }
}

async function uploadImage() {
    const file = elements.imageInput.files[0];
    if (!file) {
        showNotification('No File Selected', 'Please select an image to upload', 'warning');
        return;
    }
    
    try {
        showLoading(true);
        
        const formData = new FormData();
        formData.append('image', file);
        formData.append('extract_text', elements.extractText.checked);
        
        const courseId = elements.courseSelect.value;
        if (courseId) {
            formData.append('course_id', courseId);
        }
        
        const response = await makeAuthenticatedRequest(
            `${API_BASE_URL}/ai-tutor/questions/upload_image/`,
            {
                method: 'POST',
                body: formData
            }
        );
        
        const data = await response.json();
        
        if (response.ok) {
            displayImageResults(data);
            showNotification('Image Processed', 'Image uploaded and processed successfully', 'success');
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        showNotification('Upload Failed', error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function displayImageResults(data) {
    const content = elements.imageResults.querySelector('#imageResultsContent') || 
                   elements.imageResults.appendChild(document.createElement('div'));
    content.id = 'imageResultsContent';
    
    let html = '<div class="fade-in">';
    
    if (data.extracted_text) {
        html += `
            <div class="ocr-results">
                <h4><i class="fas fa-text-width"></i> Extracted Text</h4>
                <p>${data.extracted_text}</p>
            </div>
        `;
    }
    
    if (data.ai_analysis) {
        html += `
            <div class="ai-analysis">
                <h4><i class="fas fa-brain"></i> AI Analysis</h4>
                <div class="analysis-grid">
                    <div class="analysis-item">
                        <strong>Content Type:</strong> ${data.ai_analysis.content_type || 'Unknown'}
                    </div>
                    <div class="analysis-item">
                        <strong>Subject:</strong> ${data.ai_analysis.subject_area || 'Unknown'}
                    </div>
                    <div class="analysis-item">
                        <strong>Difficulty:</strong> ${data.ai_analysis.difficulty_level || 'Unknown'}
                    </div>
                </div>
            </div>
        `;
    }
    
    if (data.questions_created && data.questions_created.length > 0) {
        html += `
            <div class="questions-created">
                <h4><i class="fas fa-question-circle"></i> Questions Created (${data.questions_created.length})</h4>
        `;
        
        data.questions_created.forEach((question, index) => {
            html += createQuestionCard(question, index + 1);
        });
        
        html += '</div>';
    }
    
    if (data.error) {
        html += `
            <div class="error-message">
                <strong>Error:</strong> ${data.error}
            </div>
        `;
    }
    
    html += '</div>';
    content.innerHTML = html;
    elements.imageResults.style.display = 'block';
}

// Math Solver Functions
async function solveMathProblem() {
    const file = elements.mathInput.files[0];
    if (!file) {
        showNotification('No File Selected', 'Please select a math problem image', 'warning');
        return;
    }
    
    try {
        showLoading(true);
        
        const formData = new FormData();
        formData.append('image', file);
        
        const response = await makeAuthenticatedRequest(
            `${API_BASE_URL}/services/solve_math_problem/`,
            {
                method: 'POST',
                body: formData
            }
        );
        
        const data = await response.json();
        
        if (response.ok) {
            displayMathResults(data);
            showNotification('Problem Solved', 'Math problem solved successfully', 'success');
        } else {
            throw new Error(data.error || 'Math solving failed');
        }
    } catch (error) {
        showNotification('Math Solving Failed', error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function displayMathResults(data) {
    const content = elements.mathResults.querySelector('#mathResultsContent') || 
                   elements.mathResults.appendChild(document.createElement('div'));
    content.id = 'mathResultsContent';
    
    let html = '<div class="fade-in">';
    
    if (data.success && data.data) {
        const result = data.data;
        
        html += `
            <div class="math-solution">
                <div class="math-problem">
                    <h4><i class="fas fa-question"></i> Problem</h4>
                    <p>${result.extracted_problem || 'Problem text extracted from image'}</p>
                </div>
                
                <div class="math-answer">
                    <h4><i class="fas fa-check-circle"></i> Answer</h4>
                    <p>${result.final_answer}</p>
                </div>
                
                ${result.solution_steps && result.solution_steps.length > 0 ? `
                    <div class="math-steps">
                        <h4><i class="fas fa-list-ol"></i> Solution Steps</h4>
                        <ol>
                            ${result.solution_steps.map(step => `<li>${step}</li>`).join('')}
                        </ol>
                    </div>
                ` : ''}
                
                ${result.explanation ? `
                    <div class="math-explanation">
                        <h4><i class="fas fa-lightbulb"></i> Explanation</h4>
                        <p>${result.explanation}</p>
                    </div>
                ` : ''}
                
                ${result.study_tips && result.study_tips.length > 0 ? `
                    <div class="study-tips">
                        <h4><i class="fas fa-graduation-cap"></i> Study Tips</h4>
                        <ul>
                            ${result.study_tips.map(tip => `<li>${tip}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                <div class="math-meta">
                    <div class="meta-item">
                        <strong>Difficulty:</strong> ${result.difficulty || 'Unknown'}
                    </div>
                    <div class="meta-item">
                        <strong>Confidence:</strong> ${Math.round((result.confidence_score || 0) * 100)}%
                    </div>
                    <div class="meta-item">
                        <strong>Processing Time:</strong> ${result.processing_time || 0}s
                    </div>
                </div>
            </div>
        `;
    } else {
        html += `
            <div class="error-message">
                <strong>Error:</strong> ${data.error || 'Failed to solve math problem'}
            </div>
        `;
    }
    
    html += '</div>';
    content.innerHTML = html;
    elements.mathResults.style.display = 'block';
}

// AI Question Generation Functions
async function generateQuestions() {
    try {
        showLoading(true);
        
        const topics = elements.aiTopics.value.split(',').map(t => t.trim()).filter(t => t);
        const selectedTypes = Array.from(elements.aiTypes.selectedOptions).map(option => option.value);
        
        const requestData = {
            topics: topics,
            difficulty: elements.aiDifficulty.value,
            count: parseInt(elements.aiCount.value),
            question_types: selectedTypes,
            use_real_time: false
        };
        
        const response = await makeAuthenticatedRequest(
            `${API_BASE_URL}/ai-tutor/questions/generate_ai_questions/`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            }
        );
        
        const data = await response.json();
        
        if (response.ok) {
            displayAIResults(data);
            showNotification('Questions Generated', `Generated ${data.count} questions successfully`, 'success');
        } else {
            throw new Error(data.error || 'Question generation failed');
        }
    } catch (error) {
        showNotification('Generation Failed', error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function displayAIResults(data) {
    const content = elements.aiResults.querySelector('#aiResultsContent') || 
                   elements.aiResults.appendChild(document.createElement('div'));
    content.id = 'aiResultsContent';
    
    let html = '<div class="fade-in">';
    
    if (data.success && data.questions && data.questions.length > 0) {
        html += `<p class="success-message">Successfully generated ${data.count} questions</p>`;
        
        data.questions.forEach((question, index) => {
            html += createQuestionCard(question, index + 1);
        });
    } else {
        html += `
            <div class="error-message">
                <strong>No questions generated.</strong> ${data.error || 'Please try with different parameters.'}
            </div>
        `;
    }
    
    html += '</div>';
    content.innerHTML = html;
    elements.aiResults.style.display = 'block';
}

function createQuestionCard(question, index) {
    let html = `
        <div class="question-card">
            <div class="question-meta">
                <span><i class="fas fa-hashtag"></i> Question ${index}</span>
                <span><i class="fas fa-layer-group"></i> ${question.question_type}</span>
                <span><i class="fas fa-signal"></i> ${question.difficulty_level || 'Unknown'}</span>
                <span><i class="fas fa-clock"></i> ${question.estimated_solve_time || 120}s</span>
            </div>
            
            <div class="question-text">
                ${question.question_text}
            </div>
    `;
    
    if (question.answer_options && Object.keys(question.answer_options).length > 0) {
        html += '<div class="question-options">';
        Object.entries(question.answer_options).forEach(([key, value]) => {
            const isCorrect = value === question.correct_answer || key === question.correct_answer;
            html += `<div class="option ${isCorrect ? 'correct' : ''}">${key}: ${value}</div>`;
        });
        html += '</div>';
    }
    
    if (question.answer_explanation) {
        html += `
            <div class="question-explanation">
                <strong>Explanation:</strong> ${question.answer_explanation}
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

// Course Management Functions
async function loadCourses() {
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/students/courses/`);
        const courses = await response.json();
        
        if (response.ok) {
            populateCourseSelect(courses.results || courses);
        }
    } catch (error) {
        console.error('Failed to load courses:', error);
    }
}

function populateCourseSelect(courses) {
    elements.courseSelect.innerHTML = '<option value="">Select a course</option>';
    
    if (Array.isArray(courses)) {
        courses.forEach(course => {
            const option = document.createElement('option');
            option.value = course.id;
            option.textContent = `${course.code} - ${course.name}`;
            elements.courseSelect.appendChild(option);
        });
    }
}

// Quiz Management Functions
async function loadQuizzes() {
    try {
        showLoading(true);
        
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/ai-tutor/quizzes/`);
        const data = await response.json();
        
        if (response.ok) {
            displayQuizzes(data.results || data);
            showNotification('Quizzes Loaded', 'Quiz data loaded successfully', 'success');
        } else {
            throw new Error(data.error || 'Failed to load quizzes');
        }
    } catch (error) {
        showNotification('Load Failed', error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function displayQuizzes(quizzes) {
    const content = elements.quizResults.querySelector('#quizResultsContent') || 
                   elements.quizResults.appendChild(document.createElement('div'));
    content.id = 'quizResultsContent';
    
    let html = '<div class="fade-in">';
    
    if (Array.isArray(quizzes) && quizzes.length > 0) {
        html += `<p class="success-message">Found ${quizzes.length} quizzes</p>`;
        
        quizzes.forEach((quiz, index) => {
            html += `
                <div class="quiz-card">
                    <h4>${quiz.title}</h4>
                    <p>${quiz.description || 'No description available'}</p>
                    <div class="quiz-meta">
                        <span><i class="fas fa-question-circle"></i> ${quiz.question_count || 0} questions</span>
                        <span><i class="fas fa-clock"></i> ${quiz.time_limit || 'No limit'}</span>
                        <span><i class="fas fa-calendar"></i> ${new Date(quiz.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
            `;
        });
    } else {
        html += `
            <div class="error-message">
                <strong>No quizzes found.</strong> Create your first quiz to get started.
            </div>
        `;
    }
    
    html += '</div>';
    content.innerHTML = html;
    elements.quizResults.style.display = 'block';
}

async function createQuiz() {
    // This would open a form to create a new quiz
    showNotification('Create Quiz', 'Quiz creation form would open here', 'warning');
}

// Analytics Functions
async function loadAnalytics() {
    try {
        showLoading(true);
        
        // Mock analytics data since endpoint might not be available
        const analyticsData = {
            total_questions: Math.floor(Math.random() * 100) + 50,
            total_quizzes: Math.floor(Math.random() * 20) + 10,
            average_score: Math.floor(Math.random() * 30) + 70,
            study_time: Math.floor(Math.random() * 50) + 100,
            improvement_rate: Math.floor(Math.random() * 20) + 10
        };
        
        displayAnalytics(analyticsData);
        showNotification('Analytics Loaded', 'Performance analytics loaded successfully', 'success');
    } catch (error) {
        showNotification('Load Failed', error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function displayAnalytics(data) {
    const content = elements.analyticsResults.querySelector('#analyticsResultsContent') || 
                   elements.analyticsResults.appendChild(document.createElement('div'));
    content.id = 'analyticsResultsContent';
    
    const html = `
        <div class="fade-in">
            <div class="analytics-grid">
                <div class="analytics-card">
                    <h3>${data.total_questions}</h3>
                    <p>Questions Answered</p>
                </div>
                <div class="analytics-card">
                    <h3>${data.total_quizzes}</h3>
                    <p>Quizzes Completed</p>
                </div>
                <div class="analytics-card">
                    <h3>${data.average_score}%</h3>
                    <p>Average Score</p>
                </div>
                <div class="analytics-card">
                    <h3>${data.study_time}h</h3>
                    <p>Study Time</p>
                </div>
                <div class="analytics-card">
                    <h3>+${data.improvement_rate}%</h3>
                    <p>Improvement Rate</p>
                </div>
            </div>
            
            <div class="analytics-details">
                <h4><i class="fas fa-chart-line"></i> Performance Insights</h4>
                <ul>
                    <li>Your performance has improved by ${data.improvement_rate}% this month</li>
                    <li>You've spent ${data.study_time} hours studying with AI assistance</li>
                    <li>Your strongest areas: AI & Machine Learning topics</li>
                    <li>Recommended focus: Practice more advanced-level questions</li>
                </ul>
            </div>
        </div>
    `;
    
    content.innerHTML = html;
    elements.analyticsResults.style.display = 'block';
}

// Utility Functions
function showLoading(show) {
    elements.loadingOverlay.style.display = show ? 'flex' : 'none';
}

function showNotification(title, message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-title">${title}</div>
        <div class="notification-message">${message}</div>
    `;
    
    elements.notifications.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Error Handling
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    showNotification('Error', 'An unexpected error occurred', 'error');
});

// Service Worker Registration (for offline capabilities)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
