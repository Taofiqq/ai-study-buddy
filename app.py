from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv
from openai import OpenAI
import os
import logging
from collections import defaultdict
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


session_data = defaultdict(list)

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
    response.say("Welcome to Developer Voice Assistant! I'm here to help with your technical questions.")
    
    # Gather the user's subject choice
    gather = response.gather(
        num_digits=1,
        action='/handle-subject',
        method='POST',
        timeout=5
    )
    
    gather.say("Please select a topic. Press 1 for Twilio APIs, press 2 for Python Development, press 3 for Integration Help.")
    
    # If no input, repeat the menu
    response.redirect('/voice')
    
    return str(response)

@app.route("/handle-subject", methods=['POST'])
def handle_subject():
    """Handle the subject selection"""
    logger.info("=======SUBJECT HANDLING ==========")
    digit_pressed = request.values.get('Digits', None)
    response = VoiceResponse()
    
    # Map digits to technical subjects
    subjects = {
        '1': 'Twilio APIs',
        '2': 'Python Development',
        '3': 'Integration Help'
    }
    
    if digit_pressed in subjects:
        subject = subjects[digit_pressed]
        response.say(f"You've selected {subject}. What would you like to know?")
        
        # Gather user's question
        gather = response.gather(
            input='speech',
            action='/handle-question',
            method='POST',
            language='en-US',
            timeout=5
        )
        gather.say(f"Please ask your {subject} question.")
    else:
        response.say("Invalid selection.")
        response.redirect('/voice')
    
    return str(response)

@app.route("/handle-question", methods=['POST'])
def handle_question():
    """Handle the user's technical question"""
    logger.info("======= HANDLE QUESTIONS ==========")
    response = VoiceResponse()
    
    # Get the user's spoken question and subject context
    question = request.values.get('SpeechResult', '')
    subject = request.values.get('subject', 'general')
    caller_number = request.values.get('From', 'anonymous')
    
    try:
        # Generate AI response
        ai_response = generate_ai_response(question, subject)
        
        qa_pair = {
            'question': question,
            'answer': ai_response,
            'subject': subject,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        session_data[caller_number].append(qa_pair)
        logger.info(f"Stored Q&A for caller {caller_number}")
        
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
        logger.error(f"Error generating response: {e}")
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
        response.say("Thank you for using Developer Voice Assistant. Happy coding!")
    
    return str(response)

def generate_ai_response(question, subject):
    """Generate AI response using OpenAI"""
    logger.info("=======CONNECTED TO OPEN AI==========")
    try:
        # Create subject-specific prompts
        system_prompts = {
            'Twilio APIs': "You are a Twilio API expert. Provide clear, technical but accessible explanations about Twilio's services, APIs, and implementation details.",
            'Python Development': "You are a Python development expert. Provide clear, practical explanations about Python programming, best practices, and implementation patterns.",
            'Integration Help': "You are a systems integration expert. Provide clear guidance on integrating different technologies, focusing on best practices and common patterns."
        }
        
        # Create a prompt that includes context and formatting instructions
        prompt = f"""As an expert in {subject}, please answer this technical question: {question}
        Provide a clear, concise explanation suitable for voice response.
        Focus on practical, actionable information.
        Keep the response under 30 seconds when spoken."""

        # Get completion from OpenAI
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompts.get(subject, "You are a helpful technical expert.")},
                {"role": "user", "content": prompt}
            ]
        )
        logger.info("completion", completion.choices[0].message)
        return completion.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "I apologize, but I'm having trouble generating a response right now. Please try asking your question again."


# Add this function to test our setup
@app.route("/test-setup", methods=['GET'])
def test_setup():
    try:
        # Test 1: Session tracking
        test_caller = 'test_phone'
        test_qa = {
            'question': 'test question',
            'answer': 'test answer',
            'subject': 'Python Development',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        session_data[test_caller].append(test_qa)
        
        # Test 2: SendGrid
        message = Mail(
            from_email=os.getenv('SENDGRID_FROM_EMAIL'),  # Make sure this is in your .env
            to_emails=os.getenv('TEST_TO_EMAIL'),  # Add this to your .env
            subject='Test Setup - Developer Voice Assistant',
            html_content='<p>This is a test email to verify SendGrid setup.</p>')
        
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(f"response", response)
        logger.info("info logger", response)
        
        return {
            'session_test': 'OK',
            'sendgrid_test': 'OK',
            'sendgrid_status': response.status_code,
            'session_data': dict(session_data)  # Convert to dict for display
        }
    except Exception as e:
        logger.info("e",e)
        print(f"error", e)
        return {
            'error': str(e)
        }, 500
        

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT', 5001))