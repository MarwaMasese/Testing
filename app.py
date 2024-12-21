from flask import Flask, request, render_template, flash, redirect, url_for
import pandas as pd
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  
app.config['MAX_CONTENT_LENGTH'] = os.getenv('MAX_CONTENT_LENGTH')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')
app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')

# Configure Gemini
genai.configure(api_key=app.config['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-pro')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_with_gemini(df1, df2):
    """
    Use Gemini to analyze transactions
    """
    prompt = f"""
    Analyze these two sets of financial transactions and identify matches and patterns.
    Consider dates within a few days and similar amounts as potential matches.
    
    First dataset:
    {df1.to_string()}
    
    Second dataset:
    {df2.to_string()}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Analysis failed: {str(e)}"

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/reconcile', methods=['POST'])
def reconcile():
    if 'file1' not in request.files or 'file2' not in request.files:
        flash('Both files are required')
        return redirect(url_for('index'))
    
    file1 = request.files['file1']
    file2 = request.files['file2']
    
    if file1.filename == '' or file2.filename == '':
        flash('No selected files')
        return redirect(url_for('index'))
    
    if not (allowed_file(file1.filename) and allowed_file(file2.filename)):
        flash('Invalid file type. Please upload Excel files only.')
        return redirect(url_for('index'))
    
    try:
        # Save files temporarily
        filename1 = secure_filename(file1.filename)
        filename2 = secure_filename(file2.filename)
        filepath1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
        filepath2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)
        
        file1.save(filepath1)
        file2.save(filepath2)
        
        # Read Excel files
        df1 = pd.read_excel(filepath1)
        df2 = pd.read_excel(filepath2)
        
        # Get Gemini analysis
        analysis_results = analyze_with_gemini(df1, df2)
        
        # Clean up temporary files
        os.remove(filepath1)
        os.remove(filepath2)
        
        return render_template('results.html', results=analysis_results)
        
    except Exception as e:
        flash(f'Error processing files: {str(e)}')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)