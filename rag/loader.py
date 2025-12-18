from langchain_community.document_loaders import DirectoryLoader,PyMuPDFLoader


#loading data using PyMuPDF and DirectoryLoader
pdf_dir= "data/pdfs"
def load_pdf(pdf_dir):
   
   loader=DirectoryLoader(
   path=pdf_dir,
   glob='*.pdf',
   loader_cls=PyMuPDFLoader
   )

   docs=loader.load()

   return docs
