# Tourists Club Website
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-5.1-green.svg)](https://djangoproject.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## About
A full-featured web application for managing a hiking club, built with Django and PostgreSQL.  
It supports few user roles, trip creation and provides a custom admin panel.

**Key highlights**:
- Custom user model extending `AbstractUser` for flexible profile fields
- PostgreSQL database with both ORM and raw SQL query support
- Deployment-ready configuration with environment variables

## Features
- User management with distinct roles;
- Creating, editing, and viewing hiking trips;
- Submitting hiker requests and instructors processing them;
- Viewing staff, a list of hikers, and their details;
- An administrative panel with the ability to execute custom SQL queries for direct access to data;
- Full Russian localisation (language code, date/number formats).

## Backend & Core Framework
| Component | Technology |
|-----------|------------|
| Programming Language | Python 3 |
| Web Framework | Django 5.1.4|
| Database | PostgreSQL (psycopg2) |
| Authentication | Django's built-in session-based authentication with a custom AbstractUser model |
| Data Access | Django ORM + raw SQL fallback |
| Environment | Configured via `.env` |

## Technical Solutions
1. **Model-View-Template (MVT)** architectural pattern. The classic Django structure, separating data logic, business logic, and presentation.
2. **Custom user model**. Extending the built-in `AbstractUser` model to store additional fields without losing standard authentication.
3. **Localization**. `LANGUAGE_CODE = 'ru-ru'`, `DATE_FORMAT`, `DATETIME_FORMAT` are set to output in a form familiar to the user.

## Project structure
```
.
├── docker-compose.yml   # service orchestration
├── Dockerfile           # Django image definition
├── entrypoint.sh        # runs migrations and starts server
├── .env.example         # environment variables template
├── requirements.txt     # Python dependencies
├── manage.py
├── tourists/            # project settings
└── main/                # main application
    ├── models.py
    ├── views.py
    ├── templates/
    └── static/
```

## Getting started
### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- pip / virtualenv

### Installation
Clone repository:
``` bash
git clone https://github.com/your-username/tourists-site.git
cd tourists-site
```

Create a `.env` file by copying the example:
``` bash
cp .env.example .env
```

Build and run with Docker Compose:
``` bash
docker-compose up -d --build
```

To access the Django admin panel and website admin panel, create a superuser:
``` bash
docker-compose exec web python manage.py createsuperuser
```

Wait a few seconds, then visit http://localhost:8000.

