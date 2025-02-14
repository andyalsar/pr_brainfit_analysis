import os

SCOPES = [os.getenv('SCOPES', 'https://www.googleapis.com/auth/spreadsheets.readonly')]
GOOGLE_SHEET_ID = str(os.getenv('GOOGLE_SHEET_ID', 'XXX'))
GOOGLE_SHEET_RANGE = str(os.getenv('GOOGLE_SHEET_RANGE', 'user_data!A1:K1000'))
GOOGLE_CREDENTIALS_PATH = str(os.getenv('GOOGLE_CREDENTIALS_PATH', 'XXX.json'))

