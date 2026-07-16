"""
CORE API Source
Fetches open access full texts from CORE (core.ac.uk).
"""

class CoreSource:
    name = "core"
    
    def __init__(self):
        pass
        
    async def search(self, query: str, max_results: int = 10, year_from=None, year_to=None):
        # TODO: Implement CORE API search
        return []
