import pytest
import os
import tempfile
from unittest.mock import Mock, ANY
from prompthistory.tree import PromptTree
from datetime import datetime, timezone


# Define mock classes
class PromptMetaMock:
    def __init__(self, name, versions, labels, tags, last_updated_at, last_config):
        self.name = name
        self.versions = versions
        self.labels = labels
        self.tags = tags
        self.last_updated_at = last_updated_at
        self.last_config = last_config


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
        else:
            # Add new prompt
            langfuse_prompts.append(
                PromptMetaMock(
                    name=name,
                    versions=[1],
                    labels=labels,
                    tags=[],
                    last_updated_at=datetime.now(timezone.utc),
                    last_config=config,
                )
            )

    langfuse_client.create_prompt.side_effect = create_prompt_side_effect

    assert langfuse_client.client.prompts.list.call_count == 1  # Sync on initialization

    # Create the root prompt
    root_prompt = prompt_manager.create_prompt(
        name="root_prompt",
        content=None,  # Content is not used
        metadata={"model": "test_model"}
    )
    assert root_prompt["parent_id"] is None

    # Create another root prompt with a different name
    another_root_prompt = prompt_manager.create_prompt(
        name="another_root",
        content=None,
        metadata={"model": "test_model"}
    )
    assert another_root_prompt["parent_id"] is None

    # Verify Langfuse interactions
    assert langfuse_client.create_prompt.call_count == 2
    langfuse_client.create_prompt.assert_any_call(
        name="root_prompt",
        prompt=None,
        config={"model": "test_model", "parent_id": None, "created_at": ANY},
        labels=["production"],
    )
    langfuse_client.create_prompt.assert_any_call(
        name="another_root",
        prompt=None,
        config={"model": "test_model", "parent_id": None, "created_at": ANY},
        labels=["production"],
    )
    assert langfuse_client.client.prompts.list.call_count == 3  # Sync happens twice


def test_sync_with_langfuse(prompt_manager, langfuse_client):
    # Mock Langfuse's client.prompts.list() to return a set of prompts
    langfuse_client.client.prompts.list.return_value = ResponseMock(data=[
        PromptMetaMock(
            name="root_prompt",
            versions=[1],
            labels=["production"],
            tags=[],
            last_updated_at=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            last_config={"model": "test_model", "parent_id": None},
        ),
        PromptMetaMock(
            name="child_prompt",
            versions=[1],
            labels=["production"],
            tags=[],
            last_updated_at=datetime(2023, 1, 1, 0, 1, 0, tzinfo=timezone.utc),
            last_config={"model": "test_model", "parent_id": "root_prompt_v1"},
        ),
    ])

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

    # Verify Langfuse interactions
    assert langfuse_client.client.prompts.list.call_count == 2  # Sync happens twice


def test_create_prompt_with_invalid_parent(prompt_manager, langfuse_client):
    # Initialize the simulated Langfuse prompts data
    langfuse_prompts = []

    # Define a function to simulate langfuse_client.client.prompts.list()
    def prompts_list_side_effect():
        return ResponseMock(data=langfuse_prompts.copy())

    langfuse_client.client.prompts.list.side_effect = prompts_list_side_effect

    # Sync the local tree to ensure it's empty
    prompt_manager.sync_with_langfuse()

    # Attempt to create a prompt with a non-existent parent ID
    with pytest.raises(ValueError, match="Parent ID 'nonexistent_prompt_v1' does not exist."):
        prompt_manager.create_prompt(
            name="child_prompt",
            content=None,
            metadata={"model": "test_model"},
            parent_id="nonexistent_prompt_v1"
        )