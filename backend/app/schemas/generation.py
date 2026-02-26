import pydantic

class GenerateDeckRequest(pydantic.BaseModel):
    theme: str = "dark"
    aesthetic: str = "minimal"

class GenerateDocumentsRequest(pydantic.BaseModel):
    # If empty, generate all standard types
    document_types: list[str] = [
        "product-description",
        "swot-analysis",
        "market-research",
        "user-personas",
        "feature-roadmap"
    ]
