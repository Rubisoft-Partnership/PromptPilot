from flask import Flask, request, render_template
import os
from langfuse.openai import OpenAI
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the OpenAI client from LangFuse
client = OpenAI(
    base_url='http://ollama:11434/v1',  # Ollama's API endpoint
    api_key='ollama',  # Required but not used by Ollama
)

model_name = "smollm2"

@app.route('/', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user_input = request.form['message']
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_input},
                ]
            )
            response_text = response.choices[0].message.content
            logger.info(f"User input: {user_input}")
            logger.info(f"Assistant response: {response_text}")
            return render_template('chat.html', user_input=user_input, response_text=response_text)
        except Exception as e:
            logger.error(f"Error during chat completion: {e}", exc_info=True)
            return "Unexpected error occurred. Please check your request and contact support: https://langfuse.com/support.", 500
    return render_template('chat.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)