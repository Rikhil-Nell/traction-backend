"""
Pydantic models for structured field extraction from chat conversations.

Each document field model represents the data that the AI doc-agent extracts
from a user's conversational messages for a specific document type.  Every
field (except ``is_complete``) is optional so the model can be returned in a
partially-filled state as the conversation progresses.
"""

from __future__ import annotations

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Individual document-field models
# ---------------------------------------------------------------------------

class ProductDescriptionFields(BaseModel):
    is_complete: bool = False
    product_name: str | None = None
    one_liner: str | None = None
    problem_statement: str | None = None
    solution_description: str | None = None
    target_audience: str | None = None
    key_features: list[str] | None = None
    unique_value_proposition: str | None = None


class TimelineFields(BaseModel):
    is_complete: bool = False
    milestones: list[dict] | None = None
    current_stage: str | None = None
    launch_date: str | None = None


class SwotFields(BaseModel):
    is_complete: bool = False
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    opportunities: list[str] | None = None
    threats: list[str] | None = None


class MarketResearchFields(BaseModel):
    is_complete: bool = False
    tam: str | None = None
    sam: str | None = None
    som: str | None = None
    target_demographics: str | None = None
    market_trends: list[str] | None = None
    market_growth_rate: str | None = None


class FinancialProjectionsFields(BaseModel):
    is_complete: bool = False
    revenue_model: str | None = None
    year1_revenue: str | None = None
    year2_revenue: str | None = None
    year3_revenue: str | None = None
    monthly_burn_rate: str | None = None
    break_even_timeline: str | None = None
    key_cost_drivers: list[str] | None = None


class FundingRequirementsFields(BaseModel):
    is_complete: bool = False
    funding_stage: str | None = None
    amount_seeking: str | None = None
    use_of_funds: list[dict] | None = None
    current_funding: str | None = None
    runway_months: int | None = None


class ProductForecastFields(BaseModel):
    is_complete: bool = False
    year1_users: str | None = None
    year2_users: str | None = None
    year3_users: str | None = None
    conversion_rate: str | None = None
    customer_acquisition_cost: str | None = None
    lifetime_value: str | None = None
    growth_strategy: str | None = None


class CompetitiveAnalysisFields(BaseModel):
    is_complete: bool = False
    direct_competitors: list[dict] | None = None
    indirect_competitors: list[str] | None = None
    competitive_advantage: str | None = None
    market_positioning: str | None = None


class ExecutiveSummaryFields(BaseModel):
    is_complete: bool = False
    company_name: str | None = None
    mission_statement: str | None = None
    vision_statement: str | None = None
    founding_team: list[dict] | None = None
    business_model_summary: str | None = None
    traction_to_date: str | None = None


# ---------------------------------------------------------------------------
# Composite extraction result
# ---------------------------------------------------------------------------

class ExtractionResult(BaseModel):
    """Returned by the doc-agent after each conversation turn.

    ``response`` is the natural-language reply that will be shown to the user.
    The remaining fields hold the (possibly partial) structured data extracted
    so far for each document type.
    """

    response: str
    product_description: ProductDescriptionFields | None = None
    timeline: TimelineFields | None = None
    swot: SwotFields | None = None
    market_research: MarketResearchFields | None = None
    financial_projections: FinancialProjectionsFields | None = None
    funding_requirements: FundingRequirementsFields | None = None
    product_forecast: ProductForecastFields | None = None
    competitive_analysis: CompetitiveAnalysisFields | None = None
    executive_summary: ExecutiveSummaryFields | None = None


# ---------------------------------------------------------------------------
# Lookup dictionaries  (doc-type slug  ->  ...)
# ---------------------------------------------------------------------------

DOCUMENT_TYPE_FIELDS: dict[str, type[BaseModel]] = {
    "product-description": ProductDescriptionFields,
    "timeline": TimelineFields,
    "swot-analysis": SwotFields,
    "market-research": MarketResearchFields,
    "financial-projections": FinancialProjectionsFields,
    "funding-requirements": FundingRequirementsFields,
    "product-forecast": ProductForecastFields,
    "competitive-analysis": CompetitiveAnalysisFields,
    "executive-summary": ExecutiveSummaryFields,
}

DOCUMENT_TYPE_TO_ATTR: dict[str, str] = {
    "product-description": "product_description",
    "timeline": "timeline",
    "swot-analysis": "swot",
    "market-research": "market_research",
    "financial-projections": "financial_projections",
    "funding-requirements": "funding_requirements",
    "product-forecast": "product_forecast",
    "competitive-analysis": "competitive_analysis",
    "executive-summary": "executive_summary",
}

DOCUMENT_TYPE_TITLES: dict[str, str] = {
    "product-description": "Product Description",
    "timeline": "Timeline",
    "swot-analysis": "SWOT Analysis",
    "market-research": "Market Research",
    "financial-projections": "Financial Projections",
    "funding-requirements": "Funding Requirements",
    "product-forecast": "Product Forecast",
    "competitive-analysis": "Competitive Analysis",
    "executive-summary": "Executive Summary",
}
