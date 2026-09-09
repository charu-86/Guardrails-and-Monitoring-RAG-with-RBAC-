from langchain_ollama import ChatOllama
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


ollamaLLM = ChatOllama(
    model="gemma3:270m",
    temperature=0
)


# def generate_answer(question: str):
#     response = ollamaLLM.invoke(question)
#     return response.content

def generate_answer(query: str,context: str = "", provider: str = "gemini"):

    prompt = f"""
    First Analyse the question, if it is safe and not harmful from any perspective then,
    Answer the question using the following context.
    else, generate a response that indicates the question is not safe or harmful.

    Context:
    {context}

    Question:
    {query}
    """

    if provider == "ollama":

        response = ollamaLLM.invoke(prompt)
        return response.content

    elif provider == "gemini":

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )


        return response.text

    else:

        raise ValueError(
            f"Unsupported provider: {provider}"
        )

def generate_answer_without_context(query: str,context: str = "", provider: str = "ollama"):

    prompt = query

    if provider == "ollama":

        response = ollamaLLM.invoke(prompt)
        return response.content

    elif provider == "gemini":

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )


        return response.text

    else:

        raise ValueError(
            f"Unsupported provider: {provider}"
        )
def validate_query(query: str,context: str = "", provider: str = "gemini"):

    prompt = f"""
    Strictly answer in one word, if the below question is Safe to answer or Unsafe.

    Question:
    {query}
    """

    if provider == "ollama":

        response = ollamaLLM.invoke(prompt)
        return response.content

    elif provider == "gemini":

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )


        return response.text

    else:

        raise ValueError(
            f"Unsupported provider: {provider}"
        )    