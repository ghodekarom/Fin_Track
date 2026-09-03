from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class InsightCategory(str, Enum):
    QUICK_WIN = "quick_win"
    BUDGET_ALERT = "budget_alert"
    SUBSCRIPTION = "subscription"
    HIGH_IMPACT = "high_impact"


class SpendingInsight(BaseModel):
    id: str = Field(..., description="Unique deterministic or generated insight ID")
    type: InsightCategory = Field(..., description="Category of the insight for badge styling")
    title: str = Field(..., max_length=150, description="Concise catchy headline")
    description: str = Field(..., description="Clear explanation of the spending pattern found")
    potential_savings: Optional[float] = Field(None, description="Estimated monthly savings amount in local currency")
    action_tip: str = Field(..., description="Actionable recommendation the user can take immediately")
    impact_level: Literal["high", "medium", "low"] = Field("medium", description="Priority level")


class SpendingInsightsResponse(BaseModel):
    insights: List[SpendingInsight] = Field(default_factory=list)
    total_potential_monthly_savings: float = Field(0.0, description="Sum of all identified potential savings")
    currency: str = Field("INR", description="Default currency code")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    provider: str = Field("gemini-flash-latest", description="AI provider used or fallback engine")
    is_cached: bool = Field(False, description="True if served from memory cache")


# =========================================================================
# Phase 2: Predictive Overspend Warning & Dynamic Budget Allocator
# =========================================================================

class VelocityRiskLevel(str, Enum):
    SAFE = "safe"
    MODERATE = "moderate"
    CRITICAL = "critical"


class CategoryVelocityForecast(BaseModel):
    category_id: str
    category_name: str
    budget_limit: float
    current_spent: float
    daily_burn_rate: float
    projected_month_end_spend: float
    projected_overage: float
    exhaustion_day: Optional[int] = None
    risk_level: VelocityRiskLevel
    safe_daily_spend: float


class OverallVelocityForecast(BaseModel):
    overall_budget_limit: Optional[float] = None
    current_spent: float
    daily_burn_rate: float
    projected_month_end_spend: float
    projected_overage: float
    days_elapsed: int
    days_remaining: int
    safe_daily_spend: float
    risk_level: VelocityRiskLevel
    risk_message: str
    category_forecasts: List[CategoryVelocityForecast] = Field(default_factory=list)


class DynamicBudgetRecommendation(BaseModel):
    category_id: str
    category_name: str
    current_budget: Optional[float] = None
    suggested_budget: float
    average_monthly_spend: float
    reasoning: str


class ApplySuggestedBudgetRequest(BaseModel):
    category_id: str
    amount: float = Field(..., gt=0)


class PredictiveBudgetResponse(BaseModel):
    velocity: OverallVelocityForecast
    smart_allocations: List[DynamicBudgetRecommendation] = Field(default_factory=list)
    currency: str = "INR"
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# =========================================================================
# Phase 3: "Ask FinTrack AI" — Conversational Financial Assistant
# =========================================================================

class ChatMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: ChatMessageRole
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class AskAiQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500, description="Natural language question about user's finances")
    history: List[ChatMessage] = Field(default_factory=list, description="Recent conversation history for conversational context")


class AskAiQueryResponse(BaseModel):
    answer: str = Field(..., description="Markdown-formatted conversational response strictly grounded in user's data")
    related_metrics: Optional[dict] = Field(None, description="Key numerical highlights relevant to the question")
    suggested_followups: List[str] = Field(default_factory=list, description="Contextual quick prompt chips")
    provider: str = Field("gemini-flash-latest", description="LLM provider or rule fallback")


# =========================================================================
# Phase 4: Natural Language Quick-Add & Smart Auto-Categorization
# =========================================================================

class QuickAddParseRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=300, description="Natural language expense string")


class ParsedExpenseDraft(BaseModel):
    title: str = Field(..., description="Clean extracted merchant/item title")
    amount: float = Field(..., gt=0, description="Extracted numerical expense amount")
    category_id: Optional[str] = Field(None, description="Mapped category UUID if found")
    category_name: str = Field("Other", description="Mapped category name")
    expense_date: str = Field(..., description="ISO formatted YYYY-MM-DD date")
    payment_mode: Literal["cash", "card", "upi", "other"] = Field("other", description="Extracted payment method")
    notes: Optional[str] = Field(None, description="Extra notes or merchant details")
    confidence_score: float = Field(0.9, description="Extraction confidence score from 0 to 1")
    provider: str = Field("gemini-flash-latest", description="Parser engine used")


class QuickAddConfirmRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    category_id: str = Field(..., description="Category UUID")
    expense_date: str = Field(..., description="ISO formatted YYYY-MM-DD")
    payment_mode: Literal["cash", "card", "upi", "other"] = "other"
    notes: Optional[str] = None


# =========================================================================
# Phase 5: Monthly Financial Health Score & Executive Summary (Digest)
# =========================================================================

class ScorePillarBreakdown(BaseModel):
    budget_adherence: float = Field(..., ge=0, le=40, description="Score based on staying within budget (0-40)")
    savings_velocity: float = Field(..., ge=0, le=35, description="Score based on savings to spend ratio (0-35)")
    category_discipline: float = Field(..., ge=0, le=25, description="Score based on category diversification (0-25)")


class FinancialHealthScoreResponse(BaseModel):
    health_score: int = Field(..., ge=0, le=100, description="Overall health score (0-100)")
    letter_grade: str = Field(..., description="A+, A, B, C, or D")
    status_label: str = Field(..., description="Excellent, Healthy, Needs Attention, etc.")
    pillars: ScorePillarBreakdown
    executive_summary: str = Field(..., description="Personalized executive digest paragraph")
    key_achievements: List[str] = Field(default_factory=list, description="Top positive financial milestones")
    improvement_goals: List[str] = Field(default_factory=list, description="Top strategic goals for next month")
    top_spend_category: str = Field(..., description="Highest spending bucket")
    potential_monthly_savings: float = Field(0.0, description="Estimated achievable savings")
    period_month: str = Field(..., description="Month label, e.g. September 2026")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    provider: str = Field("FinTrack Health Engine", description="Algorithm or LLM provider")


