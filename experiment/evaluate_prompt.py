import logging
import json
import re
from ollama import chat, ChatResponse

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler with INFO level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create file handler with DEBUG level
file_handler = logging.FileHandler('debug.log', mode='w')
file_handler.setLevel(logging.DEBUG)

# Set a detailed format for both handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


# LLM variables
model_name = "llama3.2:3b"

improve_prompt_system = """
You are an advanced language model tasked with optimizing prompt instructions to optimize relevance.
Your goal is to revise the provided Prompt Instruction so that it maximizes the relevance metric.
You can use prompt engineering techniques such as including examples and adding instructions like: "Let's think step by step".

<TASK>
Analyze the given INSTRUCTIONS_TO_IMPROVE.
Revise and improve INSTRUCTIONS_TO_IMPROVE to maximize the relevance metric.
Ensure that the improved prompt is clear, concise.
Do NOT alter the intent or core requirements of the original prompt instruction.
Provide ONLY the improved instructions text string without any additional text or explanation.
</TASK>
"""

improve_prompt_user = """
<INSTRUCTIONS_TO_IMPROVE>
{instruction_prompt}
</INSTRUCTIONS_TO_IMPROVE>

Output ONLY the improved instructions. DO NOT include any additional text or explanation.
"""

relevance_prompt = """
You're an expert in analyzing texts and responses. Evaluate the relevance of the response to the given message.
Output a comma-separated pair score-explanation where the score is between 0 and 1, where 0 means not relevant and 1 means highly relevant, and the explanation is very brief.
PRINT THE LIST ALONE, NOTHING ELSE. The result MUST match this format:
[SCORE 0-1],[EXPLANATION]

<message>
{user_input}
</message>

<response>
{response}
</response>
"""


def improve_prompt(instruction_prompt: str, metric_prompt: str):
    logger.debug("Starting prompt improvement process.")
    logger.debug(f"Improving prompt using model '{model_name}'.")
    response: ChatResponse = chat(
        model=model_name,
        messages=[
            {"role": "system", "content": improve_prompt_system},
            {
                "role": "user",
                "content": improve_prompt_user.format(
                    instruction_prompt=instruction_prompt, metric_prompt=metric_prompt
                ),
            },
        ],
    )
    response_text = response.message.content
    logger.debug(f"Input improve prompt: {improve_prompt_user.format(instruction_prompt=instruction_prompt, metric_prompt=metric_prompt)}")
    logger.info(f"User prompt: {instruction_prompt}")
    logger.info(f"Output prompt: {response_text}")
    logger.debug("Prompt improvement completed successfully.")
    return response_text


def parse_score_explanation(text):
    logger.debug("Parsing score and explanation from the evaluator response.")
    pattern = r"^(\S+),\s*(.*)$"
    match = re.match(pattern, text)
    if match:
        logger.debug("Successfully parsed score and explanation.")
        return {"score": match.group(1).strip(), "explanation": match.group(2).strip()}
    else:
        logger.debug("Failed to parse score and explanation.")
        return {"score": None, "explanation": None}


def relevance_score(user_input: str, response: str):
    logger.debug("Evaluating relevance score using relevance prompt.")
    evaluation: ChatResponse = chat(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": relevance_prompt.format(
                    user_input=user_input, response=response
                ),
            }
        ]
    )
    result = parse_score_explanation(evaluation.message.content.strip())
    logger.info(f"Evaluating user input: {user_input}")
    logger.debug(f"Relevance prompt: {relevance_prompt.format(user_input=user_input, response=response)}")
    logger.debug(f"Assistant response: {evaluation.message.content.strip()}")
    logger.info(f"Relevance evaluation result: {result}")
    return result


def instructions_response(user_input: str):
    logger.debug("Generating response for the user instructions.")
    response: ChatResponse = chat(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are an advanced language model. Your task is to generate a response following given instructions."},
            {"role": "user", "content": user_input},
        ],
    )
    response_text = response.message.content
    logger.info(f"User input instructions: {user_input}")
    logger.info(f"Assistant response: {response_text}")
    logger.debug("Response generation completed successfully.")
    return response_text


def main(file: str, start: int, limit: int, output_file: str):
    logger.debug("Starting main function.")
    logger.debug(f"Reading data from {file}. Start: {start}, Limit: {limit}")
    prompts = []

    # Read the dataset
    if file.endswith(".jsonl"):
        logger.debug("Reading data from JSONL file.")
        with open(file, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    logger.debug(f"Skipping empty line at {line_no}.")
                    continue
                data = json.loads(line)
                if "response" in data:
                    prompts.append(data["response"])
    elif file.endswith(".json"):
        logger.debug("Reading data from JSON file.")
        with open(file, "r", encoding="utf-8") as f:
            prompts = json.load(f)[start : start + limit]
    else:
        logger.error("Invalid file format. Please provide a JSON or JSONL file.")
        return

    logger.debug(f"Total prompts read: {len(prompts)}")
    # Select the subset of prompts
    selected_prompts = prompts[start : start + limit]
    logger.debug(f"Selected {len(selected_prompts)} prompts for processing.")

    results = []
    for idx, original_prompt in enumerate(selected_prompts, start=1):
        original_prompt = original_prompt["instruction"].strip()

        logger.debug(f"Processing prompt {idx}/{len(selected_prompts)}.")
        # Improve the prompt
        improved_prompt = improve_prompt(original_prompt, relevance_prompt)

        samples = []
        n_samples = 10
        for i in range(n_samples):
            logger.debug(f"Processing sample {i + 1}/{n_samples}.")
            original_response = instructions_response(original_prompt)
            original_score = relevance_score(original_prompt, original_response)

            improved_response = instructions_response(improved_prompt)
            improved_score = relevance_score(improved_prompt, improved_response)

            samples.append({"original_response": original_response, "original_score": original_score,
             "improved_response": improved_response, "improved_score": improved_score})
            logger.debug(f"Completed sample {i + 1}/{n_samples}.")
        
        results.append(samples)
        logger.debug(f"Completed processing for prompt {idx}.")

    if file.endswith(".json"):
        logger.debug("Saving results to a JSON file.")
        with open(output_file, "w", encoding="utf-8") as out_f:
            json.dump(results, out_f, indent=4)
        logger.debug("All results saved successfully.")
    elif file.endswith(".jsonl"):
        # Save the results in a JSONL file
        logger.debug(f"Saving results to {output_file}.")
        with open(output_file, "w", encoding="utf-8") as out_f:
            for res in results:
                out_f.write(json.dumps(res) + "\n")
        logger.debug("All results saved successfully.")
    logger.debug("Main function completed.")


if __name__ == "__main__":
    # input_jsonl = "dataset/data.jsonl"
    input_jsonl = "dataset/alpaca_instructions.json"
    output_jsonl = "results/improved_results.json"
    main(input_jsonl, 0, 20, output_jsonl)