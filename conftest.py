import sys
import os

# Add both lambda directories to sys.path so imports work in tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lambda"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "daily_update_lambda"))
