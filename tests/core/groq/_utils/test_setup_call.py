"""Tests the `groq._utils.setup_call` module."""

import inspect
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from groq import Groq

from mirascope.core.groq._utils.setup_call import setup_call
from mirascope.core.groq.tool import GroqTool


@pytest.fixture()
def mock_base_setup_call() -> MagicMock:
    """Returns the mock setup_call function."""
    mock_setup_call = MagicMock()
    mock_setup_call.return_value = [MagicMock() for _ in range(3)] + [{}]
    return mock_setup_call


@patch(
    "mirascope.core.groq._utils.setup_call.convert_message_params",
    new_callable=MagicMock,
)
@patch("mirascope.core.groq._utils.setup_call._utils", new_callable=MagicMock)
def test_setup_call(
    mock_utils: MagicMock,
    mock_convert_message_params: MagicMock,
    mock_base_setup_call: MagicMock,
) -> None:
    """Tests the `setup_call` function."""
    mock_utils.setup_call = mock_base_setup_call
    fn = MagicMock()
    create, prompt_template, messages, tool_types, call_kwargs = setup_call(
        model="llama-3.1-8b-instant",
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
    assert "model" in call_kwargs and call_kwargs["model"] == "llama-3.1-8b-instant"
    assert "messages" in call_kwargs and call_kwargs["messages"] == messages
    mock_base_setup_call.assert_called_once_with(fn, {}, None, None, GroqTool, {})
    mock_convert_message_params.assert_called_once_with(
        mock_base_setup_call.return_value[1]
    )
    assert messages == mock_convert_message_params.return_value
    assert inspect.signature(create) == inspect.signature(
        Groq().chat.completions.create
    )


@patch(
    "mirascope.core.groq._utils.setup_call.convert_message_params",
    new_callable=MagicMock,
)
@patch("mirascope.core.groq._utils.setup_call._utils", new_callable=MagicMock)
def test_setup_call_json_mode(
    mock_utils: MagicMock,
    mock_convert_message_params: MagicMock,
    mock_base_setup_call: MagicMock,
) -> None:
    """Tests the `setup_call` function with JSON mode."""
    mock_utils.setup_call = mock_base_setup_call
    mock_json_mode_content = MagicMock()
    mock_json_mode_content.return_value = "\n\njson_output"
    mock_utils.json_mode_content = mock_json_mode_content
    mock_base_setup_call.return_value[1] = [{"role": "user", "content": "test"}]
    mock_base_setup_call.return_value[-1]["tools"] = MagicMock()
    mock_convert_message_params.side_effect = lambda x: x
    _, _, messages, _, call_kwargs = setup_call(
        model="llama-3.1-8b-instant",
        client=None,
        fn=MagicMock(),
        fn_args={},
        dynamic_config=None,
        tools=None,
        json_mode=True,
        call_params={},
        extract=False,
    )
    assert messages[-1] == {
        "role": "user",
        "content": "test\n\njson_output",
    }
    assert "tools" not in call_kwargs

    mock_base_setup_call.return_value[1] = [
        {"role": "user", "content": [{"type": "text", "text": "test"}]}
    ]
    _, _, messages, _, call_kwargs = setup_call(
        model="llama-3.1-8b-instant",
        client=None,
        fn=MagicMock(),
        fn_args={},
        dynamic_config=None,
        tools=None,
        json_mode=True,
        call_params={},
        extract=False,
    )
    assert messages[-1] == {
        "role": "user",
        "content": [
            {"type": "text", "text": "test"},
            {"type": "text", "text": "json_output"},
        ],
    }

    mock_base_setup_call.return_value[1] = [
        {"role": "assistant", "content": [{"type": "text", "text": "test"}]}
    ]
    _, _, messages, _, call_kwargs = setup_call(
        model="llama-3.1-8b-instant",
        client=None,
        fn=MagicMock(),
        fn_args={},
        dynamic_config=None,
        tools=None,
        json_mode=True,
        call_params={},
        extract=False,
    )
    assert messages[-1] == {
        "role": "user",
        "content": "json_output",
    }


@patch(
    "mirascope.core.groq._utils.setup_call.convert_message_params",
    new_callable=MagicMock,
)
@patch("mirascope.core.groq._utils.setup_call._utils", new_callable=MagicMock)
def test_setup_call_extract(
    mock_utils: MagicMock,
    mock_convert_message_params: MagicMock,
    mock_base_setup_call: MagicMock,
) -> None:
    """Tests the `setup_call` function with extraction."""
    mock_utils.setup_call = mock_base_setup_call
    _, _, _, tool_types, call_kwargs = setup_call(
        model="llama-3.1-8b-instant",
        client=None,
        fn=MagicMock(),
        fn_args={},
        dynamic_config=None,
        tools=None,
        json_mode=False,
        call_params={},
        extract=True,
    )
    assert "tool_choice" in call_kwargs and call_kwargs["tool_choice"] == {
        "type": "function",
        "function": {"name": cast(MagicMock, tool_types)[0]._name()},
    }