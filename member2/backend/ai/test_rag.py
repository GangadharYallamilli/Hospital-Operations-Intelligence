from member2.backend.ai.semantic_search import semantic_search
from member2.backend.ai.rag_answer_generator import create_rag_answer


question = input("Enter your question: ")

retrieved_chunks = semantic_search(question, top_k=5)

answer = create_rag_answer(
    question,
    retrieved_chunks
)

print("\nAI Answer:\n")
print(answer)