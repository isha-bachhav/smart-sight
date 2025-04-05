import requests
import trafilatura
import re
from bs4 import BeautifulSoup
import json
import random

def search_web(query):
    """
    Search the web for an answer to a query.
    
    Args:
        query (str): The search query
        
    Returns:
        str: The answer based on web search results
    """
    try:
        # Clean the query for search
        print(f"Searching the web for: {query}")
        clean_query = query.strip().replace(" ", "+")
        
        # Create random user agent to avoid blocking
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
        headers = {
            "User-Agent": random.choice(user_agents)
        }
        
        # Perform the search
        search_url = f"https://www.google.com/search?q={clean_query}"
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
            
        # Parse the search results
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for featured snippet first (Google's direct answer box)
        featured_snippet = soup.select('.V3FYCf') or soup.select('.hgKElc') or soup.select('.IZ6rdc')
        if featured_snippet:
            answer = featured_snippet[0].get_text().strip()
            return f"Based on what I found online: {answer}"
            
        # Try to get information from knowledge panel
        knowledge_panel = soup.select('.kno-rdesc span') or soup.select('.Ywxp6b')
        if knowledge_panel:
            answer = knowledge_panel[0].get_text().strip()
            return f"According to search results: {answer}"
            
        # Get search result URLs
        search_results = soup.select('.yuRUbf a') or soup.select('.DKV0Md')
        if not search_results:
            return None
            
        # Extract first few result URLs
        urls = []
        for result in search_results[:3]:
            href = result.get('href')
            if href and href.startswith('http'):
                urls.append(href)
                
        if not urls:
            return None
            
        # Visit the top result and extract content
        for url in urls:
            try:
                # Download content
                downloaded = trafilatura.fetch_url(url)
                if not downloaded:
                    continue
                    
                # Extract main text
                text = trafilatura.extract(downloaded)
                if not text or len(text) < 100:
                    continue
                    
                # Truncate to reasonable length
                text = text[:5000]
                
                # Extract relevant portions matching the query terms
                query_terms = query.lower().split()
                paragraphs = text.split('\n')
                
                relevant_paragraphs = []
                for paragraph in paragraphs:
                    if len(paragraph) > 50:  # Skip very short paragraphs
                        # Check if paragraph contains query terms
                        paragraph_lower = paragraph.lower()
                        term_count = sum(1 for term in query_terms if term in paragraph_lower)
                        if term_count > 0:
                            relevant_paragraphs.append((paragraph, term_count))
                
                # Sort by relevance (number of query terms)
                relevant_paragraphs.sort(key=lambda x: x[1], reverse=True)
                
                if relevant_paragraphs:
                    # Take top 2 most relevant paragraphs
                    answer_text = "\n".join([p[0] for p in relevant_paragraphs[:2]])
                    return f"Based on information I found online: {answer_text}"
                
            except Exception as e:
                print(f"Error processing URL {url}: {str(e)}")
                continue
        
        return None
        
    except Exception as e:
        print(f"Web search error: {str(e)}")
        return None