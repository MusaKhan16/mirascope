"""Tests the `mistral._utils.setup_call` module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mistralai.async_client import MistralAsyncClient
from mistralai.models.chat_completion import (
    ChatCompletionResponse,
    ChatCompletionStreamResponse,
    ChatMessage,
    ToolChoice,
)

from mirascope.core.mistral._utils._setup_call import setup_call
from mirascope.core.mistral.tool import MistralTool


@pytest.fixture()
def mock_base_setup_call() -> MagicMock:
    """Returns the mock setup_call function."""
    mock_setup_call = MagicMock()
    mock_setup_call.return_value = [MagicMock() for _ in range(3)] + [{}]
    return mock_setup_call


@patch(
    "mirascope.core.mistral._utils._setup_call.MistralClient.chat_stream",
    return_value=MagicMock(),
)
@patch(
    "mirascope.core.mistral._utils._setup_call.MistralClient.chat",
    return_value=MagicMock(),
)
@patch(
    "mirascope.core.mistral._utils._setup_call.convert_message_params",
    new_callable=MagicMock,
)
@patch("mirascope.core.mistral._utils._setup_call._utils", new_callable=MagicMock)
def test_setup_call(
    mock_utils: MagicMock,
    mock_convert_message_params: MagicMock,
    mock_mistral_chat: MagicMock,
    mock_mistral_chat_stream: MagicMock,
    mock_base_setup_call: MagicMock,
) -> None:
    """Tests the `setup_call` function."""
    mock_utils.setup_call = mock_base_setup_call
    mock_chat_iterator = MagicMock()
    mock_chat_iterator.__iter__.return_value = ["chat"]
    mock_mistral_chat_stream.return_value = mock_chat_iterator
    fn = MagicMock()
    create, prompt_template, messages, tool_types, call_kwargs = setup_call(
        model="mistral-large-latest",
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
    assert "model" in call_kwargs and call_kwargs["model"] == "mistral-large-latest"
    assert "messages" in call_kwargs and call_kwargs["messages"] == messages
    mock_base_setup_call.assert_called_once_with(fn, {}, None, None, MistralTool, {})
    mock_convert_message_params.assert_called_once_with(
        mock_base_setup_call.return_value[1]
    )
    assert messages == mock_convert_message_params.return_value
    create(stream=False, **call_kwargs)
    mock_mistral_chat.assert_called_once_with(**call_kwargs)
    stream = create(stream=True, **call_kwargs)
    mock_mistral_chat_stream.assert_called_once_with(**call_kwargs)
    assert next(stream) == "chat"  # pyright: ignore [reportArgumentType]


@patch(
    "mirascope.core.mistral._utils._setup_call.convert_message_params",
    new_callable=MagicMock,
)
@patch("mirascope.core.mistral._utils._setup_call._utils", new_callable=MagicMock)
@pytest.mark.asyncio
async def test_async_setup_call(
    mock_utils: MagicMock,
    mock_convert_message_params: MagicMock,
    mock_base_setup_call: MagicMock,
) -> None:
    """Tests the `setup_call` function."""
    mock_mistral_chat = AsyncMock(spec=ChatCompletionResponse)
    mock_mistral_chat.__name__ = "chat"

    mock_stream_response = AsyncMock(spec=ChatCompletionStreamResponse)
    mock_stream_response.text = "chat"

    mock_iterator = AsyncMock()
    mock_iterator.__aiter__.return_value = mock_iterator
    mock_iterator.__anext__.side_effect = [mock_stream_response, StopAsyncIteration()]

    mock_client = AsyncMock(spec=MistralAsyncClient, name="mock_client")
    mock_client.chat_stream.return_value = mock_iterator
    mock_client.chat.return_value = mock_mistral_chat

    mock_utils.setup_call = mock_base_setup_call

    fn = MagicMock()
    create, prompt_template, messages, tool_types, call_kwargs = setup_call(
        model="mistral-large-latest",
        client=mock_client,
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
    assert "model" in call_kwargs and call_kwargs["model"] == "mistral-large-latest"
    assert "messages" in call_kwargs and call_kwargs["messages"] == messages
    mock_base_setup_call.assert_called_once_with(fn, {}, None, None, MistralTool, {})
    mock_convert_message_params.assert_called_once_with(
        mock_base_setup_call.return_value[1]
    )

    mock_mistral_chat.return_value = MagicMock(spec=ChatCompletionResponse)
    chat = await create(stream=False, **call_kwargs)
    stream = await create(stream=True, **call_kwargs)
    async for chunk in stream:
        assert chunk == mock_stream_response
    assert isinstance(chat, ChatCompletionResponse)
    assert isinstance(stream, AsyncMock)


@patch(
    "mirascope.core.mistral._utils._setup_call.convert_message_params",
    new_callable=MagicMock,
)
@patch("mirascope.core.mistral._utils._setup_call._utils", new_callable=MagicMock)
def test_setup_call_json_mode(
    mock_utils: MagicMock,
    mock_convert_message_params: MagicMock,
    mock_base_setup_call: MagicMock,
) -> None:
    """Tests the `setup_call` function with JSON mode."""
    mock_utils.setup_call = mock_base_setup_call
    mock_json_mode_content = MagicMock()
    mock_json_mode_content.return_value = "\n\njson_mode_content"
    mock_utils.json_mode_content = mock_json_mode_content
    mock_base_setup_call.return_value[1] = [ChatMessage(role="user", content="test")]
    mock_base_setup_call.return_value[-1]["tools"] = MagicMock()
    mock_convert_message_params.side_effect = lambda x: x
    _, _, messages, _, call_kwargs = setup_call(
        model="mistral-large-latest",
        client=None,
        fn=MagicMock(),
        fn_args={},
        dynamic_config=None,
        tools=None,
        json_mode=True,
        call_params={},
        extract=False,
    )
    assert messages[-1].content == "test\n\njson_mode_content"
    assert "tools" not in call_kwargs

    mock_base_setup_call.return_value[1] = [
        ChatMessage(role="assistant", content="test"),
    ]
    _, _, messages, _, call_kwargs = setup_call(
        model="mistral-large-latest",
        client=None,
        fn=MagicMock(),
        fn_args={},
        dynamic_config=None,
        tools=None,
        json_mode=True,
        call_params={},
        extract=False,
    )
    assert messages[-1] == ChatMessage(role="user", content="json_mode_content")


@patch(
    "mirascope.core.mistral._utils._setup_call.convert_message_params",
    new_callable=MagicMock,
)
@patch("mirascope.core.mistral._utils._setup_call._utils", new_callable=MagicMock)
def test_setup_call_extract(
    mock_utils: MagicMock,
    mock_convert_message_params: MagicMock,
    mock_base_setup_call: MagicMock,
) -> None:
    """Tests the `setup_call` function with extraction."""
    mock_utils.setup_call = mock_base_setup_call
    _, _, _, _, call_kwargs = setup_call(
        model="mistral-large-latest",
        client=None,
        fn=MagicMock(),
        fn_args={},
        dynamic_config=None,
        tools=None,
        json_mode=False,
        call_params={},
        extract=True,
    )
    assert "tool_choice" in call_kwargs and call_kwargs["tool_choice"] == ToolChoice.any
