from bs4 import BeautifulSoup


# This function is used to truncate HTML content to a specified number of words while ignoring images.
# It takes an HTML string and a maximum word count as input, and returns a plain text string truncated to
# the specified number of words. If the input HTML is empty or None, it returns the input value as is.
def truncate_html_to_words(value: str, max_words: int = 300) -> str:
    if not value:
        return value

    soup = BeautifulSoup(value, "html.parser")

    # Remove images completely.
    for image in soup.find_all("img"):
        image.decompose()

    # Convert the remaining HTML to plain text.
    text = soup.get_text(separator=" ", strip=True)

    words = text.split()

    if len(words) <= max_words:
        return text

    return " ".join(words[:max_words]) + "..."
