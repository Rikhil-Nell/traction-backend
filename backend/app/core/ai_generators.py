"""
Dual-mode AI agent system for Traction.

Agents
------
- **doc_agent**              – Structured interview / field extraction (doc mode)
- **deck_content_agent**     – Structured JSON content for pitch deck slides
- **document_content_agent** – Writes polished markdown for individual documents
- **llms_txt_agent**         – Writes plaintext startup description for AI agents

Utility helpers handle hashing, state building, and orchestrating generation.
"""

import json
import hashlib

from pydantic_ai import Agent

from app.schemas.extraction import (
    ExtractionResult,
    DOCUMENT_TYPE_TO_ATTR,
    DOCUMENT_TYPE_TITLES,
)
from app.schemas.deck_content import PitchDeckContent
from app.core.deck_template import render_pitch_deck


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
# 2.  Deck content agent  (structured JSON for pitch deck slides)
# ---------------------------------------------------------------------------

_DECK_CONTENT_SYSTEM_PROMPT = """\
You are a world-class pitch-deck strategist.  Given structured startup data, \
produce compelling slide content as structured JSON.

## CRITICAL: You MUST populate ALL 9 slides

You must return content for every single slide:
1. **cover** — headline = company name, subheadline = one-liner
2. **problem** — the pain points being solved
3. **solution** — how the product solves the problem
4. **market** — market size and opportunity (populate tam/sam/som if available)
5. **traction** — key metrics and milestones achieved
6. **business_model** — how the company makes money
7. **team** — founding team (populate team_members if available)
8. **ask** — funding request (populate funding_amount and use_of_funds if available)
9. **vision** — future vision and closing statement

## Content guidelines

- Write **persuasive headlines**, not labels.  E.g. "We're solving a $4.2B \
  problem" not "Problem".
- Include concrete numbers from the data wherever possible.
- Make body_points punchy—max 8 words each.  3-5 points per slide.
- Fill accent_metric with the single most impressive number per slide.
- Never invent numbers.  If data is missing, write compelling qualitative \
  content instead.
"""

deck_content_agent = Agent(
    model="openai:gpt-4o",
    output_type=PitchDeckContent,
    system_prompt=_DECK_CONTENT_SYSTEM_PROMPT,
    retries=3,
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
    """Generate a pitch-deck HTML string via structured AI content + template.

    1. The *deck_content_agent* produces a ``PitchDeckContent`` (structured JSON).
    2. ``render_pitch_deck`` renders that into deterministic, high-quality HTML.

    Parameters
    ----------
    project_name:
        Human-readable project / company name.
    all_fields:
        Mapping of ``{doc_type: fields_dict}`` for every document type.
    """
    prompt = (
        f"Create pitch deck content for '{project_name}'.\n\n"
        f"Data:\n{json.dumps(all_fields, indent=2, default=str)}"
    )
    result = await deck_content_agent.run(prompt)
    content: PitchDeckContent = result.output
    return render_pitch_deck(content, project_name)


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
