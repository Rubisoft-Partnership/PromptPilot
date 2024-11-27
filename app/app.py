import os
from langfuse.openai import OpenAI
import ollama

model_name = "smollm2"

# Initialize the OpenAI client from Langfuse
client = OpenAI(
    base_url='http://ollama:11434/v1',  # Ollama's API endpoint
    api_key='ollama',  # Required but not used by Ollama
)

# Sample conversation
response = client.chat.completions.create(
    model=model_name,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ]
)

# Get the response text
response_text = response.choices[0].message.content

# Print the response
print("Response from Ollama:", response_text)