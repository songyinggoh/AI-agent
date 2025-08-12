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

    #Stage 1: extract tools that may be candidates for 
    def extract_tools_step(self, state: ResearchState) -> ResearchState:
        print(f"Finding articles about: {state.query}")
        article_query=f"{state.query} tools comparison best alternatives"
        search_results=self.firecrawl.search_companies(article_query,num_results=3)
        
        all_content=""
        for result in search_results.data:
            url=result.get("url","")
            scraped=self.firecrawl.scrape_company_pages(url)
            if scraped:
                all_content+=scraped.markdown[:1500]+"\n\n"



    #Stage 2: research the extracted tools

    #Stage 3: analyze the researched tools



