from flask import Flask, request, render_template, jsonify
import os
from langfuse.openai import OpenAI
from langfuse import Langfuse
import logging
from promptpilot.versioning.tree import PromptTree  # Import PromptTree

# Flask app instance
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Langfuse client
langfuse_client = Langfuse(
    public_key=os.environ.get('LANGFUSE_PUBLIC_KEY'),
    secret_key=os.environ.get('LANGFUSE_SECRET_KEY'),
    host=os.environ.get('LANGFUSE_HOST'),
)

# Initialize the OpenAI client from LangFuse
client = OpenAI(
    base_url="http://ollama:11434/v1",  # Ollama's API endpoint
    api_key="ollama",  # Required but not used by Ollama
)

model_name = "smollm2"
prompt_name = "movie-critic"

# Initialize the PromptTree with the Langfuse client
prompt_manager = PromptTree(langfuse_client=langfuse_client)

# Remove unused Langfuse.get_prompt if not needed

@app.route("/", methods=["GET"])
def index():
    return render_template("chat.html")

@app.route("/message", methods=["POST"])
def message():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "No message provided."}), 400

    try:
        # Get the latest system prompt using PromptTree
        system_prompt = prompt_manager.get_latest_prompt(name=prompt_name)

        # If no prompt is found, use a default
        if system_prompt:
            system_prompt = system_prompt.compile(criticLevel="expert", movie="Inception")
        else:
            system_prompt = "You are a helpful assistant."

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
        )
        response_text = response.choices[0].message.content
        logger.info(f"User input: {user_input}")
        logger.info(f"Assistant response: {response_text}")

        return jsonify({"response": response_text})
    except Exception as e:
        logger.error(f"Error during chat completion: {e}", exc_info=True)
        return jsonify({
            "error": "Unexpected error occurred. Please check your request and contact support: https://langfuse.com/support."
        }), 500

@app.route("/prompts", methods=["GET"])
def display_prompts():
    try:
        # Fetch prompts from Langfuse
        response = langfuse_client.client.prompts.list()
        prompts = response.data

        # Prepare data to display
        prompts_list = []
        for prompt_meta in prompts:
            # Get the latest version
            latest_version = max(prompt_meta.versions) if prompt_meta.versions else None

            # Get the last updated time
            last_updated = prompt_meta.last_updated_at.isoformat() if prompt_meta.last_updated_at else ''

            prompt_info = {
                "name": prompt_meta.name,
                "versions": prompt_meta.versions,
                "latest_version": latest_version,
                "labels": prompt_meta.labels,
                "tags": prompt_meta.tags,
                "last_updated_at": last_updated,
                "last_config": prompt_meta.last_config,
            }
            prompts_list.append(prompt_info)

        # Return the prompts as JSON
        return jsonify(prompts_list)

    except Exception as e:
        logger.error(f"Error fetching prompts: {e}", exc_info=True)
        return (
            "An error occurred while fetching prompts. Please try again later.",
            500,
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)