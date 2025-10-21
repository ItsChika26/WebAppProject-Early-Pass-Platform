# EarlyPass – Class & Submission Management System

<div align="center">

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![Django](https://img.shields.io/badge/django-5.2.7-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Tests](https://img.shields.io/badge/tests-passing-success.svg)
![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)

A modern, elegant class and submission management system with role-based access control, teacher approval workflows, and a beautiful, consistent UI design.

</div>

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Local Development](#local-development)
  - [Docker Deployment](#docker-deployment)
- [User Workflows](#-user-workflows)
- [Design System](#-design-system)
- [Testing](#-testing)
- [Management Commands](#-management-commands)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Documentation](#-documentation)

---

## ✨ Features

### 🔐 Authentication & User Management
- **Role-Based Access**: Students, Teachers, and Admin roles with distinct permissions
- **Enhanced Signup**: Users can register as students (with year selection) or teachers (with courses and years)
- **Secure Login/Logout**: Session-based authentication with CSRF protection
- **Password Reset**: Complete password reset flow with email support and beautiful UI
- **Account Activation**: Teachers are inactive until admin approval

### 👨‍🏫 Teacher Application & Approval
- Teachers submit applications during signup with their courses and years
- Applications enter a **Pending** state and teachers are deactivated
- Admins receive email notifications for new applications
- Admin approval via Django admin interface:
  - Teacher is activated and added to the `teacher` group
  - Classes are automatically created for each (course, year) combination
  - Students with matching years are **auto-enrolled** into these classes
- Idempotent approval process prevents duplicate classes/enrollments

### 📚 Class Proposal System
- Approved teachers can propose additional classes after registration
- Proposal workflow:
  - Teachers visit `/classes/propose/` to submit proposals
  - Admins review and approve via Django admin
  - On approval, classes are created and students are auto-enrolled
- Validation ensures class names and year ranges are proper

### 🎓 Student Experience
- Students specify their year during signup
- Automatically enrolled into all classes for their year
- Filter classes by year and search by name/course
- Submit work to assigned classes with file uploads
- View submission status (Pending/Approved/Rejected)

### 📊 Class & Submission Management
- **Class Lists**: Role-aware display
  - Staff: See all classes
  - Teachers: See classes they teach
  - Students: See classes they're enrolled in
- **Filters**: Year, course, status with HTMX-powered live filtering
- **File Submissions**: Upload and manage assignment files
- **Deadline Enforcement**: Submissions rejected after class deadlines
- **Approval Workflow**: Teachers approve/reject student submissions with feedback

### 📧 Email Notifications
- Admins notified on new teacher applications
- Password reset emails with branded templates
- Console backend for development, SMTP for production

### 🎨 Modern UI/UX
- Cohesive indigo/cyan color palette
- Responsive Bootstrap 5 design
- Smooth animations and transitions
- Consistent card-based layouts
- Inline form validation with visual feedback
- Mobile-friendly navigation

---

## 🛠 Tech Stack

### Backend
- **Django 5.2.7** – Web framework
- **django-allauth** – Authentication & account management
- **django-filter** – Advanced filtering
- **django-htmx** – HTMX integration for dynamic updates
- **django-seed** – Test data generation
- **Gunicorn** – WSGI HTTP Server

### Frontend
- **Bootstrap 5** – CSS framework
- **HTMX** – Dynamic content updates without JavaScript
- **Custom CSS** – Cohesive design system (`passes/static/passes/app.css`)

### DevOps
- **Docker** – Containerization
- **docker-compose** – Multi-container orchestration
- **WhiteNoise** – Static file serving
- **pytest** – Testing framework
- **pytest-django** – Django integration for pytest

### Database
- **SQLite** – Development database (easily swappable with PostgreSQL for production)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Docker & Docker Compose (for containerized deployment)
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd WebAppProject
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Unix/MacOS
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Seed demo data (optional)**
   ```bash
   python manage.py seed_demo
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - App: http://localhost:8000
   - Admin: http://localhost:8000/admin

### Docker Deployment

1. **Build and start containers**
   ```bash
   docker compose up --build -d
   ```

2. **Create superuser in container**
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

3. **Access the application**
   - App: http://localhost:8000
   - Admin: http://localhost:8000/admin

4. **View logs**
   ```bash
   docker compose logs -f
   ```

5. **Stop containers**
   ```bash
   docker compose down
   ```

#### Docker Configuration
- Automatic migrations on container start
- Static files collected automatically
- Gunicorn with 3 workers
- SQLite database persisted via volume mount
- Media files stored in bind-mounted directory

---

## 👥 User Workflows

### Student Workflow
1. **Signup** → Select student role and specify year
2. **Login** → View auto-enrolled classes for your year
3. **Browse Classes** → Filter by year, search by name/course
4. **Submit Work** → Upload files to enrolled classes before deadline
5. **Track Status** → View submission approval status

### Teacher Workflow
1. **Signup** → Select teacher role, provide courses and years
2. **Wait for Approval** → Account inactive until admin approves
3. **Login** → Access teaching dashboard after approval
4. **View Classes** → See all classes you teach
5. **Propose New Classes** → Submit proposals via `/classes/propose/`
6. **Review Submissions** → Approve/reject student work with feedback

### Admin Workflow
1. **Review Applications** → `/admin` → Teacher applications
2. **Approve Teachers** → Activate users, create classes, auto-enroll students
3. **Approve Proposals** → `/admin` → Proposed classes
4. **Manage Users** → Assign roles, edit profiles
5. **Monitor System** → View all classes, submissions, enrollments

---

## 🎨 Design System

EarlyPass features a cohesive, modern design system defined in `passes/static/passes/app.css`:

### Color Palette
- **Primary (Indigo)**: `#4F46E5` – Main brand color
- **Secondary (Cyan)**: `#06B6D4` – Accents and links
- **Success**: `#10B981` – Approved states
- **Danger**: `#EF4444` – Rejected/error states
- **Warning**: `#F59E0B` – Pending states
- **Neutral Grays**: `#F9FAFB` to `#1F2937`

### Components
- **Cards** (`.ep-card`): Consistent container styling with subtle shadows
- **Buttons**: Primary, secondary, success, danger variants
- **Badges**: Status indicators with color coding
- **Tables**: Striped, hoverable rows with responsive design
- **Forms**: Focus states with colored outlines, inline validation
- **Alerts**: Contextual messages with appropriate color schemes

### Typography
- Clear hierarchy with font weights (400-700)
- Responsive sizing
- Proper line heights for readability

### Responsive Design
- Mobile-first approach
- Collapsible navigation
- Stack layouts on small screens
- Touch-friendly interactive elements

---

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
pytest

# Verbose output
pytest -v

# Run specific test file
pytest passes/tests/test_auth.py -v

# Run with coverage
pytest --cov=passes --cov-report=html
```

### Test Coverage
- **Current Coverage**: 90%
- **Test Files**:
  - `passes/tests/test_auth.py` – Authentication flows
  - `passes/tests/test_basic.py` – Core models and approvals
  - `passes/tests/test_views_and_forms.py` – Views, forms, filters
  - `passes/tests/test_signals_and_ui.py` – Signals and HTMX interactions

### Manual Password Reset Test
```bash
python manage.py shell < scripts/password_reset_manual.py
```

---

## 🔧 Management Commands

### Fix Teacher Activation
Activates users for approved TeacherApplications and adds them to the `teacher` group:
```bash
python manage.py fix_teacher_activation
```

### Fix Proposed Classes
Ensures approved ProposedClass items have real Classes and enrollments:
```bash
python manage.py fix_proposed_classes
```

### Seed Demo Data
Generates test data for development:
```bash
python manage.py seed_demo
```

---

## 📁 Project Structure

```
WebAppProject/
├── earlypass/                  # Django project settings
│   ├── settings.py            # Main configuration
│   ├── urls.py                # Root URL configuration
│   └── wsgi.py                # WSGI application
├── passes/                     # Main application
│   ├── models.py              # Data models
│   ├── views.py               # View logic
│   ├── forms.py               # Form definitions
│   ├── signals.py             # Signal handlers
│   ├── signup.py              # Extended signup form
│   ├── filters.py             # Filter classes
│   ├── admin.py               # Admin configuration
│   ├── urls_classes.py        # Class-related URLs
│   ├── urls_submissions.py    # Submission-related URLs
│   ├── static/passes/         # Static assets
│   │   └── app.css           # Custom styles
│   ├── templates/passes/      # App templates
│   ├── tests/                 # Test suite
│   └── management/commands/   # Custom commands
├── templates/                  # Global templates
│   ├── base.html              # Base template
│   ├── home.html              # Landing page
│   └── account/               # Allauth templates
│       ├── login.html
│       ├── signup.html
│       ├── password_reset.html
│       └── email/             # Email templates
├── media/                      # User uploads
│   └── submissions/           # Submission files
├── staticfiles/               # Collected static files
├── scripts/                   # Utility scripts
│   └── password_reset_manual.py
├── docker-compose.yml         # Docker orchestration
├── Dockerfile                 # Container definition
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Pytest configuration
├── manage.py                  # Django CLI
├── README.md                  # This file
└── PASSWORD_RESET_GUIDE.md    # Password reset documentation
```

---

## ⚙️ Configuration

### Environment Variables

For Docker deployment, configure via `docker-compose.yml` or `.env`:

```bash
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Django Settings (`earlypass/settings.py`)

Key settings to configure:

```python
# Admin notifications
ADMINS = [
    ('Admin Name', 'admin@example.com'),
]

# Email configuration (production)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@earlypass.com'

# Class deadline defaults
DEFAULT_CLASS_DEADLINE_DAYS = 30  # Days from class creation

# Allauth configuration
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_FORMS = {
    'signup': 'passes.signup.ExtendedSignupForm',
}
```

### Static Files

Static files are served via WhiteNoise in production:
```bash
python manage.py collectstatic --noinput
```

---

## 📖 Documentation

- **[PASSWORD_RESET_GUIDE.md](PASSWORD_RESET_GUIDE.md)** – Detailed password reset setup and configuration
- **Admin Interface** – Access `/admin` for comprehensive model management
- **API Documentation** – None (traditional Django views, not REST API)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

---

## 📝 License

This project is proprietary and confidential.

---

## 🙏 Acknowledgments

- Django community for the amazing framework
- django-allauth for robust authentication
- Bootstrap team for the UI toolkit
- HTMX for seamless interactivity

---

## 📧 Support

For issues, questions, or suggestions:
- Open an issue in the repository
- Contact the development team

---

<div align="center">
Made with ❤️ using Django
</div>
