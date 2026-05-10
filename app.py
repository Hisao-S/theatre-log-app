import os.path
from flask import Flask, render_template, request, redirect, url_for
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

app = Flask(__name__)

# スプレッドシート設定
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1UnO_VzSQPRgrYzxk4t9lwLG-qsMR_QY9OcrlHW1Oqzc'

def get_sheets_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add_record():
    date = request.form.get('date')
    time = request.form.get('time')
    title = request.form.get('title')
    theater = request.form.get('theater')
    station = request.form.get('station')
    seat = request.form.get('seat')
    contact = request.form.get('contact')

    # A列を空けるために最初に "" を入れる
    values = [["", date, time, title, theater, station, seat, contact]]
    
    service = get_sheets_service()
    body = {'values': values}
    
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='観劇履歴!A2',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body=body).execute()

    return "<h1>Recorded!</h1><a href='/'>Back</a>"

if __name__ == '__main__':
    app.run(debug=True, port=5000)