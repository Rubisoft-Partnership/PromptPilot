import pytest
import os
import tempfile
from unittest.mock import Mock, ANY
from prompthistory.tree import PromptTree
from datetime import datetime, timezone


# Define mock classes
class PromptMetaMock:
    def __init__(self, name, versions, labels, tags, last_updated_at, last_config, contents=None):
        self.name = name
        self.versions = versions  # List of version numbers
        self.labels = labels
        self.tags = tags
        self.last_updated_at = last_updated_at
        self.last_config = last_config
        self.contents = contents or {}  # Dict mapping version numbers to content


class ResponseMock:
    def __init__(self, data):
        self.data = data


# Mock Langfuse client
@pytest.fixture
def langfuse_client():
    mock_client = Mock()
    mock_client.client.prompts.list.return_value = ResponseMock(data=[])  # Default empty list for syncing
    return mock_client

# Setup a temporary JSON file for testing
@pytest.fixture
def prompt_manager(langfuse_client):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_path = temp_file.name
        temp_file.write(b'{"prompts": {}}')

    prompt_manager = PromptTree(langfuse_client, temp_file_path)
    yield prompt_manager

    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)


def test_create_prompt(prompt_manager, langfuse_client):
    # Initialize the simulated Langfuse prompts data
    langfuse_prompts = []

    # Define a function to simulate langfuse_client.client.prompts.list()
    def prompts_list_side_effect():
        return ResponseMock(data=langfuse_prompts.copy())

    langfuse_client.client.prompts.list.side_effect = prompts_list_side_effect

    # Mock Langfuse's create_prompt to simulate adding the prompt to Langfuse
    def create_prompt_side_effect(name, prompt, config, labels):
        # Simulate adding the prompt to Langfuse
        existing_prompt = next((p for p in langfuse_prompts if p.name == name), None)
        if existing_prompt:
            # Increment version
            new_version = max(existing_prompt.versions) + 1
            existing_prompt.versions.append(new_version)
            existing_prompt.last_config = config
            existing_prompt.last_updated_at = datetime.now(timezone.utc)
            existing_prompt.contents[new_version] = prompt
        else:
            # Add new prompt
            new_version = 1
            contents = {new_version: prompt}
            langfuse_prompts.append(
                PromptMetaMock(
                    name=name,
                    versions=[new_version],
                    labels=labels,
                    tags=[],
                    last_updated_at=datetime.now(timezone.utc),
                    last_config=config,
                    contents=contents
                )
            )

    langfuse_client.create_prompt.side_effect = create_prompt_side_effect

    # Mock langfuse_client.get_prompt to return the prompt content
    def get_prompt_side_effect(name, version=None, **kwargs):
        # Find the prompt with the given name
        existing_prompt = next((p for p in langfuse_prompts if p.name == name), None)
        if existing_prompt is None:
            raise Exception(f"Prompt '{name}' not found.")
        if version is None:
            # Use the latest version
            version = max(existing_prompt.versions)
        if version not in existing_prompt.versions:
            raise Exception(f"Version {version} of prompt '{name}' not found.")
        # Get the content for the version
        content = existing_prompt.contents.get(version)
        if content is None:
            raise Exception(f"Content for prompt '{name}' version {version} not found.")
        # Return a mock prompt client with the content
        prompt = Mock()
        prompt.prompt = content
        prompt_client = Mock()
        prompt_client.prompt = prompt
        return prompt_client

    langfuse_client.get_prompt.side_effect = get_prompt_side_effect

    # Since the prompt_manager was instantiated in the fixture, sync_with_langfuse() was already called once
    assert langfuse_client.client.prompts.list.call_count == 1  # Sync on initialization

    # Create the root prompt
    root_prompt = prompt_manager.create_prompt(
        name="root_prompt",
        content="Root prompt content",
        metadata={"model": "test_model"}
    )
    assert root_prompt["parent_id"] is None

    # Create another root prompt with a different name
    another_root_prompt = prompt_manager.create_prompt(
        name="another_root",
        content="Another root prompt content",
        metadata={"model": "test_model"}
    )
    assert another_root_prompt["parent_id"] is None

    # Verify Langfuse interactions
    assert langfuse_client.create_prompt.call_count == 2
    langfuse_client.create_prompt.assert_any_call(
        name="root_prompt",
        prompt="Root prompt content",
        config={"model": "test_model", "parent_id": None, "created_at": ANY, "content": "Root prompt content"},
        labels=["production"],
    )
    langfuse_client.create_prompt.assert_any_call(
        name="another_root",
        prompt="Another root prompt content",
        config={"model": "test_model", "parent_id": None, "created_at": ANY, "content": "Another root prompt content"},
        labels=["production"],
    )

    # After each create_prompt call, sync_with_langfuse() is called
    # So total prompts.list call_count should be 3 (1 initial + 2 for create_prompts)
    assert langfuse_client.client.prompts.list.call_count == 3  # Sync happens on initialization and after each create

    # Verify that get_prompt was called appropriately during sync
    # We have two prompts, each with one version, and sync is called 3 times
    # So total get_prompt calls should match the number of versions synced
    # First sync (initialization): no prompts, so no get_prompt calls
    # Second sync (after first create): 1 prompt with 1 version
    # Third sync (after second create): 2 prompts with 1 version each
    assert langfuse_client.get_prompt.call_count == 3  # 1 + 2 get_prompt calls


