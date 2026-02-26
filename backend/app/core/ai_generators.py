"""
Dual-mode AI agent system for Traction.

Agents
------
- **doc_agent**              – Structured interview / field extraction (doc mode)
- **design_agent**           – Full HTML pitch-deck generation (design mode)
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


# ---------------------------------------------------------------------------
# 1.  Doc-mode agent  (structured extraction)
# ---------------------------------------------------------------------------

_DOC_SYSTEM_PROMPT = """\
You are an expert product strategist and startup advisor conducting a structured \
interview to help a founder flesh out their startup idea.  Your job is to have a \
natural, conversational dialogue while progressively extracting structured data \
for NINE document types.

## Document types and their fields

1. **Product Description**
   - product_name, one_liner, problem_statement, solution_description,
     target_audience, key_features (list[str]), unique_value_proposition

2. **Timeline**
   - milestones (list[dict]), current_stage, launch_date

3. **SWOT Analysis**
   - strengths (list[str]), weaknesses (list[str]),
     opportunities (list[str]), threats (list[str])

4. **Market Research**
   - tam, sam, som, target_demographics, market_trends (list[str]),
     market_growth_rate

5. **Financial Projections**
   - revenue_model, year1_revenue, year2_revenue, year3_revenue,
     monthly_burn_rate, break_even_timeline, key_cost_drivers (list[str])

6. **Funding Requirements**
   - funding_stage, amount_seeking, use_of_funds (list[dict]),
     current_funding, runway_months (int)

7. **Product Forecast**
   - year1_users, year2_users, year3_users, conversion_rate,
     customer_acquisition_cost, lifetime_value, growth_strategy

8. **Competitive Analysis**
   - direct_competitors (list[dict]), indirect_competitors (list[str]),
     competitive_advantage, market_positioning

9. **Executive Summary**
   - company_name, mission_statement, vision_statement,
     founding_team (list[dict]), business_model_summary, traction_to_date

## Rules

- Only extract data the user has **explicitly** mentioned.  Never invent or \
  assume values.
- Set ``is_complete`` to ``True`` for a document type **only** when ALL of its \
  fields have been populated.
- Do **not** make up data to fill gaps.
- Naturally guide the conversation toward uncovered fields without being \
  formulaic or robotic—ask follow-up questions, give brief examples, and \
  acknowledge what the user has shared.
- Your ``response`` field must always contain a helpful, conversational reply \
  that moves the interview forward.
"""

doc_agent = Agent(
    model="openai:gpt-4o-mini",
    result_type=ExtractionResult,
    system_prompt=_DOC_SYSTEM_PROMPT,
)


# ---------------------------------------------------------------------------
# 2.  Design-mode agent  (full HTML pitch deck)
# ---------------------------------------------------------------------------

_DESIGN_SYSTEM_PROMPT = """\
You are a world-class pitch-deck designer.  Given structured startup data you \
create a **bespoke, single-file HTML pitch deck** that is visually stunning and \
investor-ready.

## Design requirements

- Use the **Plus Jakarta Sans** font (import from Google Fonts).
- Dark / black background theme throughout.
- Use ``clamp()`` for all font sizes and spacing so the deck scales fluidly \
  across screen sizes.
- Aim for a **liquid glass** aesthetic: subtle glassmorphism cards, soft \
  gradients, gentle glow effects, semi-transparent surfaces.
- The deck must be a **full-screen, slide-based presentation**:
  - One ``<section>`` per slide, each taking ``100vh`` / ``100vw``.
  - Include keyboard navigation (ArrowRight / ArrowLeft / Space) and a small \
    progress indicator.

## Output structure

Your output has **TWO** sections inside the HTML:

1. **Pitch deck slides** (creative, visually rich, storytelling order):
   - Title slide, Problem, Solution, Market size, Business model, Traction, \
     Team, Financial highlights, Ask / CTA — plus any extra slides that suit \
     the data.

2. **Summary section** (appended after the last slide, strict formatting):
   - Key metrics displayed in a grid.
   - Risks and mitigations.
   - Links / references to each document type.
   - Use clean tables or definition lists—no creative liberties here.

## Rules

- Output **raw HTML only**.  No markdown fences, no explanation, no preamble.
- The HTML must be completely self-contained (inline ``<style>`` and \
  ``<script>``).
- Every slide must render correctly if opened directly in a browser.
"""

design_agent = Agent(
    model="openai:gpt-4o-mini",
    result_type=str,
    system_prompt=_DESIGN_SYSTEM_PROMPT,
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
    result_type=str,
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
    result_type=str,
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
    return result.data


async def generate_full_html(project_name: str, all_fields: dict) -> str:
    """Use the *design_agent* to produce a complete pitch-deck HTML string.

    Parameters
    ----------
    project_name:
        Human-readable project / company name.
    all_fields:
        Mapping of ``{doc_type: fields_dict}`` for every document type.
    """
    prompt = (
        f"Create a full pitch-deck HTML presentation for '{project_name}'.\n\n"
        f"Structured startup data:\n{json.dumps(all_fields, indent=2, default=str)}"
    )
    result = await design_agent.run(prompt)
    return result.data


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
    return result.data


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
