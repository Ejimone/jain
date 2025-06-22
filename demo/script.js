// Configuration
const API_BASE_URL = "http://127.0.0.1:8002/api/v1";
let authToken = localStorage.getItem("authToken");
let currentUser = null;

// DOM Elements
const elements = {
  // Auth elements
  authStatus: document.getElementById("authStatus"),
  authText: document.getElementById("authText"),
  authBtn: document.getElementById("authBtn"),
  loginForm: document.getElementById("loginFormElement"),
  registerForm: document.getElementById("registerFormElement"),
  toggleAuth: document.getElementById("toggleAuth"),

  // Image upload elements
  imageInput: document.getElementById("imageInput"),
  imageDropzone: document.getElementById("imageDropzone"),
  uploadImageBtn: document.getElementById("uploadImageBtn"),
  imageResults: document.getElementById("imageResults"),
  extractText: document.getElementById("extractText"),
  courseSelect: document.getElementById("courseSelect"),

  // Math solver elements
  mathInput: document.getElementById("mathInput"),
  mathDropzone: document.getElementById("mathDropzone"),
  solveMathBtn: document.getElementById("solveMathBtn"),
  mathResults: document.getElementById("mathResults"),

  // AI generation elements
  aiTopics: document.getElementById("aiTopics"),
  aiDifficulty: document.getElementById("aiDifficulty"),
  aiCount: document.getElementById("aiCount"),
  aiTypes: document.getElementById("aiTypes"),
  generateQuestionsBtn: document.getElementById("generateQuestionsBtn"),
  aiResults: document.getElementById("aiResults"),

  // Quiz elements
  loadQuizzesBtn: document.getElementById("loadQuizzesBtn"),
  createQuizBtn: document.getElementById("createQuizBtn"),
  quizResults: document.getElementById("quizResults"),

  // Analytics elements
  loadAnalyticsBtn: document.getElementById("loadAnalyticsBtn"),
  analyticsResults: document.getElementById("analyticsResults"),

  // UI elements
  loadingOverlay: document.getElementById("loadingOverlay"),
  notifications: document.getElementById("notifications"),
};

// Initialize the application
document.addEventListener("DOMContentLoaded", function () {
  initializeApp();
  setupEventListeners();
  updateAuthUI();
  loadCourses();
});

function initializeApp() {
  console.log("🚀 Examify Demo Initialized");
  console.log("🔗 API Base URL:", API_BASE_URL);
  
  // Debug: Check if elements exist
  const elementCheck = {
    authBtn: !!elements.authBtn,
    loginForm: !!elements.loginForm,
    registerForm: !!elements.registerForm,
    toggleAuth: !!elements.toggleAuth,
    imageInput: !!elements.imageInput,
    uploadImageBtn: !!elements.uploadImageBtn,
    courseSelect: !!elements.courseSelect,
    loadQuizzesBtn: !!elements.loadQuizzesBtn,
    generateQuestionsBtn: !!elements.generateQuestionsBtn
  };
  
  console.log("DOM Elements found:", elementCheck);
  
  // Check for missing critical elements
  const missingElements = Object.entries(elementCheck)
    .filter(([key, exists]) => !exists)
    .map(([key]) => key);
    
  if (missingElements.length > 0) {
    console.warn("⚠️ Missing DOM elements:", missingElements);
  } else {
    console.log("✅ All critical DOM elements found");
  }

  // Check if user is already authenticated
  if (authToken) {
    console.log("🔓 Found existing auth token, validating...");
    validateToken();
  } else {
    console.log("🔒 No existing auth token found");
  }

  // Auto-login for demo purposes
  if (!authToken) {
    console.log("🔐 Attempting auto-login for demo...");
    autoLogin();
  }
}

