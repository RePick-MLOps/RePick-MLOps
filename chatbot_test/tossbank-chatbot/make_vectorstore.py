from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import HuggingFaceEmbeddings

def load_embedding_model(model_name="BAAI/bge-m3"):
    return HuggingFaceEmbeddings(model_name=model_name)

def load_pdf_file_pages(filepath):
    loader = PyPDFLoader(filepath)
    pages = loader.load_and_split()

    return pages

def split_documents(chunk_size, chunk_overlap, pages):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    splited_docs = text_splitter.split_documents(pages)

    return splited_docs

if __name__ == "__main__":
    model_huggingface = load_embedding_model()
    pages = load_pdf_file_pages("./datas/sample.pdf")
    docs = split_documents(1000, 30, pages)

    # db = Chroma.from_documents(docs, model_huggingface)
    db_toFiles = Chroma.from_documents(
        docs,
        model_huggingface,
        persist_directory="./models/tossbank.db")