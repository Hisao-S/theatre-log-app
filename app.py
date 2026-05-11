import os
import json
from flask import Flask, render_template, request
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

# カレンダーの権限を追加しました
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/calendar.events'
]
SPREADSHEET_ID = '1UnO_VzSQPRgrYzxk4t9lwLG-qsMR_QY9OcrlHW1Oqzc'

def get_creds():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds:
        env_token = os.environ.get('GOOGLE_TOKEN_JSON')
        if env_token:
            info = json.loads(env_token)
            creds = Credentials.from_authorized_user_info(info, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if os.path.exists('credentials.json'):
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        else:
            env_creds = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            if env_creds:
                info = json.loads(env_creds)
                creds = Credentials.from_authorized_user_info(info, SCOPES)
    return creds

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

    creds = get_creds()

    # --- スプレッドシートへの書き込み ---
    sheet_service = build('sheets', 'v4', credentials=creds)
    values = [["", date, time, title, theater, station, seat, contact]]
    sheet_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='観劇履歴!A2',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body={'values': values}).execute()

    # --- Googleカレンダーへの登録 ---
    try:
        calendar_service = build('calendar', 'v3', credentials=creds)
        # 日時をGoogleカレンダーが読める形式に変換 (例: 2026-05-11 14:00)
        start_time_str = f"{date} {time}:00"
        start_dt = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        # 終了時間はとりあえず3時間後に設定
        end_dt = start_dt + timedelta(hours=3)

        event = {
            'summary': title,
            'location': theater,
            'description': f"最寄り駅: {station}\n座席: {seat}\n扱い: {contact}",
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Asia/Tokyo'},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Asia/Tokyo'},
        }
        calendar_service.events().insert(calendarId='primary', body=event).execute()
    except Exception as e:
        print(f"Calendar Error: {e}")

    return "<h1>Recorded! (Sheet & Calendar)</h1><a href='/'>Back</a>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
