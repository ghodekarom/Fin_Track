from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import logging
import re
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.llm import get_llm_provider
from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User
from app.schemas.ai import ParsedExpenseDraft, QuickAddConfirmRequest

logger = logging.getLogger("fintrack.ai.quickadd")

CATEGORY_KEYWORD_RULES = {
    "Food & Dining": ["food", "dinner", "lunch", "breakfast", "swiggy", "zomato", "restaurant", "cafe", "coffee", "bistro", "burger", "pizza", "starbucks", "subway", "bar"],
    "Groceries": ["grocery", "groceries", "supermarket", "mart", "milk", "vegetable", "veggies", "fruits", "pantry", "nature's basket", "zepto", "blinkit", "instamart", "bigbasket"],
    "Transportation": ["uber", "ola", "cab", "taxi", "metro", "bus", "auto", "petrol", "fuel", "diesel", "toll", "flight", "train"],
    "Entertainment": ["netflix", "spotify", "prime", "movie", "cinema", "imax", "steam", "game", "gaming", "concert", "theatre", "disney", "youtube"],
    "Shopping": ["shopping", "amazon", "flipkart", "zara", "clothes", "shirt", "shoes", "myntra", "electronics", "gadget", "watch"],
    "Utilities": ["electricity", "power", "broadband", "wifi", "internet", "water", "gas", "cylinder", "recharge", "airtel", "jio"],
    "Healthcare": ["gym", "doctor", "medicine", "pharmacy", "hospital", "clinic", "fitness", "supplement", "dentist"],
    "Housing": ["rent", "maintenance", "society", "repair", "plumber"],
}


def _deterministic_parse(
    text: str,
    categories: List[Category],
    today: date,
) -> ParsedExpenseDraft:
    """
    Robust regex and rule-based parser for expense strings. Zero crashes.
    """
    text_clean = text.strip()
    lower = text_clean.lower()

    # 1. Extract Amount
    # Matches patterns like 450, 1,200, 350.50, ₹500, Rs. 500, etc.
    amt = 100.0
    amt_match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d[\d,]*\.?\d{0,2})", lower)
    if amt_match:
        try:
            amt_str = amt_match.group(1).replace(",", "")
            amt = float(amt_str)
        except Exception:
            amt = 100.0

    # 2. Extract Payment Mode
    mode = "other"
    if any(k in lower for k in ["upi", "gpay", "phonepe", "paytm", "scan"]):
        mode = "upi"
    elif any(k in lower for k in ["card", "credit", "debit", "visa", "mastercard"]):
        mode = "card"
    elif "cash" in lower:
        mode = "cash"

    # 3. Extract Relative Date
    exp_date = today
    if "day before yesterday" in lower:
        exp_date = today - timedelta(days=2)
    elif "yesterday" in lower:
        exp_date = today - timedelta(days=1)

    # 4. Map Category
    matched_cat: Optional[Category] = None
    # First, match keyword dictionary
    for cat_name, keywords in CATEGORY_KEYWORD_RULES.items():
        if any(k in lower for k in keywords):
            matched_cat = next((c for c in categories if c.name.lower() == cat_name.lower()), None)
            if matched_cat:
                break

    # If not found, match category name directly
    if not matched_cat:
        for c in categories:
            if c.name.lower() in lower:
                matched_cat = c
                break

    if not matched_cat and categories:
        matched_cat = categories[0]

    # 5. Extract Title
    # Remove amount, payment mode, and date words from title
    remove_words = ["yesterday", "today", "day before yesterday", "via upi", "via card", "by card", "in cash", "via", "paid", "spent", "for", "on", "rs.", "rs", "inr", "₹"]
    cleaned_title = text_clean
    for rw in remove_words:
        cleaned_title = re.sub(rf"\b{re.escape(rw)}\b", "", cleaned_title, flags=re.IGNORECASE)
    # Remove isolated numbers
    cleaned_title = re.sub(r"\b\d[\d,]*\.?\d*\b", "", cleaned_title).strip()
    cleaned_title = re.sub(r"\s+", " ", cleaned_title).strip()

    if not cleaned_title or len(cleaned_title) < 3:
        cleaned_title = f"{matched_cat.name if matched_cat else 'General'} Expense"

    return ParsedExpenseDraft(
        title=cleaned_title.title(),
        amount=round(amt, 2),
        category_id=str(matched_cat.id) if matched_cat else None,
        category_name=matched_cat.name if matched_cat else "Other",
        expense_date=exp_date.isoformat(),
        payment_mode=mode,
        notes=f"Auto-parsed from: \"{text_clean}\"",
        confidence_score=0.88,
        provider="Deterministic Rule Parser",
    )


