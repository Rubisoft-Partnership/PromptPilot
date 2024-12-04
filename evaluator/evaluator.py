import os
from langfuse import Langfuse
from langfuse.openai import OpenAI
from datetime import datetime, timedelta, timezone
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Langfuse client
langfuse_client = Langfuse(
    public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
    secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
    host=os.getenv('LANGFUSE_HOST'),
)

# Initialize OpenAI client
client = OpenAI(
    base_url="http://ollama:11434/v1",
    api_key="ollama",
)

model_name = "smollm2"

BATCH_SIZE = 10
TOTAL_TRACES = 50

template_tone_eval = """
You're an expert in human emotional intelligence. Identify the tones in the text.
Output a comma-separated list of three tones: neutral, confident, joyful, optimistic, friendly, urgent, analytical, respectful.
PRINT THE LIST ALONE, NOTHING ELSE.

<text>
{text}
</text>
"""

def get_traces(tags, limit=TOTAL_TRACES, from_timestamp=None, to_timestamp=None):
    all_traces = []
    page = 1
    while len(all_traces) < limit:
        traces = langfuse_client.fetch_traces(
            page=page,
            limit=BATCH_SIZE,
            tags=tags,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp
        ).data
        if not traces:
            break
        all_traces.extend(traces)
        page += 1
    return all_traces[:limit]

def tone_score(trace):
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": template_tone_eval.format(text=trace.output)}],
        temperature=0
    )
    return response.choices[0].message.content.strip()

def joyfulness_score(trace):
    # Replace with actual Deepeval logic
    score = 0.8  # Example numeric score
    reason = "Engaging and fun."
    return {"score": score, "reason": reason}

def evaluate_trace(trace):
    tone = tone_score(trace)
    joy = joyfulness_score(trace)
    
    # Push categorical score
    langfuse_client.score(
        trace_id=trace.id,
        name="tone",
        value=tone,
        data_type="CATEGORICAL",
        comment="Automated tone evaluation"
    )
    
    # Push numeric score
    langfuse_client.score(
        trace_id=trace.id,
        name="joyfulness",
        value=joy["score"],
        data_type="NUMERIC",
        comment=joy["reason"]
    )

def main():
    while True:
        try:
            now = datetime.now(timezone.utc)
            to_timestamp = now.replace(second=0, microsecond=0)
            from_timestamp = now - timedelta(hours=1)
            
            logger.debug(f"Fetching traces from {from_timestamp} to {to_timestamp}")
            
            traces = get_traces(
                tags="ext_eval_pipelines",
                limit=TOTAL_TRACES,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp
            )
            logger.info(f"Fetched {len(traces)} traces")
            
            for trace in traces:
                if trace.output:
                    try:
                        evaluate_trace(trace)
                        logger.info(f"Evaluated trace {trace.id}")
                    except Exception as e:
                        logger.error(f"Error evaluating trace {trace.id}: {e}")
                else:
                    logger.warning(f"Trace {trace.id} has no output")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        
        time.sleep(600)  # Run every 10 minutes

if __name__ == "__main__":
    main()