from langchain_community.document_loaders import Docx2txtLoader

def parse_docx(file_path:str):
    docx_loader = Docx2txtLoader("Ritesh_Rana.docx")
    docx_documents = docx_loader.load(file_path)
    parse_docx = docx_documents[0]
    return parse_docx
