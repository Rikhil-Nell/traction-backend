import pydantic

class GenerateDeckRequest(pydantic.BaseModel):
    theme: str = "dark"
    aesthetic: str = "minimal"

class GenerateDocumentsRequest(pydantic.BaseModel):
    # If empty, generate all standard 9 types
    document_types: list[str] = [
        "product-description",
        "timeline",
        "swot-analysis",
        "market-research",
        "financial-projections",
        "funding-requirements",
        "product-forecast",
        "competitive-analysis",
        "executive-summary",
    ]
