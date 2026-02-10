"""
IPO Scraper - Works both locally and in GitHub Actions
Scrapes IPO data and either updates local DB or sends to API
"""

from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import logging
import sys
import os
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class BSToADConverter:
    """Converter for Bikram Sambat (BS) to Anno Domini (AD) dates"""
    
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
        month_lower = month_name.lower().strip()
        return self.BS_MONTHS.get(month_lower)
    
    def parse_bs_date(self, bs_date_str: str) -> Optional[Dict[str, int]]:
        if not bs_date_str:
            return None
        
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
            logger.error(f"Error converting BS to AD ({bs_year}/{bs_month}/{bs_day}): {e}")
            return None
    
    def _calculate_days_from_reference(self, bs_year: int, bs_month: int, bs_day: int) -> int:
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
        parsed = self.parse_bs_date(bs_date_str)
        if not parsed:
            return None
        
        return self.bs_to_ad(parsed['year'], parsed['month'], parsed['day'])


class MerolaganiScraper:
    """Scraper for fetching IPO data from Merolagani"""
    
    BASE_URL = "https://www.merolagani.com"
    IPO_URL = f"{BASE_URL}/Ipo.aspx?type=upcoming"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.bs_converter = BSToADConverter()
    
    def fetch_upcoming_ipos(self) -> List[Dict[str, str]]:
        try:
            logger.info(f"Fetching IPOs from {self.IPO_URL}")
            response = self.session.get(self.IPO_URL, timeout=15)
            response.raise_for_status()
            
            logger.info(f"Response status: {response.status_code}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            ipos_bs = self._parse_media_list(soup)
            ipos_with_ad = self._convert_dates_to_ad(ipos_bs)
            
            logger.info(f"Successfully scraped {len(ipos_with_ad)} IPOs")
            return ipos_with_ad
            
        except Exception as e:
            logger.error(f"Error scraping: {e}", exc_info=True)
            return []
    
    def _parse_media_list(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        ipos = []
        
        announcement_list = soup.find('div', class_='announcement-list')
        if not announcement_list:
            announcement_list = soup.find('div', id=re.compile('announcement', re.I))
        if not announcement_list:
            announcement_list = soup.find('div', class_=re.compile('list|container', re.I))
        
        if announcement_list:
            media_divs = announcement_list.find_all('div', class_='media')
            logger.info(f"Found {len(media_divs)} media divs")
            
            for media_div in media_divs:
                ipo_data = self._parse_media_div(media_div)
                if ipo_data:
                    ipos.append(ipo_data)
        else:
            logger.warning("Could not find announcement list, trying fallback")
            all_media_divs = soup.find_all('div', class_='media')
            for media_div in all_media_divs:
                ipo_data = self._parse_media_div(media_div)
                if ipo_data:
                    ipos.append(ipo_data)
        
        return ipos
    
    def _parse_media_div(self, media_div) -> Optional[Dict[str, str]]:
        try:
            media_body = media_div.find('div', class_='media-body')
            if not media_body:
                return None
            
            link = media_body.find('a')
            if not link:
                return None
            
            announcement_text = link.get_text(strip=True)
            
            if 'ipo' not in announcement_text.lower() and 'share' not in announcement_text.lower():
                return None
            
            company_name = self._extract_company_name(announcement_text)
            date_info = self._extract_date_range(announcement_text)
            
            if company_name and date_info:
                return {
                    'company': company_name,
                    'startDateBS': date_info['start'],
                    'endDateBS': date_info['end'],
                    'rawText': announcement_text
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing media div: {e}")
            return None
    
    def _extract_company_name(self, text: str) -> Optional[str]:
        separators = [' - ', ' – ', ' — ', ' IPO', ' Share']
        
        for sep in separators:
            if sep in text:
                company_part = text.split(sep)[0].strip()
                if len(company_part) > 3:
                    return company_part
        
        keywords = [' of ', ' from ', ' opens']
        for keyword in keywords:
            if keyword in text.lower():
                parts = text.split(keyword)
                if len(parts[0].strip()) > 3:
                    return parts[0].strip()
        
        words = text.split()
        if len(words) >= 3:
            return ' '.join(words[:5])
        
        return None
    
    def _extract_date_range(self, text: str) -> Optional[Dict[str, str]]:
        pattern1 = r'(\d{1,2})(?:st|nd|rd|th)\s+(\w+)\s*[-–—]\s*(\d{1,2})(?:st|nd|rd|th)\s+(\w+),?\s*(\d{4})'
        match = re.search(pattern1, text, re.IGNORECASE)
        
        if match:
            return {
                'start': f"{match.group(1)} {match.group(2)} {match.group(5)}",
                'end': f"{match.group(3)} {match.group(4)} {match.group(5)}"
            }
        
        pattern2 = r'(\d{1,2})(?:st|nd|rd|th)\s+(?:to|-)\s+(\d{1,2})(?:st|nd|rd|th)\s+(\w+),?\s*(\d{4})'
        match = re.search(pattern2, text, re.IGNORECASE)
        
        if match:
            return {
                'start': f"{match.group(1)} {match.group(3)} {match.group(4)}",
                'end': f"{match.group(2)} {match.group(3)} {match.group(4)}"
            }
        
        pattern3 = r'from\s+(\d{1,2})(?:st|nd|rd|th)\s+(\w+)\s+to\s+(\d{1,2})(?:st|nd|rd|th)\s+(\w+),?\s*(\d{4})'
        match = re.search(pattern3, text, re.IGNORECASE)
        
        if match:
            return {
                'start': f"{match.group(1)} {match.group(2)} {match.group(5)}",
                'end': f"{match.group(3)} {match.group(4)} {match.group(5)}"
            }
        
        return None
    
    def _convert_dates_to_ad(self, ipos_bs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        ipos_with_ad = []
        
        for ipo in ipos_bs:
            start_date_ad = None
            if ipo.get('startDateBS'):
                start_date_ad = self.bs_converter.convert_bs_date_string(ipo['startDateBS'])
            
            end_date_ad = None
            if ipo.get('endDateBS'):
                end_date_ad = self.bs_converter.convert_bs_date_string(ipo['endDateBS'])
            
            if start_date_ad and end_date_ad:
                ipos_with_ad.append({
                    'company': ipo['company'],
                    'startDate': start_date_ad,
                    'endDate': end_date_ad
                })
            else:
                logger.warning(f"Skipping {ipo['company']} - date conversion failed")
        
        return ipos_with_ad


def send_to_api(ipos: List[Dict[str, str]], api_url: str) -> bool:
    """Send scraped IPO data to the backend API (for GitHub Actions)"""
    try:
        payload = {
            "ipos": ipos,
            "source": "github-actions"
        }
        
        logger.info(f"Sending {len(ipos)} IPOs to API: {api_url}")
        
        response = requests.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"API Response: {result}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send data to API: {e}")
        return False


def update_local_db(ipos: List[Dict[str, str]]) -> bool:
    """Update local SQLite database (for local runs)"""
    try:
        import db
        
        logger.info(f"Updating local database with {len(ipos)} IPOs")
        db.clear_all_ipos()
        count = db.save_ipos(ipos)
        
        logger.info(f"Successfully updated database with {count} records")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update local database: {e}")
        return False


def save_to_file(ipos: List[Dict[str, str]]):
    """Save IPO data to JSON file as backup"""
    output_file = "scraped_ipos.json"
    with open(output_file, 'w') as f:
        json.dump({
            "scraped_at": datetime.now().isoformat(),
            "count": len(ipos),
            "ipos": ipos
        }, f, indent=2)
    logger.info(f"Saved {len(ipos)} IPOs to {output_file}")


def scrape_and_update():
    """Main function - works both locally and in GitHub Actions"""
    logger.info("=" * 60)
    logger.info("IPO Scraper Started")
    logger.info("=" * 60)
    
    # Check if running in GitHub Actions
    api_url = os.environ.get('API_URL')
    is_github_actions = api_url is not None
    
    if is_github_actions:
        logger.info(f"Running in GitHub Actions mode")
        logger.info(f"Target API: {api_url}")
    else:
        logger.info("Running in local mode")
    
    # Scrape IPOs
    scraper = MerolaganiScraper()
    ipos = scraper.fetch_upcoming_ipos()
    
    if not ipos:
        logger.warning("No IPO data scraped")
        return False
    
    logger.info(f"Successfully scraped {len(ipos)} IPOs:")
    for i, ipo in enumerate(ipos, 1):
        logger.info(f"  {i}. {ipo['company']}: {ipo['startDate']} to {ipo['endDate']}")
    
    # Update database or send to API
    success = False
    
    if is_github_actions:
        # GitHub Actions: Send to API
        success = send_to_api(ipos, api_url)
        if not success:
            logger.warning("API update failed, saving to backup file")
            save_to_file(ipos)
    else:
        # Local: Update database directly
        success = update_local_db(ipos)
        if success:
            save_to_file(ipos)  # Also save backup
    
    logger.info("=" * 60)
    if success:
        logger.info("✅ Scraper Completed Successfully")
    else:
        logger.info("❌ Scraper Completed with Errors")
    logger.info("=" * 60)
    
    return success


if __name__ == "__main__":
    success = scrape_and_update()
    sys.exit(0 if success else 1)