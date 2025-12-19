from langchain_text_splitters import RecursiveCharacterTextSplitter
#Splitting the document into chunks for better performance
def split_documents(docs):
    api_separators = [
    "\n## ",
    "\n### ",
    "\n#### ",
    "\nEndpoint:",
    "\nMethod:",
    "\nRequest",
    "\nResponse",
    "\nParameters",
    "\nHeaders",
    "\nBody",
    "\n```",
    "\n\n",
    "\n",
    " ",
    ""
    ]

    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=api_separators
    )
    
    chunks=text_splitter.split_documents(docs)

    return chunks
