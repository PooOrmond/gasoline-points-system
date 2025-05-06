#!/bin/bash
# Install Python dependencies
pip install -r requirements.txt

# Apply database migrations (if using Flask-Migrate)
# flask db upgrade

# Collect static files (if needed)
# flask collectstatic