import os

SCOPES = [os.getenv('SCOPES', 'https://www.googleapis.com/auth/spreadsheets.readonly')]
GOOGLE_SHEET_ID = str(os.getenv('GOOGLE_SHEET_ID', '1kMQ2ohv0EhKZKwzT0ezF-lXVB-zaHqbzabr66HyTrvo'))
GOOGLE_SHEET_RANGE = str(os.getenv('GOOGLE_SHEET_RANGE', 'user_data!A1:K1000'))
GOOGLE_CREDENTIALS_PATH = str(os.getenv('GOOGLE_CREDENTIALS_PATH', '/Users/andylow/Library/Mobile Documents/com~apple~CloudDocs/Desktop/Data/config/level-agent-406308-69554860e8b0.json'))

