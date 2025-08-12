from pyexpat import model
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
        self.llm = ChatOpenAI(model="mistral", temperature=0.1)
        self.firecrawl = FirecrawlService()
        self.prompts = DeveloperToolsPrompts()
        self.workflow=self._build_workflow()

    def _build_workflow(self):
        pass

    #Stage 1: extract tools that may be candidates for research


