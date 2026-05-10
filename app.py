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
    
    # Renderの環境変数からトークン情報を読み込む
    env_token = os.environ.get('GOOGLE_TOKEN_JSON')
    if env_token:
        info = json.loads(env_token)
        creds = Credentials.from_authorized_user_info(info, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Renderの環境変数から認証情報を読み込む
            env_creds = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            if env_creds:
                info = json.loads(env_creds)
                # クライアントIDなどの詳細設定を環境変数から直接構成
                from google_auth_oauthlib.flow import InstalledAppFlow
                # 一時的なファイルを作らずに設定を読み込む
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
    # Renderではポート番号を環境変数から取得するのが一般的です
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
