from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(docs):
    """Split documents into overlapping chunks optimised for API documentation.

    Separators are written as zero-width regex look-aheads so the separator
    text (e.g. the heading "Endpoint:") is *preserved* at the start of the
    new chunk rather than being consumed and discarded by the splitter.
    """
    api_separators = [
        r"(?=\n## )",
        r"(?=\n### )",
        r"(?=\n#### )",
        r"(?=\nEndpoint:)",
        r"(?=\nMethod:)",
        r"(?=\nRequest)",
        r"(?=\nResponse)",
        r"(?=\nParameters)",
        r"(?=\nHeaders)",
        r"(?=\nBody)",
        r"(?=\n```)",
        r"\n\n",
        r"\n",
        r" ",
        r"",
    ]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=api_separators,
        is_separator_regex=True,
    )

    return text_splitter.split_documents(docs)

