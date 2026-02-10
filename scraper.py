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
        """Normalize BS month name to month number (1-12)"""
        month_lower = month_name.lower().strip()
        return self.BS_MONTHS.get(month_lower)
    
    def parse_bs_date(self, bs_date_str: str) -> Optional[Dict[str, int]]:
        """
        Parse BS date string into components
        Handles formats like "28 Magh 2081" or "28th Magh 2081"
        """
        if not bs_date_str:
            return None
        
        # Pattern: day (with optional ordinal) month year
        pattern = r'(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)[,\s]+(\d{4})'
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
        """Convert BS date to AD date using lookup table"""
        try:
            if bs_year not in self.BS_MONTH_DAYS:
                return self._approximate_bs_to_ad(bs_year, bs_month, bs_day)
            
            if bs_month < 1 or bs_month > 12:
                return None
            
            if bs_day < 1 or bs_day > self.BS_MONTH_DAYS[bs_year][bs_month - 1]:
                return None
            
            days_diff = self._calculate_days_from_reference(bs_year, bs_month, bs_day)
            ad_date = self.REFERENCE_AD + timedelta(days=days_diff)
            
            return ad_date.strftime('%Y-%m-%d')
            
        except Exception as e:
            print(f"Error converting BS to AD ({bs_year}/{bs_month}/{bs_day}): {e}")
            return None
    
    def _calculate_days_from_reference(self, bs_year: int, bs_month: int, bs_day: int) -> int:
        """Calculate number of days from reference BS date"""
        days = 0
        ref_year = self.REFERENCE_BS['year']
        ref_month = self.REFERENCE_BS['month']
        ref_day = self.REFERENCE_BS['day']
        
        if bs_year < ref_year or (bs_year == ref_year and bs_month < ref_month):
            return -self._calculate_days_backwards(bs_year, bs_month, bs_day)
        
        if bs_year == ref_year:
            for m in range(ref_month, bs_month):
                days += self.BS_MONTH_DAYS[bs_year][m - 1]
            days += bs_day - ref_day
        else:
            for m in range(ref_month, 13):
                days += self.BS_MONTH_DAYS[ref_year][m - 1]
            days -= ref_day - 1
            
            for y in range(ref_year + 1, bs_year):
                if y in self.BS_MONTH_DAYS:
                    days += sum(self.BS_MONTH_DAYS[y])
                else:
                    days += 365
            
            for m in range(1, bs_month):
                days += self.BS_MONTH_DAYS[bs_year][m - 1]
            
            days += bs_day
        
        return days
    
    def _calculate_days_backwards(self, bs_year: int, bs_month: int, bs_day: int) -> int:
        """Calculate days backwards from reference point"""
        days = 0
        ref_year = self.REFERENCE_BS['year']
        ref_month = self.REFERENCE_BS['month']
        ref_day = self.REFERENCE_BS['day']
        
        if bs_year == ref_year:
            for m in range(bs_month, ref_month):
                days += self.BS_MONTH_DAYS[bs_year][m - 1]
            days += ref_day - bs_day
        else:
            days += self.BS_MONTH_DAYS[bs_year][bs_month - 1] - bs_day
            
            for m in range(bs_month + 1, 13):
                days += self.BS_MONTH_DAYS[bs_year][m - 1]
            
            for y in range(bs_year + 1, ref_year):
                if y in self.BS_MONTH_DAYS:
                    days += sum(self.BS_MONTH_DAYS[y])
                else:
                    days += 365
            
            for m in range(1, ref_month):
                days += self.BS_MONTH_DAYS[ref_year][m - 1]
            
            days += ref_day
        
        return days
    
    def _approximate_bs_to_ad(self, bs_year: int, bs_month: int, bs_day: int) -> str:
        """Approximate BS to AD conversion for years outside lookup table"""
        ad_year = bs_year - 57
        
        if bs_month >= 10:
            ad_year += 1
            ad_month = bs_month - 9
        else:
            ad_month = bs_month + 3
        
        ad_day = min(bs_day, 28)
        
        try:
            ad_date = datetime(ad_year, ad_month, ad_day)
            return ad_date.strftime('%Y-%m-%d')
        except:
            return datetime(ad_year, ad_month, 1).strftime('%Y-%m-%d')
    
    def convert_bs_date_string(self, bs_date_str: str) -> Optional[str]:
        """Convert BS date string directly to AD ISO format"""
        parsed = self.parse_bs_date(bs_date_str)
        if not parsed:
            return None
        
        return self.bs_to_ad(parsed['year'], parsed['month'], parsed['day'])


