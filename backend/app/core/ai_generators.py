"""
Dual-mode AI agent system for Traction.

Agents
------
- **doc_agent**              – Structured interview / field extraction (doc mode)
- **html_deck_agent**        – Generates full HTML pitch decks from reference themes
- **document_content_agent** – Writes polished markdown for individual documents
- **llms_txt_agent**         – Writes plaintext startup description for AI agents

Utility helpers handle hashing, state building, and orchestrating generation.
"""

import json
import hashlib
import random
from pathlib import Path

from pydantic_ai import Agent

from app.schemas.extraction import (
    ExtractionResult,
    DOCUMENT_TYPE_TO_ATTR,
    DOCUMENT_TYPE_TITLES,
)

# ---------------------------------------------------------------------------
# Load reference pitch-deck HTML themes at module level
# ---------------------------------------------------------------------------
_DEMO_DECKS_DIR = Path(__file__).parent / "demo_decks"
_DEMO_THEMES: list[dict[str, str]] = []
for _html_file in sorted(_DEMO_DECKS_DIR.glob("*.html")):
    _DEMO_THEMES.append({
        "name": _html_file.stem,
        "html": _html_file.read_text(encoding="utf-8"),
    })


# ---------------------------------------------------------------------------
# 1.  Doc-mode agent  (structured extraction)
# ---------------------------------------------------------------------------

_DOC_SYSTEM_PROMPT = """\
You are an expert product strategist and startup advisor conducting a structured \
interview to help a founder flesh out their startup idea.  Your job is to have a \
natural, conversational dialogue while progressively extracting structured data \
for NINE document types.

## Document types, fields, and REQUIRED fields for completion

Each document type has REQUIRED fields (marked with *) and optional fields.
Set ``is_complete=True`` when ALL REQUIRED fields have values.
Optional fields enhance quality but are NOT blockers for completion.

1. **Product Description**
   - *product_name, one_liner, *problem_statement, *solution_description,
     *target_audience, key_features (list[str]), unique_value_proposition

2. **Timeline**
   - milestones (list[dict]) — at least 1 required*, *current_stage, launch_date

3. **SWOT Analysis**
   - *strengths (list[str]) — at least 1 required, *weaknesses (list[str]) — at least 1 required,
     opportunities (list[str]), threats (list[str])

4. **Market Research**
   - tam*, target_demographics* — at least ONE of these two is required,
     sam, som, market_trends (list[str]), market_growth_rate

5. **Financial Projections**
   - *revenue_model, year1_revenue, year2_revenue, year3_revenue,
     monthly_burn_rate, break_even_timeline, key_cost_drivers (list[str])

6. **Funding Requirements**
   - *funding_stage, *amount_seeking, use_of_funds (list[dict]),
     current_funding, runway_months (int)

7. **Product Forecast**
   - *growth_strategy, year1_users, year2_users, year3_users, conversion_rate,
     customer_acquisition_cost, lifetime_value

8. **Competitive Analysis**
   - *competitive_advantage, direct_competitors (list[dict]),
     indirect_competitors (list[str]), market_positioning

9. **Executive Summary**
   - *company_name, *mission_statement, vision_statement,
     founding_team (list[dict]), business_model_summary, traction_to_date

## Rules

- Only extract data the user has **explicitly** mentioned.  Never invent or \
  assume values.
- Set ``is_complete`` to ``True`` when the REQUIRED fields (marked with * above) \
  have values.  Optional fields can remain null — they enhance quality but are \
  not blockers.
- If the user provides information that clearly maps to multiple document types \
  in a single message, extract and populate ALL applicable fields across ALL \
  document types, not just the one being discussed.
- Do **not** make up data to fill gaps.
- Naturally guide the conversation toward uncovered fields without being \
  formulaic or robotic—ask follow-up questions, give brief examples, and \
  acknowledge what the user has shared.
- Your ``response`` field must always contain a helpful, conversational reply \
  that moves the interview forward.
"""

doc_agent = Agent(
    model="openai:gpt-4o-mini",
    output_type=ExtractionResult,
    system_prompt=_DOC_SYSTEM_PROMPT,
)


# ---------------------------------------------------------------------------
# 2.  HTML deck agent  (generates full self-contained HTML pitch decks)
# ---------------------------------------------------------------------------