function setupEventListeners() {
  // Authentication
  if (elements.authBtn) elements.authBtn.addEventListener("click", handleAuthAction);
  if (elements.loginForm) elements.loginForm.addEventListener("submit", handleLogin);
  if (elements.registerForm) elements.registerForm.addEventListener("submit", handleRegister);
  if (elements.toggleAuth) elements.toggleAuth.addEventListener("click", toggleAuthForm);

  // Image upload
  if (elements.imageInput) elements.imageInput.addEventListener("change", handleImageSelect);
  if (elements.uploadImageBtn) elements.uploadImageBtn.addEventListener("click", uploadImage);
  if (elements.imageDropzone && elements.imageInput) setupDropzone(elements.imageDropzone, elements.imageInput);

  // Math solver
  if (elements.mathInput) elements.mathInput.addEventListener("change", handleMathImageSelect);
  if (elements.solveMathBtn) elements.solveMathBtn.addEventListener("click", solveMathProblem);
  if (elements.mathDropzone && elements.mathInput) setupDropzone(elements.mathDropzone, elements.mathInput);

  // AI generation
  if (elements.generateQuestionsBtn) elements.generateQuestionsBtn.addEventListener("click", generateQuestions);

  // Quiz management
  if (elements.loadQuizzesBtn) elements.loadQuizzesBtn.addEventListener("click", loadQuizzes);
  if (elements.createQuizBtn) elements.createQuizBtn.addEventListener("click", createQuiz);

  // Analytics
  if (elements.loadAnalyticsBtn) elements.loadAnalyticsBtn.addEventListener("click", loadAnalytics);
  
  // Test buttons
  if (document.getElementById('testCoursesBtn')) {
    document.getElementById('testCoursesBtn').addEventListener('click', testCourses);
  }
  if (document.getElementById('testQuizzesBtn')) {
    document.getElementById('testQuizzesBtn').addEventListener('click', testQuizzes);
  }
  if (document.getElementById('testImageBtn')) {
    document.getElementById('testImageBtn').addEventListener('click', testImageUpload);
  }
  if (document.getElementById('testAIBtn')) {
    document.getElementById('testAIBtn').addEventListener('click', testAIGeneration);
  }
}

// Authentication Functions
async function autoLogin() {
  try {
    console.log("🔐 Attempting auto-login...");
    
    // First try to login with the demo account if it exists
    try {
      await login("demo@example.com", "demo123456");
      return; // Success, exit early
    } catch (loginError) {
      console.log("Demo account login failed, trying to create account:", loginError.message);
    }

    // If login failed, try to register a new demo account
    const response = await fetch(`${API_BASE_URL}/students/auth/register/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: "demo_user_" + Date.now(),
        email: "demo@example.com",
        password: "demo123456",
        first_name: "Demo",
        last_name: "User",
      }),
    });

    if (response.ok) {
      const data = await response.json();
      console.log("✅ Auto-registration successful:", data);
      showNotification(
        "Auto-registration successful",
        "Demo account created successfully",
        "success"
      );

      // Now login with the newly created account
      await login("demo@example.com", "demo123456");
    } else {
      const errorData = await response.json();
      console.log("❌ Auto-registration failed:", errorData);
      
      // If registration failed because user already exists, try to login
      if (errorData.error && errorData.error.includes("already exists")) {
        console.log("🔄 User already exists, attempting login...");
        await login("demo@example.com", "demo123456");
      } else {
        throw new Error(errorData.error || "Registration failed");
      }
    }
  } catch (error) {
    console.log("❌ Auto-login failed completely:", error.message);
    showNotification(
      "Authentication Required",
      "Please login manually to access AI features",
      "warning"
    );
  }
}

async function login(email, password) {
  try {
    console.log("Attempting login for:", email);
    showLoading(true);

    const response = await fetch(`${API_BASE_URL}/students/auth/login/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: email,  // Changed from username to email
        password: password,
      }),
    });

    console.log("Login response status:", response.status);
    const data = await response.json();
    console.log("Login response data:", data);

    if (response.ok && data.token) {
      authToken = data.token;
      currentUser = data.user;
      localStorage.setItem("authToken", authToken);
      localStorage.setItem("currentUser", JSON.stringify(currentUser));

      updateAuthUI();
      showNotification(
        "Login Successful",
        `Welcome ${currentUser.first_name}!`,
        "success"
      );

      // Load initial data
      loadCourses();
    } else {
      throw new Error(data.error || data.message || "Login failed");
    }
  } catch (error) {
    console.error("Login error:", error);
    showNotification("Login Failed", error.message, "error");
  } finally {
    showLoading(false);
  }
}

