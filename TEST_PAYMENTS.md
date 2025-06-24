# Test Payments in Production

This guide explains how to use Xendit test payments in your deployed Railway application.

## 🧪 Why Test Payments?

Since this is a demo/portfolio project, we're using Xendit's test environment even in production. This allows:

- ✅ **Safe Testing**: No real money transactions
- ✅ **Demo Functionality**: Show payment flows to potential employers/clients
- ✅ **Development**: Test features without financial risk

## 🔧 Configuration

### Railway Environment Variables

Set these in your Railway project settings:

```bash
# Django
SECRET_KEY=your-django-secret-key-here
DEBUG=False

# Xendit Test Keys (keep these for demo purposes)
XENDIT_SECRET_KEY=xnd_development_HeoSSbZ8Icw34Qkuv8v1GsK6rpgp5M7P2g9CuZSt8jogGaRFNdwA05CsEZzTD
XENDIT_PUBLIC_KEY=xnd_public_development_GuXclYhfwJz3ee6X1FoxaIi_Nl9qvreKBeeiCnrqD05my7EtWdi1TXUdxn2uKO
XENDIT_CALLBACK_TOKEN=6ptrX95LGe6g07GWa4Hy9X8VeiuXBiS31OVcAHV7N8DcFYAp

# App URL
APP_URL=https://simple-payment-production.up.railway.app

# Test Mode (enables test features in production)
XENDIT_TEST_MODE=True
ENABLE_TEST_ENDPOINTS=True
```

## 🚀 How Test Payments Work

### 1. Payment Flow
1. User selects a package
2. Gets redirected to Xendit test payment page
3. Can use test payment methods (see below)
4. Returns to payment success page

### 2. Test Payment Methods

**Xendit Test Environment provides:**

- **Virtual Account**: Use test bank codes
- **Credit Card**: Use test card numbers
- **QR Code**: Scan test QR codes

**Test Credit Card Numbers:**
```
4000000000000002 - Visa (Success)
4000000000000044 - Visa (Declined)
5555555555554444 - Mastercard (Success)
```

### 3. Manual Test Completion

If automatic payment processing doesn't work, users can:

1. **Click "Complete Test Payment"** - Simulates successful payment
2. **Click "Verify Payment"** - Checks with Xendit API
3. **Manual access** - Direct access to premium content

## 🎯 User Experience

### For Visitors/Testers:
1. **Try the payment flow** - Experience the full UX
2. **Use test cards** - See successful payment processing
3. **Access premium content** - View the protected content
4. **No real charges** - All payments are test transactions

### For Developers/Employers:
- **Full payment integration** - See complete Xendit implementation
- **Error handling** - Robust payment status management
- **User access control** - Session-based premium access
- **Clean UI/UX** - Professional payment interface

## 🔍 Payment Status Verification

The system provides multiple ways to verify test payments:

### Automatic Verification
- Webhook callbacks from Xendit
- Real-time payment status updates
- Automatic user access granting

### Manual Verification
- API calls to Xendit to check payment status
- Manual payment simulation for testing
- Fallback access granting mechanisms

## 📋 Testing Checklist

When testing the deployed application:

1. ✅ **Home Page**: Packages are visible
2. ✅ **Payment Flow**: Redirects to Xendit properly
3. ✅ **Test Payment**: Complete payment using test methods
4. ✅ **Success Page**: Shows payment completion
5. ✅ **Premium Access**: Can access protected content
6. ✅ **Session Management**: Access persists across page loads
7. ✅ **Expiration**: Access expires after package duration

## 🛠️ Troubleshooting

### "No packages available"
Run: `python setup_production.py` on Railway

### "Payment verification failed"
Click "Complete Test Payment" button

### "Access denied to premium content"
Check if payment was successfully processed

### Environment variable issues
Verify all required variables are set in Railway

## 🚨 Production Notes

### For Real Production:
1. Change to live Xendit keys (`xnd_production_...`)
2. Set `XENDIT_TEST_MODE=False`
3. Set `ENABLE_TEST_ENDPOINTS=False`
4. Enable proper webhook security validation
5. Add SSL certificate verification

### For Demo/Portfolio:
- Keep current test configuration
- Perfect for showcasing payment integration skills
- Safe for public demonstrations
- No risk of accidental charges

## 📞 Support

If you encounter issues:
1. Check Railway logs for error messages
2. Verify environment variables are set correctly
3. Test locally first with same configuration
4. Use the "Complete Test Payment" button as fallback
