# INDIVIDUAL REPORT - LAB 14: AI EVALUATION BENCHMARKING

**Họ và tên:** Trần Việt Phương
**Mã học viên:** 2A202600433
**Ngày:** 21/04/2026

---

# Engineering Contribution

- Thiết kế Auto-Gate tự động quyết định `RELEASE`, `ROLLBACK`, hoặc `MANUAL_REVIEW`.
- Logic đánh giá đồng thời 3 nhóm metric:
  - Quality
  - Cost
  - Performance
- Viết hard-rule:
  - Rollback nếu quality giảm quá ngưỡng cho phép.
  - Rollback nếu cost hoặc latency tăng vượt ngưỡng.
  - Release chỉ khi candidate tốt hơn hoặc tương đương baseline trên toàn bộ nhóm metric.
- Đóng góp chính:
commit link: https://github.com/phuongub/Lab14-AI-Evaluation-Benchmarking/tree/27284e4a521deb6e2bfe948454d337ed5f64ecbb

# Technical Depth

- Quality metric được ưu tiên cao nhất, vì release model chất lượng thấp gây ảnh hưởng trực tiếp tới người dùng.
- Cost và Performance là ràng buộc phụ để tránh trường hợp model tốt hơn rất ít nhưng chi phí hoặc latency tăng quá nhiều.
- Sử dụng weighted score hoặc rule-based threshold:
  - Quality weight
  - Cost weight
  - Performance weight
- Trade-off:
  - Chấp nhận tăng nhẹ chi phí nếu chất lượng tăng đáng kể.
  - Không release nếu gain về quality nhỏ nhưng latency/cost tăng lớn.
- Các khái niệm có thể giải thích:
  - MRR: đo vị trí trung bình của kết quả đúng đầu tiên.
  - Cohen’s Kappa: đo mức độ đồng thuận vượt quá ngẫu nhiên.
  - Position Bias: người đánh giá thường thiên về đáp án xuất hiện trước.

# Problem Solving

- Vấn đề: metric giữa các model thường mâu thuẫn (ví dụ quality tăng nhưng cost cũng tăng mạnh).
- Cách xử lý:
  - Đặt hard-threshold trước.
  - Nếu không vi phạm hard-threshold thì dùng weighted score để quyết định.
  - Nếu điểm quá sát nhau thì trả về `MANUAL_REVIEW`.