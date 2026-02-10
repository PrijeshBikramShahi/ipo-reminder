from datetime import datetime
from bs4 import BeautifulSoup
import re
from typing import List, Dict
import requests

class MerolaganiScraper:
    """Scraper for fetching IPO data from Merolagani"""
    
    BASE_URL = "https://www.merolagani.com"
    IPO_URL = f"{BASE_URL}/Ipo.aspx?type=upcoming"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def fetch_upcoming_ipos(self) -> List[Dict[str, str]]:
        """
        Fetch upcoming IPO listings from Merolagani
        """
        try:
            print(f"Fetching IPOs from {self.IPO_URL}...")
            response = self.session.get(self.IPO_URL, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            ipos = self._parse_ipo_entries(soup)
            print(f"Found {len(ipos)} IPO entries")
            return ipos
        except requests.RequestException as e:
            print(f"Error fetching IPO data: {e}")
            return []
        except Exception as e:
            print(f"Error parsing IPO data: {e}")
            return []
    
    def _parse_ipo_entries(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parse IPO entries from the BeautifulSoup object"""
        ipos = []
        ipo_table = soup.find('table', {'class': 'table'})
        if not ipo_table:
            ipo_table = soup.find('table', id=re.compile('ipo', re.I))
        if not ipo_table:
            for table in soup.find_all('table'):
                if 'ipo' in table.get_text().lower() or 'company' in table.get_text().lower():
                    ipo_table = table
                    break
        if ipo_table:
            ipos = self._parse_table_structure(ipo_table)
        if not ipos:
            ipos = self._parse_div_structure(soup)
        return ipos

def _parse_date(self, date_str: str) -> str:
        """Convert date string to ISO format (stub)"""
        return datetime.now().strftime("%Y-%m-%d")
    
def scrape_and_update_db():
    """
    Placeholder for scraping IPOs and updating database
    """
    print("Scrape and update task triggered... (not implemented)")


if __name__ == "__main__":
    scraper = MerolaganiScraper()
    ipos = scraper.fetch_upcoming_ipos()
    print(f"Found {len(ipos)} IPOs")