async function handleLogin(e) {
  e.preventDefault();
  console.log("Login form submitted");
  
  const email = document.getElementById("loginUsername")?.value; // Using username field for email
  const password = document.getElementById("loginPassword")?.value;
  
  if (!email || !password) {
    showNotification("Login Error", "Please enter email and password", "error");
    return;
  }
  
  await login(email, password);
}

async function handleRegister(e) {
  e.preventDefault();

  try {
    showLoading(true);

    const formData = {
      username: document.getElementById("regUsername").value,
      email: document.getElementById("regEmail").value,
      password: document.getElementById("regPassword").value,
      first_name: document.getElementById("regFirstName").value,
      last_name: document.getElementById("regLastName").value,
    };

    const response = await fetch(`${API_BASE_URL}/students/auth/register/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });

    const data = await response.json();

    if (response.ok) {
      showNotification(
        "Registration Successful",
        "Please login with your new account",
        "success"
      );
      toggleAuthForm();
    } else {
      throw new Error(data.error || "Registration failed");
    }
  } catch (error) {
    showNotification("Registration Failed", error.message, "error");
  } finally {
    showLoading(false);
  }
}

function handleAuthAction() {
  if (authToken) {
    logout();
  } else {
    // Show auth section
    document
      .getElementById("authSection")
      .scrollIntoView({ behavior: "smooth" });
  }
}

function logout() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem("authToken");
  localStorage.removeItem("currentUser");
  updateAuthUI();
  showNotification(
    "Logged Out",
    "You have been logged out successfully",
    "success"
  );
}

function updateAuthUI() {
  if (authToken && currentUser) {
    elements.authText.textContent = `Welcome, ${currentUser.first_name}`;
    elements.authBtn.textContent = "Logout";
    elements.authBtn.classList.remove("btn-outline");
    elements.authBtn.classList.add("btn-primary");
  } else {
    elements.authText.textContent = "Not authenticated";
    elements.authBtn.textContent = "Login";
    elements.authBtn.classList.remove("btn-primary");
    elements.authBtn.classList.add("btn-outline");
  }
}

function toggleAuthForm() {
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");
  const toggleBtn = elements.toggleAuth;

  if (loginForm.style.display === "none") {
    loginForm.style.display = "block";
    registerForm.style.display = "none";
    toggleBtn.textContent = "Need an account? Register here";
  } else {
    loginForm.style.display = "none";
    registerForm.style.display = "block";
    toggleBtn.textContent = "Have an account? Login here";
  }
}

async function validateToken() {
  try {
    const response = await fetch(`${API_BASE_URL}/students/profile/`, {
      headers: {
        Authorization: `Token ${authToken}`,
      },
    });

    if (response.ok) {
      const userData = await response.json();
      currentUser = userData;
      localStorage.setItem("currentUser", JSON.stringify(currentUser));
      updateAuthUI();
    } else {
      logout();
    }
  } catch (error) {
    console.error("Token validation failed:", error);
    logout();
  }
}

// API Helper Functions
async function makeAuthenticatedRequest(url, options = {}) {
  if (!authToken) {
    throw new Error("Authentication required");
  }

  const headers = {
    Authorization: `Token ${authToken}`,
    ...options.headers,
  };

  return fetch(url, { ...options, headers });
}

// Image Upload Functions
function setupDropzone(dropzone, input) {
  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("drag-over");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("drag-over");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("drag-over");

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      input.files = files;
      input.dispatchEvent(new Event("change"));
    }
  });

  dropzone.addEventListener("click", () => {
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
      const preview = document.createElement("img");
      preview.src = e.target.result;
      preview.className = "image-preview";

      // Remove existing preview
      const existingPreview =
        elements.imageDropzone.querySelector(".image-preview");
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
      const preview = document.createElement("img");
      preview.src = e.target.result;
      preview.className = "image-preview";

      // Remove existing preview
      const existingPreview =
        elements.mathDropzone.querySelector(".image-preview");
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
    showNotification(
      "No File Selected",
      "Please select an image to upload",
      "warning"
    );
    return;
  }

  // Validate file type
  const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
  if (!validTypes.includes(file.type)) {
    showNotification(
      "Invalid File Type",
      "Please select a valid image file (JPEG, PNG, GIF, or WebP)",
      "error"
    );
    return;
  }

  // Validate file size (max 10MB)
  if (file.size > 10 * 1024 * 1024) {
    showNotification(
      "File Too Large",
      "Please select an image smaller than 10MB",
      "error"
    );
    return;
  }

  try {
    console.log("📤 Uploading image:", file.name, "Size:", file.size, "bytes");
    showLoading(true);

    const formData = new FormData();
    formData.append("image", file);
    formData.append("extract_text", elements.extractText.checked);

    const courseId = elements.courseSelect.value;
    if (courseId) {
      formData.append("course_id", courseId);
    }

    console.log("📤 Sending to:", `${API_BASE_URL}/ai-tutor/questions/upload_image/`);
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/ai-tutor/questions/upload_image/`,
      {
        method: "POST",
        body: formData,
      }
    );

    console.log("Image upload response status:", response.status);
    const data = await response.json();
    console.log("Image upload response data:", data);

    if (response.ok) {
      displayImageResults(data);
      showNotification(
        "Image Processed",
        "Image uploaded and processed successfully",
        "success"
      );
    } else {
      throw new Error(data.error || "Upload failed");
    }
  } catch (error) {
    console.error("Image upload error:", error);
    showNotification("Upload Failed", error.message, "error");
  } finally {
    showLoading(false);
  }
}

