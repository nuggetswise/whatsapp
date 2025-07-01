#!/bin/bash

# Resume Review App Deployment Script
echo "🚀 Deploying Resume Review App..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set environment variables (make sure to set GEMINI_API_KEY in your environment)
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  Warning: GEMINI_API_KEY environment variable not set"
    echo "   Please set it with: export GEMINI_API_KEY='your-api-key'"
fi

# Run the Streamlit app
echo "🌐 Starting Streamlit app..."
cd streamlit_apps
streamlit run resume_review_app.py --server.port 8501 --server.address 0.0.0.0 