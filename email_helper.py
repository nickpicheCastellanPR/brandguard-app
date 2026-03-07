"""
email_helper.py — Transactional email via Resend.

Handles password reset and username recovery emails.
Uses DKIM-verified no-reply@castellanpr.com.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = "Signet Studio <no-reply@castellanpr.com>"
APP_URL = os.environ.get("APP_URL", "https://signetstudio.app")


def _send_email(to: str, subject: str, html: str) -> bool:
    """Send an email via Resend. Returns True on success."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — email not sent")
        return False
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


def send_password_reset(to: str, token: str) -> bool:
    """Send a password reset email with a one-time link."""
    reset_url = f"{APP_URL}/?reset_token={token}"
    html = f"""
    <div style="font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 40px 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <span style="font-size: 1.4rem; font-weight: 800; color: #24363b; letter-spacing: 0.12em;">SIGNET STUDIO</span>
        </div>
        <div style="background: #ffffff; border: 1px solid #e0e0e0; border-top: 4px solid #24363b; padding: 30px; border-radius: 4px;">
            <h2 style="color: #24363b; font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; margin-top: 0;">PASSWORD RESET</h2>
            <p style="color: #3d3d3d; font-size: 0.9rem; line-height: 1.6;">
                We received a request to reset your password. Click the button below to set a new password.
                This link expires in 1 hour.
            </p>
            <div style="text-align: center; margin: 25px 0;">
                <a href="{reset_url}" style="
                    display: inline-block; background-color: #24363b; color: #f5f5f0;
                    padding: 12px 30px; text-decoration: none; font-weight: 700;
                    font-size: 0.85rem; letter-spacing: 0.08em; text-transform: uppercase;
                ">RESET PASSWORD</a>
            </div>
            <p style="color: #5c6b61; font-size: 0.8rem; line-height: 1.5;">
                If you didn't request this, you can safely ignore this email. Your password will not change.
            </p>
        </div>
        <div style="text-align: center; margin-top: 20px; color: #5c6b61; font-size: 0.7rem; letter-spacing: 0.08em;">
            castellanpr.com
        </div>
    </div>
    """
    return _send_email(to, "Reset your Signet Studio password", html)


def send_welcome_email(to: str, username: str) -> bool:
    """Send a welcome email after registration."""
    login_url = APP_URL
    html = f"""
    <div style="font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 40px 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <span style="font-size: 1.4rem; font-weight: 800; color: #24363b; letter-spacing: 0.12em;">SIGNET STUDIO</span>
        </div>
        <div style="background: #ffffff; border: 1px solid #e0e0e0; border-top: 4px solid #ab8f59; padding: 30px; border-radius: 4px;">
            <h2 style="color: #24363b; font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; margin-top: 0;">WELCOME TO SIGNET STUDIO</h2>
            <p style="color: #3d3d3d; font-size: 0.9rem; line-height: 1.6;">
                Your account has been created and your <strong>14-day free trial</strong> is now active.
            </p>
            <div style="margin: 20px 0; padding: 15px; background: rgba(36,54,59,0.05); border-left: 3px solid #ab8f59;">
                <span style="font-size: 0.8rem; color: #5c6b61; letter-spacing: 0.05em;">USERNAME</span><br>
                <span style="font-size: 1.05rem; font-weight: 700; color: #24363b;">{username}</span>
            </div>
            <p style="color: #3d3d3d; font-size: 0.9rem; line-height: 1.6;">
                We've loaded a sample brand (<strong>Meridian Labs</strong>) so you can explore every module right away:
            </p>
            <ul style="color: #3d3d3d; font-size: 0.85rem; line-height: 1.8; padding-left: 20px;">
                <li><strong>Content Generator</strong> &mdash; draft on-brand materials</li>
                <li><strong>Copy Editor</strong> &mdash; rewrite and audit existing copy</li>
                <li><strong>Social Assistant</strong> &mdash; create platform-optimized posts</li>
                <li><strong>Visual Compliance</strong> &mdash; audit images against brand guidelines</li>
            </ul>
            <p style="color: #3d3d3d; font-size: 0.9rem; line-height: 1.6;">
                When you're ready, head to <strong>Brand Architect</strong> to calibrate your own brand.
            </p>
            <div style="text-align: center; margin: 25px 0;">
                <a href="{login_url}" style="
                    display: inline-block; background-color: #24363b; color: #f5f5f0;
                    padding: 12px 30px; text-decoration: none; font-weight: 700;
                    font-size: 0.85rem; letter-spacing: 0.08em; text-transform: uppercase;
                ">GET STARTED</a>
            </div>
        </div>
        <div style="text-align: center; margin-top: 20px; color: #5c6b61; font-size: 0.7rem; letter-spacing: 0.08em;">
            castellanpr.com
        </div>
    </div>
    """
    return _send_email(to, "Welcome to Signet Studio — your trial is active", html)


def send_username_reminder(to: str, username: str) -> bool:
    """Send a username reminder email."""
    html = f"""
    <div style="font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 40px 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <span style="font-size: 1.4rem; font-weight: 800; color: #24363b; letter-spacing: 0.12em;">SIGNET STUDIO</span>
        </div>
        <div style="background: #ffffff; border: 1px solid #e0e0e0; border-top: 4px solid #24363b; padding: 30px; border-radius: 4px;">
            <h2 style="color: #24363b; font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; margin-top: 0;">USERNAME REMINDER</h2>
            <p style="color: #3d3d3d; font-size: 0.9rem; line-height: 1.6;">
                Your Signet Studio username is:
            </p>
            <div style="text-align: center; margin: 20px 0; padding: 15px; background: rgba(36,54,59,0.05); border-left: 3px solid #ab8f59;">
                <span style="font-size: 1.1rem; font-weight: 700; color: #24363b; letter-spacing: 0.05em;">{username}</span>
            </div>
            <p style="color: #5c6b61; font-size: 0.8rem; line-height: 1.5;">
                If you didn't request this, you can safely ignore this email.
            </p>
        </div>
        <div style="text-align: center; margin-top: 20px; color: #5c6b61; font-size: 0.7rem; letter-spacing: 0.08em;">
            castellanpr.com
        </div>
    </div>
    """
    return _send_email(to, "Your Signet Studio username", html)
