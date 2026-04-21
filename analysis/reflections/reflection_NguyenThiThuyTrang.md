# Individual Reports
**Họ Tên**: Nguyễn Thị Thùy Trang

**Mã học viên**: 2A202600214

**Nhóm**: C401-B4

---
## Engineering Contribution
- Xây dựng module Retrieval Evaluation, cụ thể là hàm `evaluate_batch`:
- Thiết kế SDG - Synthetic Data Generation (sinh dữ liệu tổng hợp) với 60 test cases
- Xây dựng Main Agent và debug để chạy benchmark
---
## Technical 
### Retrieval Evaluation Module
- Triển khai hàm `evaluate_batch` để đo chất lượng truy xuất: 
    - Hit Rate (Tỷ lệ trúng): Kiểm tra xem hệ thống có tìm được ít nhất 1 tài liệu đúng trong top-k hay không
    - MRR (Mean Reciprocal Rank — Xếp hạng nghịch đảo trung bình): Đo độ tốt của thứ tự xếp hạng, tài liệu đứng đầu -> MRR càng cao

### Synthetic Data Generation (SDG)
- Tạo 60 test cases để đánh giá hệ thống, bao phủ theo các gợi ý trong file `strategy_suggestions.md`
- Mỗi test case có cấu trúc: 
```
{
    "question": ""
    "expected_answer": "",
    "context": "",
    "metadata": {
        "difficulty": "",
        "type": "",
        "expected_retrieval_ids": [""]
    }
}
```

### Main Agent Pipeline 
- Pipeline được thiết kế như sau:
```
Question (Câu hỏi)
    ↓
Retrieval (Truy xuất tài liệu — mock dense/hybrid)
    ↓
Context Selection (Chọn ngữ cảnh)
    ↓
Answer Generation (Sinh câu trả lời)
    ↓
Output:
  - answer (câu trả lời)
  - contexts (ngữ cảnh)
  - retrieved_ids (ID tài liệu)
```
- Chia thành 2 phiên bản:

| Version       | Ý nghĩa      | Đặc điểm                |
| ------------- | ------------ | ----------------------- |
| V1 (Baseline) | Bản gốc      | Retrieval chưa tối ưu   |
| V2 (Improved) | Bản cải tiến | Retrieval chính xác hơn |

=> Nhằm so sánh hiệu năng giữa 2 version

---
## Problem Solving
**1. Hệ thống chạy chậm**:
- Nguyên nhân: do sử dụng:
    - ChromaDBs
    - LLM API 
- Giải pháp: 
    - Giảm top_k_search
    - Giảm top_k_select

**2. Thiếu dữ liệu cho retrieval**
- Nguyên nhân: Dataset ban đầu (ver 1) thiếu expected_retrieval_ids
- Giải pháp: Thêm trường này trong SDG


---