from datetime import datetime
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
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
    
    def _parse_table_structure(self, table) -> List[Dict[str, str]]:
        ipos = []
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if not cells or all(cell.find('th') or cell.name == 'th' for cell in cells):
                continue
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            ipo_data = self._extract_ipo_info(cell_texts, row)
            if ipo_data:
                ipos.append(ipo_data)
        return ipos
    
    def _parse_div_structure(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        ipos = []
        ipo_divs = soup.find_all('div', class_=re.compile('ipo|card|item', re.I))
        for div in ipo_divs:
            text_content = div.get_text(strip=True)
            if len(text_content) < 20:
                continue
            ipo_data = self._extract_ipo_info([text_content], div)
            if ipo_data:
                ipos.append(ipo_data)
        return ipos
    
    def _extract_ipo_info(self, texts: List[str], element) -> Optional[Dict[str, str]]:
        company_name = None
        start_date_bs = None
        end_date_bs = None
        raw_text = ' '.join(texts)
        # Heuristic for company name
        for text in texts:
            if not company_name and len(text) > 3:
                if any(k in text for k in ['Ltd', 'Limited', 'Bank', 'Finance', 'Insurance', 'Power', 'Hydro', 'Development']):
                    company_name = text
                    break
                elif len(text) > 10 and not re.search(r'\d{1,2}\s+\w+\s+\d{4}', text):
                    company_name = text
        if not company_name:
            for text in texts:
                if len(text) > 5 and not re.search(r'\d{1,2}\s+\w+\s+\d{4}', text):
                    company_name = text
                    break
        # Date patterns
        date_patterns = [
            r'(\d{1,2})\s+(\w+)\s+(\d{4})\s+(?:to|-)\s+(\d{1,2})\s+(\w+)\s+(\d{4})',
            r'(?:from\s+)?(\d{1,2})\s+(\w+)\s+(\d{4})\s+(?:to|–|—)\s+(\d{1,2})\s+(\w+)\s+(\d{4})',
        ]
        for text in texts:
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    start_date_bs = f"{match.group(1)} {match.group(2)} {match.group(3)}"
                    end_date_bs = f"{match.group(4)} {match.group(5)} {match.group(6)}"
                    break
            if start_date_bs and end_date_bs:
                break
        if company_name:
            return {
                'company': company_name.strip(),
                'startDateBS': start_date_bs.strip() if start_date_bs else '',
                'endDateBS': end_date_bs.strip() if end_date_bs else '',
                'rawText': raw_text.strip()
            }
        return None

    def _parse_date(self, date_str: str) -> str:
        """Parse Nepali BS date to ISO format (placeholder)"""
        return datetime.now().strftime("%Y-%m-%d")

    def convert_bs_to_ad(self, bs_date: str) -> str:
        """Convert BS date to AD (placeholder)"""
        return self._parse_date(bs_date)
    
    
    
def scrape_and_update_db():
    print("=== IPO Scraper Started ===")
    scraper = MerolaganiScraper()
    ipos = scraper.fetch_upcoming_ipos()
    if not ipos:
        print("No IPO data found or error occurred")
        return
    print(f"\n=== Scraped {len(ipos)} IPOs ===")
    for i, ipo in enumerate(ipos, 1):
        print(f"\n{i}. {ipo['company']}")
        print(f"   Start: {ipo['startDateBS']}")
        print(f"   End: {ipo['endDateBS']}")
        print(f"   Raw: {ipo['rawText'][:100]}...")
    print("\n=== Scraper Completed ===")

if __name__ == "__main__":
    scrape_and_update_db()


