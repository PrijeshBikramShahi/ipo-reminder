from typing import List, Dict
import requests

class MerolaganiScraper:
    """Scraper for IPO data (stub)"""
    
    BASE_URL = "https://merolagani.com"
    IPO_URL = f"{BASE_URL}/Ipo.aspx"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    def fetch_upcoming_ipos(self) -> List[Dict[str, str]]:
        """Placeholder for fetching IPOs"""
        print("Fetching IPOs... (not implemented)")
        return []
