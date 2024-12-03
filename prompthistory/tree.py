from datetime import datetime, timezone
import json


class PromptTree:
    def __init__(self, langfuse_client, file_path='prompt_history.json'):
        self.file_path = file_path
        self.tree = self.load_tree()
        self.langfuse_client = langfuse_client
        if langfuse_client:
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

                # Since content is not retrieved, set it to None or omit it
                prompt_info = {
                    "id": prompt_id,
                    "name": prompt_name,
                    "version": version,
                    "metadata": p.last_config or {},
                    "parent_id": (p.last_config or {}).get('parent_id'),
                    "children": [],
                    "created_at": p.last_updated_at.isoformat() if p.last_updated_at else '',
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