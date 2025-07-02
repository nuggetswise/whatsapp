import os
from flask import Flask, send_from_directory
from api.whatsapp_upload import app as whatsapp_blueprint
from routes.whatsapp_inbound import inbound

# Create main Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Register API routes
app.register_blueprint(whatsapp_blueprint, url_prefix='/api')
app.register_blueprint(inbound)

# Serve static files (PDFs)
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (PDFs) from the static directory."""
    return send_from_directory('static', filename)

# Health check endpoint
@app.route('/')
def health_check():
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "service": "Newsletter-Grounded Resume Review WhatsApp API",
        "version": "2.0.0",
        "system": "newsletter-grounded",
        "features": [
            "Newsletter-grounded feedback",
            "Job description parsing",
            "Relevance scoring",
            "WhatsApp integration",
            "Multi-platform JD support"
        ],
        "endpoints": {
            "whatsapp_upload": "/api/whatsapp-upload",
            "health": "/api/health",
            "logs": "/api/logs",
            "newsletter_status": "/api/newsletter-status",
            "whatsapp_inbound": "/whatsapp-inbound"
        }
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=False) 