def test_sync_with_langfuse(prompt_manager, langfuse_client):
    # Initialize the simulated Langfuse prompts data
    langfuse_prompts = []

    # Define the prompts to be returned by prompts.list()
    langfuse_prompts = [
        PromptMetaMock(
            name="root_prompt",
            versions=[1],
            labels=["production"],
            tags=[],
            last_updated_at=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            last_config={"model": "test_model", "parent_id": None},
            contents={1: "Root prompt content"},
        ),
        PromptMetaMock(
            name="child_prompt",
            versions=[1],
            labels=["production"],
            tags=[],
            last_updated_at=datetime(2023, 1, 1, 0, 1, 0, tzinfo=timezone.utc),
            last_config={"model": "test_model", "parent_id": "root_prompt_v1"},
            contents={1: "Child prompt content"},
        ),
    ]

    # Mock prompts.list()
    def prompts_list_side_effect():
        return ResponseMock(data=langfuse_prompts.copy())

    langfuse_client.client.prompts.list.side_effect = prompts_list_side_effect

    # Mock langfuse_client.get_prompt to return the prompt content
    def get_prompt_side_effect(name, version=None, **kwargs):
        # Find the prompt with the given name
        existing_prompt = next((p for p in langfuse_prompts if p.name == name), None)
        if existing_prompt is None:
            raise Exception(f"Prompt '{name}' not found.")
        if version is None:
            # Use the latest version
            version = max(existing_prompt.versions)
        if version not in existing_prompt.versions:
            raise Exception(f"Version {version} of prompt '{name}' not found.")
        # Get the content for the version
        content = existing_prompt.contents.get(version)
        if content is None:
            raise Exception(f"Content for prompt '{name}' version {version} not found.")
        # Return a mock prompt client with the content
        prompt = Mock()
        prompt.prompt = content
        prompt_client = Mock()
        prompt_client.prompt = prompt
        return prompt_client

    langfuse_client.get_prompt.side_effect = get_prompt_side_effect

    # Sync the local tree with Langfuse
    prompt_manager.sync_with_langfuse()

    # Verify local tree structure
    root_prompts = prompt_manager.tree["prompts"].get("root_prompt", [])
    child_prompts = prompt_manager.tree["prompts"].get("child_prompt", [])

    assert len(root_prompts) == 1
    assert len(child_prompts) == 1

    root_prompt = root_prompts[0]
    child_prompt = child_prompts[0]

    assert root_prompt["name"] == "root_prompt"
    assert root_prompt["children"] == ["child_prompt_v1"]
    assert child_prompt["parent_id"] == "root_prompt_v1"
    assert root_prompt["content"] == "Root prompt content"
    assert child_prompt["content"] == "Child prompt content"

    # Verify Langfuse interactions
    # The initial sync during initialization and this sync
    assert langfuse_client.client.prompts.list.call_count == 2  # Sync happens twice

    # get_prompt should have been called for each version during sync
    # We have two prompts, each with one version
    assert langfuse_client.get_prompt.call_count == 2


def test_create_prompt_with_invalid_parent(prompt_manager, langfuse_client):
    # Initialize the simulated Langfuse prompts data
    langfuse_prompts = []

    # Define a function to simulate langfuse_client.client.prompts.list()
    def prompts_list_side_effect():
        return ResponseMock(data=langfuse_prompts.copy())

    langfuse_client.client.prompts.list.side_effect = prompts_list_side_effect

    # Mock langfuse_client.get_prompt to raise an exception since no prompts exist
    def get_prompt_side_effect(name, version=None, **kwargs):
        raise Exception(f"Prompt '{name}' not found.")

    langfuse_client.get_prompt.side_effect = get_prompt_side_effect

    # Sync the local tree to ensure it's empty
    prompt_manager.sync_with_langfuse()

    # Attempt to create a prompt with a non-existent parent ID
    with pytest.raises(ValueError, match="Parent ID 'nonexistent_prompt_v1' does not exist."):
        prompt_manager.create_prompt(
            name="child_prompt",
            content="Child prompt content",
            metadata={"model": "test_model"},
            parent_id="nonexistent_prompt_v1"
        )

    # Verify that create_prompt was not called since the parent ID was invalid
    assert langfuse_client.create_prompt.call_count == 0

    # Verify Langfuse interactions
    # Initial sync during initialization, one sync in the test
    assert langfuse_client.client.prompts.list.call_count == 2  # Sync happens twice
    # get_prompt might not be called since there are no prompts
    assert langfuse_client.get_prompt.call_count == 0