import pytest
from unittest.mock import patch, Mock

# Mock external calls before importing the app module
with patch('prompthistory.tree.PromptTree.__init__', return_value=None), \
     patch('prompthistory.tree.PromptTree.sync_with_langfuse', return_value=None):
    from app.app import app as flask_app, prompt_manager, client as openai_client, langfuse_client

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client

def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"message" in response.data  # Adjust this based on your 'chat.html' template

@patch('app.app.prompt_manager.get_latest_prompt_content')
@patch('app.app.client.chat.completions.create')
def test_chat_post(mock_create, mock_get_latest_prompt_content, client):
    # Mock the prompt_manager's get_latest_prompt_content method
    mock_get_latest_prompt_content.return_value = "You are a helpful assistant."

    # Mock the response from OpenAI client
    mock_message = Mock()
    mock_message.content = "Hello, how can I assist you?"
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_create.return_value = mock_response

    response = client.post("/", data={"message": "Hello"})
    assert response.status_code == 200
    assert b"Hello, how can I assist you?" in response.data

    # Verify that get_latest_prompt_content was called with the correct arguments
    mock_get_latest_prompt_content.assert_called_with(name="movie-critic")

@patch('app.app.langfuse_client.client.prompts.list')
def test_display_prompts(mock_prompts_list, client):
    # Mock the prompts list response
    mock_prompt_meta = Mock()
    mock_prompt_meta.name = 'Test Prompt'
    mock_prompt_meta.versions = [1, 2, 3]
    mock_prompt_meta.last_updated_at = None
    mock_prompt_meta.labels = ['test']
    mock_prompt_meta.tags = ['sample']
    mock_prompt_meta.last_config = {'config_key': 'config_value'}

    mock_response = Mock()
    mock_response.data = [mock_prompt_meta]
    mock_prompts_list.return_value = mock_response

    response = client.get("/prompts")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'Test Prompt'
    assert data[0]['versions'] == [1, 2, 3]
    assert data[0]['labels'] == ['test']
    assert data[0]['tags'] == ['sample']
    assert data[0]['last_config'] == {'config_key': 'config_value'}