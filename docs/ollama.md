Guide: Managing Ollama Models with Docker Volume Mounting

This guide explains how to manage Ollama models by storing them in a directory within your project folder and mounting it as a volume in Docker. This approach allows for easy management of models and ensures they persist across container restarts.

Overview of the Approach

	•	Volume Mounting: We map a directory from your host machine (project folder) to the Ollama container’s model directory.
	•	Model Management: Models are stored in your project folder, making them easy to manage and update.
	•	Docker Configuration: Update your docker-compose.yml to include the volume mapping for the Ollama service.

Steps

1. Create a Directory for Models

In your project folder, create a directory to store the Ollama models:

mkdir ollama_models

2. Modify docker-compose.yml

Update your docker-compose.yml file to add a volume mapping for the Ollama service:

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ./ollama_models:/root/.ollama  # Mount the models directory
    networks:
      - langfuse-network

  # ... other services ...

networks:
  langfuse-network:
    driver: bridge

Explanation:

	•	./ollama_models is the directory in your project where models are stored.
	•	/root/.ollama is the default models directory inside the Ollama container.

3. Pull Models into the Mounted Directory

Option A: Pull Models from the Host Machine

	1.	Install Ollama on Your Host Machine (if not already installed).
	2.	Set the Ollama Home Directory to point to your project folder:

export OLLAMA_HOME=$(pwd)/ollama_models


	3.	Pull the Desired Model:

ollama pull mistral

	•	This downloads the mistral model into the ollama_models directory.

Option B: Pull Models Inside the Ollama Container

	1.	Start Docker Services:

docker-compose up -d


	2.	Pull the Model Inside the Container:

docker-compose exec ollama ollama pull mistral

	•	The model will be stored in ./ollama_models due to the volume mapping.

4. Update Your Application Code

Since the model is already pulled and stored, you can use it directly in your application.

import os
from langfuse.openai import OpenAI

# Set the Ollama host to point to the Ollama service
os.environ["OLLAMA_HOST"] = "http://ollama:11434"

# Initialize the OpenAI client with Ollama's endpoint
client = OpenAI(
    base_url='http://ollama:11434/v1',
    api_key='ollama',  # Required but unused by Ollama
)

response = client.chat.completions.create(
    model="mistral",  # Use the model you pulled
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ]
)

print("Response from Ollama:", response.choices[0].message.content)

5. Rebuild and Start Your Containers

Since you’ve modified the Docker configuration, rebuild your containers:

docker-compose down
docker-compose up --build

6. Manage Your Models

	•	Add New Models: Pull additional models using the same method.
	•	Update Models: Replace or update models directly in the ollama_models directory.
	•	Version Control: Optionally, include ollama_models in your version control system (consider .gitignore for large files).

Benefits of This Approach

	•	Persistence: Models persist across container rebuilds and restarts.
	•	Ease of Management: Manage models directly from your project folder.
	•	Simplified Configuration: No need for complex Docker setups or additional scripts.

Notes

	•	Permissions: Ensure the ollama_models directory has appropriate permissions for Docker to read and write.
	•	Storage Considerations: Be mindful of disk space, as models can be large.
	•	Cross-Platform: This approach works across different operating systems, but be aware of file system differences.

Summary

By mounting a host directory into the Ollama container, you gain full control over the models used by your application. This setup simplifies model management and enhances the portability and persistence of your development environment.

Remember: Always ensure that your Docker services are correctly configured to communicate with each other, and verify that models are properly loaded and accessible by your application.