# Django Payment Gateway with Xendit Integration

A simple Django web application that demonstrates payment gateway integration using Xendit. Users can purchase packages and gain access to premium content.

## Features

- 🏠 Landing page with available packages
- 💳 Multiple payment methods (Virtual Account, Credit/Debit Card, QR Code)
- 🔄 Real-time payment status tracking via Xendit webhooks
- 🔒 Session-based access control (no login required)
- 📊 Premium content access after successful payment
- 📱 Responsive design with Bootstrap

## Project Structure

```
payment-project/
├── env/                          # Virtual environment
├── payment_gateway/              # Django project settings
├── payments/                     # Main app
│   ├── models.py                # Package, Transaction, UserAccess models
│   ├── views.py                 # Views for payment flow
│   ├── services.py              # Xendit API integration
│   ├── admin.py                 # Django admin configuration
│   └── urls.py                  # URL routing
├── templates/payments/          # HTML templates
├── static/                      # Static files (CSS, JS, images)
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables
└── manage.py                    # Django management script
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- Xendit account (get API keys from https://dashboard.xendit.co/)

### 2. Environment Setup

```bash
# Navigate to project directory
cd "c:\Main Storage\Documents\In\payment-project"

# Activate virtual environment
.\env\Scripts\activate

# Install dependencies (already done, but for reference)
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Edit the `.env` file with your Xendit credentials:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# Xendit Configuration
XENDIT_SECRET_KEY=your-xendit-secret-key-here
XENDIT_PUBLIC_KEY=your-xendit-public-key-here
XENDIT_CALLBACK_TOKEN=your-xendit-callback-token-here

# Application URL (for callbacks)
APP_URL=http://localhost:8000
```

**Important:** Replace the Xendit keys with your actual keys from the Xendit dashboard.

### 4. Database Setup

```bash
# Apply migrations (already done, but for reference)
python manage.py migrate

# Create sample packages (already done)
# Admin user created: username=admin, password=admin123
```

### 5. Run the Application

```bash
# Start the development server
python manage.py runserver
```

The application will be available at: http://localhost:8000

## Usage Flow

1. **Landing Page**: Visit http://localhost:8000 to see available packages
2. **Select Package**: Click "Buy Package" on any package
3. **Payment**: Redirected to Xendit payment page
4. **Payment Methods**: Choose from:
   - Virtual Account (BCA, BNI, BRI, Mandiri, etc.)
   - Credit/Debit Card
   - QR Code (QRIS)
5. **Complete Payment**: Follow Xendit's payment flow
6. **Access Content**: After successful payment, access premium content

## Payment Flow

```
Landing Page → Select Package → Xendit Payment → Success/Failure → Premium Content Access
```

## API Endpoints

- `/` - Home page with packages
- `/buy/<package_id>/` - Initiate payment for package
- `/callback/xendit/` - Webhook endpoint for Xendit callbacks
- `/payment/success/` - Payment success redirect
- `/payment/failed/` - Payment failure redirect
- `/paid-content/` - Premium content (requires payment)
- `/admin/` - Django admin panel

## Database Models

### Package
- Package information (name, price, duration)
- Configurable via Django admin

### Transaction
- Payment tracking with Xendit integration
- Status: PENDING, PAID, FAILED, EXPIRED

### UserAccess  
- Session-based access control
- Automatic expiration based on package duration

## Xendit Integration

### Webhook Configuration
Configure webhook URL in Xendit dashboard:
```
http://your-domain.com/callback/xendit/
```

### Supported Payment Methods
- **Virtual Account**: All major Indonesian banks
- **Credit Card**: Visa, Mastercard, JCB
- **QR Code**: QRIS-compatible apps

## Admin Panel

Access admin panel at http://localhost:8000/admin/
- Username: `admin`
- Password: `admin123`

Manage:
- Packages (create, edit, activate/deactivate)
- Transactions (view payment history)
- User Access (view active subscriptions)

## Deployment Considerations

### For Production:
1. **Environment Variables**: Use proper secret keys
2. **Database**: Consider PostgreSQL instead of SQLite
3. **Static Files**: Configure proper static file serving
4. **HTTPS**: Required for Xendit webhooks
5. **Webhook Security**: Implement proper signature validation
6. **Error Handling**: Add comprehensive error logging

### Free Cloud Deployment Options:
- **Heroku**: Free tier with PostgreSQL addon
- **Railway**: Simple deployment with GitHub integration
- **PythonAnywhere**: Free tier suitable for testing
- **Render**: Free static sites with backend services

## Security Notes

- Session-based authentication (no passwords stored)
- CSRF protection enabled
- Webhook signature validation (basic implementation)
- Input validation on all forms
- SQL injection protection via Django ORM

## Troubleshooting

### Common Issues:

1. **Payment not processing**: Check Xendit API keys in .env
2. **Webhook not working**: Ensure callback URL is accessible
3. **Sessions not persisting**: Check Django session configuration
4. **Template not found**: Verify template paths in settings.py

### Debug Mode:
Set `DEBUG=True` in .env for detailed error messages.

## Testing

### Test Payment Flow:
1. Use Xendit test API keys
2. Xendit provides test card numbers and bank accounts
3. Monitor webhook calls in Xendit dashboard

### Sample Test Data:
- Test Card: 4000 0000 0000 0002
- Test Virtual Account: Use amounts ending in specific digits

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

This project is for educational/demonstration purposes. 

## Support

For Xendit API questions: https://docs.xendit.co/
For Django questions: https://docs.djangoproject.com/

---

**Note**: This is a demonstration project. For production use, implement additional security measures, error handling, and proper deployment practices.
