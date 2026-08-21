from langchain_community.document_loaders import PyPDFLoader

def parse_pdf(file_path:str):
    pdf_loader = PyPDFLoader("Get_Started_With_Smallpdf.pdf")
    pdf_documents = pdf_loader.load(file_path)
    parse_text = pdf_documents[0].page_content

    return parse_text
