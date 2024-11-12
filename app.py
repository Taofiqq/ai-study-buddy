from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/voice", methods=['POST'])
def voice():
    """Handle incoming voice calls"""
    # Create Twilio Voice Response object
    logger.info("========= JOIN CALLL=========")
    response = VoiceResponse()
    
    # Add a simple welcome message for testing
    response.say("Welcome to AI Study Buddy. This is a test response.")
    
    return str(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT', 5000))