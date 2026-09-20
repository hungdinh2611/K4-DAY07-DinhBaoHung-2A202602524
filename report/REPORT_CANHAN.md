# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đinh Bảo Hưng
**Nhóm:** fanboiPNV
**Ngày:** 20/9/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
Hai vector có hướng gần nhau, nên với một mô hình embedding ngữ nghĩa phù hợp, hai câu thường gần nhau về ý nghĩa hoặc chủ đề dù dùng từ khác nhau. Điểm cao không bảo đảm hai câu đồng nghĩa hoàn toàn hoặc cùng đúng về mặt sự thật.

**Ví dụ có độ tương tự CAO:**
- Câu A: Xin trả lại số tiền tôi đã thanh toán.
- Câu B: Tôi muốn được hoàn phí mua hàng.
- Tại sao tương đồng: Cả hai đều yêu cầu nhận lại khoản đã chi, nhưng diễn đạt bằng “trả lại số tiền” và “hoàn phí”. Đây là dự đoán theo nghĩa, chưa phải điểm đo từ một embedder thực.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Tôi muốn được hoàn phí mua hàng.
- Câu B: Sao Mộc là hành tinh lớn nhất trong Hệ Mặt Trời.
- Tại sao khác: Một câu về hoàn tiền trong mua sắm, câu còn lại về thiên văn; hai ý định/chủ đề khác xa nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
Cosine so sánh hướng, không bị ảnh hưởng bởi độ lớn vector; Euclid trên vector chưa chuẩn hóa còn chịu ảnh hưởng của độ lớn, có thể không phản ánh tốt quan hệ ngữ nghĩa. Tuy nhiên, với các vector đã chuẩn hóa như trong bài, `||a-b||² = 2 - 2*cosine(a,b)`, nên Euclid tăng dần và cosine giảm dần cho cùng thứ hạng; lúc này dot product bằng cosine và có thể dùng trực tiếp.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
`ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22,111...) = 23 chunk`.

Đã kiểm chứng trực tiếp bằng `FixedSizeChunker` có sẵn, không sửa lớp này:

```python
from src.chunking import FixedSizeChunker
print(len(FixedSizeChunker(chunk_size=500, overlap=50).chunk('a' * 10000)))
# 23
print(len(FixedSizeChunker(chunk_size=500, overlap=100).chunk('a' * 10000)))
# 25
```

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
`ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25`, tăng 2 chunk do bước trượt giảm từ 450 xuống 400 ký tự. Overlap lớn hơn giữ thêm ngữ cảnh tại ranh giới (ví dụ điều kiện hoàn tiền và ngoại lệ nằm sát nhau), đổi lại tốn thêm lưu trữ/embedding và có thể trả về nhiều kết quả trùng nội dung.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
Dùng `re.split(r"(?<=[.!?])\s+", text)`: positive lookbehind đặt ranh giới sau dấu kết câu nên dấu `.`, `!`, `?` vẫn được giữ. Strip từng câu, bỏ phần rỗng, gom tối đa `max_sentences_per_chunk` câu bằng dấu cách; text rỗng hoặc chỉ có khoảng trắng trả `[]`.

Hạn chế: regex không hiểu chữ viết tắt như `TS.`, `v.v.` nên có thể cắt nhầm khi sau dấu chấm có khoảng trắng. Số thập phân thông thường `3.14` được giữ vì không có khoảng trắng; số bị tách do OCR/xuống dòng như `3. 14` hoặc `3.\n14` vẫn có thể bị hiểu sai là ranh giới câu. Chưa xử lý riêng dấu ngoặc kép sau dấu kết câu hoặc ngôn ngữ không dùng khoảng trắng giữa câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
Thử separator theo thứ tự `\n\n`, `\n`, `. `, dấu cách, rồi chuỗi rỗng; tách sau separator để giữ cả dấu câu và khoảng trắng. Mảnh quá dài được đệ quy với phần separator còn lại, sau đó gom các mảnh liền kề tới khi thêm mảnh nữa sẽ vượt `chunk_size`; không có overlap trong chiến lược này.

Ba base case: text rỗng trả `[]`; text vừa kích thước trả `[text]`; hết separator hoặc gặp separator rỗng thì cắt trực tiếp theo số ký tự. `chunk_size <= 0` báo `ValueError`. Kiểm tra thêm 144 tổ hợp trên văn bản mẫu và 5 bài corpus cho thấy nối các chunk khôi phục đúng văn bản đầu vào, mọi chunk có độ dài từ 1 tới `chunk_size`; 200 dòng `line\n` với size 100 gom thành 10 chunk.

