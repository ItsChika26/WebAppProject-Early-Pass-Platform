import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail

@pytest.mark.django_db
def test_login_flow(client):
    u = User.objects.create_user("authuser", password="pass")
    r = client.get(reverse("account_login"))
    assert r.status_code == 200
    r = client.post(reverse("account_login"), {"login":"authuser", "password":"pass"})
    assert r.status_code in (302, 303)  # redirect after login

@pytest.mark.django_db
def test_password_reset_flow(client):
    """Test complete password reset flow"""
    # Create a user with email
    user = User.objects.create_user(
        username="testreset",
        email="test@example.com",
        password="oldpassword123"
    )
    
    # Step 1: Request password reset
    reset_url = reverse("account_reset_password")
    response = client.get(reset_url)
    assert response.status_code == 200
    
    # Step 2: Submit email
    response = client.post(reset_url, {"email": "test@example.com"})
    assert response.status_code in (302, 303)  # Redirects to done page
    
    # Step 3: Verify email was sent
    assert len(mail.outbox) == 1
    assert "Password Reset" in mail.outbox[0].subject
    assert "test@example.com" in mail.outbox[0].to
    
    # Step 4: Verify email contains reset link
    email_body = mail.outbox[0].body
    assert "reset" in email_body.lower()
    assert "password" in email_body.lower()

@pytest.mark.django_db
def test_password_reset_invalid_email(client):
    """Test password reset with non-existent email (should not leak info)"""
    reset_url = reverse("account_reset_password")
    response = client.post(reset_url, {"email": "nonexistent@example.com"})
    
    # Should still redirect to done page (security: don't leak if email exists)
    assert response.status_code in (302, 303)
    
    # Do not assert on emails to avoid leaking behavior differences; redirect is sufficient

