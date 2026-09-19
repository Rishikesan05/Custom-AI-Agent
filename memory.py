import os
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class MemoryStore:
    def __init__(self, user_id="default", base_dir="memory_index"):
        self.user_id = str(user_id) if user_id else "default"
        self.base_dir = base_dir
        
        # Isolate storage per user/device so memories never bleed across users
        if self.user_id and self.user_id != "default":
            safe_uid = "".join(c for c in self.user_id if c.isalnum() or c in ("-", "_"))
            self.index_path = os.path.join(self.base_dir, safe_uid)
        else:
            self.index_path = self.base_dir
            
        os.makedirs(self.index_path, exist_ok=True)
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
        
        # Load existing memory if available
        index_file = os.path.join(self.index_path, "index.faiss")
        if os.path.exists(index_file):
            self.vector_store = FAISS.load_local(
                self.index_path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        else:
            # Check if root memory_index has existing memories to inherit
            root_index = os.path.join(self.base_dir, "index.faiss")
            if self.user_id != "default" and os.path.exists(root_index):
                import shutil
                try:
                    for f in ["index.faiss", "index.pkl"]:
                        src = os.path.join(self.base_dir, f)
                        if os.path.exists(src):
                            shutil.copy2(src, os.path.join(self.index_path, f))
                    self.vector_store = FAISS.load_local(
                        self.index_path,
                        self.embeddings,
                        allow_dangerous_deserialization=True
                    )
                except Exception:
                    self.vector_store = FAISS.from_texts(["Memory initialized."], self.embeddings)
                    self.vector_store.save_local(self.index_path)
            else:
                # Initialize with a dummy document so it's ready to add and save
                self.vector_store = FAISS.from_texts(["Memory initialized."], self.embeddings)
                self.vector_store.save_local(self.index_path)

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

    def get_all_memories(self) -> list[str]:
        """Return list of all stored memory texts."""
        try:
            if hasattr(self.vector_store, "docstore") and hasattr(self.vector_store.docstore, "_dict"):
                docs = self.vector_store.docstore._dict.values()
                return [d.page_content for d in docs if d.page_content != "Memory initialized."]
        except Exception:
            pass
        return []

    def delete_memory(self, memory_text: str) -> bool:
        """Delete an individual memory fact from FAISS."""
        try:
            current = self.get_all_memories()
            remaining = [m for m in current if m.strip() != memory_text.strip()]
            if remaining:
                self.vector_store = FAISS.from_texts(["Memory initialized."] + remaining, self.embeddings)
            else:
                self.vector_store = FAISS.from_texts(["Memory initialized."], self.embeddings)
            self.vector_store.save_local(self.index_path)
            return True
        except Exception as e:
            print(f"Error deleting memory: {e}")
            return False

    def clear_memory(self):
        """Clear all stored memories and reset the index."""
        self.vector_store = FAISS.from_texts(["Memory initialized."], self.embeddings)
        self.vector_store.save_local(self.index_path)

    @staticmethod
    def rename_vault(old_uid: str, new_uid: str, base_dir="memory_index") -> bool:
        """Safely copy/rename an existing vault directory to a new vault ID without data loss."""
        import shutil
        old_safe = "".join(c for c in str(old_uid) if c.isalnum() or c in ("-", "_")) if old_uid and old_uid != "default" else "default"
        new_safe = "".join(c for c in str(new_uid) if c.isalnum() or c in ("-", "_")) if new_uid and new_uid != "default" else "default"
        if not new_safe or old_safe == new_safe:
            return False
        
        old_path = os.path.join(base_dir, old_safe) if old_safe != "default" else base_dir
        new_path = os.path.join(base_dir, new_safe) if new_safe != "default" else base_dir
        
        try:
            if os.path.exists(old_path) and os.path.exists(os.path.join(old_path, "index.faiss")):
                os.makedirs(new_path, exist_ok=True)
                for f in ["index.faiss", "index.pkl"]:
                    src = os.path.join(old_path, f)
                    if os.path.exists(src):
                        shutil.copy2(src, os.path.join(new_path, f))
                return True
        except Exception as e:
            print(f"Error migrating vault: {e}")
        return False

