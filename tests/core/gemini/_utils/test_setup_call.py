"""Tests the `gemini._utils.setup_call` module."""

import inspect
from unittest.mock import MagicMock, patch

import pytest
from google.generativeai import GenerativeModel  # type: ignore

from mirascope.core.gemini._utils.setup_call import setup_call
from mirascope.core.gemini.tool import GeminiTool


@pytest.fixture()
def mock_base_setup_call() -> MagicMock:
    """Returns the mock setup_call function."""
    mock_setup_call = MagicMock()
    mock_setup_call.return_value = [MagicMock() for _ in range(3)] + [{}]
    return mock_setup_call


@patch(
    "mirascope.core.gemini._utils.setup_call.convert_message_params",
    new_callable=MagicMock,
)
@patch("mirascope.core.gemini._utils.setup_call._utils", new_callable=MagicMock)
@patch(
    "mirascope.core.gemini._utils.setup_call.GenerativeModel", new_callable=MagicMock
)
def test_setup_call(
    mock_generative_model: MagicMock,
    mock_utils: MagicMock,
    mock_convert_message_params: MagicMock,
    mock_base_setup_call: MagicMock,
) -> None:
    """Tests the `setup_call` function."""
    generative_model = GenerativeModel(model_name="gemini-flash-1.5")
    mock_generative_model.return_value = generative_model
    mock_utils.setup_call = mock_base_setup_call
    fn = MagicMock()
    create, prompt_template, messages, tool_types, call_kwargs = setup_call(
        model="gemini-flash-1.5",
        client=None,
        fn=fn,
        fn_args={},
        dynamic_config=None,
        tools=None,
        json_mode=False,
        call_params={},
        extract=False,
    )
    assert prompt_template == mock_base_setup_call.return_value[0]
    assert tool_types == mock_base_setup_call.return_value[2]
    assert "contents" in call_kwargs and call_kwargs["contents"] == messages
    mock_base_setup_call.assert_called_once_with(fn, {}, None, None, GeminiTool, {})
    mock_convert_message_params.assert_called_once_with(
        mock_base_setup_call.return_value[1]
    )
    assert messages == mock_convert_message_params.return_value
    mock_generative_model.assert_called_once_with(model_name="gemini-flash-1.5")
    assert inspect.signature(create) == inspect.signature(
        generative_model.generate_content
    )


@patch(
    "mirascope.core.gemini._utils.setup_call.convert_message_params",
    new_callable=MagicMock,
)
@patch("mirascope.core.gemini._utils.setup_call._utils", new_callable=MagicMock)
def test_setup_call_json_mode(
    mock_utils: MagicMock,
    mock_convert_message_params: MagicMock,
    mock_base_setup_call: MagicMock,
) -> None:
    """Tests the `setup_call` function with JSON mode."""
    mock_utils.setup_call = mock_base_setup_call
    mock_utils.json_mode_content = MagicMock()
    mock_base_setup_call.return_value[1] = [
        {"role": "user", "parts": [{"type": "text", "text": "test"}]}
    ]
    mock_base_setup_call.return_value[-1]["tools"] = MagicMock()
    mock_convert_message_params.side_effect = lambda x: x
    _, _, messages, _, call_kwargs = setup_call(
        model="gpt-4o",
        client=None,
        fn=MagicMock(),
        fn_args={},
        dynamic_config=None,
        tools=None,
        json_mode=True,
        call_params={},
        extract=False,
    )
    assert messages[-1]["parts"][-1] == mock_utils.json_mode_content.return_value
    assert "tools" not in call_kwargs


@patch(
    "mirascope.core.gemini._utils.setup_call.convert_message_params",
    new_callable=MagicMock,
)
@patch("mirascope.core.gemini._utils.setup_call._utils", new_callable=MagicMock)
def test_setup_call_extract(
    mock_utils: MagicMock,
    mock_convert_message_params: MagicMock,
    mock_base_setup_call: MagicMock,
) -> None:
    """Tests the `setup_call` function with extraction."""
    mock_utils.setup_call = mock_base_setup_call
    _, _, _, _, call_kwargs = setup_call(
        model="gpt-4o",
        client=None,
        fn=MagicMock(),
        fn_args={},
        dynamic_config=None,
        tools=None,
        json_mode=False,
        call_params={},
        extract=True,
    )
    assert "tool_config" in call_kwargs and call_kwargs["tool_config"] == {
        "function_calling_config": {"mode": "auto"}
    }