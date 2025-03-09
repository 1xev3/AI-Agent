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
from AI_Agent import BaseTool, ToolParameter, AI_Agent, AI_Client, AIMessageStorage

logger = logging.getLogger(__name__)

WHO_AM_I = """You are an internet search assistant.

For searching:
1. Search the internet using search_internet tool to find relevant pages
2. For each promising search result, use get_page_content tool to retrieve and analyze the actual content
3. Combine and analyze information from multiple sources to provide a comprehensive answer

Important:
- Always check page content with get_page_content tool for the most relevant results to ensure accuracy
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

                logger.debug(f"Search results: {results}")

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

    async def execute(self, url: str, max_chars: int = 10000) -> Dict:
        logger.info(f"Getting page content from: {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return {"success": False, "error": f"HTTP {response.status}"}
                    
                    html = await response.text()
                    
                    # Parse HTML and clean content
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove unwanted elements
                    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                        element.decompose()
                    
                    # Get clean text
                    text = ' '.join(soup.stripped_strings)
                    
                    # Truncate to max_chars
                    if len(text) > max_chars:
                        text = text[:max_chars] + "..."
                    
                    return {
                        "success": True,
                        "url": url,
                        "content": text,
                        "length": len(text)
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
            description="Query for the search. Write what you want: to search or to get page content"
        )
    ]
    returns = "Search results and analysis"

    def __init__(self, client: AI_Client):
        self.agent = AI_Agent(
            client=client,
            message_storage=AIMessageStorage(),
            who_am_i=WHO_AM_I
        )
        
        self.agent.register_tool(SearchInternetTool())
        self.agent.register_tool(GetPageContentTool())

    async def execute(self, request: str) -> str:
        logger.info(f"Running agent with request: {request}")
        result = await self.agent.run(request) 
        # logger.info(f"Agent result: { pformat(self.agent.message_storage.get_messages_as_dict())}")
        return result
