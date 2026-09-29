import re
import unicodedata

from ftfy import fix_text


def repair_mojibake(text):
    """
    Repair common mojibake produced by PDF text extraction.

    This is a generic repair step and is not tied to a particular
    hospital or document.
    """

    if not text:
        return ""

    # First let ftfy repair standard encoding problems.
    text = fix_text(text)

    # Some PDF extraction paths can leave a second layer of
    # incorrectly decoded UTF-8 bytes. Repair only when the
    # text clearly contains mojibake markers.
    mojibake_markers = (
        "â",
        "Â",
        "Ã",
        "ð",
    )

    if any(marker in text for marker in mojibake_markers):

        try:
            repaired = text.encode("latin1").decode("utf-8")

            # Only accept the repair if it actually improves the text.
            if sum(text.count(x) for x in mojibake_markers) > \
               sum(repaired.count(x) for x in mojibake_markers):
                text = repaired

        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    return text


def clean_text(text):
    """
    Generic text cleaning for uploaded documents.
    """

    if not text:
        return ""

    # Repair encoding
    text = repair_mojibake(text)

    # Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Replace non-breaking spaces
    text = text.replace("\u00a0", " ")

    # Remove zero-width characters
    text = text.replace("\u200b", "")
    text = text.replace("\u200c", "")
    text = text.replace("\u200d", "")
    text = text.replace("\ufeff", "")

    cleaned_lines = []

    for line in text.split("\n"):

        # Normalize spaces and tabs
        line = re.sub(r"[ \t]+", " ", line)

        # Remove leading/trailing spaces
        line = line.strip()

        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def clean_table(table):
    """
    Clean all cells in an extracted table.
    """

    cleaned_table = []

    for row in table:

        cleaned_row = []

        for cell in row:

            if cell is None:
                cell = ""

            cleaned_row.append(clean_text(str(cell)))

        cleaned_table.append(cleaned_row)

    return cleaned_table


if __name__ == "__main__":

    sample_text = """
    The Trustâ€™s performance â€“ during 2024/25.

    Â£410m Income

    Directorsâ€™ report

    â€¢ Emergency Department

    NHS Oversight Framework â€¦
    """

    print("Before cleaning:")
    print(sample_text)

    cleaned = clean_text(sample_text)

    print("\nAfter cleaning:")
    print(cleaned)