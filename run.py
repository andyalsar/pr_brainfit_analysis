# run.py
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent / 'src')
sys.path.append(src_path)

from pr_brainfit.main import main

if __name__ == "__main__":
    main()