from datetime import datetime, timezone
import json
from langfuse.model import TextPromptClient, ChatPromptClient
from langfuse.api.resources.prompts.types import Prompt_Text, Prompt_Chat
import logging

logger = logging.getLogger(__name__)

class PromptTree:
    def __init__(self, langfuse_client, file_path='prompt_history.json'):
        self.file_path = file_path
        self.tree = self.load_tree()
        self.langfuse_client = langfuse_client
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

    def create_prompt(self, name, content, metadata, parent_id=None):
        # Validate the parent ID
        if parent_id:
            # Build prompt_map for validation
            prompt_map = {}
            for prompt_versions in self.tree["prompts"].values():
                for prompt in prompt_versions:
                    prompt_map[prompt['id']] = prompt

            if parent_id not in prompt_map:
                raise ValueError(f"Parent ID '{parent_id}' does not exist.")

        # Assign version as the next available version for the prompt name
        version = self.get_next_version(name)

        # Update metadata
        metadata = metadata or {}
        metadata["parent_id"] = parent_id  # Store tree relationship in metadata
        timestamp = datetime.now(timezone.utc).isoformat()
        metadata["created_at"] = timestamp
        # Store content in metadata (optional)
        if content is not None:
            metadata["content"] = content

        # Push directly to Langfuse
        self.langfuse_client.create_prompt(
            name=name,
            prompt=content,
            config=metadata,
            labels=["production"],  # Mark as production if needed
        )

        # Synchronize local tree after creating the prompt
        self.sync_with_langfuse()

        # Retrieve the prompt info
        prompt_id = f"{name}_v{version}"
        prompt_info = next(
            (p for p in self.tree["prompts"][name] if p["id"] == prompt_id), None
        )

        return prompt_info

    def sync_with_langfuse(self):
        # Fetch all prompts from Langfuse
        response = self.langfuse_client.client.prompts.list()
        langfuse_prompts = response.data  # List of PromptMeta objects

        # Rebuild the local tree from Langfuse
        self.tree = {"prompts": {}}

        for p in langfuse_prompts:
            prompt_name = p.name
            versions = p.versions  # List of version numbers

            # Initialize the prompt entry if it doesn't exist
            if prompt_name not in self.tree["prompts"]:
                self.tree["prompts"][prompt_name] = []

            for version in versions:
                # Create a unique ID for the prompt version
                prompt_id = f"{prompt_name}_v{version}"

                # Fetch the prompt content using get_prompt
                try:
                    prompt_client = self.langfuse_client.get_prompt(
                        name=prompt_name,
                        version=version,
                        cache_ttl_seconds=0,  # Disable caching to get the latest
                        max_retries=2,
                        fetch_timeout_seconds=10,
                    )
                    content = prompt_client.prompt  # The prompt content
                    prompt_type = 'chat' if isinstance(prompt_client, ChatPromptClient) else 'text'
                    config = prompt_client.config
                    labels = prompt_client.labels
                    tags = prompt_client.tags
                except Exception as e:
                    logger.error(f"Error fetching prompt '{prompt_name}' version {version}: {e}")
                    content = None  # Handle the error as needed
                    prompt_type = None
                    config = {}
                    labels = []
                    tags = []

                # Get metadata from the prompt's last_config
                metadata = config.copy()
                metadata["content"] = content  # Update metadata with content

                prompt_info = {
                    "id": prompt_id,
                    "name": prompt_name,
                    "version": version,
                    "metadata": metadata,
                    "parent_id": metadata.get('parent_id'),
                    "children": [],
                    "created_at": p.last_updated_at.isoformat() if p.last_updated_at else '',
                    "content": content,  # Store the content
                    "type": prompt_type,
                    "config": config,
                    "labels": labels,
                    "tags": tags,
                }

                # Append the prompt version to the list
                self.tree["prompts"][prompt_name].append(prompt_info)

        # Rebuild parent-child relationships
        self._rebuild_relationships()
        # Save the updated tree locally
        self.save_tree()

    def _rebuild_relationships(self):
        # Build a mapping from prompt IDs to prompt info
        prompt_map = {}
        for prompt_versions in self.tree["prompts"].values():
            for prompt in prompt_versions:
                prompt_map[prompt['id']] = prompt

        # Now set up parent-child relationships
        for prompt in prompt_map.values():
            parent_id = prompt.get('parent_id')
            if parent_id and parent_id in prompt_map:
                parent_prompt = prompt_map[parent_id]
                parent_prompt['children'].append(prompt['id'])

    def get_next_version(self, name):
        # Get the list of versions for the prompt name
        versions = [p['version'] for p in self.tree['prompts'].get(name, [])]
        return max(versions, default=0) + 1

    def get_latest_prompt(self, name):
        # Retrieve the latest prompt version for the given name
        if name in self.tree['prompts']:
            prompts = self.tree['prompts'][name]
            # Sort prompts by version descending
            sorted_prompts = sorted(prompts, key=lambda x: x['version'], reverse=True)
            latest_prompt_data = sorted_prompts[0]

            # Now, create a PromptClient object
            prompt_type = latest_prompt_data.get('type', 'text')
            prompt_content = latest_prompt_data.get('content')
            prompt_name = latest_prompt_data.get('name')
            prompt_version = latest_prompt_data.get('version')
            prompt_config = latest_prompt_data.get('config', {})
            prompt_labels = latest_prompt_data.get('labels', [])
            prompt_tags = latest_prompt_data.get('tags', [])

            # Construct the appropriate Prompt object
            if prompt_type == 'text':
                prompt = Prompt_Text(
                    name=prompt_name,
                    version=prompt_version,
                    prompt=prompt_content,
                    config=prompt_config,
                    labels=prompt_labels,
                    tags=prompt_tags,
                )
                prompt_client = TextPromptClient(prompt=prompt)
            elif prompt_type == 'chat':
                prompt = Prompt_Chat(
                    name=prompt_name,
                    version=prompt_version,
                    prompt=prompt_content,  # Should be a list of ChatMessageDict
                    config=prompt_config,
                    labels=prompt_labels,
                    tags=prompt_tags,
                )
                prompt_client = ChatPromptClient(prompt=prompt)
            else:
                # Unknown type, return None or raise an error
                logger.error(f"Unknown prompt type '{prompt_type}' for prompt '{prompt_name}'")
                return None

            return prompt_client
        else:
            return None