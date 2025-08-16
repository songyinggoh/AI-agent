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

    #WorkflowStage 1: extract prospective tools
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
        except Exception as e:
            print(f"Error in extract_tools_step: {e}")
            return {"extracted_tools":[]}

    #Workflow Stage 2: research the extracted tools
    def _analyze_company_content(self,company_name: str, content: str) -> CompanyAnalysis:
        structured_llm=self.llm.with_structured_output(CompanyAnalysis)
        messages=[
            SystemMessage(content=self.prompts.TOOL_ANALYSIS_SYSTEM),
            HumanMessage(content=self.prompts.tool_analysis_user(company_name,content))
        ]
        try:
            analysis=structured_llm.invoke(messages)
            return analysis
        except Exception as e:
            print(e)
            return CompanyAnalysis(
                pricing_model="Unknown",
                is_open_source=None,
                tech_stack=[],
                description="No description available",
                api_available=None,
                language_support=[],
                integration_capabilities=[],
            )
    
    def _research_step(self,state:ResearchState) -> Dict[str,Any]:
        extracted_tools=getattr(state,"extracted_tools",[])

        if not extracted_tools:
            print("No extracted tools found, executing direct search")
            search_results=self.firecrawl.search_companies(state.query,num_results=4)
            tool_names=[
                result.get("metadata",{}).get("title","Unknown")
                for result in search_results.data

            ]
        else:
            tool_names=extracted_tools[:4]
        print(f"Researching tools: {', '.join(tool_names)}")









    #Workflow Stage 3: analyze the researched tools



