# Vercel serverless function handler for Flask app
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# This is the WSGI handler that Vercel will use
# Vercel expects a function that can handle requests
handler = app
