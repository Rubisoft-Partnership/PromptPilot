from datetime import datetime, timezone
import json
from langfuse.model import TextPromptClient, ChatPromptClient
from langfuse.api.resources.prompts.types import Prompt_Text, Prompt_Chat
import logging

logger = logging.getLogger(__name__)

class PromptTree:
    def __init__(self, langfuse_client, file_path='prompt_history.json'):
        self.file_path = file_path
        self.langfuse_client = langfuse_client
        self.tree = self.load_tree()
        self.sync_with_langfuse()

    def load_tree(self):
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Initialize with an empty dictionary of prompts
            return {"prompts": {}}

    def save_tree(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.tree, f, indent=2)

    def create_prompt(self, name, content, config, parent_id=None):
        # Validate the parent ID
        if parent_id:
            if not self.get_prompt_by_id(parent_id):
                raise ValueError(f"Parent ID '{parent_id}' does not exist.")

        # Assign version as the next available version for the prompt name
        version = self.get_next_version(name)

        # Create a unique ID for the prompt version
        prompt_id = f"{name}_v{version}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Prepare minimal prompt info
        prompt_info = {
            "id": prompt_id,
            "name": name,
            "version": version,
            "parent_id": parent_id,
            "created_at": timestamp
        }

        # Push to Langfuse
        try:
            self.langfuse_client.create_prompt(
                name=name,
                prompt=content,
                config=config,
                labels=["production"],  # Adjust labels as needed
                tags=config.get("tags", [])  # Assuming tags are part of config
            )
        except Exception as e:
            logger.error(f"Error creating prompt '{name}': {e}")
            raise

        # Update local tree
        if name not in self.tree["prompts"]:
            self.tree["prompts"][name] = []
        self.tree["prompts"][name].append(prompt_info)

        # Save the updated tree locally
        self.save_tree()

        return prompt_info

    def sync_with_langfuse(self):
        try:
            # Fetch all prompts from Langfuse
            response = self.langfuse_client.client.prompts.list()
            langfuse_prompts = response.data  # List of PromptMeta objects
        except Exception as e:
            logger.error(f"Error fetching prompts from Langfuse: {e}")
            return

        # Rebuild the local tree from Langfuse
        self.tree = {"prompts": {}}

        for p in langfuse_prompts:
            prompt_name = p.name
            versions = p.versions  # List of version numbers

            if prompt_name not in self.tree["prompts"]:
                self.tree["prompts"][prompt_name] = []

            for version in versions:
                prompt_id = f"{prompt_name}_v{version}"

                # Fetch the prompt details from Langfuse
                try:
                    prompt_client = self.langfuse_client.get_prompt(
                        name=prompt_name,
                        version=version,
                        cache_ttl_seconds=0,  # Disable caching to get the latest
                        max_retries=2,
                        fetch_timeout_seconds=10,
                    )
                    config = prompt_client.config
                    parent_id = config.get("parent_id")
                except Exception as e:
                    logger.error(f"Error fetching prompt '{prompt_name}' version {version}: {e}")
                    parent_id = None

                # Prepare minimal prompt info
                prompt_info = {
                    "id": prompt_id,
                    "name": prompt_name,
                    "version": version,
                    "parent_id": parent_id,
                    "created_at": p.last_updated_at.isoformat() if p.last_updated_at else ''
                }

                self.tree["prompts"][prompt_name].append(prompt_info)

        # Save the updated tree locally
        self.save_tree()

    def get_prompt_by_id(self, prompt_id):
        for prompts in self.tree["prompts"].values():
            for prompt in prompts:
                if prompt["id"] == prompt_id:
                    return prompt
        return None

    def get_next_version(self, name):
        # Get the list of versions for the prompt name
        versions = [p['version'] for p in self.tree['prompts'].get(name, [])]
        return max(versions, default=0) + 1

    def get_latest_prompt(self, name):
        if name in self.tree['prompts']:
            prompts = self.tree['prompts'][name]
            # Sort prompts by version descending
            sorted_prompts = sorted(prompts, key=lambda x: x['version'], reverse=True)
            latest_prompt_info = sorted_prompts[0]

            # Fetch the full prompt details from Langfuse
            try:
                prompt_client = self.langfuse_client.get_prompt(
                    name=name,
                    version=latest_prompt_info['version'],
                    cache_ttl_seconds=0,
                    max_retries=2,
                    fetch_timeout_seconds=10,
                )
                return prompt_client
            except Exception as e:
                logger.error(f"Error fetching latest prompt '{name}': {e}")
                return None
        else:
            return None