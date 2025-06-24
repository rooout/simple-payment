# Deployment Guide

This guide shows how to deploy the Django Payment Gateway to various free cloud platforms.

## Option 1: Railway (Recommended)

Railway offers easy deployment with GitHub integration.

### Steps:

1. **Prepare for Railway**:
   ```bash
   # Create runtime.txt
   echo "python-3.12.5" > runtime.txt
   
   # Create Procfile
   echo "web: gunicorn payment_gateway.wsgi --log-file -" > Procfile
   
   # Update requirements.txt
   pip freeze > requirements.txt
   ```

2. **Update settings for production**:
   - Add Railway domain to `ALLOWED_HOSTS`
   - Configure database for production
   - Set environment variables

3. **Deploy**:
   - Push code to GitHub
   - Connect Railway to your repository
   - Set environment variables in Railway dashboard
   - Deploy automatically

### Environment Variables for Railway:
```
SECRET_KEY=your-production-secret-key
DEBUG=False
XENDIT_SECRET_KEY=your-xendit-secret-key
XENDIT_PUBLIC_KEY=your-xendit-public-key
XENDIT_CALLBACK_TOKEN=your-xendit-callback-token
APP_URL=https://your-app-name.railway.app
```

## Option 2: Heroku

### Prerequisites:
```bash
# Install Heroku CLI
# Create Procfile
echo "web: gunicorn payment_gateway.wsgi" > Procfile

# Create runtime.txt
echo "python-3.12.5" > runtime.txt

# Update requirements.txt to include gunicorn
echo "gunicorn==21.2.0" >> requirements.txt
```

### Deployment:
```bash
# Initialize git repo
git init
git add .
git commit -m "Initial commit"

# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
heroku config:set XENDIT_SECRET_KEY=your-xendit-key
heroku config:set XENDIT_PUBLIC_KEY=your-xendit-public-key
heroku config:set XENDIT_CALLBACK_TOKEN=your-callback-token
heroku config:set APP_URL=https://your-app-name.herokuapp.com

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser
```

## Option 3: Render

### Setup:
1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: payment-gateway
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn payment_gateway.wsgi:application
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: False
```

2. Connect GitHub repository to Render
3. Set environment variables in Render dashboard

## Option 4: PythonAnywhere

### Steps:
1. Upload code to PythonAnywhere
2. Create virtual environment
3. Install requirements
4. Configure WSGI file
5. Set environment variables in web app settings

## Production Settings

### Create `production_settings.py`:
```python
from .settings import *
import os

DEBUG = False
ALLOWED_HOSTS = [
    'your-domain.com',
    'your-app.railway.app',  # Railway domain
    'your-app.herokuapp.com',  # Heroku domain
]

# Database for production (PostgreSQL recommended)
if 'DATABASE_URL' in os.environ:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Additional Production Requirements:
```
# Add to requirements.txt
gunicorn==21.2.0
psycopg2-binary==2.9.7  # For PostgreSQL
dj-database-url==2.1.0
whitenoise==6.5.0       # For static files
```

## Domain and SSL Setup

### For custom domain:
1. Configure DNS records
2. Update `ALLOWED_HOSTS`
3. Configure SSL certificate
4. Update Xendit webhook URL

## Database Migration for Production

```bash
# Run on production server
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser

# Create packages
python manage.py shell
>>> from payments.models import Package
>>> # Create packages manually or via admin
```

## Monitoring and Logging

### Basic logging configuration:
```python
# Add to settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
        },
    },
    'loggers': {
        'payments': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Security Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use environment variables for secrets
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Enable HTTPS redirect
- [ ] Set secure cookie flags
- [ ] Implement proper webhook signature validation
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure proper error pages
- [ ] Set up monitoring and alerts
- [ ] Regular security updates

## Testing the Deployment

1. **Smoke Test**:
   - Visit homepage
   - Check package display
   - Test payment flow (with test API keys first)

2. **Webhook Test**:
   - Configure webhook URL in Xendit dashboard
   - Test payment completion
   - Verify callback processing

3. **Load Test**:
   - Test with multiple concurrent users
   - Monitor response times
   - Check database performance

## Troubleshooting

### Common Production Issues:

1. **Static files not loading**:
   - Configure `STATIC_ROOT`
   - Run `collectstatic`
   - Use WhiteNoise for Django

2. **Database connection errors**:
   - Check database URL
   - Verify connection limits
   - Run migrations

3. **Webhook not working**:
   - Ensure HTTPS is configured
   - Check firewall settings
   - Verify callback URL accessibility

4. **Session issues**:
   - Configure session backend for production
   - Check session cookie settings

## Cost Considerations

### Free Tier Limitations:
- **Railway**: 512MB RAM, sleeps after inactivity
- **Heroku**: 512MB RAM, sleeps after 30min inactivity
- **Render**: 512MB RAM, slower cold starts
- **PythonAnywhere**: Limited request/day on free tier

### Upgrade Triggers:
- High traffic volume
- Need for persistent background tasks
- Database size limits
- Custom domain requirements

---

Choose the platform that best fits your needs and technical comfort level. Railway is recommended for its simplicity and Git integration.