_DECK_HTML_SYSTEM_PROMPT = """\
You are a world-class pitch-deck designer who produces stunning, self-contained \
HTML pitch decks.

## Task

Given startup data and a reference HTML deck, produce a COMPLETE self-contained \
HTML pitch deck that matches the reference's visual aesthetic but uses the \
provided startup's content.

## Mandatory structure

- Output ONLY valid HTML. Start with `<!DOCTYPE html>`, end with `</html>`.
- No markdown fences, no explanation, no preamble — raw HTML only.
- Exactly 9 slides: cover, problem, solution, market, traction, \
  business_model, team, ask, vision.
- HLS.js video backgrounds via CDN \
  (`https://cdn.jsdelivr.net/npm/hls.js@latest`).
- Keyboard navigation: ArrowLeft / ArrowRight / Space to navigate, \
  F for fullscreen.
- Progress dots and a slide counter (e.g. "3 / 9").
- Responsive sizing with `clamp()` throughout.
- Tailwind CSS via CDN for utility classes.
- Lucide Icons via CDN for any icons.
- Google Fonts `<link>` for the fonts used by the reference theme.

## Content rules

- Write PERSUASIVE headlines, not labels.  \
  "Solving a $4.2 B crisis" not "Problem".
- Include concrete numbers from the startup data wherever possible.
- Bullet points: punchy, max 8 words each, 3–5 per slide.
- NEVER invent numbers.  If data is missing, use compelling qualitative \
  content instead.
- Cover slide: company name large, one-liner below.
- Market slide: show TAM / SAM / SOM as big highlight numbers if available.
- Ask slide: funding amount prominent, use-of-funds breakdown.

## Style matching

Reproduce the reference deck's visual DNA exactly:
- Same color palette, gradients, and accent colors.
- Same font families and typographic scale.
- Same card / glass / border treatment.
- Same animation and transition style.
- Same layout patterns and spacing approach.

Adapt the content structure to fit the startup's actual data while maintaining \
the aesthetic perfectly.
"""

html_deck_agent = Agent(
    model="openai:gpt-5.2",
    output_type=str,
    system_prompt=_DECK_HTML_SYSTEM_PROMPT,
    retries=2,
)


# ---------------------------------------------------------------------------
# 3.  Document content agent  (markdown for individual docs)
# ---------------------------------------------------------------------------

_DOC_CONTENT_SYSTEM_PROMPT = """\
You are a professional business writer.  Given a document type and its \
extracted fields, write a polished, well-structured **markdown** document.

Rules:
- Use proper markdown headings, bullet lists, and tables where appropriate.
- Be concise but thorough—this document will be read by investors and \
  stakeholders.
- Do not include any preamble such as "Here is your document".  Start directly \
  with the content.
- Output raw markdown only.
"""

document_content_agent = Agent(
    model="openai:gpt-4o-mini",
    output_type=str,
    system_prompt=_DOC_CONTENT_SYSTEM_PROMPT,
)


# ---------------------------------------------------------------------------
# 4.  LLMs.txt agent  (plaintext startup description for AI agents)
# ---------------------------------------------------------------------------

_LLMS_TXT_SYSTEM_PROMPT = """\
You write concise, plaintext descriptions of startups that are optimised for \
consumption by other AI agents and large-language models.

Given structured startup data, produce a single plaintext document (no markdown, \
no HTML) that covers:
- What the company does (one paragraph)
- Target market and size
- Business model
- Traction and key metrics
- Team highlights
- Funding status

Keep the tone neutral and factual.  Output plaintext only.
"""

llms_txt_agent = Agent(
    model="openai:gpt-4o-mini",
    output_type=str,
    system_prompt=_LLMS_TXT_SYSTEM_PROMPT,
)


# ===================================================================
# Utility functions
# ===================================================================

