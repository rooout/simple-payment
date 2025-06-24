web: python setup_production.py && gunicorn payment_gateway.wsgi:application --bind 0.0.0.0:$PORT
release: python manage.py migrate && python create_packages.py
