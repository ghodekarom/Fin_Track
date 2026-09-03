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
    provider: str = Field("gemini-1.5-flash", description="AI provider used or fallback engine")
    is_cached: bool = Field(False, description="True if served from memory cache")
