# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Tổng quan Benchmark
- **Tổng số cases:** 60
- **Tỉ lệ Pass/Fail:** 17 Pass / 43 Fail (Tỉ lệ đạt: 28.33%)
- **Điểm RAGAS trung bình:**
    - Hit Rate: 0.00
    - MRR: 0.00
- **Điểm LLM-Judge trung bình:** 2.32 / 5.0

## 2. Phân nhóm lỗi (Failure Clustering)
| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |
|----------|----------|---------------------|
| **Retrieval Failure** | 60 (100%) | Bước truy xuất thất bại hoàn toàn (Hit Rate = 0.0). Vector DB không lấy được chunk dữ liệu nào khớp với Ground Truth. |
| **Repetitive Irrelevancy** | ~40 | Agent bị "kẹt" context, liên tục trả lời lặp lại một câu duy nhất (VD: *"Nhân viên mới trong 30 ngày đầu được cấp Level 1..."*) cho hàng loạt câu hỏi không liên quan. |
| **Judge Rate Limit (429)** | 60 (100%) | Cơ chế Async chạy quá nhanh khiến API của OpenAI và Google báo lỗi vượt quá giới hạn (Rate Limit Exceeded), buộc phải dùng Heuristic Fallback để chấm điểm. |

## 3. Phân tích 5 Whys (Chọn 3 case tệ nhất)

### Case #1: Agent trả lời lạc đề, lặp lại câu trả lời cũ
1. **Symptom:** Khách hỏi *"Ai là người phê duyệt quyền truy cập Level 1?"* (Case số 3) hoặc *"Quyền Standard Access áp dụng cho ai?"* (Case số 4), Agent đều trả lời cứng nhắc: *"Nhân viên mới trong 30 ngày đầu được cấp Level 1 - Read Only"*.
2. **Why 1:** LLM sinh câu trả lời dựa trên một context sai hoàn toàn.
3. **Why 2:** Retriever không lấy được tài liệu phù hợp (bằng chứng là Hit Rate và MRR đều bằng 0.0).
4. **Why 3:** Pipeline Ingestion (nạp dữ liệu) có thể bị lỗi cấu hình, hoặc Embedding model không bắt được ngữ nghĩa câu hỏi.
5. **Why 4:** Chưa có cơ chế Fallback Prompt cho LLM (Ví dụ: "Nếu không thấy thông tin trong context, hãy nói Tôi không biết").
6. **Root Cause:** **Lỗi nghiêm trọng ở Ingestion & Retrieval Pipeline** kết hợp với Prompting thiếu chặt chẽ.

### Case #2: Hệ thống Judge không đáng tin cậy (Chấm 5 điểm cho câu trả lời sai)
1. **Symptom:** Khách hỏi *"Khi nghỉ ốm hơn 3 ngày liên tiếp thì cần thêm giấy tờ gì?"* (Case số 17), Agent trả lời đúng, nhưng điểm 5 này lại không đến từ AI mà từ thuật toán dự phòng (Mock Judge).
2. **Why 1:** Cả OpenAI và Gemini Judge đều báo lỗi `429 RateLimitReached`.
3. **Why 2:** Gửi 60 requests cùng lúc qua cơ chế `asyncio.gather()` khiến hệ thống vượt quá giới hạn "Tokens Per Minute" (TPM) hoặc "Requests Per Minute" (RPM) của gói Free Tier.
4. **Why 3:** Mã nguồn `runner.py` chạy bất đồng bộ (async) nhưng không có cơ chế kiểm soát luồng (Concurrency limit/Batching).
5. **Root Cause:** **Thiếu cơ chế Rate Limiting & Throttling** trong kiến trúc của hệ thống Eval Engine.

### Case #3: Đánh giá RAGAS Hit Rate luôn bằng 0.0
1. **Symptom:** Dù có một số case Agent trả lời đúng (như nghỉ phép 12 ngày), RAGAS Hit Rate vẫn trả về 0.0.
2. **Why 1:** Hàm đánh giá Hit Rate không tìm thấy ID của chunk được truy xuất trùng với `Ground Truth IDs` trong tệp `golden_set.jsonl`.
3. **Why 2:** Dữ liệu ID sinh ra từ file `synthetic_gen.py` không khớp với ID thực tế được lưu vào Vector DB.
4. **Root Cause:** **Mất đồng bộ (Mismatch) dữ liệu metadata** giữa quá trình tạo Synthetic Data và quá trình Ingestion.

## 4. Kế hoạch cải tiến (Action Plan)

**1. Sửa lỗi Ingestion & Retrieval (Ưu tiên Cao nhất):**
- Rà soát lại code sinh dữ liệu `synthetic_gen.py` và Vector DB để đảm bảo `chunk_id` khớp nhau hoàn toàn, từ đó tính chính xác Hit Rate.
- Nâng cấp chiến lược Chunking (chuyển từ Fixed-size sang Semantic Chunking) để các quy định về chính sách không bị cắt đứt đoạn.

**2. Tối ưu Hệ thống Đánh giá (Performance & Rate Limit):**
- Thêm thư viện `aiolimiter` hoặc cơ chế Semaphore `asyncio.Semaphore(5)` vào hàm gọi API trong `llm_judge.py` để giới hạn số luồng gọi cùng lúc, tránh bị API khóa vì spam (Lỗi 429).
- Bật cơ chế Exponential Backoff (chờ và thử lại) khi gặp mã lỗi 429 thay vì fallback ngay lập tức về Heuristic Score.

**3. Tối ưu LLM Prompting:**
- [ ] Cập nhật System Prompt cho Main Agent: *"Chỉ sử dụng thông tin từ context. Nếu context không chứa câu trả lời, tuyệt đối không bịa đặt và hãy trả lời: 'Tôi chưa có đủ thông tin'."*

---