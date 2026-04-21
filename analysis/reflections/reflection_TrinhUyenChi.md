# INDIVIDUAL REPORT - LAB 13: AI EVALUATION BENCHMARKING

Họ và tên: Trịnh Uyên Chi

Mã học viên: 2A202600435  

Ngày: 21/04/2026

### **Engineering Contribution (15/15)**
* **Module Phức tạp:** Chịu trách nhiệm thiết kế và triển khai lõi xử lý của **Multi-Model Judge Engine**. Thay vì chỉ lấy điểm trung bình thô, tôi đã xây dựng hệ thống **Consensus Logic** tự động để tổng hợp kết quả từ nhiều giám khảo (GPT-4o, Gemini 1.5 Pro).
* **Đóng góp kỹ thuật:** * Xây dựng hàm `_calculate_agreement_rate` sử dụng công thức hiệu chuẩn (Calibration) toán học để đo lường độ tin cậy của kết quả.
    * Triển khai logic **Conflict Resolution**: Tự động phát hiện và gắn cờ (flagging) các trường hợp giám khảo "cãi nhau" vượt ngưỡng `conflict_threshold`, giúp hệ thống Gatekeeper ngăn chặn việc phát hành các phiên bản AI kém chất lượng.
    * Tối ưu hóa hiệu năng bằng cách phối hợp với đồng đội triển khai `asyncio.gather`, giúp gọi đồng thời nhiều Judge, đáp ứng tiêu chuẩn chạy 50 cases dưới 2 phút.

### **Technical Depth (15/15)**
* **Hệ số đồng thuận & Cohen's Kappa:** Trong bài làm, tôi đã sử dụng công thức tính khoảng cách điểm số để đo lường sự đồng thuận. Khái niệm này tương đồng với **Cohen's Kappa** — một chỉ số thống kê dùng để đo lường mức độ đồng ý giữa hai người đánh giá (raters) về các mục phân loại, giúp loại bỏ yếu tố "trùng hợp ngẫu nhiên" trong đánh giá.
* **Position Bias:** Hiểu rõ hiện tượng LLM thường có xu hướng thiên vị các đáp án đứng ở vị trí đầu tiên trong prompt. Để xử lý việc này, tôi đã thiết kế kiến trúc sẵn sàng cho việc đổi chỗ câu trả lời (Swap positions) để kiểm tra tính nhất quán của Judge.
* **Trade-off (Chi phí & Chất lượng):** Việc sử dụng 2 Judge (GPT + Gemini) giúp tăng độ khách quan và giảm sai số cá nhân của model, nhưng làm tăng gấp đôi chi phí API và thời gian xử lý. Tôi đã tối ưu bằng cách đề xuất logic: chỉ khi có xung đột mới cần gọi thêm Judge thứ 3 hoặc sự can thiệp của con người, giúp cân bằng giữa ngân sách và chất lượng đánh giá.

### **Problem Solving (10/10)**
* **Vấn đề:** Khi tích hợp code giữa hai người làm chung Mission 2, dễ xảy ra tình trạng chồng chéo logic hoặc xung đột khi push code (Merge Conflict).
* **Giải quyết:** Tôi đã đề xuất cấu trúc Class với các **Private Methods** (`_calculate_agreement_rate`, `_resolve_consensus`) tách biệt hoàn toàn phần "Tính toán toán học" khỏi phần "Gọi API". Điều này cho phép tôi và đồng đội làm việc song song trên cùng một file mà không ảnh hưởng đến logic của nhau, đồng thời giúp việc Unit Test dữ liệu thô trở nên cực kỳ nhanh chóng mà không cần tốn tiền gọi API thật.
* **Xử lý lỗi (Robustness):** Thiết kế logic xử lý trường hợp một trong hai Judge bị sập (Fallback/Error) bằng cách tự động tin tưởng model còn lại nếu điểm số vẫn trong ngưỡng an toàn, đảm bảo pipeline không bị dừng đột ngột khi chạy benchmark số lượng lớn.

---