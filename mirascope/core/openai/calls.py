"""The `openai_call` decorator for easy OpenAI API typed functions."""

import datetime
import inspect
from typing import (
    Awaitable,
    Callable,
    ParamSpec,
    Unpack,
    overload,
)

from openai import AsyncOpenAI, OpenAI

from ..base import BaseTool
from .call_params import OpenAICallParams
from .call_response import OpenAICallResponse
from .call_response_chunk import OpenAICallResponseChunk
from .function_return import OpenAICallFunctionReturn
from .streams import OpenAIAsyncStream, OpenAIStream
from .utils import setup_call

P = ParamSpec("P")


def openai_call(
    tools: list[type[BaseTool] | Callable] | None = None,
    **call_params: Unpack[OpenAICallParams],
):
    '''A decorator for calling the OpenAI API with a typed function.

    This decorator is used to wrap a typed function that calls the OpenAI API. It parses
    the docstring of the wrapped function as the messages array and templates the input
    arguments for the function into each message's template.

    Example:

    ```python
    @openai_call(model="gpt-4o")
    def recommend_book(genre: str):
        """Recommend a {genre} book."""

    response = recommend_book("fantasy")
    ```

    Args:
        tools: The tools to use in the OpenAI API call.
        **call_params: The `OpenAICallParams` call parameters to use in the API call.

    Returns:
        The decorator for turning a typed function into an OpenAI API call.
    '''

    @overload
    def call_decorator(
        fn: Callable[P, OpenAICallFunctionReturn],
    ) -> Callable[P, OpenAICallResponse]: ...  # pragma: no cover

    @overload
    def call_decorator(
        fn: Callable[P, Awaitable[OpenAICallFunctionReturn]],
    ) -> Callable[P, Awaitable[OpenAICallResponse]]: ...  # pragma: no cover

    def call_decorator(
        fn: Callable[P, OpenAICallFunctionReturn | Awaitable[OpenAICallFunctionReturn]],
    ) -> Callable[P, OpenAICallResponse | Awaitable[OpenAICallResponse]]:
        if inspect.iscoroutinefunction(fn):

            async def inner_async(
                *args: P.args, **kwargs: P.kwargs
            ) -> OpenAICallResponse:
                fn_args = inspect.signature(fn).bind(*args, **kwargs).arguments
                fn_return = await fn(*args, **kwargs)
                prompt_template, messages, tool_types, call_kwargs = setup_call(
                    fn, fn_args, fn_return, tools, call_params
                )
                client = AsyncOpenAI()
                start_time = datetime.datetime.now().timestamp() * 1000
                response = await client.chat.completions.create(
                    messages=messages, **call_kwargs
                )
                return OpenAICallResponse(
                    response=response,
                    tool_types=tool_types,
                    prompt_template=prompt_template,
                    fn_args=fn_args,
                    fn_return=fn_return,
                    messages=messages,
                    call_params=call_kwargs,
                    user_message_param=messages[-1]
                    if messages[-1]["role"] == "user"
                    else None,
                    start_time=start_time,
                    end_time=datetime.datetime.now().timestamp() * 1000,
                    cost=None,  # NEED THIS FIXED
                )

            return inner_async
        else:

            def inner(*args: P.args, **kwargs: P.kwargs) -> OpenAICallResponse:
                fn_args = inspect.signature(fn).bind(*args, **kwargs).arguments
                fn_return = fn(*args, **kwargs)
                assert not inspect.isawaitable(fn_return)
                prompt_template, messages, tool_types, call_kwargs = setup_call(
                    fn, fn_args, fn_return, tools, call_params
                )
                client = OpenAI()
                start_time = datetime.datetime.now().timestamp() * 1000
                response = client.chat.completions.create(
                    messages=messages, **call_kwargs
                )
                return OpenAICallResponse(
                    response=response,
                    tool_types=tool_types,
                    prompt_template=prompt_template,
                    fn_args=fn_args,
                    fn_return=fn_return,
                    messages=messages,
                    call_params=call_kwargs,
                    user_message_param=messages[-1]
                    if messages[-1]["role"] == "user"
                    else None,
                    start_time=start_time,
                    end_time=datetime.datetime.now().timestamp() * 1000,
                    cost=None,  # NEED THIS FIXED
                )

            return inner

    return call_decorator


def openai_stream(
    tools: list[type[BaseTool] | Callable] | None = None,
    **call_params: Unpack[OpenAICallParams],
):
    '''A decorator for streaming the OpenAI API with a typed function.

    This decorator is used to wrap a typed function that calls the OpenAI API and
    streams the response. It parses the docstring of the wrapped function as the
    messages array and templates the input arguments for the function into each
    message's template.

    Example:

    ```python
    @openai_stream(model="gpt-4o")
    def recommend_book(genre: str):
        """Recommend a {genre} book."""

    stream = recommend_book("fantasy")
    for chunk in stream:
        print(chunk.content, end="", flush=True)
    ```

    Args:
        tools: The tools to use in the OpenAI API call.
        **call_params: The `OpenAICallParams` call parameters to use in the API call.

    Returns:
        The decorator for turning a typed function into an OpenAI API stream.
    '''

    @overload
    def stream_decorator(
        fn: Callable[P, OpenAICallFunctionReturn],
    ) -> Callable[P, OpenAIStream]: ...  # pragma: no cover

    @overload
    def stream_decorator(
        fn: Callable[P, Awaitable[OpenAICallFunctionReturn]],
    ) -> Callable[P, Awaitable[OpenAIAsyncStream]]: ...  # pragma: no cover

    def stream_decorator(
        fn: Callable[P, OpenAICallFunctionReturn | Awaitable[OpenAICallFunctionReturn]],
    ) -> Callable[P, OpenAIStream | Awaitable[OpenAIAsyncStream]]:
        if inspect.iscoroutinefunction(fn):

            async def inner_async(
                *args: P.args, **kwargs: P.kwargs
            ) -> OpenAIAsyncStream:
                fn_args = inspect.signature(fn).bind(*args, **kwargs).arguments
                fn_return = await fn(*args, **kwargs)
                _, messages, tool_types, call_kwargs = setup_call(
                    fn, fn_args, fn_return, tools, call_params
                )
                client = AsyncOpenAI()
                stream = await client.chat.completions.create(
                    messages=messages, stream=True, **call_kwargs
                )

                async def generator():
                    async for chunk in stream:
                        yield OpenAICallResponseChunk(
                            chunk=chunk,
                            user_message_param=messages[-1]
                            if messages[-1]["role"] == "user"
                            else None,
                            tool_types=tool_types,
                            cost=None,  # NEED THIS FIXED
                        )

                return OpenAIAsyncStream(generator())

            return inner_async
        else:

            def inner(*args: P.args, **kwargs: P.kwargs) -> OpenAIStream:
                fn_args = inspect.signature(fn).bind(*args, **kwargs).arguments
                fn_return = fn(*args, **kwargs)
                assert not inspect.isawaitable(fn_return)
                _, messages, tool_types, call_kwargs = setup_call(
                    fn, fn_args, fn_return, tools, call_params
                )
                client = OpenAI()
                stream = client.chat.completions.create(
                    messages=messages, stream=True, **call_kwargs
                )

                def generator():
                    for chunk in stream:
                        yield OpenAICallResponseChunk(
                            chunk=chunk,
                            user_message_param=messages[-1]
                            if messages[-1]["role"] == "user"
                            else None,
                            tool_types=tool_types,
                            cost=None,  # NEED THIS FIXED
                        )

                return OpenAIStream(generator())

            return inner

    return stream_decorator
