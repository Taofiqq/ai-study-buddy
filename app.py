from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv
from openai import OpenAI
import os
import logging

load_dotenv()
app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/voice", methods=['POST'])
def voice():
    """Handle incoming calls with an interactive menu"""
    logger.info("=======VOICE RECEIVED==========")
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
    logger.info("=======SUBJECT HANDLING ==========")
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
    logger.info("======= HANDLE QUESTIONS ==========")
    response = VoiceResponse()
    
    # Get the user's spoken question and subject context
    question = request.values.get('SpeechResult', '')
    subject = request.values.get('subject', 'general')  # Get subject from session if available
    
    try:
        # Generate AI response
        ai_response = generate_ai_response(question, subject)
        
        # Convert AI response to speech
        response.say(ai_response)
        
        # Ask if they want to ask another question
        gather = response.gather(
            num_digits=1,
            action='/handle-continue',
            method='POST',
            timeout=5
        )
        gather.say("Would you like to ask another question? Press 1 for yes, or 2 to end the session.")
        
    except Exception as e:
        print(f"Error generating response: {e}")
        response.say("I apologize, but I'm having trouble generating a response. Please try asking your question again.")
        response.redirect('/voice')
    
    return str(response)

@app.route("/handle-continue", methods=['POST'])
def handle_continue():
    """Handle whether the user wants to continue"""
    logger.info("=======HANDLE CONTINUE==========")
    digit_pressed = request.values.get('Digits', None)
    response = VoiceResponse()
    
    if digit_pressed == '1':
        response.redirect('/voice')
    else:
        response.say("Thank you for using AI Study Buddy. Goodbye!")
    
    return str(response)

def generate_ai_response(question, subject):
    """Generate AI response using OpenAI"""
    logger.info("=======CONNECTED TO OPEN AI==========")
    try:
        # Create a prompt that includes context and formatting instructions
        prompt = f"""You are a helpful study buddy explaining a {subject} concept. 
        The question is: {question}
        Please provide a clear, concise explanation suitable for voice response.
        Keep the response under 30 seconds when spoken."""

        # Get completion from OpenAI
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful and knowledgeable tutor, providing clear and concise explanations."},
                {"role": "user", "content": prompt}
            ]
        )
        logger.info("completion", completion)
        # Extract and return the response
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "I apologize, but I'm having trouble generating a response right now. Please try asking your question again."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT', 5000))