from __future__ import annotations

import asyncio
import time
from collections.abc import Sequence

from rich.console import Console

from agents import Runner, RunResult, custom_span, gen_trace_id, trace

from .agents.financials_agent import financials_agent
from .agents.planner_agent import FinancialSearchItem, FinancialSearchPlan, planner_agent
from .agents.risk_agent import risk_agent
from .agents.search_agent import search_agent
from .agents.verifier_agent import VerificationResult, verifier_agent
from .agents.writer_agent import FinancialReportData, writer_agent
from .printer import Printer


async def _summary_extractor(run_result: RunResult) -> str:
    """Custom output extractor for sub‑agents that return an AnalysisSummary."""
    # The financial/risk analyst agents emit an AnalysisSummary with a `summary` field.
    # We want the tool call to return just that summary text so the writer can drop it inline.
    return str(run_result.final_output.summary)


class FinancialResearchManager:
    """
    Orchestrates the full flow: planning, searching, sub‑analysis, writing, and verification.
    """

    def __init__(self, callback=None) -> None:
        self.console = Console()
        self.printer = Printer(self.console)
        self.callback = callback

    def _log(self, agent_name, action, details):
        """Helper to log agent actions if callback is present."""
        if self.callback and hasattr(self.callback, 'log_agent_action'):
            self.callback.log_agent_action(agent_name, action, details)

    async def run(self, query: str) -> None:
        trace_id = gen_trace_id()
        with trace("Financial research trace", trace_id=trace_id):
            self.printer.update_item(
                "trace_id",
                f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}",
                is_done=True,
                hide_checkmark=True,
            )
            self.printer.update_item("start", "Starting financial research...", is_done=True)
            search_plan = await self._plan_searches(query)
            search_results = await self._perform_searches(search_plan)
            report = await self._write_report(query, search_results)
            verification = await self._verify_report(report)

            final_report = f"Report summary\n\n{report.short_summary}"
            self.printer.update_item("final_report", final_report, is_done=True)

            self.printer.end()

        # Print to stdout
        print("\n\n=====REPORT=====\n\n")
        print(f"Report:\n{report.markdown_report}")
        print("\n\n=====FOLLOW UP QUESTIONS=====\n\n")
        print("\n".join(report.follow_up_questions))
        print("\n\n=====VERIFICATION=====\n\n")
        print(verification)

    async def _plan_searches(self, query: str) -> FinancialSearchPlan:
        self.printer.update_item("planning", "Planning searches...")
        self._log("Planner", "Analyzing query", query)
        
        result = await Runner.run(planner_agent, f"Query: {query}")
        
        plan = result.final_output_as(FinancialSearchPlan)
        self._log("Planner", "Generated search plan", f"Created {len(plan.searches)} search queries")
        for item in plan.searches:
            self._log("Planner", "New search query", f"Query: {item.query}\nReason: {item.reason}")
            
        self.printer.update_item(
            "planning",
            f"Will perform {len(plan.searches)} searches",
            is_done=True,
        )
        return plan

    async def _perform_searches(self, search_plan: FinancialSearchPlan) -> Sequence[str]:
        with custom_span("Search the web"):
            self.printer.update_item("searching", "Searching...")
            tasks = [asyncio.create_task(self._search(item)) for item in search_plan.searches]
            results: list[str] = []
            num_completed = 0
            for task in asyncio.as_completed(tasks):
                result = await task
                if result is not None:
                    results.append(result)
                num_completed += 1
                self.printer.update_item(
                    "searching", f"Searching... {num_completed}/{len(tasks)} completed"
                )
            self.printer.mark_item_done("searching")
            return results

    async def _search(self, item: FinancialSearchItem) -> str | None:
        input_data = f"Search term: {item.query}\nReason: {item.reason}"
        self._log("Search", "Executing search", f"Query: {item.query}")
        try:
            result = await Runner.run(search_agent, input_data)
            output = str(result.final_output)
            self._log("Search", "Search completed", f"Found results for: {item.query}")
            return output
        except Exception as e:
            self._log("Search", "Search failed", f"Error: {str(e)}")
            return None

    async def _write_report(self, query: str, search_results: Sequence[str]) -> FinancialReportData:
        # Expose the specialist analysts as tools so the writer can invoke them inline
        # and still produce the final FinancialReportData output.
        fundamentals_tool = financials_agent.as_tool(
            tool_name="fundamentals_analysis",
            tool_description="Use to get a short write‑up of key financial metrics",
            custom_output_extractor=_summary_extractor,
        )
        risk_tool = risk_agent.as_tool(
            tool_name="risk_analysis",
            tool_description="Use to get a short write‑up of potential red flags",
            custom_output_extractor=_summary_extractor,
        )
        writer_with_tools = writer_agent.clone(tools=[fundamentals_tool, risk_tool])
        self.printer.update_item("writing", "Thinking about report...")
        self._log("Writer", "Starting report generation", "Synthesizing search results...")
        
        input_data = f"Original query: {query}\nSummarized search results: {search_results}"
        result = Runner.run_streamed(writer_with_tools, input_data)
        update_messages = [
            "Planning report structure...",
            "Writing sections...",
            "Finalizing report...",
        ]
        last_update = time.time()
        next_message = 0
        async for _ in result.stream_events():
            if time.time() - last_update > 5 and next_message < len(update_messages):
                self.printer.update_item("writing", update_messages[next_message])
                self._log("Writer", "Progress update", update_messages[next_message])
                next_message += 1
                last_update = time.time()
        self.printer.mark_item_done("writing")
        return result.final_output_as(FinancialReportData)

    async def _verify_report(self, report: FinancialReportData) -> VerificationResult:
        self.printer.update_item("verifying", "Verifying report...")
        self._log("Verifier", "Starting verification", "Checking report for accuracy and consistency")
        
        result = await Runner.run(verifier_agent, report.markdown_report)
        verification = result.final_output_as(VerificationResult)
        
        self._log("Verifier", "Verification complete", f"Verified: {verification.verified}\nIssues: {verification.issues}")
        self.printer.mark_item_done("verifying")
        return verification
