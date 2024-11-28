from flask import Flask, request, render_template
import os
from langfuse.openai import OpenAI

app = Flask(__name__)

# Initialize the OpenAI client
client = OpenAI(
    base_url='http://ollama:11434/v1',
    api_key='ollama',
)

model_name = "smollm2"

@app.route('/', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user_input = request.form['message']
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input},
            ]
        )
        response_text = response.choices[0].message.content
        return render_template('chat.html', user_input=user_input, response_text=response_text)
    return render_template('chat.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)