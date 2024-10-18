from mirascope.core import BaseDynamicConfig, BaseTool, anthropic, prompt_template


class GetBookAuthor(BaseTool):
    title: str

    def call(self) -> str:
        if self.title == "The Name of the Wind":
            return "Patrick Rothfuss"
        elif self.title == "Mistborn: The Final Empire":
            return "Brandon Sanderson"
        else:
            return "Unknown"


@anthropic.call("claude-3-5-sonnet-20240620", tools=[GetBookAuthor])
@prompt_template(
    """
    MESSAGES: {history}
    USER: {query}
    """
)
def identify_author(
    book: str, history: list[anthropic.AnthropicMessageParam]
) -> BaseDynamicConfig:
    return {"computed_fields": {"query": f"Who wrote {book}" if book else ""}}


history = []
response = identify_author("The Name of the Wind", history)
history += [response.user_message_param, response.message_param]
while tool := response.tool:
    tools_and_outputs = [(tool, tool.call())]
    history += response.tool_message_params(tools_and_outputs)
    response = identify_author("", history)
    history.append(response.message_param)
print(response.content)
# Output: The Name of the Wind was written by Patrick Rothfuss.