import pytest
import os
import tempfile
from unittest.mock import MagicMock
from prompthistory.tree import PromptTree

# Mock Langfuse client
@pytest.fixture
def langfuse_client():
    mock_client = MagicMock()
    mock_client.list_prompts.return_value = []  # Default empty list for syncing
    return mock_client

# Setup a temporary JSON file for testing
@pytest.fixture
def prompt_manager(langfuse_client):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_path = temp_file.name
        temp_file.write(b'{"prompts": []}')

    prompt_manager = PromptTree(temp_file_path)
    yield prompt_manager

    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)


def test_create_prompt(prompt_manager, langfuse_client):
    # Mock Langfuse's create_prompt to simulate success
    langfuse_client.create_prompt.return_value = None

    # Mock Langfuse's list_prompts for synchronization
    langfuse_client.list_prompts.side_effect = [
        [],  # Initially, Langfuse is empty
        [    # After creating the root prompt, Langfuse contains it
            {
                "version": 1,
                "name": "root_prompt",
                "prompt": "This is the root prompt.",
                "config": {"model": "test_model", "parent_id": None},
                "created_at": "2023-01-01T00:00:00Z",
            }
        ],
    ]

    # Create the root prompt
    root_prompt = prompt_manager.create_prompt(
        name="root_prompt",
        content="This is the root prompt.",
        metadata={"model": "test_model"},
        langfuse_client=langfuse_client,
    )
    assert root_prompt["parent_id"] is None

    # Synchronize the local tree to update with the root prompt
    prompt_manager.sync_with_langfuse(langfuse_client)

    # Attempt to create another root prompt (should fail)
    with pytest.raises(ValueError, match="A root prompt already exists"):
        prompt_manager.create_prompt(
            name="another_root",
            content="This is another root prompt.",
            metadata={"model": "test_model"},
            langfuse_client=langfuse_client,
        )

    # Verify Langfuse interactions
    langfuse_client.create_prompt.assert_called_once_with(
        name="root_prompt",
        prompt="This is the root prompt.",
        config={"model": "test_model", "parent_id": None, "created_at": root_prompt["created_at"]},
        labels=["production"],
    )
    assert langfuse_client.list_prompts.call_count == 2  # Sync happens twice


def test_sync_with_langfuse(prompt_manager, langfuse_client):
    # Mock Langfuse's list_prompts to return a set of prompts
    langfuse_client.list_prompts.return_value = [
        {
            "version": 1,
            "name": "root_prompt",
            "prompt": "This is the root prompt.",
            "config": {"model": "test_model", "parent_id": None},
            "created_at": "2023-01-01T00:00:00Z",
        },
        {
            "version": 2,
            "name": "child_prompt",
            "prompt": "This is a child prompt.",
            "config": {"model": "test_model", "parent_id": 1},
            "created_at": "2023-01-01T00:01:00Z",
        },
    ]

    # Sync the local tree with Langfuse
    prompt_manager.sync_with_langfuse(langfuse_client)

    # Verify local tree structure
    root_prompt = next(p for p in prompt_manager.tree["prompts"] if p["id"] == 1)
    child_prompt = next(p for p in prompt_manager.tree["prompts"] if p["id"] == 2)

    assert root_prompt["name"] == "root_prompt"
    assert root_prompt["children"] == [2]
    assert child_prompt["parent_id"] == 1

    # Verify Langfuse interactions
    langfuse_client.list_prompts.assert_called_once()


def test_create_prompt_with_invalid_parent(prompt_manager, langfuse_client):
    # Attempt to create a prompt with a non-existent parent ID
    with pytest.raises(ValueError, match="Parent ID 'nonexistent_id' does not exist"):
        prompt_manager.create_prompt(
            name="child_prompt",
            content="This is a child prompt.",
            metadata={"model": "test_model"},
            langfuse_client=langfuse_client,
            parent_id="nonexistent_id"
        )