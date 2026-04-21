# INDIVIDUAL REPORT - LAB 14: AI EVALUATION BENCHMARKING

**Họ và tên:** Trịnh Uyên Chi

**Mã học viên:** 2A202600435  

**Ngày:** 21/04/2026

### **1. Engineering Contribution**
* Trực tiếp thiết kế và triển khai lõi xử lý của Multi-Model Judge Engine. Tôi đã xây dựng hệ thống Consensus Logic tự động để hợp nhất kết quả từ các giám khảo AI khác nhau.
* **Đóng góp kỹ thuật:** 
    * Xây dựng hàm `_calculate_agreement_rate` sử dụng công thức hiệu chuẩn (Calibration) toán học để đo lường độ tin cậy của hệ thống đánh giá.
    * Triển khai logic Conflict Resolution: Tự động phát hiện xung đột điểm số vượt ngưỡng, đồng thời thiết kế cơ chế Fallback Mock Judge để đảm bảo pipeline không bị gián đoạn khi API gặp lỗi.
    * Phân tích và xử lý dữ liệu từ 60 test cases, thực hiện Failure Clustering để phân loại các lỗi hệ thống vào các nhóm: Retrieval Failure, Response Irrelevancy và Rate Limit.

### **2. Technical Depth**
* **Hiểu biết về Calibration & RAG Metrics:** Áp dụng kiến thức về đo lường sự đồng thuận (tương tự Cohen's Kappa) để tính toán độ tin cậy của Judge. Đồng thời, tôi đã chỉ ra được nguyên nhân cốt lõi khiến Hit Rate bằng 0.0 là do sự mất đồng bộ ID giữa script SDG và Ingestion Pipeline, chứ không đơn thuần là lỗi từ model.
* **Tối ưu hiệu năng vs. Chi phí:** Phối hợp triển khai `asyncio.gather` để đạt tốc độ benchmark dưới 2 phút. Tuy nhiên, qua quá trình thực hiện, tôi đã nhận diện được sự đánh đổi (Trade-off) giữa tốc độ và giới hạn API (RPM/TPM), từ đó đề xuất giải pháp dùng Semaphore để kiểm soát luồng tránh lỗi 429.

### **3. Problem Solving**
* **Vấn đề:** Trong quá trình tích hợp, hệ thống xuất hiện "điểm ảo" (điểm 5 cho câu trả lời sai) và lỗi xung đột khi push code giữa các thành viên làm chung Mission 2.
* **Giải quyết:** 
    * Về kỹ thuật: Tôi đề xuất cấu trúc Class với các **Private Methods** để tách biệt logic tính toán toán học khỏi logic gọi API, giúp team làm việc song song mà không bị Merge Conflict.
    * Về dữ liệu: Thực hiện phân tích **5 Whys** sâu sát trên file `benchmark_results.json` để truy vết từ triệu chứng "điểm ảo" đến nguyên nhân gốc rễ là hệ thống Judge bị sập và phải dùng Heuristic fallback.