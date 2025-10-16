import requests
from bs4 import BeautifulSoup
import json
import argparse
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
            # Add random delay to avoid rate limiting
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
                    # Try with different User-Agent
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

def scrape_answer_key(source, is_file=False):
    """
    Parses an SSC-style answer key HTML file or URL to calculate scores.

    This function replicates the logic from the provided JavaScript code, including
    extracting candidate details, iterating through questions, and applying a
    specific scoring scheme (no negative marking for the first section group).

    Args:
        source (str): The URL or local file path of the answer key.
        is_file (bool): True if the source is a local file path, False if it's a URL.

    Returns:
        dict: A dictionary containing the parsed candidate info, score summary,
              section-wise breakdown, and question-wise results. Returns None on error.
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

    # 1. Extract Candidate Information
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
        print("Error: Could not parse candidate information table. The HTML structure might be different.")
        return None

    # 2. Process Questions and Calculate Score
    all_question_data = {}
    section_results = []
    total_marks = 0.0
    section_one_marks = 0.0
    section_two_marks = 0.0

    # Constants from your JS logic
    EACH_QUE_POS_MARKS = 3
    EACH_QUE_NEG_MARKS = 1

    wrapper = soup.find('div', class_='wrapper')
    if not wrapper:
        print("Error: Main content 'wrapper' not found in HTML.")
        return None

    # Loop through main groups (grp-cntnr)
    groups = wrapper.find_all('div', class_='grp-cntnr')
    for i, group in enumerate(groups):
        # Loop through sections within a group (section-cntnr)
        sections = group.find_all('div', class_='section-cntnr')
        for section in sections:
            section_name_element = section.find('div', class_='section-lbl')
            section_name = section_name_element.text.strip() if section_name_element else "Unknown Section"
            
            questions = section.find_all('div', class_='question-pnl')
            right, not_attempted, bonus, wrong = 0, 0, 0, 0

            for question in questions:
                menu_tbl = question.find('table', class_='menu-tbl')
                bold_elements = menu_tbl.find_all('td', class_='bold')

                # Get Question ID (handling the edge case from your JS)
                question_id = bold_elements[0].text.strip()
                if len(question_id) < 5 and len(bold_elements) > 1:
                    question_id = bold_elements[1].text.strip()

                # Get the option chosen by the candidate
                chosen_opt = bold_elements[-1].text.strip()

                # Find the correct answer (using try-except like your JS)
                try:
                    right_ans_element = question.find('td', class_='rightAns')
                    right_opt = right_ans_element.text.strip()[0] # Get first character e.g., "1)" -> "1"
                    
                    if chosen_opt == "--":
                        not_attempted += 1
                        all_question_data[question_id] = "skipped"
                    elif chosen_opt == right_opt:
                        right += 1
                        all_question_data[question_id] = "right"
                    else:
                        wrong += 1
                        all_question_data[question_id] = "wrong"
                except AttributeError: # This is triggered if find() returns None
                    bonus += 1
                    all_question_data[question_id] = "bonus"
            
            # 3. Apply Scoring Logic
            marks = 0.0
            if i == 0:  # First group has no negative marking
                marks = (right + bonus) * EACH_QUE_POS_MARKS
                section_one_marks += marks
            else:  # Subsequent groups have negative marking
                marks = (right + bonus) * EACH_QUE_POS_MARKS - (wrong * EACH_QUE_NEG_MARKS)
                if i == 1: # Specifically track marks for the second group
                    section_two_marks += marks
            
            total_marks += marks

            section_results.append({
                'section_name': section_name[9:],
                'total_questions': len(questions),
                'attempted': len(questions) - not_attempted,
                'not_attempted': not_attempted,
                'right': right,
                'wrong': wrong,
                'bonus': bonus,
                'marks_in_section': round(marks, 2)
            })

    # 4. Compile the Final Result
    final_result = {
        'candidate_info': candidate_info,
        'exam_summary': {
            'total_marks': round(total_marks, 2),
            'section_one_total': round(section_one_marks, 2),
            'section_two_total': round(section_two_marks, 2)
        },
        'section_details': section_results,
        'question_wise_data': all_question_data
    }

    return final_result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A Python script to scrape and evaluate SSC-style answer keys from a URL or local file."
    )
    parser.add_argument("source", help="The URL or the local file path to the answer key HTML.")
    parser.add_argument("-f", "--file", action="store_true", help="Flag to indicate that the source is a local file.")
    
    args = parser.parse_args()
    
    result = scrape_answer_key(args.source, is_file=args.file)
    
    if result:
        # Pretty print the JSON output
        print(json.dumps(result, indent=4))