def compute_fields_hash(documents_fields: list[dict | None]) -> str:
    """Return a deterministic SHA-256 hex digest of all document fields.

    Parameters
    ----------
    documents_fields:
        A list where each element is either a dict of extracted fields for a
        document or ``None`` if the document has no fields yet.
    """
    canonical = json.dumps(documents_fields, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def build_extraction_state(documents: list) -> dict:
    """Build a ``{doc_type: {is_complete, fields}}`` mapping from *ProjectDocument* records.

    Parameters
    ----------
    documents:
        Iterable of ``ProjectDocument`` ORM instances (or any object with
        ``.type`` and ``.fields`` attributes).
    """
    state: dict[str, dict] = {}
    for doc in documents:
        raw = doc.fields or {}
        if isinstance(raw, dict):
            is_complete = raw.get("is_complete", False)
            fields = {k: v for k, v in raw.items() if k != "is_complete"}
        else:
            is_complete = False
            fields = {}
        state[doc.type] = {
            "is_complete": is_complete,
            "fields": fields,
        }
    return state


def check_all_complete(extraction_state: dict) -> bool:
    """Return ``True`` only when all 9 document types are present and marked complete."""
    if len(extraction_state) < len(DOCUMENT_TYPE_TO_ATTR):
        return False
    return all(
        info.get("is_complete", False)
        for info in extraction_state.values()
    )


async def generate_document_content(doc_type: str, project_name: str, fields: dict) -> str:
    """Use the *document_content_agent* to write polished markdown for one document.

    Parameters
    ----------
    doc_type:
        The document slug, e.g. ``"product-description"``.
    project_name:
        Human-readable project / company name.
    fields:
        Dict of extracted field values for this document type.
    """
    title = DOCUMENT_TYPE_TITLES.get(doc_type, doc_type)
    prompt = (
        f"Write a '{title}' document for the project '{project_name}'.\n\n"
        f"Extracted fields:\n{json.dumps(fields, indent=2, default=str)}\n\n"
        f"Use these fields as the authoritative source of data.  "
        f"Output polished markdown only."
    )
    result = await document_content_agent.run(prompt)
    return result.output


async def generate_full_html(project_name: str, all_fields: dict) -> str:
    """Generate a pitch-deck HTML string by having the LLM produce a full deck
    modelled after a randomly selected reference theme.

    Parameters
    ----------
    project_name:
        Human-readable project / company name.
    all_fields:
        Mapping of ``{doc_type: fields_dict}`` for every document type.
    """
    theme = random.choice(_DEMO_THEMES) if _DEMO_THEMES else None

    prompt = f"Create a pitch deck for '{project_name}'.\n\n"
    prompt += f"Startup data:\n{json.dumps(all_fields, indent=2, default=str)}\n\n"

    if theme:
        prompt += (
            f"Reference HTML deck (theme: '{theme['name']}') — match this "
            f"aesthetic exactly:\n\n{theme['html']}"
        )

    result = await html_deck_agent.run(prompt)
    html = result.output

    # Strip markdown fences if the model wrapped the output
    html = html.strip()
    if html.startswith("```"):
        lines = html.split("\n")
        # Remove opening fence (e.g. ```html) and closing fence (```)
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        elif lines[0].startswith("```"):
            lines = lines[1:]
        html = "\n".join(lines)

    return html


async def generate_llms_txt(project_name: str, all_fields: dict) -> str:
    """Use the *llms_txt_agent* to produce a plaintext startup description.

    Parameters
    ----------
    project_name:
        Human-readable project / company name.
    all_fields:
        Mapping of ``{doc_type: fields_dict}`` for every document type.
    """
    prompt = (
        f"Write a plaintext startup description for '{project_name}'.\n\n"
        f"Structured data:\n{json.dumps(all_fields, indent=2, default=str)}"
    )
    result = await llms_txt_agent.run(prompt)
    return result.output


async def generate_ai_json(project_name: str, all_fields: dict) -> dict:
    """Build a machine-readable JSON summary of the startup.

    This is a deterministic transformation (no LLM call) that packages all
    extracted fields into a single dict keyed by document type, with a
    top-level ``project_name`` entry.

    Parameters
    ----------
    project_name:
        Human-readable project / company name.
    all_fields:
        Mapping of ``{doc_type: fields_dict}`` for every document type.
    """
    return {
        "project_name": project_name,
        "documents": {
            doc_type: {
                "title": DOCUMENT_TYPE_TITLES.get(doc_type, doc_type),
                "fields": fields,
            }
            for doc_type, fields in all_fields.items()
        },
    }
