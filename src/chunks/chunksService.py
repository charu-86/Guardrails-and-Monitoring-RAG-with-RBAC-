from langchain.text_splitter import RecursiveCharacterTextSplitter

from ingestion.models import IngestedDocument
langchainChunks = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100

)
def chunk_document(Document)-> list[str]:
    chunks = langchainChunks.split_text(Document.text)
    return chunks
def query_document(text: str) -> list[str]:
    chunks = langchainChunks.split_text(text)
    return chunks

def chunk_Ingested_document(document: IngestedDocument) -> list[str]:
    return langchainChunks.split_text(document.content)