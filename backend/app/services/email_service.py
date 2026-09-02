import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import httpx

from app.config import settings
from app.core.exceptions import ValidationException

logger = logging.getLogger("fintrack.email")


def _send_smtp_sync(to_email: str, subject: str, text_content: str, html_content: str) -> None:
    """Synchronous SMTP worker for Google SMTP or standard SMTP relays."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg["To"] = to_email

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")

        msg.attach(part1)
        msg.attach(part2)

        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            server.starttls()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAILS_FROM_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"[GOOGLE SMTP] Email successfully dispatched to {to_email}")
        logger.info(f"Email sent via Google SMTP to {to_email}")
    except Exception as exc:
        print(f"[GOOGLE SMTP ERROR] Failed to send email to {to_email}: {exc}")
        logger.error(f"Failed to send email via SMTP to {to_email}: {exc}")


async def _dispatch_email(to_email: str, subject: str, text_content: str, html_content: str) -> None:
    """
    Unified email dispatcher:
    1. If RESEND_API_KEY is configured (Production), dispatches via Resend REST API.
    2. If SMTP_HOST & credentials are configured (Google SMTP in local/dev), dispatches via SMTP.
    3. Fallback: logs to console.
    """
    # 1. Resend API (Production)
    if settings.RESEND_API_KEY:
        from_email = settings.EMAILS_FROM_EMAIL.strip() if settings.EMAILS_FROM_EMAIL else ""
        if not from_email or from_email == "noreply@fintrack.app":
            from_email = "onboarding@resend.dev"

        sender_name = settings.EMAILS_FROM_NAME.strip() if settings.EMAILS_FROM_NAME else "FinTrack"
        sender_string = f"{sender_name} <{from_email}>"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {settings.RESEND_API_KEY.strip()}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": sender_string,
                        "to": [to_email],
                        "subject": subject,
                        "html": html_content,
                        "text": text_content,
                    },
                )
                if response.status_code in (200, 201):
                    logger.info(f"[RESEND] Email successfully dispatched to {to_email}")
                    print(f"[RESEND] Email successfully dispatched to {to_email}")
                    return
                else:
                    err_json = {}
                    try:
                        err_json = response.json()
                    except Exception:
                        pass
                    err_msg = err_json.get("message") or response.text or "Failed to send email via Resend"
                    logger.error(f"[RESEND ERROR] Status {response.status_code}: {err_msg}")
                    print(f"[RESEND ERROR] Status {response.status_code}: {err_msg}")
                    raise ValidationException(f"Email delivery error: {err_msg}", field="email")
        except ValidationException:
            raise
        except Exception as exc:
            logger.error(f"[RESEND EXCEPTION] Failed to dispatch email to {to_email}: {exc}")
            print(f"[RESEND EXCEPTION] Failed to dispatch email to {to_email}: {exc}")
            raise ValidationException(f"Failed to send email: {exc}", field="email")

    # 2. Google / Standard SMTP (Local / Staging)
    if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
        await asyncio.to_thread(_send_smtp_sync, to_email, subject, text_content, html_content)
        return

    # 3. Development Fallback (Console output)
    logger.info(f"[DEV EMAIL] To: {to_email} | Subject: {subject}")
    print(f"\n=========================================\n[DEV EMAIL] Email to: {to_email}\nSubject: {subject}\n{text_content}\n=========================================\n")


async def send_password_reset_email(to_email: str, reset_token: str) -> None:
    """Send a password reset email to the user with a reset link."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    subject = "Reset Your FinTrack Password"

    text_content = f"""
Hello,

You requested a password reset for your FinTrack account.
Click the link below (or copy and paste it into your browser) to reset your password:

{reset_url}

This link is valid for {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes. If you did not request this, please ignore this email.

Best regards,
The FinTrack Team
"""

    html_content = f"""
<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #09090b; color: #f4f4f5; padding: 24px;">
  <div style="max-width: 540px; margin: 0 auto; background-color: #18181b; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 32px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);">
    <div style="display: inline-block; padding: 6px 12px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 8px; color: #10b981; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px;">
      FinTrack Security
    </div>
    <h2 style="color: #ffffff; margin-top: 0; font-size: 22px; font-weight: 700;">Reset Your Password</h2>
    <p style="color: #a1a1aa; font-size: 15px; line-height: 1.6;">
      We received a request to reset the password for your FinTrack account associated with <strong>{to_email}</strong>.
    </p>
    <div style="margin: 32px 0; text-align: center;">
      <a href="{reset_url}" style="background-color: #10b981; color: #09090b; padding: 12px 28px; font-weight: 700; text-decoration: none; border-radius: 10px; display: inline-block; font-size: 14px;">
        Reset Password
      </a>
    </div>
    <p style="color: #71717a; font-size: 13px; line-height: 1.5;">
      If the button above does not work, copy and paste this URL into your browser:<br/>
      <a href="{reset_url}" style="color: #10b981; word-break: break-all;">{reset_url}</a>
    </p>
    <p style="color: #71717a; font-size: 12px; margin-top: 32px; border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 16px;">
      This link is valid for {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes. If you did not make this request, you can safely ignore this email.
    </p>
  </div>
</body>
</html>
"""

    await _dispatch_email(to_email, subject, text_content, html_content)


async def send_verification_code_email(to_email: str, code: str) -> None:
    """Send a 6-digit verification code to the user's email for registration."""
    subject = f"Your FinTrack Verification Code: {code}"

    text_content = f"""
Hello,

Your 6-digit email verification code for FinTrack is:

{code}

This code is valid for {settings.EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES} minutes.
If you did not request this verification code, please ignore this email.

Best regards,
The FinTrack Team
"""

    html_content = f"""
<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #09090b; color: #f4f4f5; padding: 24px;">
  <div style="max-width: 540px; margin: 0 auto; background-color: #18181b; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 32px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);">
    <div style="display: inline-block; padding: 6px 12px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 8px; color: #10b981; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px;">
      FinTrack Security
    </div>
    <h2 style="color: #ffffff; margin-top: 0; font-size: 22px; font-weight: 700;">Verify Your Email Address</h2>
    <p style="color: #a1a1aa; font-size: 15px; line-height: 1.6;">
      Thank you for choosing FinTrack. Use the 6-digit verification code below to complete your registration for <strong>{to_email}</strong>:
    </p>
    <div style="margin: 28px 0; text-align: center;">
      <div style="display: inline-block; background-color: #09090b; border: 2px dashed #10b981; border-radius: 12px; padding: 16px 36px; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #10b981; font-family: monospace;">
        {code}
      </div>
    </div>
    <p style="color: #71717a; font-size: 13px; line-height: 1.5; text-align: center;">
      This code is valid for <strong>{settings.EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES} minutes</strong>. Do not share this code with anyone.
    </p>
    <p style="color: #71717a; font-size: 12px; margin-top: 32px; border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 16px;">
      If you did not initiate this registration request, you can safely ignore this email.
    </p>
  </div>
</body>
</html>
"""

    await _dispatch_email(to_email, subject, text_content, html_content)