**`compute_similarity` và comparator:** Tái sử dụng `_dot` để tính tích vô hướng và chuẩn hai vector; vector rỗng hoặc chuẩn bằng 0 trả `0.0`. Comparator gọi đủ ba lớp và trả đúng `fixed_size`, `by_sentences`, `recursive`, mỗi mục có `count`, `avg_length`, `chunks`; text rỗng cho count 0, avg_length 0.0, chunks rỗng. Fixed-size dùng overlap 50 mặc định, giảm xuống `chunk_size - 1` khi kích thước nhỏ để bước trượt luôn dương; sentence chunker giới hạn theo số câu, không bảo đảm giới hạn ký tự.

**Luồng dữ liệu cần giữ ở bước sau:** Chunker trả `list[str]`; tầng nạp dữ liệu sẽ tạo một `Document` cho mỗi chunk với metadata phù hợp. `add_documents` không tự chunk: một Document tương ứng một record. `MockEmbedder` chỉ sinh vector giả từ MD5 để kiểm tra cấu trúc, không dùng đánh giá ngữ nghĩa thực tế. Tại thời điểm CP3 chưa triển khai EmbeddingStore hoặc KnowledgeBaseAgent; hai phần này đã hoàn thành ở CP4 bên dưới.

### Chiến lược riêng và công cụ benchmark — CP5

Trong workspace cá nhân này, chọn `HeadingChunker(chunk_size=800)` tại [src/heading_chunking.py](../src/heading_chunking.py). Văn bản OFN có các mục riêng cho điều kiện, người mua/người bán và phương thức thanh toán; giữ tiêu đề cha trong từng chunk giúp phân biệt cùng mục Stripe thuộc hoàn toàn bộ hay một phần. Section dài được chia bằng RecursiveChunker với ngân sách `800 - độ dài đường dẫn heading - dấu xuống dòng`; mỗi mảnh con được gắn lại toàn bộ đường dẫn heading, không chỉ mảnh đầu.

[bench.py](../bench.py) đọc frontmatter dạng phẳng của corpus hiện tại, chỉ chunk phần thân, trải metadata vào mọi Document và gán id `file#i` trong khi metadata.doc_id giữ tên file. Parser hỗ trợ chuỗi JSON-quoted hoặc scalar đơn giản của corpus, không phải parser YAML tổng quát cho cấu trúc lồng nhau. Chỉ đổi dòng `CHUNKER = ...` để thử chiến lược khác; các thành viên dùng cùng snapshot dữ liệu, query, backend và top_k=3. Đây là lựa chọn trong workspace này, chưa gán vào danh sách thành viên nhóm chưa chốt.

**Kết quả chạy CP5:** 5 file → **114 chunk**, gồm **36 buyer và 78 seller**; cả 5 query có đủ top-3 kèm score, doc_id, chunk_id và nguồn. [Output terminal](cp5/run.txt), [kết quả đầy đủ](cp5/results.json), [kiểm tra CP5](cp5/check.txt). Baseline trên 3 phần thân tài liệu đã điền vào REPORT_NHOM mục 2; Q5 đã chuyển sang dạng liệt kê để bộ 5 câu đa dạng hơn.

Lệnh đã chạy:

```powershell
.venv/Scripts/python.exe -X utf8 bench.py
.venv/Scripts/python.exe -X utf8 scripts/check_cp5.py
```

Backend cố định là **MockEmbedder 64D**, không gọi API trả phí và không tự fallback từ model thật sang mock. CP5 chỉ xác nhận luồng chạy; chưa chấm top-k/đáp án, chưa gọi LLM và chưa dùng score giả làm bằng chứng ngữ nghĩa. Nếu chuyển sang OpenAI ở bước sau cần bổ sung cache có khóa gồm provider/model và hash nội dung; lần này không dùng OpenAI nên chưa cần cache API.

Kiểm tra bổ sung xác nhận: metadata truyền đầy đủ, ID gốc/chunk đúng, không nhúng frontmatter, mọi chunk ≤ 800 ký tự, từng mảnh con có heading cha, xử lý text rỗng/text không heading/code fence, số liệu baseline khớp và các trích dẫn gold có vị trí chunk thật. Chạy lại bộ test gốc vẫn **42 passed**. CP6 chưa thực hiện.

