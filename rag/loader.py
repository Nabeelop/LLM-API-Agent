from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader

def load_pdf(path: str):
    loader = DirectoryLoader(
        path,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader
    )
    return loader.load()

def load_single_pdf(file_path: str):
    loader = PyPDFLoader(file_path)
    return loader.load()
