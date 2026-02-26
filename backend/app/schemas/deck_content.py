"""
Pydantic models for structured pitch deck content.

The AI deck-content agent outputs a ``PitchDeckContent`` instance, which is
then rendered into deterministic HTML by the template in
``app.core.deck_template``.
"""

from __future__ import annotations

from pydantic import BaseModel


class SlideContent(BaseModel):
    headline: str
    subheadline: str
    body_points: list[str]
    accent_metric: str | None = None
    accent_label: str | None = None


class CoverSlide(SlideContent):
    pass


class ProblemSlide(SlideContent):
    pass


class SolutionSlide(SlideContent):
    pass


class MarketSlide(SlideContent):
    tam: str | None = None
    sam: str | None = None
    som: str | None = None


class TractionSlide(SlideContent):
    pass


class BusinessModelSlide(SlideContent):
    pass


class TeamSlide(SlideContent):
    team_members: list[dict] | None = None


class AskSlide(SlideContent):
    funding_amount: str | None = None
    use_of_funds: list[dict] | None = None


class VisionSlide(SlideContent):
    pass


class PitchDeckContent(BaseModel):
    cover: CoverSlide
    problem: ProblemSlide
    solution: SolutionSlide
    market: MarketSlide
    traction: TractionSlide
    business_model: BusinessModelSlide
    team: TeamSlide
    ask: AskSlide
    vision: VisionSlide
