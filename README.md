# Creator Resume Review

A Gemini-powered resume optimization tool that provides personalized feedback based on expert creator insights, with both Streamlit web interface and WhatsApp integration.

## Features

### 🌐 Streamlit Web App
- Upload PDF resumes for AI-powered review
- Target specific job postings or role types
- Get personalized feedback based on creator expertise
- Grounded in real newsletter content from Aakash

### 📱 WhatsApp Integration
- Send resumes via WhatsApp for instant review
- Receive AI-optimized feedback and PDF
- Automatic job description extraction
- Creator-grounded citations and insights

## Quick Start

### Prerequisites
- Python 3.8+
- Gemini API key
- Twilio account (for WhatsApp integration)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd creatorresumereview
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your API keys
```

### Environment Variables

Create a `.env` file with the following variables:

```env
# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Twilio WhatsApp Configuration (for WhatsApp integration)
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_WHATSAPP_NUMBER=+1234567890

# Static File Server (optional)
STATIC_BASE_URL=https://your-domain.com/static

# Flask Configuration
FLASK_ENV=production
PORT=5000
```

## Usage

### Streamlit Web App

Run the Streamlit app:
```bash
streamlit run streamlit_apps/resume_review_app.py
```

Visit `http://localhost:8501` to use the web interface.

### WhatsApp API

Run the Flask API server:
```bash
python app.py
```

The API will be available at `http://localhost:5000`.

#### API Endpoints

**POST /api/whatsapp-upload**
- Accepts resume URL, job URL, and phone number
- Returns AI-optimized feedback and PDF

Example request:
```json
{
    "resumeUrl": "https://example.com/resume.pdf",
    "jobUrl": "https://jobs.company.com/product-manager",
    "userMessage": "Optional user message",
    "phone": "+1234567890"
}
```

**GET /api/health**
- Health check endpoint

**GET /api/logs**
- View recent activity logs

## Architecture

### Core Components

- **`core/creator_review.py`** - Gemini AI integration and resume processing logic
- **`utils/pdf_writer.py`** - PDF generation with styled output
- **`routes/whatsapp_response.py`** - Twilio WhatsApp integration
- **`api/whatsapp_upload.py`** - Main API endpoint for WhatsApp processing
- **`streamlit_apps/resume_review_app.py`** - Web interface

### Data Flow

1. **WhatsApp Flow:**
   - User sends resume URL + job URL via WhatsApp
   - API downloads and processes resume
   - Gemini AI generates personalized feedback
   - PDF is created with optimized bullets
   - Response sent back via WhatsApp

2. **Web Flow:**
   - User uploads PDF via Streamlit interface
   - Same AI processing pipeline
   - Results displayed in web interface

### Guardrails

- **File Validation:** Only PDF files under 5MB accepted
- **Confidence Scoring:** Reviews with score < 0.82 trigger fallback messages
- **Error Handling:** Graceful error messages sent via WhatsApp
- **Rate Limiting:** Built-in request throttling
- **Logging:** All user activity logged to `review_logs.json`

## Creator Grounding

The system is grounded in real expertise from Aakash's newsletter on resume optimization, following 6 key principles:

1. **Recast experience to become ideal**
2. **Re-tell story to be a straight line**
3. **Customize every bullet for the job**
4. **Use keywords the ATS seeks**
5. **Drop examples to intrigue**
6. **Flip weaknesses into strengths**

## Deployment

### Local Development
```bash
# Run Streamlit app
streamlit run streamlit_apps/resume_review_app.py

# Run API server (in another terminal)
python app.py
```

### Production Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY=your_key
export TWILIO_ACCOUNT_SID=your_sid
export TWILIO_AUTH_TOKEN=your_token
export TWILIO_WHATSAPP_NUMBER=your_number

# Run the API server
python app.py
```

### Docker Deployment
```bash
# Build image
docker build -t resume-review .

# Run container
docker run -p 5000:5000 --env-file .env resume-review
```

## Monitoring

- **Health Check:** `GET /api/health`
- **Activity Logs:** `GET /api/logs`
- **Log File:** `review_logs.json` (local file)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the logs: `GET /api/logs`
- Review error messages in the response
- Ensure all environment variables are set correctly 