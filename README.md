# InfluenceAI Tool Backend

A Django REST Framework backend for the InfluenceAI Tool platform that enables influencers and brands to connect and analyze Instagram performance metrics.

## Overview

InfluenceAI Tool is a platform that facilitates authentication with Instagram, manages user sessions, and provides analytics capabilities for both influencers and brands. The backend handles:

- User authentication (Instagram, Facebook, Google, Email Magic Links)
- User type management (Influencer/Brand)
- Instagram API integration
- JWT-based session management
- Analytics for Instagram metrics and insights

## Technology Stack

- **Framework**: Django 4.2+
- **API**: Django REST Framework
- **Authentication**: JWT Authentication
- **Database**: PostgreSQL
- **External APIs**: Instagram Graph API, Facebook Login API

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Pip
- Virtual environment tool (venv, pipenv, or conda)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/influenceaitool.git
   cd influenceaitool/backend
   ```

2. Set up a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Create a `.env` file in the project root with:

   ```
   DEBUG=True
   SECRET_KEY=your_secret_key_here
   DATABASE_URL=postgres://user:password@localhost:5432/influenceaitool

   # Instagram API Credentials
   INSTAGRAM_APP_ID=your_instagram_app_id
   INSTAGRAM_APP_SECRET=your_instagram_app_secret

   # JWT Settings
   JWT_SECRET_KEY=your_jwt_secret_key
   JWT_EXPIRATION_DAYS=30

   # Email Service (for Magic Links)
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.resend.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your_email_user
   EMAIL_HOST_PASSWORD=your_email_password
   ```

5. Run database migrations:

   ```bash
   python manage.py migrate
   ```

6. Create a superuser (admin):

   ```bash
   python manage.py createsuperuser
   ```

7. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
backend/
├── manage.py
├── influenceaitool/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── authentication/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── services/
│       ├── __init__.py
│       ├── instagram_auth_service.py
│       ├── facebook_auth_service.py
│       ├── google_auth_service.py
│       └── magic_link_service.py
├── users/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── instagram/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── services/
│       ├── __init__.py
│       └── instagram_service.py
└── analytics/
    ├── __init__.py
    ├── models.py
    ├── serializers.py
    ├── views.py
    └── urls.py
```

## API Endpoints

### Authentication

- `POST /api/auth/user-type/` - Set user type (Influencer/Brand)
- `GET /api/auth/instagram/login/` - Initiate Instagram login
- `GET /api/auth/instagram/callback/` - Instagram login callback
- `GET /api/auth/facebook/login/` - Initiate Facebook login
- `GET /api/auth/facebook/callback/` - Facebook login callback
- `GET /api/auth/google/login/` - Initiate Google login
- `GET /api/auth/google/callback/` - Google login callback
- `POST /api/auth/magic-link/` - Request magic link authentication
- `GET /api/auth/verify-magic-link/` - Verify magic link and authenticate
- `POST /api/auth/logout/` - Logout user

### Users

- `GET /api/users/me/` - Get current user profile
- `PATCH /api/users/me/` - Update current user profile
- `GET /api/users/connected-accounts/` - List connected social accounts
- `DELETE /api/users/connected-accounts/{id}/` - Remove connected account

### Instagram

- `GET /api/instagram/profile/` - Get user's Instagram profile details
- `GET /api/instagram/media/` - List Instagram media
- `GET /api/instagram/media/{id}/` - Get specific media details
- `GET /api/instagram/media/{id}/insights/` - Get media insights

### Analytics

- `GET /api/analytics/overview/` - Get account overview metrics
- `GET /api/analytics/followers/` - Get follower demographics
- `GET /api/analytics/content/` - Get content performance metrics

## Authentication Flow

The backend implements multiple authentication strategies:

1. **Instagram/Facebook Authentication**:

   - Uses OAuth2 flow with Facebook and Instagram APIs
   - Exchanges authorization code for access token
   - Retrieves user profile information
   - Creates/updates user and generates JWT

2. **Google Authentication**:

   - Uses OAuth2 flow with Google APIs
   - Verifies ID token
   - Creates/updates user and generates JWT

3. **Magic Link Authentication**:
   - User submits email
   - System generates secure token
   - Email with magic link is sent via Resend
   - User clicks link, token is verified
   - User is authenticated and JWT is generated

JWT tokens are stored as cookies and used for subsequent authenticated requests.

## Instagram API Integration

The backend integrates with the Instagram Graph API to fetch:

- User profile data
- Media content (posts, stories, reels)
- Engagement metrics
- Audience insights
- Content performance analytics

See the `InstagramService` class for implementation details.

## Development

### Running Tests

```bash
python manage.py test
```

### Code Style

This project follows PEP 8 style guidelines. To check code style:

```bash
flake8
```

### Making Migrations

After changing models:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Deployment

For production deployment:

1. Update settings in `influenceaitool/settings/production.py`
2. Set environment variables for all sensitive information
3. Collect static files:
   ```bash
   python manage.py collectstatic
   ```
4. Configure a production web server (Gunicorn/uWSGI) with Nginx
5. Set up SSL certification

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## License

This project is proprietary. All rights reserved. Unauthorized copying, modification, distribution, or use of this software, via any medium, is strictly prohibited.
