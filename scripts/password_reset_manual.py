"""
Quick manual test for password reset functionality.
Run with: python manage.py shell < scripts/password_reset_manual.py
"""

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from django.core import mail

print("\n" + "="*60)
print("Testing Password Reset Flow")
print("="*60 + "\n")

# Create test user
print("1. Creating test user...")
User.objects.filter(username="pwresettest").delete()  # Clean up first
user = User.objects.create_user(
    username="pwresettest",
    email="pwresettest@example.com",
    password="oldpass123"
)
print(f"   ✓ Created user: {user.username} with email: {user.email}")

# Test password reset request
print("\n2. Requesting password reset...")
client = Client()
response = client.get(reverse("account_reset_password"))
print(f"   ✓ Password reset page loads: {response.status_code == 200}")

# Submit password reset form
print("\n3. Submitting password reset form...")
mail.outbox = []  # Clear any existing emails
response = client.post(
    reverse("account_reset_password"),
    {"email": "pwresettest@example.com"}
)
print(f"   ✓ Form submitted successfully: {response.status_code in (302, 303)}")

# Check email
print("\n4. Checking email...")
if len(mail.outbox) > 0:
    email = mail.outbox[0]
    print(f"   ✓ Email sent to: {email.to[0]}")
    print(f"   ✓ Subject: {email.subject}")
    print(f"   ✓ From: {email.from_email}")
    print("\n   Email body preview:")
    print("   " + "-"*56)
    for line in email.body.split('\n')[:10]:
        print(f"   {line}")
    print("   " + "-"*56)
else:
    print("   ✗ No email sent!")

# Test with invalid email (security check)
print("\n5. Testing with non-existent email (security check)...")
mail.outbox = []
response = client.post(
    reverse("account_reset_password"),
    {"email": "nonexistent@example.com"}
)
print(f"   ✓ Still redirects (no info leak): {response.status_code in (302, 303)}")
print(f"   ✓ No email sent: {len(mail.outbox) == 0}")

print("\n" + "="*60)
print("Password Reset Tests Complete!")
print("="*60 + "\n")

print("To test the full flow manually:")
print("1. Start server: python manage.py runserver")
print("2. Visit: http://localhost:8000/accounts/password/reset/")
print("3. Enter: pwresettest@example.com")
print("4. Check terminal for email with reset link")
print("5. Copy and visit the reset URL")
print("6. Enter new password\n")
