import asyncio
import sys
from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models.user import User
from app.models.email_verification import EmailVerificationCode


async def delete_user_by_email(email: str):
    if not email or not email.strip():
        print("❌ Error: Please provide an email address to delete.")
        print("Usage: python delete_user.py <email>")
        return

    email_clean = email.lower().strip()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_maker() as db:
        # 1. Delete user from users table (cascades to expenses, budgets, categories, tokens)
        user_result = await db.execute(
            delete(User).where(func.lower(User.email) == email_clean)
        )
        # 2. Delete any old verification codes for this email
        otp_result = await db.execute(
            delete(EmailVerificationCode).where(func.lower(EmailVerificationCode.email) == email_clean)
        )
        await db.commit()

        deleted_users = user_result.rowcount
        deleted_otps = otp_result.rowcount

        if deleted_users > 0:
            print(f"✅ Successfully deleted user '{email_clean}' ({deleted_users} user record(s), {deleted_otps} verification code(s)).")
            print("👉 You can now re-register with this email on the registration page.")
        else:
            print(f"ℹ️ No user found with email '{email_clean}' in the users table.")
            if deleted_otps > 0:
                print(f"🧹 Cleaned up {deleted_otps} previous verification code(s).")
            print("👉 The email is free and available to register.")

    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        target_email = input("Enter email address to delete: ").strip()
    else:
        target_email = sys.argv[1].strip()

    asyncio.run(delete_user_by_email(target_email))
