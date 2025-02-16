# PR_brainfit_analysis/config/settings.py

from pathlib import Path
import os
import pytz

# Data paths and directories
DATA_DIR = Path(os.getenv('DATA_DIR', 'data'))
OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', 'outputs'))

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

import os
from pathlib import Path
import pytz

# Try to import local config
try:
    import config_local
    GOOGLE_CREDENTIALS_PATH = config_local.GOOGLE_CREDENTIALS_PATH
    GOOGLE_SHEET_ID = config_local.GOOGLE_SHEET_ID
    GOOGLE_SHEET_RANGE = config_local.GOOGLE_SHEET_RANGE
    BIOMETRIC_DATA_PATH = config_local.BIOMETRIC_DATA_PATH
    CASK_DATA_PATH = config_local.CASK_DATA_PATH
except ImportError:
    # Default values if no local config exists
    DATA_DIR = Path(os.getenv('DATA_DIR', 'data'))
    GOOGLE_CREDENTIALS_PATH = DATA_DIR / 'credentials.json'
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    GOOGLE_SHEET_RANGE = os.getenv('GOOGLE_SHEET_RANGE', 'user_data!A1:K1000')
    BIOMETRIC_DATA_PATH = DATA_DIR / 'historic_processed_data_for_plotting.json'
    CASK_DATA_PATH = DATA_DIR / 'cask_data.csv'
    
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Time settings
DEFAULT_TIMEZONE = pytz.timezone('Europe/London')
WORKING_HOURS = {
    'start': '08:00',
    'end': '17:00'
}

# Group configuration
GROUP_MAPPING = {
    'DALMUIR': ['dalmuir', 'Dalmuir'],
    'KILMALID': ['kilmalid', 'Kilmalid'],
    'KB3': ['kb3', 'KB3', 'NOPS'],
    'SUPERVISORS': ['dalm_sup', 'kilm_sup', 'KB3_sup']
}

# Activity level thresholds (percentage above resting heart rate)
ACTIVITY_THRESHOLDS = {
    'sedentary': 20,    # 0-20% above resting
    'light': 40,        # 20-40% above resting
    'moderate': 70,     # 40-70% above resting
    'intense': 100      # >70% above resting
}

# Stress calculation parameters
STRESS_PARAMS = {
    'min_stress': 0,
    'max_stress': 100,
    'resting_hr_percentile': 5,  # Use 5th percentile for resting heart rate
    'time_weight': 0.3          # Weight for time-of-day adjustment
}

# Data quality thresholds
QUALITY_THRESHOLDS = {
    'min_daily_records': 100,    # Minimum records per day
    'max_hr': 200,               # Maximum reasonable heart rate
    'min_hr': 40,                # Minimum reasonable heart rate
}