import pytest 
from unittest.mock import patch, MagicMock
from backend.chat import generate_response

# testing of response generation in the chat module 
@patch("backend.chat.response_generator")
@patch("backend.chat.st")
def test_generate_response(mock_st, mock_response_generator):
    # Mock Streamlit session state
    mock_st.session_state.selected_subject = "Math"
    mock_st.session_state.selected_main_topic = "Algebra"
    mock_st.session_state.selected_sub_topic = "Factoring"
    mock_st.session_state.chat_history = [{"role": "user", "message": "How do I factor x^2 + 5x + 6?"}]
    mock_st.session_state.user_id = 1

    # Configure the mocked ResponseGenerator
    mock_response_generator.generate_response.return_value = ("You factor by finding numbers...", "lecture")

    # Call the actual function
    response = generate_response("How do I factor x^2 + 5x + 6?")

    # Assertions
    assert "factor" in response
    assert mock_st.session_state.chosen_strategy == "lecture"
    mock_response_generator.generate_response.assert_called_once()
