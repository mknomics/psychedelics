#!/usr/bin/env python3
"""
Erowid Experience Reports Scraper

Setup Instructions:
1. Create and activate virtual environment:
   python3 -m venv webscraping_env
   source webscraping_env/bin/activate

2. Install required packages:
   pip install requests beautifulsoup4 pandas lxml python-dateutil tqdm

3. Run the script:
   python erowid_scraper.py

The script will scrape experience reports from three Erowid listing pages
and save results to erowid_experiences.csv
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import random
import logging
import re
from typing import List, Dict, Optional, Tuple, Any
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from dateutil import parser as date_parser
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
BASE_URL = 'https://www.erowid.org'
TIMEOUT = 30
MIN_SLEEP = 1
MAX_SLEEP = 3

def get_session() -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({'User-Agent': USER_AGENT})
    # Disable SSL verification for Erowid (they have certificate issues)
    session.verify = False
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return session

def get_soup(url: str, session: Optional[requests.Session] = None) -> Optional[BeautifulSoup]:
    """Fetch URL and return BeautifulSoup object."""
    if session is None:
        session = get_session()
    
    try:
        response = session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'lxml')
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

def parse_weight(text: str) -> Tuple[Optional[float], Optional[str]]:
    """Parse weight text into numeric value and scale."""
    if not text:
        return None, None
    
    try:
        # Remove extra whitespace and normalize
        text = text.strip()
        # Match patterns like "170 lb", "77 kg", "170.5 lbs"
        match = re.match(r'([\d.]+)\s*([a-zA-Z]+)', text)
        if match:
            weight_val = float(match.group(1))
            weight_scale = match.group(2).lower().rstrip('s')  # Remove plural 's'
            return weight_val, weight_scale
    except Exception as e:
        logger.debug(f"Could not parse weight '{text}': {e}")
    
    return None, None

def parse_dates(raw: str) -> Optional[datetime]:
    """Parse date string to datetime object."""
    if not raw:
        return None
    
    try:
        # Try to parse with dateutil
        return date_parser.parse(raw)
    except Exception:
        # Try to extract just a year
        year_match = re.search(r'\b(19|20)\d{2}\b', raw)
        if year_match:
            try:
                year = int(year_match.group())
                return datetime(year, 1, 1)
            except Exception:
                pass
    
    return None

def get_total_pages(url: str, session: requests.Session) -> int:
    """Get the total number of pages for a listing."""
    soup = get_soup(url, session)
    if not soup:
        return 1
    
    # Look for pagination in results-table
    results_table = soup.find('table', class_='results-table')
    if results_table:
        page_links = []
        for link in results_table.find_all('a'):
            text = link.get_text(strip=True)
            if text.isdigit():
                page_links.append(int(text))
        
        if page_links:
            return max(page_links)
    
    return 1  # Default to 1 page if no pagination found

def parse_listing(url: str, session: requests.Session) -> List[Dict[str, str]]:
    """Parse a listing page and extract basic experience info."""
    soup = get_soup(url, session)
    if not soup:
        return []
    
    experiences = []
    
    # Find the experience list table
    table = soup.find('table', class_='exp-list-table')
    if not table:
        logger.warning(f"No experience table found on {url}")
        return []
    
    # Find all experience rows
    rows = table.find_all('tr', class_='exp-list-row')
    
    for row in rows:
        try:
            exp_data = {}
            
            # Extract rating
            rating_cell = row.find('td', class_='exp-rating')
            if rating_cell:
                img = rating_cell.find('img')
                if img and img.get('alt'):
                    exp_data['experience_rating'] = img['alt']
                else:
                    exp_data['experience_rating'] = None
            
            # Extract author
            author_cell = row.find('td', class_='exp-author')
            if author_cell:
                exp_data['author'] = author_cell.get_text(strip=True)
            
            # Extract title and detail URL
            title_cell = row.find('td', class_='exp-title')
            if title_cell:
                exp_data['title'] = title_cell.get_text(strip=True)
                link = title_cell.find('a')
                if link and link.get('href'):
                    # Convert relative URL to absolute
                    detail_url = link['href']
                    if not detail_url.startswith('http'):
                        # Fix URL construction
                        if not detail_url.startswith('/'):
                            detail_url = '/' + detail_url
                        detail_url = BASE_URL + detail_url
                    exp_data['detail_url'] = detail_url
            
            if 'detail_url' in exp_data:
                experiences.append(exp_data)
        except Exception as e:
            logger.error(f"Error parsing listing row: {e}")
            continue
    
    logger.info(f"Found {len(experiences)} experiences on {url}")
    return experiences

def parse_detail(detail_url: str, session: requests.Session) -> Dict[str, Any]:
    """Parse a detail page and extract all detailed information."""
    soup = get_soup(detail_url, session)
    if not soup:
        return {}
    
    details = {}
    
    try:
        # Parse dose chart
        dose_table = soup.find('table', class_='dosechart')
        if dose_table:
            dose_rows = dose_table.find_all('tr')
            dose_data_rows = []
            for row in dose_rows:
                # Check if row has actual dose data (not header)
                if row.find('td', class_='dosechart-substance'):
                    dose_data_rows.append(row)
            
            for i in range(1, 11):  # 1 to 10
                if i <= len(dose_data_rows):
                    row = dose_data_rows[i-1]
                    # The cells might be in different order, so use class names
                    substance_cell = row.find('td', class_='dosechart-substance')
                    amount_cell = row.find('td', class_='dosechart-amount')
                    method_cell = row.find('td', class_='dosechart-method')
                    
                    details[f'substance_{i}'] = substance_cell.get_text(strip=True) if substance_cell else None
                    details[f'dose_{i}'] = amount_cell.get_text(strip=True) if amount_cell else None
                    details[f'method_{i}'] = method_cell.get_text(strip=True) if method_cell else None
                else:
                    details[f'substance_{i}'] = None
                    details[f'dose_{i}'] = None
                    details[f'method_{i}'] = None
        else:
            # No dose chart found, fill with None
            for i in range(1, 11):
                details[f'substance_{i}'] = None
                details[f'dose_{i}'] = None
                details[f'method_{i}'] = None
        
        # Parse body weight
        weight_table = soup.find('table', class_='bodyweight')
        if weight_table:
            weight_cell = weight_table.find('td', class_='bodyweight-amount')
            if weight_cell:
                weight_text = weight_cell.get_text(strip=True)
                weight_val, weight_scale = parse_weight(weight_text)
                details['weight_val'] = weight_val
                details['weight_scale'] = weight_scale
            else:
                details['weight_val'] = None
                details['weight_scale'] = None
        else:
            details['weight_val'] = None
            details['weight_scale'] = None
        
        # Parse main narrative text
        # The text is in the report-text-surround div, but we need to exclude tables
        report_div = soup.find('div', class_='report-text-surround')
        if report_div:
            # Clone the div to avoid modifying the original
            import copy
            report_copy = copy.copy(report_div)
            # Remove all tables from the copy
            for table in report_copy.find_all('table'):
                table.decompose()
            
            # Get text with preserved line breaks
            text = report_copy.get_text(separator='\n', strip=True)
            # Clean up excessive newlines
            text = re.sub(r'\n{3,}', '\n\n', text)
            details['text'] = text if text else None
        else:
            # Fallback: try to find text between HTML comments
            html_str = str(soup)
            start_marker = '<!--Start Body -->'
            end_marker = '<!--End Body -->'
            
            if start_marker in html_str and end_marker in html_str:
                start_idx = html_str.index(start_marker) + len(start_marker)
                end_idx = html_str.index(end_marker)
                body_html = html_str[start_idx:end_idx]
                
                # Parse the extracted HTML
                body_soup = BeautifulSoup(body_html, 'lxml')
                text = body_soup.get_text(separator='\n', strip=True)
                text = re.sub(r'\n{3,}', '\n\n', text)
                details['text'] = text if text else None
            else:
                details['text'] = None
        
        # Parse foot data
        footdata_table = soup.find('table', class_='footdata')
        if footdata_table:
            # ID
            id_cell = footdata_table.find('td', class_='footdata-expid')
            if id_cell:
                id_text = id_cell.get_text(strip=True)
                # Strip all non-digits
                id_digits = re.sub(r'\D', '', id_text)
                details['id'] = int(id_digits) if id_digits else None
            else:
                details['id'] = None
            
            # Gender
            gender_cell = footdata_table.find('td', class_='footdata-gender')
            details['gender'] = gender_cell.get_text(strip=True) if gender_cell else None
            
            # Age at experience
            age_cell = footdata_table.find('td', class_='footdata-ageofexp')
            details['age_experience'] = age_cell.get_text(strip=True) if age_cell else None
            
            # Published date
            pubdate_cell = footdata_table.find('td', class_='footdata-pubdate')
            if pubdate_cell:
                pubdate_text = pubdate_cell.get_text(strip=True)
                # Remove "Published: " prefix
                pubdate_text = re.sub(r'^Published:\s*', '', pubdate_text)
                parsed_date = parse_dates(pubdate_text)
                details['date_published'] = parsed_date if parsed_date else pubdate_text
            else:
                details['date_published'] = None
            
            # Number of views
            views_cell = footdata_table.find('td', class_='footdata-numviews')
            if views_cell:
                views_text = views_cell.get_text(strip=True)
                # Remove "Views: " and commas
                views_text = re.sub(r'^Views:\s*', '', views_text)
                views_text = views_text.replace(',', '')
                try:
                    details['number_views'] = int(views_text)
                except ValueError:
                    details['number_views'] = None
            else:
                details['number_views'] = None
            
            # Date of experience (best effort)
            # Look for various patterns in footdata
            all_cells = footdata_table.find_all('td')
            date_experience = None
            
            for cell in all_cells:
                cell_text = cell.get_text(strip=True)
                # Look for patterns like "Exp Year: 2020" or "Date of Experience: ..."
                if 'exp year' in cell_text.lower() or 'experience' in cell_text.lower():
                    # Try to extract date/year
                    date_match = re.search(r':\s*(.+)', cell_text)
                    if date_match:
                        date_str = date_match.group(1)
                        date_experience = parse_dates(date_str)
                        if date_experience:
                            break
            
            details['date_experience'] = date_experience
        else:
            # No footdata table
            details['id'] = None
            details['gender'] = None
            details['age_experience'] = None
            details['date_published'] = None
            details['number_views'] = None
            details['date_experience'] = None
            
    except Exception as e:
        logger.error(f"Error parsing detail page {detail_url}: {e}")
    
    return details

def main(limit_per_page=None):
    """Main function to orchestrate the scraping process.
    
    Args:
        limit_per_page: Optional limit on number of experiences to scrape per listing page
    """
    # URLs to scrape
    listing_urls = [
        'https://www.erowid.org/experiences/exp.cgi?S1=39',
        'https://www.erowid.org/experiences/exp.cgi?S1=2',
        'https://www.erowid.org/experiences/exp.cgi?S1=8'
    ]
    
    session = get_session()
    all_experiences = []
    
    # Process each listing page
    for base_listing_url in listing_urls:
        # Get total number of pages for this listing
        total_pages = get_total_pages(base_listing_url, session)
        logger.info(f"Processing {base_listing_url} - Found {total_pages} pages")
        
        # Iterate through all pages
        for page_num in range(1, total_pages + 1):
            # Construct URL for this page
            start_offset = (page_num - 1) * 100
            page_url = f"{base_listing_url}&ShowViews=0&Cellar=0&Start={start_offset}&Max=100"
            
            logger.info(f"Processing page {page_num}/{total_pages}: {page_url}")
            experiences = parse_listing(page_url, session)
            
            # Apply limit if specified (for testing)
            if limit_per_page:
                experiences = experiences[:limit_per_page]
                logger.info(f"Limited to {limit_per_page} experiences per page")
                # If limit is set, only process first page
                if page_num == 1:
                    pass  # Continue processing this page
                else:
                    break  # Skip remaining pages
            
            # Process each detail page with progress bar
            page_desc = f"Page {page_num}/{total_pages} of S1={base_listing_url.split('S1=')[1]}"
            for exp in tqdm(experiences, desc=page_desc):
                # Be polite - random sleep between requests
                time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
                
                if 'detail_url' in exp:
                    try:
                        detail_data = parse_detail(exp['detail_url'], session)
                        # Merge listing data with detail data
                        full_exp = {**exp, **detail_data}
                        # Remove detail_url as it's not in final schema
                        full_exp.pop('detail_url', None)
                        all_experiences.append(full_exp)
                    except Exception as e:
                        logger.error(f"Failed to parse detail page {exp.get('detail_url')}: {e}")
                        # Still add the listing data even if detail parsing fails
                        full_exp = exp.copy()
                        full_exp.pop('detail_url', None)
                        all_experiences.append(full_exp)
    
    logger.info(f"Total experiences scraped: {len(all_experiences)}")
    
    # Create DataFrame with exact column order
    columns = [
        'title', 'author', 'date_experience', 'date_published', 'gender', 
        'age_experience', 'experience_rating', 'weight_val', 'weight_scale', 
        'text', 'id', 'number_views'
    ]
    
    # Add dose columns
    for i in range(1, 11):
        columns.extend([f'substance_{i}', f'dose_{i}', f'method_{i}'])
    
    # Create DataFrame
    df = pd.DataFrame(all_experiences)
    
    # Ensure all columns exist
    for col in columns:
        if col not in df.columns:
            df[col] = None
    
    # Reorder columns to match exact schema
    df = df[columns]
    
    # Save to CSV
    output_file = 'erowid_experiences.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    logger.info(f"Data saved to {output_file}")
    
    # Print dtypes and head
    print("\nDataFrame dtypes:")
    print(df.dtypes)
    print("\nFirst 3 rows:")
    print(df.head(3))
    
    # Validation
    print(f"\nTotal columns: {len(df.columns)} (expected 42)")
    print(f"Total rows: {len(df)}")
    
    # Check for required fields
    required_fields = ['title', 'author', 'experience_rating']
    missing_required = df[required_fields].isnull().sum()
    if missing_required.any():
        print("\nWarning: Missing required fields:")
        print(missing_required[missing_required > 0])

if __name__ == "__main__":
    import sys
    # Check if a limit was provided as command line argument
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            logger.info(f"Running with limit of {limit} experiences per page")
            main(limit_per_page=limit)
        except ValueError:
            logger.error("Invalid limit value. Please provide an integer.")
            sys.exit(1)
    else:
        main()