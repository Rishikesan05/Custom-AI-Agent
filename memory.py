import os
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class MemoryStore:
    def __init__(self, index_path="memory_index"):
        self.index_path = index_path
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
        
        # Load existing memory if available
        if os.path.exists(self.index_path):
            self.vector_store = FAISS.load_local(
                self.index_path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        else:
            # Initialize with a dummy document so it's ready to add and save
            self.vector_store = FAISS.from_texts(["Memory initialized."], self.embeddings)

    def save_memory(self, memory_text: str):
        """Save a new memory text into the FAISS index."""
        doc = Document(page_content=memory_text)
        self.vector_store.add_documents([doc])
        self.vector_store.save_local(self.index_path)

    def recall_memories(self, query: str, k=3) -> str:
        """Recall top-k relevant memories for a given query."""
        docs = self.vector_store.similarity_search(query, k=k)
        # Filter out the dummy init message
        valid_docs = [d.page_content for d in docs if d.page_content != "Memory initialized."]
        if not valid_docs:
            return ""
        
        return "\n".join(f"- {mem}" for mem in valid_docs)
