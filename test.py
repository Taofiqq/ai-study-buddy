# test.py
import os
from dotenv import load_dotenv
from twilio.rest import Client
import openai

load_dotenv()

def test_credentials():
    # Test Twilio credentials
    try:
        twilio_client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        print("Twilio credentials are valid!")
    except Exception as e:
        print(f"Twilio credentials error: {e}")

    # Test OpenAI credentials
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print("OpenAI credentials are valid!")
    except Exception as e:
        print(f"OpenAI credentials error: {e}")

if __name__ == "__main__":
    test_credentials()