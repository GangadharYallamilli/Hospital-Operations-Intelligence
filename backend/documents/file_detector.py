import os


SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".xlsx": "xlsx",
    ".csv": "csv"
}


def detect_file_type(file_path):
    """
    Automatically detect the uploaded file type
    using its file extension.
    """

    extension = os.path.splitext(file_path)[1].lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    return SUPPORTED_EXTENSIONS[extension]


def get_file_information(file_path):
    """
    Return basic information about an uploaded file.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_type = detect_file_type(file_path)

    return {
        "file_name": file_name,
        "file_type": file_type,
        "extension": os.path.splitext(file_path)[1].lower(),
        "file_size_bytes": file_size
    }


if __name__ == "__main__":

    test_folder = "member2/documents/original"

    for file_name in os.listdir(test_folder):

        file_path = os.path.join(test_folder, file_name)

        # Ignore folders and internal files
        if not os.path.isfile(file_path):
            continue

        # Ignore files that are not supported
        extension = os.path.splitext(file_name)[1].lower()

        if extension not in SUPPORTED_EXTENSIONS:
            continue

        try:
            information = get_file_information(file_path)

            print(
                f"{information['file_name']} "
                f"-> {information['file_type']}"
            )

        except ValueError as error:
            print(f"{file_name} -> {error}")