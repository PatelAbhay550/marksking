from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import uuid
import tempfile

# Import both scraper functions, renaming the first one for clarity
from scraper import scrape_answer_key as scrape_mts_key
from scraper_je import scrape_je_answer_key
from scraper_chsl import scrape_chsl_answer_key

# --- Configuration ---
ALLOWED_EXTENSIONS = {'html', 'htm'}
SECRET_KEY = 'a-very-secret-key-for-dev' # Change for production!

# --- App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

def allowed_file(filename):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- DEBUG ROUTE ---
@app.route('/test')
def test():
    """Simple test route to verify the app is working."""
    return {"status": "success", "message": "Flask app is running on Vercel!", "routes": ["Homepage: /", "MTS: /mts", "JE: /ssc-je", "CHSL: /chsl"]}

# --- ROOT ROUTE (Landing Page) ---
@app.route('/', methods=['GET'])
def home():
    """Landing page with links to all calculators."""
    return render_template('index.html')

# --- SSC MTS ROUTE ---
@app.route('/mts', methods=['GET', 'POST'])
def calculate_mts_score():
    try:
        if request.method == 'POST':
            result = None
            ans_key_url = request.form.get('ans_key_url')
            file = request.files.get('ans_key_file')

            if ans_key_url:
                print(f"Processing MTS URL: {ans_key_url}")
                result = scrape_mts_key(source=ans_key_url, is_file=False)
            elif file and file.filename != '':
                if allowed_file(file.filename):
                    # Use temporary file instead of uploads directory
                    with tempfile.NamedTemporaryFile(mode='w+', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                        content = file.read().decode('utf-8')
                        temp_file.write(content)
                        filepath = temp_file.name
                    
                    print(f"Processing MTS file: {filepath}")
                    result = scrape_mts_key(source=filepath, is_file=True)
                    
                    # Clean up temporary file
                    try:
                        os.remove(filepath)
                    except:
                        pass
                else:
                    flash('Invalid file type. Please upload an HTML file.', 'danger')
                    return redirect(request.url)
            else:
                flash('Please provide a URL or upload a file.', 'warning')
                return redirect(request.url)

            if result:
                return render_template('results.html', data=result)
            else:
                flash('Could not process the MTS answer key. The URL may be invalid or the HTML structure might not be supported.', 'danger')
                return redirect(request.url)
                
        return render_template('mts_index.html')
    except Exception as e:
        print(f"Error in MTS route: {str(e)}")
        flash('An error occurred while processing your request.', 'danger')
        return render_template('mts_index.html')

# --- SSC JE ROUTE (Fixed and Fully Implemented) ---
@app.route('/ssc-je', methods=['GET', 'POST'])
def calculate_je_score():
    if request.method == 'POST':
        result = None
        source = None
        is_file = False
        ans_key_url = request.form.get('ans_key_url')
        file = request.files.get('ans_key_file')

        if ans_key_url:
            # --- Process URL ---
            print(f"Processing JE URL: {ans_key_url}")
            source = ans_key_url
            is_file = False

        elif file and file.filename != '':
            # --- Process File ---
            if allowed_file(file.filename):
                # Use temporary file instead of uploads directory
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                    content = file.read().decode('utf-8')
                    temp_file.write(content)
                    filepath = temp_file.name
                
                print(f"Processing JE file: {filepath}")
                source = filepath
                is_file = True
            else:
                flash('Invalid file type. Please upload an HTML file.', 'danger')
                return redirect(request.url)
        else:
            flash('Please provide a URL or upload a file.', 'warning')
            return redirect(request.url)
        
        # --- Call the specific JE scraper ---
        result = scrape_je_answer_key(source=source, is_file=is_file)

        # --- Clean up file if it exists ---
        if is_file and source and os.path.exists(source):
            try:
                os.remove(source)
            except:
                pass

        # --- Handle Result ---
        if result:
            # Render the specific JE results page
            return render_template('results_je.html', data=result)
        else:
            flash('Could not process the JE answer key. The URL may be invalid or the HTML structure might not be supported.', 'danger')
            return redirect(request.url)
            
    # For GET request, show the JE form
    return render_template('je_index.html')

# --- NEW: SSC CHSL Calculator Route ---
@app.route('/chsl', methods=['GET', 'POST'])
def calculate_chsl_score():
    """Handles logic for the universal SSC CHSL calculator."""
    if request.method == 'POST':
        result = None
        source = None
        is_file = False
        ans_key_url = request.form.get('ans_key_url')
        file = request.files.get('ans_key_file')

        if ans_key_url:
            source, is_file = ans_key_url, False
        elif file and file.filename != '':
            if allowed_file(file.filename):
                # Use temporary file instead of uploads directory
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                    content = file.read().decode('utf-8')
                    temp_file.write(content)
                    filepath = temp_file.name
                source, is_file = filepath, True
            else:
                flash('Invalid file type. Please upload an HTML file.', 'danger')
                return redirect(url_for('calculate_chsl_score'))
        else:
            flash('Please provide a URL or upload a file.', 'warning')
            return redirect(url_for('calculate_chsl_score'))
        
        # Call the specific CHSL scraper
        result = scrape_chsl_answer_key(source=source, is_file=is_file)

        if is_file and source and os.path.exists(source):
            try:
                os.remove(source)
            except:
                pass

        if result:
            # Render the specific CHSL results page
            return render_template('results_chsl.html', data=result)
        else:
            flash('Could not process the CHSL answer key. The URL may be invalid or the format is not supported.', 'danger')
            return redirect(url_for('calculate_chsl_score'))
            
    # For GET request, show the CHSL form
    return render_template('chsl_index.html')

if __name__ == '__main__':
    app.run()

# Vercel entry point - the app object itself is the WSGI application
# No additional handler needed when using @vercel/python