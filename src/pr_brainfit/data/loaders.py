# PR_brainfit_analysis/data/loaders.py

import json
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import pytz
from pr_brainfit.config.settings import * 

def load_biometric_data(file_path):
    """Load and process biometric data from JSON"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Initialize lists for raw data
    raw_records = []
    
    for user_id, user_data in data.items():
        raw_data = user_data.get('historic_raw_data', [])
        for record in raw_data:
            record['user_id'] = user_id
            raw_records.append(record)
    
    # Convert to DataFrame
    df = pd.DataFrame(raw_records)
    
    # Use ISO8601 format to handle timestamps with microseconds
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
    
    return df


def load_user_data():
    """Load user mapping data from Google Sheets and filter for PR org and relevant groups"""
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_PATH, 
        scopes=SCOPES
    )
    
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=GOOGLE_SHEET_RANGE
    ).execute()
    
    values = result.get('values', [])
    headers = [col.strip().lower() for col in values[0]]
    df = pd.DataFrame(values[1:], columns=headers)
    
    # Convert age to numeric
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    
    # Filter for PR org and specific groups
    valid_groups = ['kilmalid', 'dalmuir', 'kb3', 'nops']
    df = df[
        (df['org'].str.lower() == 'pr') & 
        (df['group'].str.lower().isin(valid_groups))
    ]
    print(df)
    return df

def load_cask_data(file_path):
    df = pd.read_csv(file_path)
    
    # Create date column from year and month
    df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01')
    
    # Convert site names to match standardized groups
    df['site'] = df['site'].str.upper()
    valid_sites = ['KILMALID', 'DALMUIR', 'KB3']
    df = df[df['site'].isin(valid_sites)]
    
    # Calculate month-over-month changes
    # Divide by 100 to get proper decimal representation of percentages
    df['receipts_mom_var'] = df.groupby('site')['receipts'].pct_change()  # Remove the * 100
    df['dispatches_mom_var'] = df.groupby('site')['dispatches'].pct_change()  # Remove the * 100
    
    # Calculate efficiency ratio
    df['efficiency_ratio'] = df['dispatches'] / df['receipts']
    
    return df
