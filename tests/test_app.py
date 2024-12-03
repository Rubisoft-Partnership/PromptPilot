import pytest
from unittest.mock import patch, Mock
from app.app import app as flask_app

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client

def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"message" in response.data

@patch('app.app.client.chat.completions.create')
def test_chat_post(mock_create, client):
    # Mock the response from OpenAI client
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Hello, how can I assist you?"))]
    mock_create.return_value = mock_response

    response = client.post("/", data={"message": "Hello"})
    assert response.status_code == 200
    assert b"Hello, how can I assist you?" in response.data