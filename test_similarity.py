from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Tải mô hình nhúng thực tế
model = SentenceTransformer('all-MiniLM-L6-v2')

pairs = [
    # Cặp 1 (Từ Q1): Khác từ vựng nhưng cùng ý nghĩa (Paraphrase)
    ("Can I add a new product to an order that has already been placed?", 
     "Is it possible to include extra items in a basket after checkout?"),
    
    # Cặp 2 (Từ Q3): Trùng 90% từ vựng nhưng NGƯỢC NGHĨA (Negation)
    ("A cancelled order cannot be edited or refunded.", 
     "A cancelled order can be edited or refunded."),
    
    # Cặp 3 (Từ Q4 & Q5): Cùng chủ đề (Subscription) nhưng khác câu hỏi
    ("When is card payment taken for a subscription?", 
     "How must a change to the subscription schedule be handled?"),
    
    # Cặp 4 (Từ Q2): Khác cấu trúc nhưng diễn đạt cùng một thông tin
    ("Stripe payments can take 3-5 working days to appear on a customer’s bank statement.", 
     "The buyer will see the refunded money in their bank account within a week."),
    
    # Cặp 5 (Từ Q2 & Q5): Hoàn toàn không liên quan
    ("Clicking the 'X' will void the whole payment.", 
     "You can change the products the customer orders via subscription.")
]

print("--- KẾT QUẢ ĐIỂM TƯƠNG TỰ (COSINE SIMILARITY) ---")
for i, (a, b) in enumerate(pairs, 1):
    embeddings = model.encode([a, b])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    print(f"Cặp {i} score: {score:.3f}")