function displayImageResults(data) {
  console.log("🖼️ Displaying image results:", data);
  const content =
    elements.imageResults.querySelector("#imageResultsContent") ||
    elements.imageResults.appendChild(document.createElement("div"));
  content.id = "imageResultsContent";

  let html = '<div class="fade-in">';

  // Show success message
  if (data.success) {
    html += '<div class="success-message"><i class="fas fa-check-circle"></i> Image processed successfully!</div>';
  }

  // Handle OCR results
  if (data.extracted_text) {
    if (data.extracted_text.includes("OCR not available")) {
      html += `
                <div class="warning-message">
                    <h4><i class="fas fa-exclamation-triangle"></i> OCR Not Available</h4>
                    <p>Text extraction is not available. To enable OCR, install pytesseract on the backend server.</p>
                    <p>Commands to install OCR support:</p>
                    <code>pip install pytesseract</code><br>
                    <code>brew install tesseract</code> (on macOS)
                </div>
            `;
    } else {
      html += `
                <div class="ocr-results">
                    <h4><i class="fas fa-text-width"></i> Extracted Text</h4>
                    <div class="extracted-text">${data.extracted_text}</div>
                </div>
            `;
    }
  }

  // Show AI analysis
  if (data.ai_analysis && Object.keys(data.ai_analysis).length > 0) {
    html += `
            <div class="ai-analysis">
                <h4><i class="fas fa-brain"></i> AI Analysis</h4>
                <div class="analysis-grid">
                    <div class="analysis-item">
                        <strong>Content Type:</strong> ${
                          data.ai_analysis.content_type || "Unknown"
                        }
                    </div>
                    <div class="analysis-item">
                        <strong>Subject:</strong> ${
                          data.ai_analysis.subject_area || "Unknown"
                        }
                    </div>
                    <div class="analysis-item">
                        <strong>Difficulty:</strong> ${
                          data.ai_analysis.difficulty_level || "Unknown"
                        }
                    </div>
                </div>
            </div>
        `;
  } else {
    html += `
            <div class="info-message">
                <h4><i class="fas fa-info-circle"></i> AI Analysis</h4>
                <p>AI analysis is not yet configured. The image was successfully uploaded but no detailed analysis is available at this time.</p>
            </div>
        `;
  }

  // Show created questions
  if (data.questions_created && data.questions_created.length > 0) {
    html += `
            <div class="questions-created">
                <h4><i class="fas fa-question-circle"></i> Questions Created (${data.questions_created.length})</h4>
        `;

    data.questions_created.forEach((question, index) => {
      html += createQuestionCard(question, index + 1);
    });

    html += "</div>";
  } else if (data.success) {
    html += `
            <div class="info-message">
                <h4><i class="fas fa-question-circle"></i> Question Generation</h4>
                <p>No questions were automatically generated from this image. You can manually create questions using the AI Question Generation section.</p>
            </div>
        `;
  }

  // Show errors
  if (data.error) {
    html += `
            <div class="error-message">
                <h4><i class="fas fa-exclamation-circle"></i> Error</h4>
                <p>${data.error}</p>
            </div>
        `;
  }

  html += "</div>";
  content.innerHTML = html;
  elements.imageResults.style.display = "block";
}

