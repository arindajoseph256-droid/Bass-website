/**
 * EduShare - AI Learning Platform
 * Main JavaScript Application
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// State Management
const state = {
    user: null,
    token: localStorage.getItem('token'),
    isAuthenticated: !!localStorage.getItem('token'),
    authMode: 'login', // 'login' or 'signup'
};

// DOM Elements
const elements = {
    navbar: document.getElementById('navbar'),
    mobileMenuBtn: document.getElementById('mobileMenuBtn'),
    navLinks: document.getElementById('navLinks'),
    loginBtn: document.getElementById('loginBtn'),
    signupBtn: document.getElementById('signupBtn'),
    heroSignupBtn: document.getElementById('heroSignupBtn'),
    authModal: document.getElementById('authModal'),
    modalClose: document.getElementById('modalClose'),
    authForm: document.getElementById('authForm'),
    modalTitle: document.getElementById('modalTitle'),
    modalSubtitle: document.getElementById('modalSubtitle'),
    authSubmit: document.getElementById('authSubmit'),
    switchAuth: document.getElementById('switchAuth'),
    nameFields: document.getElementById('nameFields'),
    chatInput: document.getElementById('chatInput'),
    sendBtn: document.getElementById('sendBtn'),
    chatMessages: document.getElementById('chatMessages'),
    coursesGrid: document.getElementById('coursesGrid'),
};

// Sample Courses Data (for demo)
const sampleCourses = [
    {
        id: 1,
        title: 'Complete Python Programming Masterclass',
        category: 'Programming',
        thumbnail: 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=400&h=250&fit=crop',
        price: 49.99,
        originalPrice: 99.99,
        students: 12500,
        rating: 4.8,
        duration: '42 hours',
        lessons: 156,
    },
    {
        id: 2,
        title: 'Machine Learning with Python',
        category: 'Data Science',
        thumbnail: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=400&h=250&fit=crop',
        price: 79.99,
        originalPrice: 149.99,
        students: 8500,
        rating: 4.9,
        duration: '38 hours',
        lessons: 124,
    },
    {
        id: 3,
        title: 'Web Development Bootcamp 2024',
        category: 'Web Development',
        thumbnail: 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=400&h=250&fit=crop',
        price: 59.99,
        originalPrice: 129.99,
        students: 15000,
        rating: 4.7,
        duration: '52 hours',
        lessons: 198,
    },
    {
        id: 4,
        title: 'AWS Cloud Solutions Architect',
        category: 'Cloud Computing',
        thumbnail: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400&h=250&fit=crop',
        price: 89.99,
        originalPrice: 199.99,
        students: 6200,
        rating: 4.6,
        duration: '45 hours',
        lessons: 142,
    },
    {
        id: 5,
        title: 'Data Structures & Algorithms',
        category: 'Computer Science',
        thumbnail: 'https://images.unsplash.com/photo-1509228468518-180dd4864904?w=400&h=250&fit=crop',
        price: 39.99,
        originalPrice: 79.99,
        students: 9800,
        rating: 4.8,
        duration: '35 hours',
        lessons: 118,
    },
    {
        id: 6,
        title: 'React - The Complete Guide',
        category: 'Web Development',
        thumbnail: 'https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=400&h=250&fit=crop',
        price: 54.99,
        originalPrice: 109.99,
        students: 11000,
        rating: 4.9,
        duration: '48 hours',
        lessons: 165,
    },
];

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initAuthModal();
    initChat();
    initCourseCards();
    initScrollEffects();
    checkAuthStatus();
});

// Navigation
function initNavigation() {
    // Mobile menu toggle
    elements.mobileMenuBtn?.addEventListener('click', () => {
        elements.navLinks.classList.toggle('active');
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(anchor.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
                elements.navLinks?.classList.remove('active');
            }
        });
    });
}

// Auth Modal
function initAuthModal() {
    // Open modal buttons
    [elements.loginBtn, elements.signupBtn, elements.heroSignupBtn].forEach(btn => {
        btn?.addEventListener('click', () => {
            openAuthModal('login');
        });
    });

    // Close modal
    elements.modalClose?.addEventListener('click', closeAuthModal);
    elements.authModal?.addEventListener('click', (e) => {
        if (e.target === elements.authModal) closeAuthModal();
    });

    // Switch between login/signup
    elements.switchAuth?.addEventListener('click', (e) => {
        e.preventDefault();
        state.authMode = state.authMode === 'login' ? 'signup' : 'login';
        updateAuthForm();
    });

    // Form submission
    elements.authForm?.addEventListener('submit', handleAuthSubmit);
}

function openAuthModal(mode = 'login') {
    state.authMode = mode;
    updateAuthForm();
    elements.authModal?.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeAuthModal() {
    elements.authModal?.classList.remove('active');
    document.body.style.overflow = '';
    elements.authForm?.reset();
}

function updateAuthForm() {
    if (state.authMode === 'login') {
        elements.modalTitle.textContent = 'Welcome Back';
        elements.modalSubtitle.textContent = 'Sign in to continue learning';
        elements.authSubmit.textContent = 'Sign In';
        elements.switchAuth.textContent = 'Sign up';
        elements.nameFields.style.display = 'none';
    } else {
        elements.modalTitle.textContent = 'Create Account';
        elements.modalSubtitle.textContent = 'Start your learning journey today';
        elements.authSubmit.textContent = 'Create Account';
        elements.switchAuth.textContent = 'Sign in';
        elements.nameFields.style.display = 'block';
    }
}

async function handleAuthSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(elements.authForm);
    const data = Object.fromEntries(formData);
    
    const endpoint = state.authMode === 'login' ? '/accounts/login/' : '/accounts/register/';
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        
        const result = await response.json();
        
        if (response.ok) {
            if (state.authMode === 'login') {
                localStorage.setItem('token', result.access);
                localStorage.setItem('refreshToken', result.refresh);
                state.token = result.access;
                state.isAuthenticated = true;
                updateAuthUI();
            }
            closeAuthModal();
            showNotification(state.authMode === 'login' ? 'Welcome back!' : 'Account created successfully!', 'success');
        } else {
            showNotification(result.error || 'An error occurred', 'error');
        }
    } catch (error) {
        console.error('Auth error:', error);
        showNotification('Network error. Please try again.', 'error');
    }
}

function checkAuthStatus() {
    if (state.isAuthenticated) {
        updateAuthUI();
    }
}

function updateAuthUI() {
    if (state.isAuthenticated) {
        elements.loginBtn.textContent = 'Dashboard';
        elements.loginBtn.onclick = () => window.location.href = '/dashboard.html';
        elements.signupBtn.textContent = 'Logout';
        elements.signupBtn.onclick = logout;
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    state.token = null;
    state.isAuthenticated = false;
    updateAuthUI();
    showNotification('Logged out successfully', 'success');
}

// Chat functionality
function initChat() {
    elements.sendBtn?.addEventListener('click', sendMessage);
    elements.chatInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
}

async function sendMessage() {
    const message = elements.chatInput.value.trim();
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    elements.chatInput.value = '';
    
    // Simulate AI response
    setTimeout(() => {
        const response = generateAIResponse(message);
        addMessage(response, 'bot');
    }, 1000);
}

function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type === 'user' ? 'user' : 'bot'}`;
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${content}</p>
        </div>
        <span class="timestamp">${time}</span>
    `;
    
    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function generateAIResponse(message) {
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
        return "Hello! I'm your AI study assistant. I can help you understand difficult concepts, create flashcards, generate practice questions, and much more. What would you like to learn about today?";
    }
    
    if (lowerMessage.includes('python')) {
        return "Python is a versatile programming language! I can help you learn Python fundamentals, advanced concepts, or specific topics like data structures, file handling, or web development with frameworks like Django and Flask. What specific Python topic would you like to explore?";
    }
    
    if (lowerMessage.includes('machine learning') || lowerMessage.includes('ml')) {
        return "Machine learning is an exciting field! I can help you understand supervised learning, unsupervised learning, neural networks, and more. Would you like me to explain a specific ML algorithm or create some practice questions for you?";
    }
    
    if (lowerMessage.includes('help')) {
        return "I can help you with:\n• Explaining complex topics\n• Creating flashcards for any subject\n• Generating practice questions\n• Summarizing study materials\n• Checking grammar and writing\n• Creating personalized study plans\n\nWhat would you like to work on?";
    }
    
    return "That's an interesting question! I can help explain concepts, create study materials, or generate practice questions. Could you tell me more about what specific topic or subject you'd like to explore?";
}

// Course Cards
function initCourseCards() {
    if (!elements.coursesGrid) return;
    
    const coursesHTML = sampleCourses.map(course => createCourseCard(course)).join('');
    elements.coursesGrid.innerHTML = coursesHTML;
}

function createCourseCard(course) {
    return `
        <div class="course-card">
            <div class="course-thumbnail">
                <img src="${course.thumbnail}" alt="${course.title}" loading="lazy">
                <span class="course-badge">${course.category}</span>
            </div>
            <div class="course-body">
                <div class="course-category">${course.category}</div>
                <h3 class="course-title">${course.title}</h3>
                <div class="course-meta">
                    <span><i class="fas fa-user-graduate"></i> ${formatNumber(course.students)}</span>
                    <span><i class="fas fa-clock"></i> ${course.duration}</span>
                    <span><i class="fas fa-play-circle"></i> ${course.lessons} lessons</span>
                </div>
                <div class="course-footer">
                    <div class="course-price">
                        $${course.price}
                        <span class="original">$${course.originalPrice}</span>
                    </div>
                    <div class="course-rating">
                        <i class="fas fa-star"></i>
                        <span>${course.rating}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function formatNumber(num) {
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Scroll Effects
function initScrollEffects() {
    window.addEventListener('scroll', () => {
        // Navbar shadow
        if (window.scrollY > 10) {
            elements.navbar?.classList.add('scrolled');
        } else {
            elements.navbar?.classList.remove('scrolled');
        }
    });
}

// Notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add notification styles
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : '#3B82F6'};
        color: white;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 0.75rem;
        z-index: 3000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// API Helper Functions
async function apiCall(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    
    if (state.token) {
        headers['Authorization'] = `Bearer ${state.token}`;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'API request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Export for use in other modules
window.EduShare = {
    state,
    apiCall,
    showNotification,
    logout,
};