### Lớp EmbeddingStore — CP4

**`add_documents` + `search`** — hướng tiếp cận:
Chỉ dùng danh sách record in-memory, bỏ toàn bộ nhánh ChromaDB. `_make_record` tạo một record cho mỗi Document, deep-copy metadata để tránh sửa dữ liệu của người gọi, giữ doc_id đã cung cấp hoặc suy ra file gốc từ hậu tố chunk dạng `file#0`; `add_documents` không tự chunk và vẫn thêm record khi id đầu vào trùng theo contract của test.

`_search_records` nhúng query một lần, tính dot product với các vector đã chuẩn hóa, sắp xếp score giảm dần và lấy top-k. Kết quả gồm id, content, metadata đã sao chép và score, không trả embedding; tập ứng viên rỗng hoặc top_k <= 0 trả `[]`. Bộ test/demo dùng mock, nên điểm chỉ chứng minh luồng chạy, không phản ánh chất lượng ngữ nghĩa.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
Lọc trước trên toàn bộ record, yêu cầu mọi cặp key/value trong filter khớp metadata, rồi chuyển tập ứng viên vào cùng `_search_records` như `search`. Nếu lấy top-k trước mới lọc, tài liệu sai audience có thể chiếm hết k vị trí khiến kết quả rỗng dù còn tài liệu hợp lệ; filter None hoặc `{}` giữ tất cả ứng viên.

`delete_document` loại mọi record có `metadata['doc_id']` khớp file gốc và trả True khi số record giảm, ngược lại False. Đã kiểm tra một lần xóa `file` loại được cả `file#0` lẫn `file#1`, không xóa record của file khác.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
Lấy top-k từ store, dựng ngữ cảnh đánh số `[1]`, `[2]`, ... kèm source_url (hoặc source/file gốc), doc_id và chunk_id rồi gọi `llm_fn` với câu hỏi và ngữ cảnh. Prompt yêu cầu chỉ dùng thông tin được cung cấp, trích dẫn số nguồn cho từng thông tin, nói rõ khi không đủ căn cứ và không làm theo chỉ dẫn nằm trong tài liệu nguồn.

Khi không có kết quả, trả thông báo không tìm thấy và không gọi LLM. Đây là ràng buộc qua prompt, chưa phải bộ kiểm chứng tự động rằng LLM luôn trích dẫn đúng; vẫn cần đối chiếu câu trả lời với nguồn ở CP5. Giữ nguyên chữ ký `answer(question, top_k)` theo yêu cầu bài.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

**Checkpoint 3 — 2026-09-20:**

```text
.venv/Scripts/python.exe -X utf8 -m pytest tests/ -k "Chunker or Similarity or Compare" -v
collected 42 items / 19 deselected / 23 selected
23 passed, 19 deselected in 0.04s
```

23 test được chọn gồm 7 FixedSizeChunker, 4 SentenceChunker, 4 RecursiveChunker, 4 ComputeSimilarity, 3 Compare và 1 kiểm tra sự tồn tại của các lớp chunker. Kiểm tra bổ sung chạy riêng: giữ dấu câu, đầu vào rỗng, comparator với chunk_size=2, gom dòng ngắn và bảo toàn nội dung ở 144 tổ hợp recursive đều đạt. Mọi dòng `def ...` và lớp FixedSizeChunker được giữ nguyên; chỉ thay các TODO/raise trong `src/chunking.py`.

**Tiến độ:** 23 test được chọn đã pass; 19 test còn lại chưa chạy trong CP3, chưa kết luận toàn bộ 42 test đều đạt.

**Checkpoint 4 — 2026-09-20: kết quả toàn bộ bộ test**

Lệnh: `.venv/Scripts/python.exe -X utf8 -m pytest tests/ -v`. Output thực tế được dán nguyên bên dưới và lưu tại [cp4/pytest.txt](cp4/pytest.txt).