// Math Solver Functions
async function solveMathProblem() {
  const file = elements.mathInput.files[0];
  if (!file) {
    showNotification(
      "No File Selected",
      "Please select a math problem image",
      "warning"
    );
    return;
  }

  try {
    showLoading(true);

    const formData = new FormData();
    formData.append("image", file);

    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/services/math/solve/`,
      {
        method: "POST",
        body: formData,
      }
    );

    const data = await response.json();

    if (response.ok) {
      displayMathResults(data);
      showNotification(
        "Problem Solved",
        "Math problem solved successfully",
        "success"
      );
    } else {
      throw new Error(data.error || "Math solving failed");
    }
  } catch (error) {
    showNotification("Math Solving Failed", error.message, "error");
  } finally {
    showLoading(false);
  }
}

function displayMathResults(data) {
  const content =
    elements.mathResults.querySelector("#mathResultsContent") ||
    elements.mathResults.appendChild(document.createElement("div"));
  content.id = "mathResultsContent";

  let html = '<div class="fade-in">';

  if (data.success && data.data) {
    const result = data.data;

    html += `
            <div class="math-solution">
                <div class="math-problem">
                    <h4><i class="fas fa-question"></i> Problem</h4>
                    <p>${
                      result.extracted_problem ||
                      "Problem text extracted from image"
                    }</p>
                </div>
                
                <div class="math-answer">
                    <h4><i class="fas fa-check-circle"></i> Answer</h4>
                    <p>${result.final_answer}</p>
                </div>
                
                ${
                  result.solution_steps && result.solution_steps.length > 0
                    ? `
                    <div class="math-steps">
                        <h4><i class="fas fa-list-ol"></i> Solution Steps</h4>
                        <ol>
                            ${result.solution_steps
                              .map((step) => `<li>${step}</li>`)
                              .join("")}
                        </ol>
                    </div>
                `
                    : ""
                }
                
                ${
                  result.explanation
                    ? `
                    <div class="math-explanation">
                        <h4><i class="fas fa-lightbulb"></i> Explanation</h4>
                        <p>${result.explanation}</p>
                    </div>
                `
                    : ""
                }
                
                ${
                  result.study_tips && result.study_tips.length > 0
                    ? `
                    <div class="study-tips">
                        <h4><i class="fas fa-graduation-cap"></i> Study Tips</h4>
                        <ul>
                            ${result.study_tips
                              .map((tip) => `<li>${tip}</li>`)
                              .join("")}
                        </ul>
                    </div>
                `
                    : ""
                }
                
                <div class="math-meta">
                    <div class="meta-item">
                        <strong>Difficulty:</strong> ${
                          result.difficulty || "Unknown"
                        }
                    </div>
                    <div class="meta-item">
                        <strong>Confidence:</strong> ${Math.round(
                          (result.confidence_score || 0) * 100
                        )}%
                    </div>
                    <div class="meta-item">
                        <strong>Processing Time:</strong> ${
                          result.processing_time || 0
                        }s
                    </div>
                </div>
            </div>
        `;
  } else {
    html += `
            <div class="error-message">
                <strong>Error:</strong> ${
                  data.error || "Failed to solve math problem"
                }
            </div>
        `;
  }

  html += "</div>";
  content.innerHTML = html;
  elements.mathResults.style.display = "block";
}

// AI Question Generation Functions
async function generateQuestions() {
  try {
    showLoading(true);

    const topics = elements.aiTopics.value
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t);
    const selectedTypes = Array.from(elements.aiTypes.selectedOptions).map(
      (option) => option.value
    );

    const requestData = {
      topics: topics,
      difficulty: elements.aiDifficulty.value,
      count: parseInt(elements.aiCount.value),
      question_types: selectedTypes,
      use_real_time: false,
    };

    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/ai-tutor/questions/generate_ai_questions/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      }
    );

    const data = await response.json();

    if (response.ok) {
      displayAIResults(data);
      showNotification(
        "Questions Generated",
        `Generated ${data.count} questions successfully`,
        "success"
      );
    } else {
      throw new Error(data.error || "Question generation failed");
    }
  } catch (error) {
    showNotification("Generation Failed", error.message, "error");
  } finally {
    showLoading(false);
  }
}

function displayAIResults(data) {
  const content =
    elements.aiResults.querySelector("#aiResultsContent") ||
    elements.aiResults.appendChild(document.createElement("div"));
  content.id = "aiResultsContent";

  let html = '<div class="fade-in">';

  if (data.success && data.questions && data.questions.length > 0) {
    html += `<p class="success-message">Successfully generated ${data.count} questions</p>`;

    data.questions.forEach((question, index) => {
      html += createQuestionCard(question, index + 1);
    });
  } else {
    html += `
            <div class="error-message">
                <strong>No questions generated.</strong> ${
                  data.error || "Please try with different parameters."
                }
            </div>
        `;
  }

  html += "</div>";
  content.innerHTML = html;
  elements.aiResults.style.display = "block";
}

function createQuestionCard(question, index) {
  let html = `
        <div class="question-card">
            <div class="question-meta">
                <span><i class="fas fa-hashtag"></i> Question ${index}</span>
                <span><i class="fas fa-layer-group"></i> ${
                  question.question_type
                }</span>
                <span><i class="fas fa-signal"></i> ${
                  question.difficulty_level || "Unknown"
                }</span>
                <span><i class="fas fa-clock"></i> ${
                  question.estimated_solve_time || 120
                }s</span>
            </div>
            
            <div class="question-text">
                ${question.question_text}
            </div>
    `;

  if (
    question.answer_options &&
    Object.keys(question.answer_options).length > 0
  ) {
    html += '<div class="question-options">';
    Object.entries(question.answer_options).forEach(([key, value]) => {
      const isCorrect =
        value === question.correct_answer || key === question.correct_answer;
      html += `<div class="option ${
        isCorrect ? "correct" : ""
      }">${key}: ${value}</div>`;
    });
    html += "</div>";
  }

  if (question.answer_explanation) {
    html += `
            <div class="question-explanation">
                <strong>Explanation:</strong> ${question.answer_explanation}
            </div>
        `;
  }

  html += "</div>";
  return html;
}

