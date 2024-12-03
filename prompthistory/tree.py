from datetime import datetime, timezone
import json


class PromptTree:
    def __init__(self, file_path='prompt_history.json'):
        self.file_path = file_path
        self.tree = self.load_tree()

    def load_tree(self):
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"prompts": []}

    def save_tree(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.tree, f, indent=2)

    def create_prompt(self, name, content, metadata, langfuse_client, parent_id=None):
        # Check if a root already exists and enforce parent_id if true
        if parent_id is None and any(p['parent_id'] is None for p in self.tree['prompts']):
            raise ValueError("A root prompt already exists. You must specify a parent_id.")

        # Validate the parent ID
        if parent_id and not any(p['id'] == parent_id for p in self.tree['prompts']):
            raise ValueError(f"Parent ID '{parent_id}' does not exist.")

        # Assign version as the ID (matching Langfuse versioning)
        timestamp = datetime.now(timezone.utc).isoformat()
        version = self.get_next_version(name)

        # Push directly to Langfuse
        metadata["parent_id"] = parent_id  # Store tree relationship in metadata
        metadata["created_at"] = timestamp

        langfuse_client.create_prompt(
            name=name,
            prompt=content,
            config=metadata,
            labels=["production"],  # Mark as production if needed
        )

        # Synchronize local tree after creating the prompt
        self.sync_with_langfuse(langfuse_client)

        return {
            "id": version,
            "name": name,
            "version": version,
            "content": content,
            "metadata": metadata,
            "parent_id": parent_id,
            "children": [],
            "created_at": timestamp,
        }

    def sync_with_langfuse(self, langfuse_client):
        # Fetch all prompts from Langfuse
        langfuse_prompts = langfuse_client.list_prompts()

        # Rebuild the local tree from Langfuse
        self.tree = {"prompts": []}
        prompt_map = {}

        for p in langfuse_prompts:
            prompt = {
                "id": p['version'],  # Ensure the ID matches the version
                "name": p['name'],
                "version": p['version'],
                "content": p['prompt'],
                "metadata": p.get('config', {}),
                "parent_id": p.get('config', {}).get('parent_id'),
                "children": [],
                "created_at": p.get('created_at', ''),
            }
            self.tree['prompts'].append(prompt)
            prompt_map[p['version']] = prompt

        # Rebuild parent-child relationships
        for prompt in self.tree['prompts']:
            parent_id = prompt['parent_id']
            if parent_id and parent_id in prompt_map:
                parent = prompt_map[parent_id]
                parent['children'].append(prompt['id'])

        # Save the updated tree locally
        self.save_tree()

    def get_next_version(self, name):
        # Fetch the latest version directly from Langfuse metadata
        prompts = [p for p in self.tree['prompts'] if p['name'] == name]
        return max((p['version'] for p in prompts), default=0) + 1