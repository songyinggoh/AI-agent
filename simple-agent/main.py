from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_community.chat_models import ChatOllama
from dotenv import load_dotenv
import asyncio
import os

#loads environment variable file
load_dotenv()

model = ChatOllama(
    model="mistral",
    temperature=0,
)

#define server parameters for connecting to MCP tool server
server_params = StdioServerParameters(
    command="npx",
    env={
        "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY"),
    },
    args=["firecrawl-mcp"]
)

async def main():
    #connects to MCP client running on local computer
    async with stdio_client(server_params) as (read,write):
        #creates new session
        async with ClientSession(read,write) as session:
            #initializes new session
            await session.initialize()
            #loads tools
            tools = await load_mcp_tools(session)
            #creates agent
            agent = create_react_agent(model, tools)
            #setting up messages
            messages=[
                {
                    "role":"system",
                    "content":"You are a helpful assistant that can use the Firecrawl API to scrape websites, crawl pages, and extract data using Firecrawl tools. Think step by step and use the appropriate tools to help the user."

                }
            ]
            print("Available-Tools -",*[tool.name for tool in tools])
            print("-"*60)

            while True:
                user_input = input("Enter your query (type 'quit' to exit): ")
                if user_input == "quit":
                    print("Goodbye")
                    break
                
                messages.append({"role":"user","content":user_input[:10000]})

                try:
                    #allows the agent to utilize all of the tools and the LLM
                    agent_response=await agent.ainvoke({"messages":messages})

                    ai_message=agent_response["messages"][-1]["content"]
                    print("\nAgent:", ai_message)

                except Exception as e:
                    print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())


