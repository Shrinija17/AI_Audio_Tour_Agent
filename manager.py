from __future__ import annotations

import asyncio
from rich.console import Console

from agent import (
    History, Culture, Architecture, Culinary, Planner, FinalTour,
    run_architecture_agent, run_culinary_agent, run_culture_agent,
    run_history_agent, run_planner_agent, run_orchestrator_agent
)
from printer import Printer


class TourManager:
    """
    Orchestrates the full tour generation flow using Claude-powered agents.
    """

    def __init__(self) -> None:
        self.console = Console()
        self.printer = Printer(self.console)

    async def run(self, query: str, interests: list, duration: str) -> str:
        self.printer.update_item("start", "Starting tour research...", is_done=True)
        
        # Get plan based on selected interests
        planner = await self._get_plan(query, interests, duration)
        
        # Initialize research results
        research_results = {}
        
        # Calculate word limits based on duration
        # Assuming average speaking rate of 150 words per minute
        words_per_minute = 150
        total_words = int(duration) * words_per_minute
        words_per_section = total_words // len(interests)
        
        # Only research selected interests
        if "Architecture" in interests:
            research_results["architecture"] = await self._get_architecture(query, interests, words_per_section)
        
        if "History" in interests:
            research_results["history"] = await self._get_history(query, interests, words_per_section)
        
        if "Culinary" in interests:
            research_results["culinary"] = await self._get_culinary(query, interests, words_per_section)
        
        if "Culture" in interests:
            research_results["culture"] = await self._get_culture(query, interests, words_per_section)
        
        # Get final tour with only selected interests
        final_tour = await self._get_final_tour(
            query, 
            interests, 
            duration, 
            research_results
        )
        
        self.printer.update_item("final_report", "", is_done=True)
        self.printer.end()

        # Build final tour content based on selected interests
        sections = []
        
        # Add introduction
        if final_tour.introduction:
            sections.append(final_tour.introduction)
        
        # Add selected interest sections
        if "Architecture" in interests and final_tour.architecture:
            sections.append(final_tour.architecture)
        if "History" in interests and final_tour.history:
            sections.append(final_tour.history)
        if "Culture" in interests and final_tour.culture:
            sections.append(final_tour.culture)
        if "Culinary" in interests and final_tour.culinary:
            sections.append(final_tour.culinary)
        
        # Add conclusion
        if final_tour.conclusion:
            sections.append(final_tour.conclusion)
        
        # Format final tour with natural transitions
        final = "\n\n".join(sections)
        return final
        
    async def _get_plan(self, query: str, interests: list, duration: str) -> Planner:
        self.printer.update_item("Planner", "Planning your personalized tour...")
        result = await run_planner_agent(query, interests, duration)
        self.printer.update_item(
            "Planner",
            "Completed planning",
            is_done=True,
        )
        return result
    
    async def _get_history(self, query: str, interests: list, word_limit: int) -> History:
        self.printer.update_item("History", "Researching historical highlights...")
        result = await run_history_agent(query, interests, word_limit)
        self.printer.update_item(
            "History",
            "Completed history research",
            is_done=True,
        )
        return result

    async def _get_architecture(self, query: str, interests: list, word_limit: int) -> Architecture:
        self.printer.update_item("Architecture", "Exploring architectural wonders...")
        result = await run_architecture_agent(query, interests, word_limit)
        self.printer.update_item(
            "Architecture",
            "Completed architecture research",
            is_done=True,
        )
        return result
    
    async def _get_culinary(self, query: str, interests: list, word_limit: int) -> Culinary:
        self.printer.update_item("Culinary", "Discovering local flavors...")
        result = await run_culinary_agent(query, interests, word_limit)
        self.printer.update_item(
            "Culinary",
            "Completed culinary research",
            is_done=True,
        )
        return result
    
    async def _get_culture(self, query: str, interests: list, word_limit: int) -> Culture:
        self.printer.update_item("Culture", "Exploring cultural highlights...")
        result = await run_culture_agent(query, interests, word_limit)
        self.printer.update_item(
            "Culture",
            "Completed culture research",
            is_done=True,
        )
        return result
    
    async def _get_final_tour(self, query: str, interests: list, duration: float, research_results: dict) -> FinalTour:
        self.printer.update_item("Final Tour", "Creating your personalized tour...")
        result = await run_orchestrator_agent(query, interests, duration, research_results)
        self.printer.update_item(
            "Final Tour",
            "Completed Final Tour Guide Creation",
            is_done=True,
        )
        return result
