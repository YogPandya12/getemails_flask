# import sys
# sys.path.append('./env/lib/site-packages')
from flask import Flask, request, render_template, send_file
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import os
import logging
from logging.handlers import RotatingFileHandler

# project_root = '/home/jobnearby/getemails.hcuboidtech.com/'
# template_path = os.path.join(project_root, '/templates')
# static_path = os.path.join(project_root, '/static')
# app = Flask(__name__, template_folder=template_path, static_folder=static_path)
app = Flask(__name__)
application = app

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename='app.log',  
    level=logging.DEBUG, 
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

def find_url_column(columns):
    keywords = ['website', 'url', 'websites', 'urls']
    for col in columns:
        if any(keyword in col.lower() for keyword in keywords):
            return col
    return None

def extract_emails_from_url(url):
    """Fetch emails from the given URL with better error handling."""
    if pd.isna(url) or not isinstance(url, str):
        return ""
    
    if not url.startswith(('http://', 'https://')):
        url = f"http://{url}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        text = ' '.join(soup.stripped_strings)
        
        raw_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        
        valid_emails = [email for email in raw_emails if not email[0].isdigit()]
        
        return ', '.join(set(valid_emails)) if valid_emails else "No email ID found"
    except requests.exceptions.RequestException:
        return "URL not working"
    except Exception as e:
        return f"Error: {str(e)}"

def get_optimal_workers(file_size):
    """Return optimal number of workers based on the file size."""
    if file_size <= 100:
        return 5  
    elif file_size <= 300:
        return 10  
    else:
        return 20 

def process_urls_in_parallel(df, url_column, num_workers):
    """Process all URLs in parallel using ThreadPoolExecutor."""
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        return list(executor.map(extract_emails_from_url, df[url_column]))

@app.route('/')
def upload_file():
    app.logger.info('Home route was accessed.')
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process_file():    
    app.logger.info('Process route entry.')
    file = request.files['file']
    app.logger.info('Request of file')

    if not file or not file.filename.endswith('.xlsx'):
        app.logger.info('Invalid file')
        return "Invalid file type. Please upload an Excel file.", 400

    try:
        app.logger.info('Valid file')
        df = pd.read_excel(file)
        
        url_column = find_url_column(df.columns)
        if not url_column:
            app.logger.info('Column not found.')
            return "No column found that likely contains URLs.", 400
        
        app.logger.info('Getting workers.')
        num_workers = get_optimal_workers(len(df))
        
        app.logger.info('Start finding emails')
        df['Emails'] = process_urls_in_parallel(df, url_column, num_workers)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        original_filename = file.filename
        processed_filename = f"processed_{original_filename}"

        app.logger.info('File sent back')
        return send_file(output, as_attachment=True, download_name=processed_filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=3)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    app.run(debug=True)