async def parse_natural_language_expense(
    db: AsyncSession,
    user: User,
    text: str,
) -> ParsedExpenseDraft:
    """
    Parse a natural language expense sentence into a structured draft.
    Uses Gemini when available, falling back to deterministic parser.
    """
    today = datetime.now(timezone.utc).date()

    # 1. Fetch user's categories
    cat_query = select(Category).where(
        or_(Category.user_id == user.id, Category.is_default == True)
    )
    res = await db.execute(cat_query)
    categories = list(res.scalars().all())

    cat_names = [c.name for c in categories]

    # 2. Try LLM parsing
    llm = get_llm_provider()
    if llm:
        system_instruction = (
            "You are FinTrack AI's Natural Language Expense Parser. "
            "Given an input string describing an expense, extract the fields and return strictly JSON matching: "
            "{'title': string, 'amount': number, 'category_name': string, 'expense_date': 'YYYY-MM-DD', 'payment_mode': 'cash'|'card'|'upi'|'other', 'notes': string}. "
            f"The 'category_name' MUST be chosen from this exact list: {cat_names}. "
            f"Today's date is {today.isoformat()}. Resolve relative dates like 'yesterday' or 'last Friday' correctly."
        )

        try:
            res_json = await llm.generate_structured_json(
                system_instruction=system_instruction,
                prompt=f"Parse this expense: \"{text}\"",
            )
            cat_name = res_json.get("category_name", "Other")
            matched_cat = next((c for c in categories if c.name.lower() == cat_name.lower()), None)
            if not matched_cat and categories:
                matched_cat = categories[0]

            parsed_amt = float(res_json.get("amount", 100.0))
            parsed_date = res_json.get("expense_date", today.isoformat())
            parsed_mode = res_json.get("payment_mode", "other")
            if parsed_mode not in ["cash", "card", "upi", "other"]:
                parsed_mode = "other"

            return ParsedExpenseDraft(
                title=str(res_json.get("title", text[:30])).strip().title(),
                amount=round(parsed_amt, 2),
                category_id=str(matched_cat.id) if matched_cat else None,
                category_name=matched_cat.name if matched_cat else "Other",
                expense_date=parsed_date,
                payment_mode=parsed_mode,
                notes=res_json.get("notes"),
                confidence_score=0.96,
                provider=f"Gemini ({settings.AI_MODEL_NAME})",
            )
        except Exception as exc:
            logger.warning(f"Gemini quick-add parse error: {exc}. Using deterministic parser.")

    # 3. Fallback
    return _deterministic_parse(text, categories, today)


async def confirm_and_save_expense(
    db: AsyncSession,
    user: User,
    payload: QuickAddConfirmRequest,
) -> Expense:
    """
    Save the confirmed parsed expense directly to the database.
    """
    exp_date = date.fromisoformat(payload.expense_date)
    new_expense = Expense(
        user_id=user.id,
        category_id=UUID(payload.category_id),
        amount=Decimal(str(payload.amount)),
        title=payload.title,
        expense_date=exp_date,
        payment_mode=payload.payment_mode,
        notes=payload.notes,
    )
    db.add(new_expense)
    await db.commit()
    
    from app.services.expense_service import get_expense_by_id
    return await get_expense_by_id(db, user.id, new_expense.id)
