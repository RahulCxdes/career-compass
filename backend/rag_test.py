# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_chroma import Chroma

# # 1. Load embeddings (MiniLM)
# embedding_model = HuggingFaceEmbeddings(
#     model_name="sentence-transformers/all-MiniLM-L6-v2"
# )

# # 2. Create Chroma store (new API)
# db = Chroma(
#     collection_name="career_docs",
#     embedding_function=embedding_model,
#     persist_directory="chroma_store"
# )

# # 3. Add documents
# documents = [
#     "Python is required for backend roles and data science.",
#     "React is used for frontend development.",
#     "Docker is important for DevOps.",
# ]

# db.add_texts(documents)

# # 4. Query
# query = "What skills do I need for data science?"
# results = db.similarity_search(query, k=2)

# print("\nRAG Results:")
# for r in results:
#     print("-", r.page_content)
