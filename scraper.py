from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta


class BSToADConverter:
    """
    Converter for Bikram Sambat (BS) to Anno Domini (AD) dates
    Uses a lookup table for BS to AD conversion
    """
    
    # BS month names (Nepali calendar months)
    BS_MONTHS = {
        'baisakh': 1, 'baishakh': 1,
        'jestha': 2, 'jeth': 2,
        'ashadh': 3, 'asar': 3, 'ashad': 3,
        'shrawan': 4, 'shravan': 4, 'sawan': 4,
        'bhadra': 5, 'bhadau': 5,
        'ashwin': 6, 'ashoj': 6,
        'kartik': 7, 'kartik': 7,
        'mangsir': 8, 'mangshir': 8,
        'poush': 9, 'paush': 9, 'push': 9,
        'magh': 10, 'maghe': 10,
        'falgun': 11, 'phalgun': 11,
        'chaitra': 12, 'chait': 12
    }
    
    # Days in each BS month for common years (2080-2085)
    # Format: {year: [days_in_each_month]}
    BS_MONTH_DAYS = {
        2080: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2081: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2082: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2083: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2084: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2085: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2086: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
    }
    
    # Reference point: BS 2080/1/1 = AD 2023/4/14
    REFERENCE_BS = {'year': 2080, 'month': 1, 'day': 1}
    REFERENCE_AD = datetime(2023, 4, 14)
    
    def normalize_month_name(self, month_name: str) -> Optional[int]:
        """
        Normalize BS month name to month number (1-12)
        
        Args:
            month_name: BS month name (e.g., "Magh", "Falgun")
        
        Returns:
            Month number (1-12) or None if not recognized
        """
        month_lower = month_name.lower().strip()
        return self.BS_MONTHS.get(month_lower)
    
    def parse_bs_date(self, bs_date_str: str) -> Optional[Dict[str, int]]:
        """
        Parse BS date string into components
        
        Args:
            bs_date_str: BS date string (e.g., "28 Magh 2081")
        
        Returns:
            Dictionary with 'year', 'month', 'day' or None if parsing fails
        """
        if not bs_date_str:
            return None
        
        # Pattern: day month year
        pattern = r'(\d{1,2})\s+(\w+)\s+(\d{4})'
        match = re.search(pattern, bs_date_str, re.IGNORECASE)
        
        if not match:
            return None
        
        day = int(match.group(1))
        month_name = match.group(2)
        year = int(match.group(3))
        
        month = self.normalize_month_name(month_name)
        
        if not month:
            return None
        
        return {'year': year, 'month': month, 'day': day}
    
    def bs_to_ad(self, bs_year: int, bs_month: int, bs_day: int) -> Optional[str]:
        """
        Convert BS date to AD date using lookup table and calculation
        
        Args:
            bs_year: BS year
            bs_month: BS month (1-12)
            bs_day: BS day
        
        Returns:
            AD date in ISO format (YYYY-MM-DD) or None if conversion fails
        """
        try:
            # Validate inputs
            if bs_year not in self.BS_MONTH_DAYS:
                # For years outside our lookup table, use approximation
                return self._approximate_bs_to_ad(bs_year, bs_month, bs_day)
            
            if bs_month < 1 or bs_month > 12:
                return None
            
            # Validate day is within month range
            if bs_day < 1 or bs_day > self.BS_MONTH_DAYS[bs_year][bs_month - 1]:
                return None
            
            # Calculate days from reference point
            days_diff = self._calculate_days_from_reference(bs_year, bs_month, bs_day)
            
            # Add to reference AD date
            ad_date = self.REFERENCE_AD + timedelta(days=days_diff)
            
            return ad_date.strftime('%Y-%m-%d')
            
        except Exception as e:
            print(f"Error converting BS to AD ({bs_year}/{bs_month}/{bs_day}): {e}")
            return None
    
    def _calculate_days_from_reference(self, bs_year: int, bs_month: int, bs_day: int) -> int:
        """
        Calculate number of days from reference BS date
        
        Args:
            bs_year: Target BS year
            bs_month: Target BS month
            bs_day: Target BS day
        
        Returns:
            Number of days from reference point
        """
        days = 0
        ref_year = self.REFERENCE_BS['year']
        ref_month = self.REFERENCE_BS['month']
        ref_day = self.REFERENCE_BS['day']
        
        # If target date is before reference, calculate backwards
        if bs_year < ref_year or (bs_year == ref_year and bs_month < ref_month):
            return -self._calculate_days_backwards(bs_year, bs_month, bs_day)
        
        # Calculate forward from reference date
        # First, complete the reference year if needed
        if bs_year == ref_year:
            # Same year
            for m in range(ref_month, bs_month):
                days += self.BS_MONTH_DAYS[bs_year][m - 1]
            days += bs_day - ref_day
        else:
            # Different years
            # Complete reference year
            for m in range(ref_month, 13):
                days += self.BS_MONTH_DAYS[ref_year][m - 1]
            days -= ref_day - 1  # Subtract remaining days in ref month
            
            # Add complete years in between
            for y in range(ref_year + 1, bs_year):
                if y in self.BS_MONTH_DAYS:
                    days += sum(self.BS_MONTH_DAYS[y])
                else:
                    days += 365  # Approximate
            
            # Add months in target year
            for m in range(1, bs_month):
                days += self.BS_MONTH_DAYS[bs_year][m - 1]
            
            # Add days in target month
            days += bs_day
        
        return days
    
    def _calculate_days_backwards(self, bs_year: int, bs_month: int, bs_day: int) -> int:
        """Calculate days backwards from reference point"""
        days = 0
        ref_year = self.REFERENCE_BS['year']
        ref_month = self.REFERENCE_BS['month']
        ref_day = self.REFERENCE_BS['day']
        
        # Calculate from target to reference
        if bs_year == ref_year:
            for m in range(bs_month, ref_month):
                days += self.BS_MONTH_DAYS[bs_year][m - 1]
            days += ref_day - bs_day
        else:
            # Add remaining days in target month
            days += self.BS_MONTH_DAYS[bs_year][bs_month - 1] - bs_day
            
            # Add complete months in target year
            for m in range(bs_month + 1, 13):
                days += self.BS_MONTH_DAYS[bs_year][m - 1]
            
            # Add complete years
            for y in range(bs_year + 1, ref_year):
                if y in self.BS_MONTH_DAYS:
                    days += sum(self.BS_MONTH_DAYS[y])
                else:
                    days += 365
            
            # Add months in reference year
            for m in range(1, ref_month):
                days += self.BS_MONTH_DAYS[ref_year][m - 1]
            
            # Add days in reference month
            days += ref_day
        
        return days
    
    def _approximate_bs_to_ad(self, bs_year: int, bs_month: int, bs_day: int) -> str:
        """
        Approximate BS to AD conversion for years outside lookup table
        BS year - 56/57 ≈ AD year (varies by month)
        """
        # Rough approximation: BS - 56.7 = AD
        ad_year = bs_year - 57
        
        # Approximate month mapping (BS year starts around April)
        # Months 1-3 (Baisakh-Ashadh) map to April-June
        # Months 4-6 (Shrawan-Ashwin) map to July-September
        # Months 7-9 (Kartik-Poush) map to October-December
        # Months 10-12 (Magh-Chaitra) map to January-March (next AD year)
        
        if bs_month >= 10:
            ad_year += 1
            ad_month = bs_month - 9
        else:
            ad_month = bs_month + 3
        
        # Clamp day to valid range
        ad_day = min(bs_day, 28)  # Conservative to avoid invalid dates
        
        try:
            ad_date = datetime(ad_year, ad_month, ad_day)
            return ad_date.strftime('%Y-%m-%d')
        except:
            return datetime(ad_year, ad_month, 1).strftime('%Y-%m-%d')
    
    def convert_bs_date_string(self, bs_date_str: str) -> Optional[str]:
        """
        Convert BS date string directly to AD ISO format
        
        Args:
            bs_date_str: BS date string (e.g., "28 Magh 2081")
        
        Returns:
            AD date in ISO format or None
        """
        parsed = self.parse_bs_date(bs_date_str)
        if not parsed:
            return None
        
        return self.bs_to_ad(parsed['year'], parsed['month'], parsed['day'])


