from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv
import os
import logging

load_dotenv()
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/voice", methods=['POST'])
def voice():
    """Handle incoming calls with an interactive menu"""
    logger.info("========= CALL JOINED =========")
    response = VoiceResponse()
    
    # Initial greeting
    response.say("Welcome to AI Study Buddy! Let's start your study session.")
    
    # Gather the user's subject choice
    gather = response.gather(
        num_digits=1,
        action='/handle-subject',
        method='POST',
        timeout=5
    )
    
    gather.say("Please select a subject to study. Press 1 for Mathematics, press 2 for Science, press 3 for History.")
    
    # If no input, repeat the menu
    response.redirect('/voice')
    
    return str(response)

@app.route("/handle-subject", methods=['POST'])
def handle_subject():
    """Handle the subject selection"""
    logger.info("========= REACHED HANDLE SUBJECT =========")
    digit_pressed = request.values.get('Digits', None)
    response = VoiceResponse()
    
    # Map digits to subjects
    subjects = {
        '1': 'Mathematics',
        '2': 'Science',
        '3': 'History'
    }
    
    if digit_pressed in subjects:
        subject = subjects[digit_pressed]
        response.say(f"You've selected {subject}. Let's begin your study session.")
        
        # Gather user's question
        gather = response.gather(
            input='speech',
            action='/handle-question',
            method='POST',
            language='en-US',
            timeout=5
        )
        gather.say("Please ask your question about " + subject)
    else:
        response.say("Invalid selection.")
        response.redirect('/voice')
    
    return str(response)

@app.route("/handle-question", methods=['POST'])
def handle_question():
    """Handle the user's study question"""
    response = VoiceResponse()
    
    # Get the user's spoken question
    question = request.values.get('SpeechResult', '')
    print(f"Received question: {question}")  # Debug print
    
    # For now, just echo the question back
    response.say(f"You asked: {question}. This feature will be implemented next.")
    
    return str(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT', 5000))