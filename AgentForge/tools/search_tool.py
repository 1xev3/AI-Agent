# Standard library imports
import logging
import asyncio
from typing import Dict, List, Optional
from urllib.parse import urlparse
from pprint import pformat

# Third party imports
from bs4 import BeautifulSoup
import aiohttp
from duckduckgo_search import DDGS

# Local imports
from AgentForge.core.tool_base import BaseTool, ToolParameter
from AgentForge.core.agent import Agent
from AgentForge.core.message_storage import MessageStorage

logger = logging.getLogger(__name__)

WHO_AM_I = """You are an internet search assistant.

For searching:
1. Search the internet using search_internet tool to find relevant pages
2. For each promising search result, use get_page_content tool to retrieve and analyze the actual content
3. Combine and analyze information from multiple sources to provide a comprehensive answer

Important:
- Always check page content with get_page_content tool
- Provide sources and quote relevant parts from the retrieved content
- If the content is not relevant, try another search result
- Try to ask in another way (reinvoke search_internet tool) if you can't find what you need
- If in the end nothing useful is found, return "Nothing useful found"

Always provide sources of information in your response."""

class SearchInternetTool(BaseTool):
    name = "search_internet"
    description = "Internet search tool" 
    parameters = [
        ToolParameter(
            name="query",
            type="string",
            description="Search query"
        )
    ]
    returns = """[{
"title",
"url",
"description"}]"""

    async def execute(self, query: str, max_results: int = 4) -> List[Dict]:
        logger.info(f"Searching internet for: {query}")
        try:
            # Create new DDGS instance with timeout and retries
            with DDGS() as ddgs:
                # Try using the regular search first
                try:
                    results = list(ddgs.text(query, max_results=max_results))
                except Exception as e:
                    logger.warning(f"Regular search failed, trying alternative method: {e}")
                    # Try alternative search method
                    results = list(ddgs.news(query, max_results=max_results))

                if not results:
                    logger.warning("No results found")
                    return []

                return [{
                    "title": result.get("title", "No title"),
                    "url": result.get("href", ""),
                    "description": result.get("body", "No description")
                } for result in results]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

class GetPageContentTool(BaseTool):
    name = "get_page_content"
    description = "Extracts clean text content from a webpage"
    parameters = [
        ToolParameter(
            name="url",
            type="string",
            description="URL of the webpage"
        )
    ]
    returns = "Cleaned text content from the webpage"

    def __init__(self, ai_summarize: bool = True):
        self.ai_summarize = ai_summarize

    def on_register(self, parent_agent: Agent):
        self.parent_agent = parent_agent

    async def execute(self, url: str, max_chars: int = 10000) -> Dict:
        logger.info(f"Getting page content from: {url}")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url, allow_redirects=True, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"HTTP {response.status}")
                        return {"success": False, "error": f"HTTP {response.status}"}
                    
                    html = await response.text()
                    
                    # Parse HTML and clean content
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove more unwanted elements
                    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'form', 'noscript', 'meta', 'link']):
                        element.decompose()
                    
                    # Remove elements with specific classes/ids that often contain ads or irrelevant content
                    for element in soup.find_all(class_=lambda x: x and any(word in str(x).lower() for word in ['ad', 'banner', 'popup', 'modal', 'cookie'])):
                        element.decompose()
                    
                    # Get clean text with better formatting
                    paragraphs = []
                    for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                        text = p.get_text().strip()
                        if text:
                            paragraphs.append(text)
                    
                    text = '\n'.join(paragraphs)
                    
                    # Truncate to max_chars
                    if len(text) > max_chars:
                        text = text[:max_chars] + "..."

                    if len(text) < 100:
                        logger.warning(f"Page content is too short.")
                        return {"success": True, "content": "Nothing useful found", "url": url}

                    summarized_text = text
                    if self.ai_summarize:
                        logger.info(f"Summarizing text with AI")
                        summarized_text = await self.parent_agent.client.generate_message([
                            {"role": "user", "content": f"Summarize the following text short and concise:\n{text}"}
                        ])
                    
                    return {
                        "success": True,
                        "url": url,
                        "content": summarized_text,
                        "length": len(summarized_text)
                    }
        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            return {"success": False, "error": str(e)}

class SearchAgentTool(BaseTool):
    name = "search_agent"
    description = "Intelligent internet search assistant"
    parameters = [
        ToolParameter(
            name="request",
            type="string",
            description="Query for the search. Write what you want: to search or to get page content. Better to write in English."
        )
    ]
    returns = "Search results and analysis"

    def on_register(self, parent_agent: Agent):
        self.parent_agent = parent_agent
        client = self.parent_agent.client
        self.agent = Agent(
            client=client,
            message_storage=MessageStorage(),
            who_am_i=WHO_AM_I,
            tools=[
                SearchInternetTool(), 
                GetPageContentTool()
            ]
        )

    async def execute(self, request: str) -> str:
        logger.info(f"Running agent with request: {request}")
        result = await self.agent.run(request) 
        # logger.info(f"Agent result: { pformat(self.agent.message_storage.get_messages_as_dict())}")
        return result
