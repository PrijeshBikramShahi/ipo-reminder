from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
import requests

class BSToADConverter:
    """Converter for Bikram Sambat (BS) to Anno Domini (AD) dates"""
    
    BS_MONTHS = {
        'baisakh': 1, 'baishakh': 1, 'baisak': 1, 'baishak': 1,
        'jestha': 2, 'jeth': 2, 'jesth': 2,
        'ashadh': 3, 'asar': 3, 'ashad': 3, 'ashaar': 3,
        'shrawan': 4, 'shravan': 4, 'sawan': 4,
        'bhadra': 5, 'bhadau': 5,
        'ashwin': 6, 'ashoj': 6,
        'kartik': 7,
        'mangsir': 8, 'mangshir': 8,
        'poush': 9, 'paush': 9, 'push': 9,
        'magh': 10, 'maghe': 10,
        'falgun': 11, 'phalgun': 11,
        'chaitra': 12, 'chait': 12
    }
    
    BS_MONTH_DAYS = {
        2080: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2081: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2082: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2083: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2084: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2085: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2086: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
    }
    
    REFERENCE_BS = {'year': 2080, 'month': 1, 'day': 1}
    REFERENCE_AD = datetime(2023, 4, 14)
    
    def normalize_month_name(self, month_name: str) -> Optional[int]:
        return self.BS_MONTHS.get(month_name.lower().strip())
    
    def parse_bs_date(self, bs_date_str: str) -> Optional[Dict[str, int]]:
        pattern = r'(\d{1,2})\s+(\w+)\s+(\d{4})'
        match = re.search(pattern, bs_date_str, re.IGNORECASE)
        if not match:
            return None
        day, month_name, year = int(match.group(1)), match.group(2), int(match.group(3))
        month = self.normalize_month_name(month_name)
        if not month:
            return None
        return {'year': year, 'month': month, 'day': day}
    
    def bs_to_ad(self, bs_year: int, bs_month: int, bs_day: int) -> Optional[str]:
        if bs_year not in self.BS_MONTH_DAYS:
            return self._approximate_bs_to_ad(bs_year, bs_month, bs_day)
        if bs_month < 1 or bs_month > 12:
            return None
        if bs_day < 1 or bs_day > self.BS_MONTH_DAYS[bs_year][bs_month - 1]:
            return None
        days_diff = self._calculate_days_from_reference(bs_year, bs_month, bs_day)
        ad_date = self.REFERENCE_AD + timedelta(days=days_diff)
        return ad_date.strftime('%Y-%m-%d')
    
    # Internal helper methods (_calculate_days_from_reference, _calculate_days_backwards, _approximate_bs_to_ad)
    # and convert_bs_date_string as in the provided extended code


class MerolaganiScraper:
    """Scraper for fetching IPO data from Merolagani"""
    
    BASE_URL = "https://www.merolagani.com"
    IPO_URL = f"{BASE_URL}/Ipo.aspx?type=upcoming"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.bs_converter = BSToADConverter()
    
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
    
    def _convert_dates_to_ad(self, ipos_bs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        ipos_with_ad = []
        for ipo in ipos_bs:
            start_date_ad = self.bs_converter.convert_bs_date_string(ipo.get('startDateBS'))
            end_date_ad = self.bs_converter.convert_bs_date_string(ipo.get('endDateBS'))
            if start_date_ad and end_date_ad:
                ipos_with_ad.append({
                    'company': ipo['company'],
                    'startDateBS': ipo['startDateBS'],
                    'endDateBS': ipo['endDateBS'],
                    'startDateAD': start_date_ad,
                    'endDateAD': end_date_ad,
                    'rawText': ipo['rawText']
                })
            else:
                print(f"Warning: Could not convert dates for {ipo['company']}")
        return ipos_with_ad

    
    
    
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


