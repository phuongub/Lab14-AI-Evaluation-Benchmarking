# INDIVIDUAL REPORT - LAB 14: AI EVALUATION BENCHMARKING

**Họ và tên:** Phạm Nguyễn Tiến Mạnh  
**Mã học viên:** 2A202600418  
**Ngày:** 21/04/2026

---

## Engineering Contribution (15/15)

**Module Phức tạp:** Chịu trách nhiệm thiết kế và triển khai toàn bộ file llm_judge, bao gồm pipeline gọi API, hệ thống prompt engineering, xử lý JSON và cơ chế fallback tự động.

**Đóng góp kỹ thuật:**

- Triển khai `evaluate_multi_judge`: Orchestrate toàn bộ luồng đánh giá, gọi song song cả hai Judge (OpenAI và Google) thông qua `asyncio.gather`.
- Thiết kế `_system_prompt` và `_user_prompt`: Xây dựng rubric đánh giá 5 tiêu chí (accuracy, faithfulness, safety, helpfulness, professionalism) và định dạng JSON schema bắt buộc trả về, đảm bảo các Judge chấm điểm có cấu trúc và có thể so sánh được.
- Triển khai `_parse_judge_json` và `_extract_json_object`: Xử lý nhiều trường hợp đầu ra thực tế của LLM (JSON thuần, JSON bọc trong markdown fence, JSON lồng trong văn bản) bằng cách kết hợp regex và parser thủ công duyệt từng ký tự để trích xuất object hợp lệ.
- Xây dựng hệ thống **Fallback & Robustness**: Thiết kế `_fallback_judge` với `_heuristic_score` tính điểm dựa trên token overlap giữa câu trả lời và ground truth khi API thực tế không khả dụng, cùng `_clamp_score` để ép điểm về đúng thang 1–5 trong mọi tình huống.

---

## Technical Depth (15/15)

**Rubric Engineering & Prompt Design:** Thiết kế rubric 5 tiêu chí với trọng số ưu tiên rõ ràng (accuracy và faithfulness được nhấn mạnh hơn), ép buộc model trả về JSON schema cố định — đây là yếu tố then chốt để kết quả từ hai Judge có thể so sánh và tổng hợp được.

**Position Bias:** Hiểu rõ hiện tượng LLM thường có xu hướng thiên vị các đáp án đứng ở vị trí đầu tiên trong prompt. Để xử lý việc này, tôi đã thiết kế skeleton `check_position_bias` sẵn sàng cho việc đổi chỗ câu trả lời (Swap positions) để kiểm tra tính nhất quán của Judge trong các phiên bản tiếp theo.

**Trade-off (Chi phí & Chất lượng):** Việc sử dụng 2 Judge (GPT + Gemini) giúp tăng độ khách quan và giảm sai số cá nhân của model, nhưng làm tăng gấp đôi chi phí API và thời gian xử lý. Tôi đã tối ưu bằng cách đề xuất logic: chỉ khi có xung đột mới cần gọi thêm Judge thứ 3 hoặc sự can thiệp của con người, giúp cân bằng giữa ngân sách và chất lượng đánh giá.

---

## Problem Solving (10/10)

**Vấn đề:** Output thực tế của LLM không bao giờ đảm bảo trả về JSON thuần — model có thể bọc kết quả trong markdown fence (` ```json `), lồng JSON vào văn bản giải thích, hoặc trả về JSON bị lỗi cú pháp. Đây là điểm dễ làm sập toàn bộ pipeline khi chạy benchmark số lượng lớn.

**Giải quyết:** Thiết kế `_parse_judge_json` theo kiến trúc phòng thủ nhiều lớp: thử parse trực tiếp trước, nếu thất bại mới gọi `_extract_json_object` để dùng regex tìm fenced block, và cuối cùng duyệt từng ký tự để tìm object JSON hợp lệ đầu tiên trong chuỗi. Mọi trường hợp lỗi đều fallback về `_parse_error` với điểm mặc định thay vì crash.

**Xử lý lỗi (Robustness):** Trong `evaluate_multi_judge`, thiết kế thêm logic phát hiện khi một trong hai Judge bị sập hoàn toàn (flag `fallback=True` hoặc `error=True`): nếu chỉ còn một model hoạt động tốt, pipeline tự động lấy điểm của model đó thay vì dừng lại — đảm bảo benchmark không bị gián đoạn giữa chừng khi chạy hàng loạt cases.
