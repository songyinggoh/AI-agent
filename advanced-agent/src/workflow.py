from pyexpat import model
from typing import Dict, Any
from langgraph.graph import StateGraph,END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from .models import ResearchState, CompanyAnalysis, CompanyInfo
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
        #search results are URLs of websites
        search_results=self.firecrawl.search_companies(article_query,num_results=3)
        
        all_content=""
        #gets search results from search_results@line26
        for result in search_results.data:
            #takes URLs
            url=result.get("url","")
            #scrape URLs
            scraped=self.firecrawl.scrape_company_pages(url)
            if scraped:
                all_content+=scraped.markdown[:1500]+"\n\n"

        messages=[
            SystemMessage(content=self.prompts.TOOL_EXTRACTION_SYSTEM),
            HumanMessage(content=self.prompts.tool_extraction_user(state.query,all_content))

        ]

        try:
            response=self.llm.invoke(messages)
            tool_names=[
                name.strip()
                for name in response.content.strip().split("\n")
                if name.strip()
            ]
            print(f"Extracted tools:{', '.join(tool_names[:5])}")
            return {"extracted_tools":tool_names}

    #Stage 2: research the extracted tools

    #Stage 3: analyze the researched tools



