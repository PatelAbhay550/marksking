import requests
from bs4 import BeautifulSoup
import json
import argparse

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
            response = requests.get(source, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            html_content = response.text
        except requests.RequestException as e:
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