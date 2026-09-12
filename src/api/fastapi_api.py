from fastapi import FastAPI, Response, HTTPException

from database.model import DocumentItem

from database.vector import (
    addDocument,
    generateAnswerWithoutContext,
    queryDocument,
    QueryDocumentUpdated,
    deleteDocument,
    getAllDocuments,
    deleteAllDocuments,
    generateAnswerFromQuery,
    generateAnswerFromQueryWithContext,
    validate_query,
    isPromptValid
)

from guardrails.guardrailService import (
    validate_input,
    validate_output
)

from ingestion.ingestion_service import IngestionService

from ingestion.models import LocalPDFRequest


app = FastAPI()


ingestion_service = IngestionService()


@app.get("/")
def read_root():

    return {"Hello": "World"}


@app.post("/ingest/local-pdf")
def ingest_local_pdf(request: LocalPDFRequest):

    document = ingestion_service.ingest_local_pdf(
        request.file_path
    )

    return {
        "status": "success",
        "document_id": document.id,
        "filename": document.filename,
        "file_type": document.file_type,
        "content_length": len(document.content),
        "metadata": document.metadata
    }


@app.post("/import-data")
def import_data(item: DocumentItem):

    try:

        addDocument(item)

        return {
            "status": "success",
            "message": f"Document {item.id} imported successfully."
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/search")
def search_data(
    query: str,
    n_results: int = 1
):

    results = queryDocument(
        text=query,
        n_results=n_results
    )

    return {
        "results": results
    }


@app.get("/search-updated")
def search_data_updated(
    query: str,
    n_results: int = 1
):

    results = QueryDocumentUpdated(
        text=query,
        n_results=n_results
    )

    return {
        "results": results
    }


@app.get("/get-all-documents")
def get_all_documents():

    return getAllDocuments()


@app.post("/delete-AllDocument")
def delete_document():

    deleteAllDocuments()

    return {
        "status": "success",
        "message": "All documents deleted successfully."
    }


@app.post("/ollama-query")
def ollama_query(query: str):

    try:

        if validate_input(query):

            return {
                "answer": "Prompt is not accurate"
            }

        answer = generateAnswerWithoutContext(query)

        answer = validate_output(answer)

        return {
            "answer": answer
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@app.post("/ollama-query-with-context")
def ollama_query_with_context(
    query: str,
    n_results: int = 3
):

    if validate_input(query):

        return {
            "answer": "Prompt is not accurate"
        }

    answer = generateAnswerFromQueryWithContext(
        query,
        n_results,
        "ollama"
    )

    answer = validate_output(answer)

    return {
        "answer": answer
    }


@app.post("/gemini-query-with-context")
def gemini_query_with_context(
    query: str,
    n_results: int = 3
):

    if not isPromptValid(query):

        return {
            "answer": "Prompt is not accurate"
        }

    answer = generateAnswerFromQueryWithContext(
        query,
        n_results,
        "gemini"
    )

    return {
        "answer": answer
    }


@app.get("/favicon.ico")
def favicon():

    return Response(status_code=204)