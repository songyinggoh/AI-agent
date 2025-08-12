from typing import Dict, Any
from langgraph.graph import StateGraph,END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from .models import ResearchState, CompanyAnalysis, CompanyAnalysis
from .firecrawl import FirecrawlService
from .prompts import DeveloperToolsPrompts


class Workflow:
    def __init__(self):
        self.graph = StateGraph(ResearchState)
        self.llm = ChatOpenAI(temperature=0.7)
        self.firecrawl = FirecrawlService()
        self.prompts = DeveloperToolsPrompts()