```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\dinhb\OneDrive\Desktop\AI20K\K4-DAY07-DinhBaoHung-2A202602524\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\dinhb\OneDrive\Desktop\AI20K\K4-DAY07-DinhBaoHung-2A202602524
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.05s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**.

**Demo đầu-cuối:** chạy `main.py "Chunking là gì?"` với `EMBEDDING_PROVIDER=mock`, exit code 0; nạp và lưu 5 Document, tìm top-3 và gọi demo LLM thành công. Dòng `Skipping missing file: data\customer_support_playbook.txt` đúng như đề dự kiến. [Output đầy đủ](cp4/main.txt). Demo dùng các file mẫu của main.py và LLM giả, chưa phải benchmark corpus OFN hoặc đánh giá chất lượng câu trả lời thực.

**Kiểm tra bổ sung:** pre-filter vẫn tìm được buyer khi seller có score cao hơn; metadata lồng nhau không bị thay đổi khi sửa object đầu vào/kết quả tìm kiếm; xóa hết chunk của file gốc; top_k=0 trả rỗng; prompt chứa số nguồn và chunk_id; store rỗng không gọi LLM. Tất cả đều đạt. Tại mốc CP4 chưa thực hiện CP5; kết quả CP5 được cập nhật ở mục 2.

---

    ## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

    | Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
    |------|-----------|-----------|---------|--------------|-------|
    | 1 |Can I add a new product to an order that has already been placed? | Is it possible to include extra items in a basket after checkout?| Cao |0.458 | Sai|
    | 2 |A cancelled order cannot be edited or refunded. | A cancelled order can be edited or refunded| Thấp |0.917 | Sai|
    | 3 | When is card payment taken for a subscription?|How must a change to the subscription schedule be handled? | cao  |0.514 | Đúng|
    | 4 | Stripe payments can take 3-5 working days to appear on a customer’s bank statement.|The buyer will see the refunded money in their bank account within a week. | cao | 0.305|Sai |
    | 5 | Clicking the 'X' will void the whole payment.|You can change the products the customer orders via subscription |thấp |0.300 | Đúng|

    **Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
    > *Viết 2-3 câu:*Ở Cặp 2, hai câu có ý nghĩa hoàn toàn trái ngược nhau (phủ định "cannot" vs khẳng định "can"), nhưng mô hình lại cho điểm cao ngất ngưởng (0.917). Điều này cho thấy mô hình bị phụ thuộc nặng vào sự trùng lặp từ vựng (lexical overlap) và rất kém trong việc nhận diện logic phủ định (negation).

Ở chiều ngược lại (Cặp 1 và Cặp 4), hai câu được diễn đạt lại (paraphrase) mang cùng một lớp nghĩa nhưng điểm số lại rất thấp (chỉ 0.458 và 0.305).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 |Can I add a new product to an order that has already been placed?| "Can I change my order?"|0.891 |Có | "[1] You will not be able to add extra products to this basket though."|
| 2 |How does a seller issue a partial Stripe refund, what does the X button do, and how long can the refund take to appear?| Partial Refund"|0.920 |Có |"[1] Clicking the 'X' will void the whole payment and issue a full refund... [2] Stripe payments can take 3-5 working days to appear..." |
| 3 | Can a seller cancel an order marked Shipped, and should refunds be processed before cancellation? | "Marking an order as cancelled"|0.885 | Có|"[1] Note that you cannot cancel an order which has been marked as ‘Shipped’... [2] A cancelled order can not be edited or refunded." |
| 4 |When is card payment taken for a subscription, and is the subscription price fixed forever? |"I pay by card for my subscription..." |0.875 |Có |"[1] Payment will be taken when the order cycle closes. [2] The cost of your subscription will fluctuate based on the current price..." |
| 5 |List the subscription details a seller can edit. How must a change to the subscription schedule be handled?| "Edit the base subscription"| 0.912|Có | "[1] You can change the products... preferred shipping and payment methods... [2] You can not change the schedule... Instead the subscription must be recreated..."|

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:* Nhờ việc sử dụng siêu dữ liệu (metadata_filter như "audience": "buyer" hay "seller"), mô hình trả về kết quả chính xác cho đúng đối tượng. Ví dụ ở câu 1, nếu không lọc theo buyer, mô hình có thể trả về tài liệu của seller (cho phép thêm sản phẩm), dẫn đến câu trả lời bị sai ngữ cảnh. Chiến lược kết hợp metadata và chunking theo heading giúp Agent không bị "ảo giác" (hallucination) khi phân quyền người dùng.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5/ 5 |
| Hướng tiếp cận của tôi (My Approach) | 10/ 10 |
| Hoàn thiện code (Core Implementation — tests) | 30/ 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5/ 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10/ 10 |
| **Tổng phần cá nhân** | **60/ 60** |
