from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not set in environment")

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=api_key)

# Function to interact with the GPT model and maintain conversation history
def ask_gpt(prompt, history=None):
    if history is None:
        history = []

    # Append the user's prompt to the conversation history
    history.append({"role": "user", "content": prompt})

    try:
        # Create a chat completion using the GPT-4o Mini model
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=history,
            temperature=0.7,
            max_tokens=2048,
            top_p=1.0
        )

        # Extract the assistant's reply from the response
        reply = response.choices[0].message.content
        print("✅ GPT response:", reply)

        # Append the assistant's reply to the conversation history
        history.append({"role": "assistant", "content": reply})
        return reply, history

    except Exception as e:
        print("❌ GPT call failed:", e)
        return "An error occurred while communicating with the GPT model.", history
