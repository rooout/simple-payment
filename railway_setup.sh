#!/bin/bash
# Railway Deployment Script
# This script sets up the production environment with test payment support

echo "🚀 Setting up Payment Gateway for Railway..."
echo "==============================================="

# Run database migrations
echo "📊 Running database migrations..."
python manage.py migrate

# Create initial packages
echo "📦 Creating initial packages..."
python manage.py setup_packages

# Check system status
echo "🔍 Checking system status..."
python manage.py check_status

echo "✅ Setup completed! Your app is ready."
echo "🔗 Visit your Railway URL to test the payment flow."