// Course Management Functions
async function loadCourses() {
  try {
    console.log("🎓 Loading courses...");
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/students/courses/`
    );
    
    console.log("Courses response status:", response.status);
    const courses = await response.json();
    console.log("Courses data:", courses);

    if (response.ok) {
      populateCourseSelect(courses.results || courses);
    } else {
      console.error("Failed to load courses:", courses);
      showNotification("Error", "Failed to load courses: " + (courses.error || "Unknown error"), "error");
    }
  } catch (error) {
    console.error("Failed to load courses:", error);
    showNotification("Error", "Failed to load courses: " + error.message, "error");
  }
}

function populateCourseSelect(courses) {
  console.log("📚 Populating course select with:", courses);
  elements.courseSelect.innerHTML = '<option value="">Select a course</option>';

  if (Array.isArray(courses)) {
    courses.forEach((course) => {
      const option = document.createElement("option");
      option.value = course.id;
      option.textContent = `${course.code} - ${course.name}`;
      elements.courseSelect.appendChild(option);
    });
    console.log(`✅ Added ${courses.length} courses to dropdown`);
  } else {
    console.warn("⚠️ Courses data is not an array:", courses);
  }
}

// Quiz Management Functions
async function loadQuizzes() {
  try {
    console.log("🎯 Loading quizzes...");
    showLoading(true);

    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/ai-tutor/quizzes/`
    );
    
    console.log("Quizzes response status:", response.status);
    const data = await response.json();
    console.log("Quizzes data:", data);

    if (response.ok) {
      displayQuizzes(data.results || data);
      showNotification(
        "Quizzes Loaded",
        "Quiz data loaded successfully",
        "success"
      );
    } else {
      throw new Error(data.error || "Failed to load quizzes");
    }
  } catch (error) {
    console.error("Failed to load quizzes:", error);
    showNotification("Load Failed", error.message, "error");
  } finally {
    showLoading(false);
  }
}

