from duckduckgo_search import DDGS

def search_web(query, max_results=3):
    try:
        with DDGS() as ddgs:
            return [r for r in ddgs.text(query, max_results=max_results)]
    except Exception as e:
        return f"Search failed: {str(e)}"
