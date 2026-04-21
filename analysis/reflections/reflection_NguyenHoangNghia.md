# Individual Technical Reflection

**Thông tin cá nhân:**
- **Họ và tên:** Nguyễn Hoàng Nghĩa
- **Mã sinh viên:** 2A202600161
- **Nhóm**: C401-B4
- **Ngày**: 21/04/2026

---

## 1. Engineering Contribution 

Tôi chịu trách nhiệm chính trong việc xây dựng file `main.py`.
### System Integration 
Tôi đã thiết kế luồng dữ liệu để kết nối 3 module phức tạp từ các thành viên khác:
- **Data Module:** Lấy dữ liệu từ `golden_set.jsonl` và tích hợp `RetrievalEvaluator` để tính toán Hit Rate/MRR.
- **AI Module:** Khởi tạo và điều phối `MainAgent` (V1 & V2) để lấy kết quả trả về.
- **Judge Module:** Tích hợp `LLMJudge` (Consensus Engine) để chấm điểm đa mô hình (OpenAI & Gemini).\

### Async Execution Control
Trong file `main.py`, tôi đã triển khai cấu trúc `asyncio` để đảm bảo hệ thống không bị nghẽn (bottleneck) khi gọi nhiều API cùng lúc. Việc này tối ưu hóa hiệu suất, cho phép đánh giá hàng loạt test case trong thời gian ngắn nhất.

* Link commit: https://github.com/VinUni-AI20k/Lab14-AI-Evaluation-Benchmarking/commit/d4c7996736732041498ab2dec094178f52c2af9b
---

## 2. Technical Depth

### Giải thích các khái niệm quan trọng
* MRR (Mean Reciprocal Rank): Đo lường xem tài liệu đúng nằm ở vị trí thứ mấy. Tài liệu đúng càng nằm ở trên đầu (hạng 1) thì điểm càng cao (1/1,1/2,1/3...).
* Cohen's Kappa: Chỉ số đo độ đồng thuận giữa 2 giám khảo (ví dụ: GPT và Gemini). Nó giúp loại trừ trường hợp 2 giám khảo "đoán mò" mà vẫn trùng kết quả với nhau.
* Position Bias: Hiện tượng AI bị "thiên vị" vị trí, thường chỉ tập trung vào thông tin ở đầu hoặc cuối đoạn văn mà bỏ qua nội dung ở giữa, hoặc ưu tiên chọn đáp án đứng trước.

* **Trade-off giữa Chất lượng và Chi phí:** Thông qua việc điều phối trong `main.py`, tôi đã tính toán và báo cáo tổng chi phí cho mỗi lần chạy Eval. Tôi nhận ra rằng việc chạy Multi-Judge tuy tốn kém hơn nhưng mang lại độ tin cậy cao hơn gấp nhiều lần so với việc chỉ tin vào một Model đơn lẻ.

---

## 3. Problem Solving 

###  Xử lý xung đột định dạng dữ liệu
**Vấn đề:** Trong quá trình tích hợp tại main.py, tôi phát hiện tệp dữ liệu golden_set.jsonl không đồng nhất: nhiều test case thiếu trường expected_retrieval_ids (danh sách ID tài liệu chuẩn) mà chỉ có trường expected_answer (văn bản đáp án). Điều này khiến logic tính toán các chỉ số Retrieval (Hit Rate, MRR) trong ExpertEvaluator bị lỗi hoặc luôn trả về giá trị 0, gây sai lệch báo cáo hiệu năng của Agent.

**Cách giải quyết:**
1. Tôi kiểm tra lại phần code trong file main.py để tìm được dòng nào phụ trách việc tính toán metric
2. Sửa lại expected_retrieval_ids thành expected_answer.
3. **Kết quả:** Pipeline đánh giá không còn bị gián đoạn. Các chỉ số metrics được tính toán chính xác dựa trên dữ liệu thực tế hiện có, đảm bảo tính khách quan cho cả hai phiên bản Agent V1 và V2.
---

