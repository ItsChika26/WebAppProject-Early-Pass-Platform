# Password Reset Flow - Testing Guide

## Overview
The password reset functionality is now fully implemented with:
- Styled UI pages matching the EarlyPass design system
- Email sending via Django's email backend
- Custom email templates
- Complete user flow from request to password change

## Flow Steps

### 1. Request Password Reset
- **URL**: `/accounts/password/reset/`
- **Page**: Clean form asking for email address
- **Action**: User enters their email and clicks "Send reset email"

### 2. Confirmation Page
- **URL**: `/accounts/password/reset/done/`
- **Page**: Shows success message with email icon
- **Content**: Tells user to check their email for instructions

### 3. Email Sent
- **Backend**: Console backend (emails appear in terminal during development)
- **Contains**: Password reset link with unique token
- **Template**: Custom EarlyPass-branded message

### 4. Reset Password
- **URL**: `/accounts/password/reset/key/<uidb64>/<token>/`
- **Page**: Form to enter new password twice
- **Validation**: Shows password requirements checklist
- **Action**: User enters new password and confirms

### 5. Success Page
- **URL**: `/accounts/password/reset/key/done/`
- **Page**: Success message with checkmark
- **Action**: Redirects user to login with new password

## Email Configuration

### Current Setup (Development)
```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = 'noreply@earlypass.com'
```

Emails are printed to the console/terminal where Django is running.

### Production Setup Options

#### Option 1: Gmail SMTP
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Use App Password, not regular password
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

#### Option 2: SendGrid
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'your-sendgrid-api-key'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
```

#### Option 3: Mailgun
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'postmaster@yourdomain.mailgun.org'
EMAIL_HOST_PASSWORD = 'your-mailgun-smtp-password'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
```

## Testing Instructions

### 1. Start the development server
```powershell
python manage.py runserver
```

### 2. Create a test user (if you don't have one)
```powershell
python manage.py createsuperuser
# Or sign up through the website
```

### 3. Test the flow
1. Go to http://localhost:8000/accounts/password/reset/
2. Enter your email address
3. Click "Send reset email"
4. Check your terminal/console for the email with the reset link
5. Copy the reset URL from the terminal
6. Paste it in your browser
7. Enter a new password
8. Verify you can login with the new password

### 4. Verify email content
The console should show something like:
```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Password Reset for EarlyPass
From: noreply@earlypass.com
To: user@example.com

Hello from EarlyPass!

You're receiving this email because you (or someone else) requested a password reset for your account.

Please click the link below to reset your password:

http://localhost:8000/accounts/password/reset/key/...

If you didn't request this, please ignore this email...
```

## Security Features

✅ **Token-based**: Each reset link contains a unique, time-limited token  
✅ **Single-use**: Tokens expire after being used once  
✅ **Time-limited**: Tokens expire after a set period (default: 3 days)  
✅ **No information leakage**: Same message shown whether email exists or not  
✅ **HTTPS ready**: Works with secure connections in production  

## Customization

### Change token expiration time
Add to settings.py:
```python
PASSWORD_RESET_TIMEOUT = 86400  # 1 day in seconds (default is 3 days)
```

### Customize email templates
Edit these files:
- `templates/account/email/password_reset_key_subject.txt` (subject line)
- `templates/account/email/password_reset_key_message.txt` (email body)

### Customize page templates
Edit these files:
- `templates/account/password_reset.html` (request form)
- `templates/account/password_reset_done.html` (email sent confirmation)
- `templates/account/password_reset_from_key.html` (new password form)
- `templates/account/password_reset_from_key_done.html` (success page)

## Troubleshooting

### Emails not appearing in console?
- Make sure `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"`
- Check the terminal where `python manage.py runserver` is running
- Ensure `ACCOUNT_EMAIL_REQUIRED = True` in settings

### Reset link doesn't work?
- Check if the token has expired
- Verify the URL is complete (not broken across lines)
- Make sure you're using the same browser session
- Clear cookies and try again

### User says they didn't receive email?
- For security, the system shows success even if email doesn't exist
- In production, check spam folders
- Verify email server credentials are correct
- Check email server logs

## Next Steps

To move to production email:
1. Choose an email service provider (Gmail, SendGrid, Mailgun, etc.)
2. Get SMTP credentials or API keys
3. Update `settings.py` with production email configuration
4. Store credentials in environment variables (never commit to git!)
5. Test thoroughly before deploying

Example with environment variables:
```python
import os

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@earlypass.com')
```