class MerolaganiScraper:
    """
    Scraper for fetching IPO data from Merolagani
    Parses the media list format with announcement divs
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
            
            # Extract IPO entries from media list format
            ipos_bs = self._parse_media_list(soup)
            
            # Convert BS dates to AD dates
            ipos_with_ad = self._convert_dates_to_ad(ipos_bs)
            
            print(f"Found {len(ipos_with_ad)} IPO entries with valid dates")
            return ipos_with_ad
            
        except requests.RequestException as e:
            print(f"Error fetching IPO data: {e}")
            return []
        except Exception as e:
            print(f"Error parsing IPO data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_media_list(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Parse IPO entries from the media list format
        
        Merolagani uses a structure like:
        <div class="announcement-list">
            <div class="media">
                <div class="media-body">
                    <small class="text-muted">Posted: 2082/10/15</small>
                    <a href="...">Company Name - IPO details with 28th Magh - 4th Falgun, 2082</a>
                </div>
            </div>
        </div>
        """
        ipos = []
        
        # Look for announcement list container
        announcement_list = soup.find('div', class_='announcement-list')
        
        if not announcement_list:
            # Try alternative selectors
            announcement_list = soup.find('div', id=re.compile('announcement', re.I))
        
        if not announcement_list:
            # Look for any container with media divs
            announcement_list = soup.find('div', class_=re.compile('list|container', re.I))
        
        if announcement_list:
            # Find all media divs (each represents an IPO announcement)
            media_divs = announcement_list.find_all('div', class_='media')
            
            print(f"Found {len(media_divs)} media divs in announcement list")
            
            for media_div in media_divs:
                ipo_data = self._parse_media_div(media_div)
                if ipo_data:
                    ipos.append(ipo_data)
        else:
            print("Warning: Could not find announcement-list div")
            # Fallback: try to find all media divs on the page
            all_media_divs = soup.find_all('div', class_='media')
            print(f"Fallback: Found {len(all_media_divs)} media divs on page")
            
            for media_div in all_media_divs:
                ipo_data = self._parse_media_div(media_div)
                if ipo_data:
                    ipos.append(ipo_data)
        
        return ipos
    
    def _parse_media_div(self, media_div) -> Optional[Dict[str, str]]:
        """
        Parse a single media div to extract IPO information
        
        Args:
            media_div: BeautifulSoup div element with class 'media'
        
        Returns:
            Dictionary with company, startDateBS, endDateBS, rawText or None
        """
        try:
            # Find the media-body which contains the announcement text
            media_body = media_div.find('div', class_='media-body')
            
            if not media_body:
                return None
            
            # Find the link element which contains the company name and IPO details
            link = media_body.find('a')
            
            if not link:
                return None
            
            # Get the full announcement text
            announcement_text = link.get_text(strip=True)
            raw_text = announcement_text
            
            # Skip if this doesn't look like an IPO announcement
            if 'ipo' not in announcement_text.lower() and 'share' not in announcement_text.lower():
                return None
            
            print(f"Processing announcement: {announcement_text[:100]}...")
            
            # Extract company name (usually before the dash or hyphen)
            company_name = self._extract_company_name(announcement_text)
            
            # Extract BS date range
            # Patterns like: "28th Magh - 4th Falgun, 2082" or "15th to 19th Falgun, 2082"
            date_info = self._extract_date_range(announcement_text)
            
            if company_name and date_info:
                return {
                    'company': company_name,
                    'startDateBS': date_info['start'],
                    'endDateBS': date_info['end'],
                    'rawText': raw_text
                }
            
            return None
            
        except Exception as e:
            print(f"Error parsing media div: {e}")
            return None
    
    def _extract_company_name(self, text: str) -> Optional[str]:
        """
        Extract company name from announcement text
        
        Usually the company name appears before a dash or certain keywords
        """
        # Try to find company name before common separators
        separators = [' - ', ' – ', ' — ', ' IPO', ' Share']
        
        for sep in separators:
            if sep in text:
                company_part = text.split(sep)[0].strip()
                if len(company_part) > 3:
                    return company_part
        
        # Fallback: use first part before "of" or other keywords
        keywords = [' of ', ' from ', ' opens']
        for keyword in keywords:
            if keyword in text.lower():
                parts = text.split(keyword)
                if len(parts[0].strip()) > 3:
                    return parts[0].strip()
        
        # Last resort: take first meaningful chunk
        words = text.split()
        if len(words) >= 3:
            # Take first 3-5 words as company name
            return ' '.join(words[:5])
        
        return None
    
    def _extract_date_range(self, text: str) -> Optional[Dict[str, str]]:
        """
        Extract BS date range from announcement text
        
        Handles formats like:
        - "28th Magh - 4th Falgun, 2082"
        - "15th to 19th Falgun, 2082"
        - "from 1st Chaitra to 5th Chaitra, 2082"
        """
        # Pattern 1: "DDth Month - DDth Month, YYYY"
        pattern1 = r'(\d{1,2})(?:st|nd|rd|th)\s+(\w+)\s*[-–—]\s*(\d{1,2})(?:st|nd|rd|th)\s+(\w+),?\s*(\d{4})'
        match = re.search(pattern1, text, re.IGNORECASE)
        
        if match:
            start_day = match.group(1)
            start_month = match.group(2)
            end_day = match.group(3)
            end_month = match.group(4)
            year = match.group(5)
            
            return {
                'start': f"{start_day} {start_month} {year}",
                'end': f"{end_day} {end_month} {year}"
            }
        
        # Pattern 2: "DDth to DDth Month, YYYY" (same month)
        pattern2 = r'(\d{1,2})(?:st|nd|rd|th)\s+(?:to|-)\s+(\d{1,2})(?:st|nd|rd|th)\s+(\w+),?\s*(\d{4})'
        match = re.search(pattern2, text, re.IGNORECASE)
        
        if match:
            start_day = match.group(1)
            end_day = match.group(2)
            month = match.group(3)
            year = match.group(4)
            
            return {
                'start': f"{start_day} {month} {year}",
                'end': f"{end_day} {month} {year}"
            }
        
        # Pattern 3: "from DDth Month to DDth Month, YYYY"
        pattern3 = r'from\s+(\d{1,2})(?:st|nd|rd|th)\s+(\w+)\s+to\s+(\d{1,2})(?:st|nd|rd|th)\s+(\w+),?\s*(\d{4})'
        match = re.search(pattern3, text, re.IGNORECASE)
        
        if match:
            start_day = match.group(1)
            start_month = match.group(2)
            end_day = match.group(3)
            end_month = match.group(4)
            year = match.group(5)
            
            return {
                'start': f"{start_day} {start_month} {year}",
                'end': f"{end_day} {end_month} {year}"
            }
        
        return None
    
    def _convert_dates_to_ad(self, ipos_bs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert BS dates to AD dates for all IPO entries"""
        ipos_with_ad = []
        
        for ipo in ipos_bs:
            start_date_ad = None
            if ipo.get('startDateBS'):
                start_date_ad = self.bs_converter.convert_bs_date_string(ipo['startDateBS'])
            
            end_date_ad = None
            if ipo.get('endDateBS'):
                end_date_ad = self.bs_converter.convert_bs_date_string(ipo['endDateBS'])
            
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
    """Main function to scrape IPOs and update database"""
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
    # Test the scraper with the media list format
    scrape_and_update_db()