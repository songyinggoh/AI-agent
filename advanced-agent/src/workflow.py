from pyexpat import model
from typing import Dict, Any
from langgraph.graph import StateGraph,END
from langchain_ollama.llms import OllamaLLM
from langchain_core.messages import HumanMessage, SystemMessage
from .models import ResearchState, CompanyAnalysis, CompanyInfo
from .firecrawl import FirecrawlService
from .prompts import DeveloperToolsPrompts


class Workflow:
    def __init__(self):
        self.graph = StateGraph(ResearchState)
        self.llm = OllamaLLM(model="mistral", temperature=0.1)
        self.firecrawl = FirecrawlService()
        self.prompts = DeveloperToolsPrompts()
        self.workflow=self._build_workflow()

    def _build_workflow(self):
        graph=StateGraph(ResearchState)
        graph.add_node("extract_tools",self.extract_tools_step)
        graph.add_node("research",self._research_step)
        graph.add_node("analyze",self._analyze_step)
        graph.set_entry_point("extract_tools")
        graph.add_edge("extract_tools","research")
        graph.add_edge("research","analyze")
        graph.add_edge("analyze",END)
        return graph.compile()

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
        ##Tool Identification

        #get extracted tools from state object
        extracted_tools=getattr(state,"extracted_tools",[])
        #If extracted_tools is empty,  
        if not extracted_tools:
            print("No extracted tools found, executing direct search")
            #it executes a direct search using self.firecrawl.search_companies
            #with state.query.
            #retrieves up to four search results
            search_results=self.firecrawl.search_companies(state.query,num_results=4)
            #and uses their titles as the tool names.
            tool_names=[
                result.get("metadata",{}).get("title","Unknown")
                for result in search_results.data

            ]
        else:
            tool_names=extracted_tools[:4]
        print(f"Researching tools: {', '.join(tool_names)}")

        ##Company Research and Analysis
        companies=[]
        #iterations through tool_names
        for tool_name in tool_names:
            #For each tool name, it performs a more specific search for its "official site" 
            tool_search_results=self.firecrawl.search_companies(tool_name+" official site", num_results=1)
            #If the search results are not empty, it extracts the first result.
            if tool_search_results:
                result=tool_search_results.data[0]
                url=result.get("url","")
                #extracts the URL, name, and description to create a CompanyInfo object.
                company=CompanyInfo(
                    name=tool_name,
                    description=result.get("markdown",""),
                    website=url,
                    tech_stack=[],
                    competitors=[],
                )
                #scrapes content of found URL
                scraped=self.firecrawl.scrape_company_pages(url)
                #if the scraping is successful, 
                #it passes the scraped markdown content to another internal method, 
                #self._analyze_company_content, for further analysis.
                if scraped:
                    content=scraped.markdown
                    analysis=self._analyze_company_content(company.name, content)

                    company.pricing_model=analysis.pricing_model
                    company.is_open_source=analysis.is_open_source
                    company.tech_stack=analysis.tech_stack
                    company.description=analysis.description
                    company.api_available=analysis.api_available
                    company.language_support=analysis.language_support
                    company.integration_capabilities=analysis.integration_capabilities

                companies.append(company)
            
            return {"companies":companies}


    #Workflow Stage 3: analyze the researched tools

    def _analyze_step(self, state: ResearchState) -> Dict[str, Any]:
        print("Generating recommendations")

        company_data=" ".join([
            company.json() for company in state.companies
        ])

        messages=[
            SystemMessage(content=self.prompts.RECOMMENDATIONS_SYSTEM),
            HumanMessage(content=self.prompts.recommendations_user(state.query,company_data))
        ]

        response=self.llm.invoke(messages)
        return {"analysis":response.content}


    def run(self, query:str) -> ResearchState:
        initial_state=ResearchState(query=query)
        final_state=self.workflow.invoke(initial_state)
        return ResearchState(**final_state)
