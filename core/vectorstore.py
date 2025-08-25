from langchain_pinecone import PineconeVectorStore
from .embedding import get_embedding

_vectorstore = None

def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = PineconeVectorStore.from_existing_index(
            index_name='swpre10',  # 1024차원 인덱스명
            embedding=get_embedding()
        )
    return _vectorstore 