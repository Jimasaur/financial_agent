from typing import Optional, List
from pydantic import BaseModel

from agents import Agent
from agents import WebSearchTool
from agents.model_settings import ModelSettings

# Agent to sanity‑check a synthesized report for consistency and recall.
# This can be used to flag potential gaps or obvious mistakes.
VERIFIER_PROMPT = (
    "You are a meticulous fact-checker and auditor. Given a financial report, "
    "verify the most critical claims by searching the web for supporting evidence. "
    "To be efficient, you must:"
    "1) Prioritize high-stakes numbers (revenue, EPS, growth rates) and recent news."
    "2) Batch your searches to check multiple facts in a single query where possible."
    "3) Flag anything unsupported or contradictory."
    "Do not verify every single minor detail. Focus on the core thesis and key metrics."
)

class FactCheck(BaseModel):
    claim: str
    verified: bool
    evidence: str
    source_url: Optional[str] = None

class VerificationResult(BaseModel):
    verified: bool
    """Whether the report seems coherent and plausible."""

    issues: str
    """If not verified, describe the main issues or concerns."""
    
    fact_checks: List[FactCheck] = []
    """List of specific claims checked."""


verifier_agent = Agent(
    name="VerificationAgent",
    instructions=VERIFIER_PROMPT,
    model="gpt-5-pro-2025-10-06",
    output_type=VerificationResult,
    tools=[WebSearchTool()],
    model_settings=ModelSettings(tool_choice="auto")
)
