from mirascope.core import Messages, gemini


def get_book_author(title: str) -> str:
    """Returns the author of the book with the given title

    Args:
        title: The title of the book.
    """
    if title == "The Name of the Wind":
        return "Patrick Rothfuss"
    elif title == "Mistborn: The Final Empire":
        return "Brandon Sanderson"
    else:
        return "Unknown"


@gemini.call("gemini-1.5-flash", tools=[get_book_author])
def identify_authors(books: list[str]) -> Messages.Type:
    return Messages.User(f"Who wrote {books}?")


response = identify_authors(["The Name of the Wind", "Mistborn: The Final Empire"])
if tools := response.tools:
    for tool in tools:
        print(tool.call())
else:
    print(response.content)