import requests
from bs4 import BeautifulSoup
import json
import argparse

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
            response = requests.get(source, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()  # Raise an exception for bad status codes
            html_content = response.text
        except requests.RequestException as e:
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