class MerolaganiScraper:
    """
    Scraper for fetching IPO data from Merolagani
    """
    
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
        
        Returns:
            List of IPO dictionaries with company, dates (BS and AD), and rawText
        """
        try:
            print(f"Fetching IPOs from {self.IPO_URL}...")
            response = self.session.get(self.IPO_URL, timeout=10)
            response.raise_for_status()
            
            print(f"Response status: {response.status_code}")
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract IPO entries with BS dates
            ipos_bs = self._parse_ipo_entries(soup)
            
            # Convert BS dates to AD dates
            ipos_with_ad = self._convert_dates_to_ad(ipos_bs)
            
            print(f"Found {len(ipos_with_ad)} IPO entries with valid dates")
            return ipos_with_ad
            
        except requests.RequestException as e:
            print(f"Error fetching IPO data: {e}")
            return []
        except Exception as e:
            print(f"Error parsing IPO data: {e}")
            return []
    
    def _parse_ipo_entries(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Parse IPO entries from the BeautifulSoup object
        
        Args:
            soup: BeautifulSoup object of the IPO page
        
        Returns:
            List of parsed IPO dictionaries with BS dates
        """
        ipos = []
        
        # Merolagani typically uses a table structure for IPO listings
        ipo_table = soup.find('table', {'class': 'table'})
        
        if not ipo_table:
            ipo_table = soup.find('table', id=re.compile('ipo', re.I))
        
        if not ipo_table:
            tables = soup.find_all('table')
            for table in tables:
                table_text = table.get_text().lower()
                if 'ipo' in table_text or 'company' in table_text:
                    ipo_table = table
                    break
        
        if ipo_table:
            ipos = self._parse_table_structure(ipo_table)
        
        # Fallback: Look for div-based structure
        if not ipos:
            ipos = self._parse_div_structure(soup)
        
        return ipos
    
    def _parse_table_structure(self, table) -> List[Dict[str, str]]:
        """Parse IPO data from table structure"""
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
        """Parse IPO data from div-based structure"""
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
        """Extract IPO information from text content"""
        company_name = None
        start_date_bs = None
        end_date_bs = None
        raw_text = ' '.join(texts)
        
        # Extract company name
        for text in texts:
            if not company_name and len(text) > 3:
                if any(keyword in text for keyword in ['Ltd', 'Limited', 'Bank', 'Finance', 'Insurance', 'Power', 'Hydro', 'Development', 'Company']):
                    company_name = text
                    break
                elif len(text) > 10 and not re.search(r'\d{1,2}\s+\w+\s+\d{4}', text):
                    company_name = text
        
        if not company_name:
            for text in texts:
                if len(text) > 5 and not re.search(r'\d{1,2}\s+\w+\s+\d{4}', text):
                    company_name = text
                    break
        
        # Extract date range
        date_patterns = [
            r'(\d{1,2})\s+(\w+)\s+(\d{4})\s+(?:to|-|–|—)\s+(\d{1,2})\s+(\w+)\s+(\d{4})',
            r'(?:from\s+)?(\d{1,2})\s+(\w+)\s+(\d{4})\s+(?:to|–|—)\s+(\d{1,2})\s+(\w+)\s+(\d{4})',
        ]
        
        for text in texts:
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    start_day = match.group(1)
                    start_month = match.group(2)
                    start_year = match.group(3)
                    
                    end_day = match.group(4)
                    end_month = match.group(5)
                    end_year = match.group(6)
                    
                    start_date_bs = f"{start_day} {start_month} {start_year}"
                    end_date_bs = f"{end_day} {end_month} {end_year}"
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
    
    def _convert_dates_to_ad(self, ipos_bs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Convert BS dates to AD dates for all IPO entries
        
        Args:
            ipos_bs: List of IPO dictionaries with BS dates
        
        Returns:
            List of IPO dictionaries with both BS and AD dates
        """
        ipos_with_ad = []
        
        for ipo in ipos_bs:
            # Convert start date
            start_date_ad = None
            if ipo.get('startDateBS'):
                start_date_ad = self.bs_converter.convert_bs_date_string(ipo['startDateBS'])
            
            # Convert end date
            end_date_ad = None
            if ipo.get('endDateBS'):
                end_date_ad = self.bs_converter.convert_bs_date_string(ipo['endDateBS'])
            
            # Only include IPOs with valid AD conversions
            if start_date_ad and end_date_ad:
                ipo_entry = {
                    'company': ipo['company'],
                    'startDateBS': ipo['startDateBS'],
                    'endDateBS': ipo['endDateBS'],
                    'startDateAD': start_date_ad,
                    'endDateAD': end_date_ad,
                    'rawText': ipo['rawText']
                }
                ipos_with_ad.append(ipo_entry)
            else:
                print(f"Warning: Could not convert dates for {ipo['company']}")
                print(f"  Start BS: {ipo.get('startDateBS')} -> AD: {start_date_ad}")
                print(f"  End BS: {ipo.get('endDateBS')} -> AD: {end_date_ad}")
        
        return ipos_with_ad


def scrape_and_update_db():
    """
    Main function to scrape IPOs and update database
    """
    print("=== IPO Scraper Started ===\n")
    
    scraper = MerolaganiScraper()
    ipos = scraper.fetch_upcoming_ipos()
    
    if not ipos:
        print("No IPO data found or error occurred")
        return
    
    print(f"\n=== Scraped {len(ipos)} IPOs with Valid Dates ===\n")
    for i, ipo in enumerate(ipos, 1):
        print(f"{i}. {ipo['company']}")
        print(f"   BS: {ipo['startDateBS']} to {ipo['endDateBS']}")
        print(f"   AD: {ipo['startDateAD']} to {ipo['endDateAD']}")
        print(f"   Raw: {ipo['rawText'][:80]}...")
        print()
    
    # TODO: Save to database
    # import db
    # db_ready_ipos = [
    #     {
    #         'company': ipo['company'],
    #         'startDate': ipo['startDateAD'],
    #         'endDate': ipo['endDateAD']
    #     }
    #     for ipo in ipos
    # ]
    # 
    # db.clear_all_ipos()
    # count = db.save_ipos(db_ready_ipos)
    # print(f"=== Updated database with {count} IPO records ===")
    
    print("=== Scraper Completed ===")
    
    return ipos


if __name__ == "__main__":
    # Test the scraper with date conversion
    scrape_and_update_db()