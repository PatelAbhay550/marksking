import requests
from bs4 import BeautifulSoup
import json
import argparse
import re
from urllib.parse import urlparse, parse_qs
import time
import random

# Try to import advanced bypass utilities
try:
    from bypass_utils import make_advanced_request
    ADVANCED_BYPASS_AVAILABLE = True
    print("✓ Advanced bypass utilities loaded")
except ImportError:
    ADVANCED_BYPASS_AVAILABLE = False
    print("⚠️ Advanced bypass utilities not available, using basic method")

def make_request_with_retry(url, max_retries=3):
    """
    Make HTTP request with enhanced headers and retry logic to bypass restrictions.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = random.uniform(1, 3)
                print(f"Retrying in {delay:.1f} seconds... (attempt {attempt + 1})")
                time.sleep(delay)
            
            print(f"Attempting to fetch URL (attempt {attempt + 1}): {url}")
            response = session.get(url, timeout=30)
            
            if response.status_code == 200:
                print("✓ Successfully fetched content")
                return response.text
            elif response.status_code == 403:
                print(f"✗ 403 Forbidden - Server blocking request (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    user_agents = [
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ]
                    session.headers['User-Agent'] = random.choice(user_agents)
                continue
            else:
                print(f"✗ HTTP {response.status_code}: {response.reason}")
                response.raise_for_status()
                
        except requests.exceptions.Timeout:
            print(f"✗ Timeout error (attempt {attempt + 1})")
        except requests.exceptions.ConnectionError:
            print(f"✗ Connection error (attempt {attempt + 1})")
        except requests.RequestException as e:
            print(f"✗ Request error (attempt {attempt + 1}): {e}")
            
        if attempt == max_retries - 1:
            raise Exception(f"Failed to fetch URL after {max_retries} attempts. Server may be blocking requests.")
    
    return None

# --- SSC CHSL Tier-I Marking Scheme ---
POS_MARKS = 2
NEG_MARKS = 0.5

def _parse_tcs_html(soup):
    """Parses the modern, class-based TCS answer key format."""
    print("-> Detected TCS format. Parsing...")
    # 1. Extract Candidate Info
    candidate_info = {}
    try:
        info_table = soup.find('table')
        # Robust keyword search for details
        for row in info_table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) == 2:
                label = cells[0].text.lower().strip()
                value = cells[1].text.strip()
                if 'roll' in label: candidate_info['roll_no'] = value
                elif 'candidate name' in label: candidate_info['cand_name'] = value
                elif 'venue' in label: candidate_info['venue_name'] = value
                elif 'date' in label: candidate_info['exam_date'] = value
                elif 'time' in label: candidate_info['exam_time'] = value
                elif 'subject' in label: candidate_info['subject'] = value
    except Exception as e:
        print(f"Warning: Could not parse candidate info from TCS key. {e}")

    # 2. Process Questions
    all_question_data = {}
    section_results = []
    total_marks = 0.0
    
    wrapper = soup.find('div', class_='wrapper')
    groups = wrapper.find_all('div', class_='grp-cntnr')
    
    for group in groups:
        sections = group.find_all('div', class_='section-cntnr')
        for section in sections:
            section_name = section.find('span', class_='section-lbl-text').text.strip()
            questions = section.find_all('div', class_='question-pnl')
            right, wrong, not_attempted, bonus = 0, 0, 0, 0

            for q in questions:
                bold_elements = q.find('table', class_='menu-tbl').find_all('td', class_='bold')
                q_id = bold_elements[1].text.strip() if len(bold_elements[0].text.strip()) < 5 else bold_elements[0].text.strip()
                chosen_opt = bold_elements[-1].text.strip()

                try:
                    right_opt = q.find('td', class_='rightAns').text.strip()[0]
                    if chosen_opt == '--':
                        not_attempted += 1
                        all_question_data[q_id] = "skipped"
                    elif chosen_opt == right_opt:
                        right += 1
                        all_question_data[q_id] = "right"
                    else:
                        wrong += 1
                        all_question_data[q_id] = "wrong"
                except AttributeError:
                    bonus += 1
                    all_question_data[q_id] = "bonus"
            
            marks = (right + bonus) * POS_MARKS - (wrong * NEG_MARKS)
            total_marks += marks
            section_results.append({ 'section_name': section_name, 'right': right, 'wrong': wrong, 'not_attempted': not_attempted, 'bonus': bonus, 'marks_in_section': round(marks, 2) })

    return { 'candidate_info': candidate_info, 'exam_summary': {'total_marks': round(total_marks, 2)}, 'section_details': section_results, 'question_wise_data': all_question_data }

def _parse_eduquity_html(soup):
    """Parses the older, color-based Eduquity answer key format."""
    print("-> Detected Eduquity format. Parsing...")
    # 1. Extract Candidate Info
    candidate_info = {}
    try:
        main_table = soup.find_all('table')[3]
        info_table = main_table.find_all('table')[1]
        for i, cell in enumerate(info_table.find_all('td')):
            label = cell.text.lower().strip()
            if 'roll number' in label and i + 1 < len(info_table.find_all('td')):
                candidate_info['roll_no'] = info_table.find_all('td')[i+1].text.replace(":", "").strip()
            # ... add similar robust checks for other fields
    except Exception as e:
        print(f"Warning: Could not parse candidate info from Eduquity key. {e}")


    # 2. Process Questions
    all_question_data = {}
    section_results = [] # Eduquity format makes section detection difficult, so we aggregate
    total_marks = 0.0
    right, wrong, not_attempted, bonus = 0, 0, 0, 0

    question_tables = soup.select('table[border="2"][cellpadding="2"]') # A more specific selector for question tables
    
    for i, q_table in enumerate(question_tables):
        q_id = f"Q-{i+1}" # Default Question ID
        
        # Robustly determine question status by color
        if q_table.find('tr', {'bgcolor': 'green'}):
            right += 1
            all_question_data[q_id] = "right"
        elif q_table.find('tr', {'bgcolor': 'red'}):
            wrong += 1
            all_question_data[q_id] = "wrong"
        elif q_table.find('tr', {'bgcolor': 'gray'}):
            not_attempted += 1
            all_question_data[q_id] = "skipped"
        else:
            bonus += 1
            all_question_data[q_id] = "bonus"

    marks = (right + bonus) * POS_MARKS - (wrong * NEG_MARKS)
    section_results.append({ 'section_name': "Overall Paper", 'right': right, 'wrong': wrong, 'not_attempted': not_attempted, 'bonus': bonus, 'marks_in_section': round(marks, 2) })

    return { 'candidate_info': candidate_info, 'exam_summary': {'total_marks': round(marks, 2)}, 'section_details': section_results, 'question_wise_data': all_question_data }


def scrape_chsl_answer_key(source, is_file=False):
    """
    Universal scraper for SSC CHSL. Auto-detects TCS or Eduquity format.
    """
    html_content = ""
    if is_file:
        with open(source, 'r', encoding='utf-8') as f:
            html_content = f.read()
    else:
        try:
            # Try advanced bypass first if available
            if ADVANCED_BYPASS_AVAILABLE:
                print("🚀 Using advanced bypass techniques...")
                html_content = make_advanced_request(source)
            else:
                print("📡 Using basic bypass method...")
                html_content = make_request_with_retry(source)
                
            if not html_content:
                return None
        except Exception as e:
            print(f"Error fetching URL: {e}")
            return None
    
    soup = BeautifulSoup(html_content, 'html.parser')

    # --- The Auto-Detector Logic ---
    if "ssccbt.com" in source or "SSC ONLINE EXAMINATION" in html_content:
        return _parse_eduquity_html(soup)
    elif "digialm" in source or soup.find('div', class_='grp-cntnr'):
        return _parse_tcs_html(soup)
    else:
        print("Warning: Could not determine format. Attempting Eduquity parser as a fallback.")
        return _parse_eduquity_html(soup)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A universal Python scraper for SSC CHSL (TCS/Eduquity) answer keys.")
    parser.add_argument("source", help="The URL or local file path to the answer key HTML.")
    parser.add_argument("-f", "--file", action="store_true", help="Flag to indicate the source is a local file.")
    
    args = parser.parse_args()
    
    result = scrape_chsl_answer_key(args.source, is_file=args.file)
    
    if result:
        print(json.dumps(result, indent=4))