from fastapi import APIRouter

from app.api.v1 import auth, budgets, categories, dashboard, expenses, health

api_router = APIRouter()

# Mount API endpoints
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
