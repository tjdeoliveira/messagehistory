from flask import Flask, render_template, request, redirect, url_for, send_file
import requests
import pandas as pd
import time
import openpyxl
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_chats', methods=['POST'])
def get_chats():
    company_id = request.form['company_id']
    bearer_token = request.form['bearer_token']
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    start_date = pd.to_datetime(start_date).date()
    end_date = pd.to_datetime(end_date).date()

    base_url = f"https://api.huggy.app/v3/companies/{company_id}/chats/"

    params = {
        "page": 0,
        "created_at_from": start_date,
        "created_at_to": end_date
    }

    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }

    all_chats = []

    while True:
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code != 200:
            return f"Erro ao fazer a requisição: {response.status_code}"

        data = response.json()

        if not data:
            break

        all_chats.extend(data)

        params["page"] += 1

        time.sleep(0.5)

    df = pd.DataFrame(all_chats)

    df['createdAt'] = pd.to_datetime(df['createdAt'], errors='coerce').dt.date
    chat_ids = df['id'].tolist()

    base_url_messages = f"https://api.huggy.app/v3/companies/{company_id}/chats/{{id}}/messages"
    all_messages = []

    for chat_id in chat_ids:
        url = base_url_messages.format(id=chat_id)
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Erro ao fazer a requisição para chat ID {chat_id}: {response.status_code}")
            continue

        data = response.json()
        all_messages.extend(data)

        time.sleep(0.2)

    messages_df = pd.DataFrame(all_messages)
    output_filename_messages = "chat_messages.xlsx"
    messages_df.to_excel(output_filename_messages, index=False)

    return redirect(url_for('download_file', filename=output_filename_messages))

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

