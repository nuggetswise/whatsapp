# Resume Review App by Aakash

A Streamlit app that provides grounded resume feedback using Gemini AI, based on real expertise from creator newsletters.

## Features

- **PDF Resume Upload**: Upload your resume in PDF format
- **Target Role Selection**: Choose from various PM roles (Series A startup, FAANG, etc.)
- **Grounded Feedback**: AI feedback based on real article content from Aakash's newsletter
- **Specific Improvements**: Get 3-5 actionable suggestions with highlighted quotes
- **Source Attribution**: See the original article content that grounds the feedback

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app**:
   ```bash
   cd streamlit_apps
   streamlit run resume_review_app.py
   ```

3. **Use the app**:
   - Upload your resume PDF in the sidebar
   - Select your target role from the dropdown
   - Click "Get Review" to receive personalized feedback

## How It Works

The app uses hardcoded grounding content from Aakash's newsletter:
> "Most PM resumes are filled with lines like: 'Led roadmap planning for multiple product features.' Instead, show the outcome. What did that roadmap achieve? Did revenue go up? Did user retention increase? You need to show what changed because of your work."

This content is used to provide specific, actionable feedback that's grounded in proven strategies.

## Technical Details

- **Framework**: Streamlit
- **PDF Processing**: PyPDF2 for text extraction
- **AI Model**: Gemini (currently using mock responses)
- **Grounding**: Real article content from creator newsletters

## Environment Setup

1. **Set your Gemini API key**:
   ```bash
   export GEMINI_API_KEY='your-gemini-api-key-here'
   ```
   
   Or create a `.env` file:
   ```
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

2. **Get your API key** from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Next Steps

- Add more creators and grounding content
- Implement user authentication and feedback history
- Add more role types and customization options 