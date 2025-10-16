import requests
from bs4 import BeautifulSoup
import json
import argparse
import time
import random

# Try to import proxy-only utilities
try:
    from proxy_only import make_proxy_only_request
    PROXY_ONLY_AVAILABLE = True
    print("✓ Proxy-only utilities loaded")
except ImportError:
    PROXY_ONLY_AVAILABLE = False
    print("⚠️ Proxy-only utilities not available")

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

def scrape_je_answer_key(source, is_file=False):
    """
    Parses an SSC JE (Junior Engineer) style answer key from an HTML file or URL.

    This scraper is specifically adapted for the SSC JE exam pattern:
    - Marking Scheme: +1 for correct, -0.25 for incorrect.
    - Parsing: Uses a fixed-index method for candidate details.
    
    Args:
        source (str): The URL or local file path of the answer key.
        is_file (bool): True if the source is a local file path, False if it's a URL.

    Returns:
        dict: A dictionary containing parsed info, score summary, and section details.
              Returns None on error.
    """
    html_content = ""
    if is_file:
        try:
            with open(source, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except FileNotFoundError:
            print(f"Error: File not found at '{source}'")
            return None
    else:
        try:
            # Use proxy-only method for maximum reliability
            if PROXY_ONLY_AVAILABLE:
                print("🌐 Using proxy-only method...")
                html_content = make_proxy_only_request(source)
            elif ADVANCED_BYPASS_AVAILABLE:
                print("🔄 Using advanced bypass with proxy priority...")
                from bypass_utils import SSCBypassManager
                bypass_manager = SSCBypassManager()
                html_content = bypass_manager.try_proxy_methods(source)
                if html_content and html_content.status_code == 200:
                    html_content = html_content.text
                    print("✅ Success: Proxy method")
                else:
                    print("📡 Proxy methods failed, trying advanced bypass...")
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

    # 1. Extract Candidate Information (Rigid, index-based method)
    candidate_info = {}
    try:
        info_table = soup.find('table')
        cells = info_table.find_all('td')
        candidate_info = {
            'roll_no': cells[1].text.strip(),
            'cand_name': cells[3].text.strip(),
            'venue_name': cells[5].text.strip(),
            'exam_date': cells[7].text.strip(),
            'exam_time': cells[9].text.strip(),
            'subject': cells[11].text.strip()
        }
    except (AttributeError, IndexError):
        print("Error: Could not parse candidate info table. The HTML structure may have changed.")
        return None

    # 2. Process Questions and Calculate Score
    # --- SSC JE Marking Scheme ---
    EACH_QUE_POS_MARKS = 1
    EACH_QUE_NEG_MARKS = 0.25

    all_question_data = {}
    section_results = []
    total_marks = 0.0

    wrapper = soup.find('div', class_='wrapper')
    if not wrapper:
        print("Error: Main content 'wrapper' not found.")
        return None

    groups = wrapper.find_all('div', class_='grp-cntnr')
    for group in groups:
        sections = group.find_all('div', class_='section-cntnr')
        for section in sections:
            section_name_element = section.find('span', class_='section-lbl-text')
            section_name = section_name_element.text.strip() if section_name_element else "Unknown Section"
            
            questions = section.find_all('div', class_='question-pnl')
            right, not_attempted, bonus, wrong = 0, 0, 0, 0

            for question in questions:
                menu_tbl = question.find('table', class_='menu-tbl')
                bold_elements = menu_tbl.find_all('td', class_='bold')
                question_id = bold_elements[0].text.strip()
                chosen_opt = bold_elements[-1].text.strip()

                try:
                    right_ans_element = question.find('td', class_='rightAns')
                    right_opt = right_ans_element.text.strip()[0]
                    
                    if chosen_opt == "--":
                        not_attempted += 1
                        all_question_data[question_id] = "skipped"
                    elif chosen_opt == right_opt:
                        right += 1
                        all_question_data[question_id] = "right"
                    else:
                        wrong += 1
                        all_question_data[question_id] = "wrong"
                except AttributeError:
                    bonus += 1
                    all_question_data[question_id] = "bonus"
            
            # Universal scoring logic for all sections
            marks = (right + bonus) * EACH_QUE_POS_MARKS - (wrong * EACH_QUE_NEG_MARKS)
            total_marks += marks

            section_results.append({
                'section_name': section_name,
                'total_questions': len(questions),
                'attempted': len(questions) - not_attempted,
                'not_attempted': not_attempted,
                'right': right,
                'wrong': wrong,
                'bonus': bonus,
                'marks_in_section': round(marks, 2)
            })

    # 4. Compile Final Result
    final_result = {
        'candidate_info': candidate_info,
        'exam_summary': {
            'total_marks': round(total_marks, 2)
        },
        'section_details': section_results,
        'question_wise_data': all_question_data
    }

    return final_result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A Python scraper for SSC JE exam answer keys.")
    parser.add_argument("source", help="The URL or local file path to the answer key HTML.")
    parser.add_argument("-f", "--file", action="store_true", help="Flag to indicate the source is a local file.")
    
    args = parser.parse_args()
    
    result = scrape_je_answer_key(args.source, is_file=args.file)
    
    if result:
        print(json.dumps(result, indent=4))