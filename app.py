import os
import json
from flask import Flask, render_template, request
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1UnO_VzSQPRgrYzxk4t9lwLG-qsMR_QY9OcrlHW1Oqzc'

def get_sheets_service():
    creds = None
    
    # 1. まずはPC上の「token.json」を探す（ローカル環境用）
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 2. 「token.json」がない場合、Renderの環境変数を探す（公開環境用）
    if not creds:
        env_token = os.environ.get('GOOGLE_TOKEN_JSON')
        if env_token:
            info = json.loads(env_token)
            creds = Credentials.from_authorized_user_info(info, SCOPES)
    
    # トークンが期限切れなら更新
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    # それでも認証できない（初回など）場合、credentials情報を取得
    if not creds or not creds.valid:
        # PC上の「credentials.json」を探す
        if os.path.exists('credentials.json'):
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        else:
            # Renderの環境変数を探す
            env_creds = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            if env_creds:
                info = json.loads(env_creds)
                creds = Credentials.from_authorized_user_info(info, SCOPES)

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
