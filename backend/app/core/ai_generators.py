import httpx
from pydantic_ai import Agent

# Simple agent for document expansion
document_agent = Agent(
    model="openai:gpt-4o-mini",
    system_prompt=(
        "You are an expert product strategist. Output high quality markdown based on the provided project prompt and document type."
    )
)

async def generate_document_content(doc_type: str, project_name: str, project_prompt: str) -> str:
    """Uses Pydantic AI to generate the markdown content for a specific document type."""
    prompt = (
        f"Generate a detailed '{doc_type}' document for the project '{project_name}'.\n"
        f"Project details: {project_prompt}\n"
        f"Output ONLY the raw markdown content without any XML wrappers or intros."
    )
    result = await document_agent.run(prompt)
    return result.data


async def generate_deck_html(project_name: str, project_prompt: str, theme: str = "dark") -> list[str]:
    """
    Placeholder for the actual HTML generation logic. 
    In a real system, this might call a specialized service or use a highly-tuned agent to build Reveal.js slides.
    For Phase 1 API layout, we return a structural array.
    """
    # For now, simulate a multi-slide response based on the project data
    return [
        f"<section><h1>{project_name}</h1><p>Created with Traction AI</p></section>",
        f"<section><h2>The Idea</h2><p>{project_prompt}</p></section>",
        f"<section><h2>Next Steps</h2><ul><li>Market Research</li><li>MVP Build</li></ul></section>"
    ]
