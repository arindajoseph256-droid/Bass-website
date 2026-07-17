# EduShare - AI-Powered Learning Management System

<div align="center">
    <img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python">
    <img src="https://img.shields.io/badge/Django-4.2+-green.svg" alt="Django">
    <img src="https://img.shields.io/badge/DRF-3.14+-red.svg" alt="DRF">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</div>

EduShare is a modern, AI-powered Learning Management System (LMS) built with Django and JavaScript. It combines traditional course management features with advanced AI capabilities to provide a personalized learning experience.

## 🚀 Features

### Core Features
- **User Authentication**: JWT-based authentication with role-based access control (Admin, Teacher, Student)
- **Course Management**: Create, edit, and publish courses with categories and reviews
- **Lesson Content**: Video lessons, PDF materials, and interactive content
- **Assignments**: Create assignments, collect submissions, and provide feedback
- **Quizzes**: Multiple question types (MCQ, True/False, Fill in Blank, Essay) with auto-grading
- **Certificates**: Generate and verify completion certificates
- **Discussion Forums**: Course-specific forums for student interaction
- **Notifications**: Real-time notifications and email alerts
- **Analytics**: Comprehensive learning analytics and progress tracking

### AI Features
- **AI Tutor**: 24/7 AI assistant for answering questions and explaining concepts
- **Auto-generated Questions**: Create practice quizzes automatically
- **Flashcards**: Generate flashcards from study materials
- **Grammar Checker**: Check and improve writing
- **Study Plans**: Personalized study schedules
- **Text Summarization**: Quick summaries of long content

## 📋 Requirements

- Python 3.12+
- PostgreSQL 15+ (or SQLite for development)
- Redis 7+ (for Celery)
- Docker & Docker Compose (optional)

## 🛠️ Installation

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/arindajoseph256-droid/Bass-website.git
cd Bass-website

# Copy environment variables
cp backend/.env.example backend/.env

# Build and run with Docker Compose
docker-compose up -d
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/arindajoseph256-droid/Bass-website.git
cd Bass-website

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

## 📁 Project Structure

```
edushare/
├── backend/
│   ├── accounts/          # User authentication and profiles
│   ├── courses/          # Course management
│   ├── lessons/          # Lesson content
│   ├── assignments/      # Assignments and submissions
│   ├── quizzes/          # Quiz system
│   ├── certificates/     # Certificates
│   ├── forums/          # Discussion forums
│   ├── notifications/    # Notifications
│   ├── analytics/        # Learning analytics
│   ├── ai/               # AI tutor integration
│   ├── schools/          # School management
│   ├── uploads/          # File uploads
│   ├── users/            # User management
│   ├── search/           # Global search
│   ├── config/           # Django settings
│   └── common/           # Shared utilities
├── frontend/
│   ├── static/           # Static files (CSS, JS)
│   └── index.html        # Main HTML file
├── deployment/           # Deployment configs
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile.backend    # Backend Docker image
├── Dockerfile.nginx      # Nginx Docker image
└── nginx.conf           # Nginx configuration
```

## 🔐 API Endpoints

### Authentication
- `POST /api/accounts/register/` - User registration
- `POST /api/accounts/login/` - User login
- `GET /api/accounts/profile/` - Get user profile

### Courses
- `GET /api/courses/` - List courses
- `POST /api/courses/` - Create course (teacher)
- `GET /api/courses/{id}/` - Course detail
- `POST /api/courses/{id}/enroll/` - Enroll in course

### AI Tutor
- `GET /api/ai/sessions/` - List chat sessions
- `POST /api/ai/sessions/` - Create session
- `POST /api/ai/sessions/{id}/send_message/` - Send message
- `POST /api/ai/generate/questions/` - Generate questions
- `POST /api/ai/generate/flashcards/` - Generate flashcards

### Analytics
- `GET /api/analytics/dashboard/` - Dashboard stats

## 🧪 Testing

```bash
cd backend
python manage.py test
```

## 📦 Deployment

### Docker Deployment

```bash
docker-compose up -d
```

### Production Checklist

1. Set `DEBUG=False` in environment
2. Use strong `SECRET_KEY`
3. Configure PostgreSQL database
4. Set up Redis for caching and Celery
5. Configure email service
6. Set up SSL certificates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.
