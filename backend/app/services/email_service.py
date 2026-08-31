import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger("fintrack.email")


async def send_password_reset_email(to_email: str, reset_token: str) -> None:
    """Send a password reset email to the user with a reset link."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    subject = "Reset Your FinTrack Password"

    text_content = f"""
Hello,

You requested a password reset for your FinTrack account.
Click the link below (or copy and paste it into your browser) to reset your password:

{reset_url}

This link is valid for 1 hour. If you did not request this, please ignore this email.

Best regards,
The FinTrack Team
"""

    html_content = f"""
<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #09090b; color: #f4f4f5; padding: 24px;">
  <div style="max-width: 540px; margin: 0 auto; background-color: #18181b; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 32px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);">
    <h2 style="color: #10b981; margin-top: 0;">FinTrack — Password Reset</h2>
    <p style="color: #a1a1aa; font-size: 15px; line-height: 1.6;">
      We received a request to reset the password for your FinTrack account associated with <strong>{to_email}</strong>.
    </p>
    <div style="margin: 32px 0; text-align: center;">
      <a href="{reset_url}" style="background-color: #10b981; color: #000000; padding: 12px 24px; font-weight: 600; text-decoration: none; border-radius: 10px; display: inline-block;">
        Reset Password
      </a>
    </div>
    <p style="color: #71717a; font-size: 13px; line-height: 1.5;">
      If the button above does not work, copy and paste this URL into your browser:<br/>
      <a href="{reset_url}" style="color: #10b981; word-break: break-all;">{reset_url}</a>
    </p>
    <p style="color: #71717a; font-size: 12px; margin-top: 32px; border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 16px;">
      This link is valid for 1 hour. If you did not make this request, you can safely ignore this email.
    </p>
  </div>
</body>
</html>
"""

    # If SMTP is not configured in development, log the link and return
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.info(f"[DEV EMAIL] Password reset for {to_email}: {reset_url}")
        print(f"\n=========================================\n[DEV EMAIL] Password reset for {to_email}:\n{reset_url}\n=========================================\n")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg["To"] = to_email

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")

        msg.attach(part1)
        msg.attach(part2)

        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAILS_FROM_EMAIL, to_email, msg.as_string())
        server.quit()
        logger.info(f"Password reset email sent to {to_email}")
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email}: {exc}")
