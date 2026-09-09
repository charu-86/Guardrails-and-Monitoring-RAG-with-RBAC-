from database.chroma import collect
from chuks.chunksService import chunk_document, query_document
from llm.llmService import generate_answer, generate_answer_without_context, validate_query

def addDocument(document):
    doc = []
    ids = []
    metadata = []
    chunks = chunk_document(document)
    for index, chunk in enumerate(chunks):

        doc.append(chunk)
        ids.append(f"{document.id}_{index}")
        metadata.append({
            "document_id": document.id,
            "category": document.category,
            "chunk_index": index
        })

    collect.add(
        documents=doc,
        metadatas=metadata,
        ids=ids
    )

def queryDocument(text: str, n_results: int = 1):
    chunks = query_document(text)
    results = []
    for chunk in chunks:
        result = collect.query(
            query_texts=[chunk],
            n_results=n_results
        )
        results.append(result)
    return results

def QueryDocumentUpdated(text: str, n_results: int = 1) -> list[str]:
    result = collect.query(
        query_texts=[text],
        n_results=n_results
    )
    return result

# def deleteDocument(document_id):
#     chunks_document = chunk_document(document_id)
#     for Index in enumerate(chunks_document):
#         collect.delete(ids=[f"{document_id}_{Index}"])
def deleteDocument(document_id):

    collect.delete(
        where={
            "document_id": document_id
        }
    )

# def updateDocument(document):
#     doc = []
#     ids = []
#     metadata = []
#     chunks = chunk_document(document)

#     for Index, chunk in enumerate(chunks):
#         doc.append(chunk)
#         metadata.append({"category": document.category})
#         ids.append(f"{document.id}_{Index}")

#     collect.update(
#         documents=doc,
#         metadatas=metadata,
#         ids=ids
#     )

def getAllDocuments():
    return collect.get()

def deleteAllDocuments():
    all_docs = collect.get()

    if all_docs["ids"]:
        collect.delete(ids=all_docs["ids"])

def generateAnswerFromQuery(query: str) -> str:
        answer = generate_answer(query)
        return answer
def generateAnswerWithoutContext(query: str) -> str:
        answer = generate_answer_without_context(query)
        return answer

def generateAnswerFromQueryWithContext(query: str, n_results: int = 3, modelStr: str = "gemini") -> str:
    context = queryDocument(text=query, n_results=n_results)
    answer = generate_answer(query= query, context=context, provider= modelStr)
    # answer = context
    return answer

def isPromptValid(query: str) -> bool:
    answer = validate_query(query = query)
    if answer == "Unsafe":
        return False
    return True
     
     