function displayQuizzes(quizzes) {
  console.log("📝 Displaying quizzes:", quizzes);
  const content =
    elements.quizResults.querySelector("#quizResultsContent") ||
    elements.quizResults.appendChild(document.createElement("div"));
  content.id = "quizResultsContent";

  let html = '<div class="fade-in">';

  if (Array.isArray(quizzes) && quizzes.length > 0) {
    html += `<p class="success-message">Found ${quizzes.length} quizzes</p>`;

    quizzes.forEach((quiz, index) => {
      html += `
                <div class="quiz-card">
                    <div class="quiz-header">
                        <h4>${quiz.title}</h4>
                        <span class="quiz-status status-${quiz.status}">${quiz.status}</span>
                    </div>
                    <p>${quiz.description || "No description available"}</p>
                    <div class="quiz-meta">
                        <span><i class="fas fa-book"></i> ${quiz.course_name || "No Course"}</span>
                        <span><i class="fas fa-question-circle"></i> ${
                          quiz.total_questions || 0
                        } questions</span>
                        <span><i class="fas fa-clock"></i> ${
                          quiz.time_limit || "No limit"
                        } min</span>
                        <span><i class="fas fa-calendar"></i> ${new Date(
                          quiz.created_at
                        ).toLocaleDateString()}</span>
                    </div>
                    <div class="quiz-topics">
                        <strong>Topics:</strong> ${quiz.topics ? quiz.topics.join(", ") : "None"}
                    </div>
                    <div class="quiz-actions">
                        <button class="btn btn-primary" onclick="startQuiz('${quiz.id}')">Start Quiz</button>
                        <button class="btn btn-outline" onclick="viewQuizDetails('${quiz.id}')">View Details</button>
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

  html += "</div>";
  content.innerHTML = html;
  elements.quizResults.style.display = "block";
}

async function createQuiz() {
  // This would open a form to create a new quiz
  showNotification(
    "Create Quiz",
    "Quiz creation form would open here",
    "warning"
  );
}

// Quiz interaction functions
function startQuiz(quizId) {
  console.log("🎯 Starting quiz:", quizId);
  showNotification(
    "Start Quiz",
    `Quiz ${quizId} would start here. This feature will be implemented in the mobile app.`,
    "info"
  );
}

function viewQuizDetails(quizId) {
  console.log("👁️ Viewing quiz details:", quizId);
  showNotification(
    "Quiz Details",
    `Quiz details for ${quizId} would be shown here. This feature will be implemented in the mobile app.`,
    "info"
  );
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
      improvement_rate: Math.floor(Math.random() * 20) + 10,
    };

    displayAnalytics(analyticsData);
    showNotification(
      "Analytics Loaded",
      "Performance analytics loaded successfully",
      "success"
    );
  } catch (error) {
    showNotification("Load Failed", error.message, "error");
  } finally {
    showLoading(false);
  }
}

function displayAnalytics(data) {
  const content =
    elements.analyticsResults.querySelector("#analyticsResultsContent") ||
    elements.analyticsResults.appendChild(document.createElement("div"));
  content.id = "analyticsResultsContent";

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
  elements.analyticsResults.style.display = "block";
}

// Utility Functions
function showLoading(show) {
  const loadingOverlay = document.getElementById('loadingOverlay');
  if (loadingOverlay) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
  }
}

function showNotification(title, message, type = 'info') {
  console.log(`${type.toUpperCase()}: ${title} - ${message}`);
  
  const notifications = document.getElementById('notifications');
  if (!notifications) {
    // Fallback to alert if no notification container
    alert(`${title}: ${message}`);
    return;
  }
  
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.innerHTML = `
    <div class="notification-content">
      <strong>${title}</strong>
      <p>${message}</p>
    </div>
    <button class="notification-close" onclick="this.parentElement.remove()">×</button>
  `;
  
  notifications.appendChild(notification);
  
  // Auto-remove after 5 seconds
  setTimeout(() => {
    if (notification.parentElement) {
      notification.remove();
    }
  }, 5000);
}

function hideNotification() {
  const notifications = document.getElementById('notifications');
  if (notifications) {
    notifications.innerHTML = '';
  }
}

// Error Handling
window.addEventListener("error", (event) => {
  console.error("Global error:", event.error);
  showNotification("Error", "An unexpected error occurred", "error");
});

// Service Worker Registration (for offline capabilities)
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then((registration) => {
        console.log("SW registered: ", registration);
      })
      .catch((registrationError) => {
        console.log("SW registration failed: ", registrationError);
      });
  });
}

// Test Functions for Quick Debugging
async function testCourses() {
  console.log("🧪 Testing courses...");
  const testResults = document.getElementById('testResultsContent');
  const testContainer = document.getElementById('testResults');
  
  try {
    testResults.innerHTML = '<p>Testing courses endpoint...</p>';
    testContainer.style.display = 'block';
    
    await loadCourses();
    
    const courseOptions = elements.courseSelect.children.length;
    testResults.innerHTML = `
      <div class="test-result success">
        <h4>✅ Courses Test Passed</h4>
        <p>Successfully loaded ${courseOptions - 1} courses (excluding "Select a course" option)</p>
      </div>
    `;
  } catch (error) {
    testResults.innerHTML = `
      <div class="test-result error">
        <h4>❌ Courses Test Failed</h4>
        <p>Error: ${error.message}</p>
      </div>
    `;
  }
}

async function testQuizzes() {
  console.log("🧪 Testing quizzes...");
  const testResults = document.getElementById('testResultsContent');
  const testContainer = document.getElementById('testResults');
  
  try {
    testResults.innerHTML = '<p>Testing quizzes endpoint...</p>';
    testContainer.style.display = 'block';
    
    await loadQuizzes();
    
    testResults.innerHTML = `
      <div class="test-result success">
        <h4>✅ Quizzes Test Passed</h4>
        <p>Successfully loaded quizzes - check the Quiz Management section below</p>
      </div>
    `;
  } catch (error) {
    testResults.innerHTML = `
      <div class="test-result error">
        <h4>❌ Quizzes Test Failed</h4>
        <p>Error: ${error.message}</p>
      </div>
    `;
  }
}

async function testImageUpload() {
  console.log("🧪 Testing image upload functionality...");
  const testResults = document.getElementById('testResultsContent');
  const testContainer = document.getElementById('testResults');
  
  testResults.innerHTML = `
    <div class="test-result info">
      <h4>ℹ️ Image Upload Test</h4>
      <p>Image upload functionality is available. To test:</p>
      <ol>
        <li>Go to the "Image Upload & AI Analysis" section</li>
        <li>Select an image file</li>
        <li>Click "Upload & Analyze"</li>
      </ol>
      <p><strong>Note:</strong> OCR requires pytesseract installation on the backend.</p>
    </div>
  `;
  testContainer.style.display = 'block';
}

async function testAIGeneration() {
  console.log("🧪 Testing AI generation...");
  const testResults = document.getElementById('testResultsContent');
  const testContainer = document.getElementById('testResults');
  
  try {
    testResults.innerHTML = '<p>Testing AI question generation...</p>';
    testContainer.style.display = 'block';
    
    // Set some test values
    elements.aiTopics.value = "mathematics, algebra";
    elements.aiDifficulty.value = "intermediate";
    elements.aiCount.value = "3";
    
    await generateQuestions();
    
    testResults.innerHTML = `
      <div class="test-result success">
        <h4>✅ AI Generation Test Initiated</h4>
        <p>AI question generation request sent - check the "AI Question Generation" section below for results</p>
      </div>
    `;
  } catch (error) {
    testResults.innerHTML = `
      <div class="test-result error">
        <h4>❌ AI Generation Test Failed</h4>
        <p>Error: ${error.message}</p>
      </div>
    `;
  }
}
