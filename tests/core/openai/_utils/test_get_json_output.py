"""Tests the `openai._utils.get_json_output` module."""

import pytest
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import (
    Choice as ChunkChoice,
)
from openai.types.chat.chat_completion_chunk import (
    ChoiceDelta,
    ChoiceDeltaToolCall,
    ChoiceDeltaToolCallFunction,
)
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)

from mirascope.core.openai._utils._get_json_output import get_json_output
from mirascope.core.openai.call_response import OpenAICallResponse
from mirascope.core.openai.call_response_chunk import OpenAICallResponseChunk


def test_get_json_output_call_response() -> None:
    """Tests the `get_json_output` function with a call response."""
    tool_call = ChatCompletionMessageToolCall(
        id="id",
        function=Function(
            arguments='{"title": "The Name of the Wind", "author": "Patrick Rothfuss"}',
            name="FormatBook",
        ),
        type="function",
    )
    choices = [
        Choice(
            finish_reason="stop",
            index=0,
            message=ChatCompletionMessage(
                content="json_output", role="assistant", tool_calls=[tool_call]
            ),
        )
    ]
    completion = ChatCompletion(
        id="id",
        choices=choices,
        created=0,
        model="gpt-4o",
        object="chat.completion",
    )
    call_response = OpenAICallResponse(
        metadata={},
        response=completion,
        tool_types=None,
        prompt_template="",
        fn_args={},
        dynamic_config=None,
        messages=[],
        call_params={},
        call_kwargs={},
        user_message_param=None,
        start_time=0,
        end_time=0,
    )
    assert get_json_output(call_response, json_mode=True) == "json_output"
    assert (
        get_json_output(call_response, json_mode=False)
        == '{"title": "The Name of the Wind", "author": "Patrick Rothfuss"}'
    )

    completion.choices[0].message.content = None
    completion.choices[0].message.tool_calls = None
    with pytest.raises(
        ValueError, match="No tool call or JSON object found in response."
    ):
        get_json_output(call_response, json_mode=False)


def test_get_json_output_call_response_chunk() -> None:
    """Tests the `get_json_output` function with a call response chunk."""
    tool_call = ChoiceDeltaToolCall(
        index=0,
        id="id",
        function=ChoiceDeltaToolCallFunction(
            arguments='{"title": "The Name of the Wind", "author": "Patrick Rothfuss"}',
            name="function",
        ),
        type="function",
    )
    choices = [
        ChunkChoice(
            delta=ChoiceDelta(content="json_output", tool_calls=[tool_call]),
            index=0,
            finish_reason="stop",
        )
    ]
    chunk = ChatCompletionChunk(
        id="id",
        choices=choices,
        created=0,
        model="gpt-4o",
        object="chat.completion.chunk",
    )
    call_response_chunk = OpenAICallResponseChunk(chunk=chunk)
    assert get_json_output(call_response_chunk, json_mode=True) == "json_output"
    assert (
        get_json_output(call_response_chunk, json_mode=False)
        == '{"title": "The Name of the Wind", "author": "Patrick Rothfuss"}'
    )

    chunk.choices[0].delta.tool_calls = None
    assert get_json_output(call_response_chunk, json_mode=False) == ""
