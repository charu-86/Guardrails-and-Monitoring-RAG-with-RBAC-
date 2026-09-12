from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import chromadb

client = chromadb.PersistentClient("./data/chroma")

collect = client.get_or_create_collection("my_collection")
