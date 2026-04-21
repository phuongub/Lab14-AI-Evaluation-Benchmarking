# 🛡️ AI Agent Release Strategy (DevOps/Analyst)

Tài liệu này ghi lại chiến lược kiểm soát chất lượng (Quality Gate) cho hệ thống AI Eval Factory, giúp đảm bảo tính ổn định của Agent trước khi phát hành.

---

## 🏗️ Phân loại chỉ số

Hệ thống sử dụng cơ chế **3 Judge** để đánh giá tính khách quan. Dù có 3 Judge giúp giảm thiểu rủi ro sai lệch điểm số, chúng ta vẫn cần các bộ quy tắc sau:

### 🔴 Hard Gates (Bất di bất dịch - PHẢI CHẶN)
Nếu vi phạm các chỉ số này, hệ thống sẽ tự động dừng quá trình Release (`BLOCK`).

| Chỉ số | Ngưỡng (Threshold) | Lý do |
| :--- | :--- | :--- |
| **AI Score Delta** | Không giảm quá **-5%** | Bảo vệ chất lượng cốt lõi của câu trả lời. |
| **Retrieval Hit Rate** | Tối thiểu **0.75** | Đảm bảo Agent không bị ảo giác do thiếu dữ liệu. |
| **Agreement Rate** | Tối thiểu **0.7** | Đảm bảo các Judge có sự đồng thuận cao (kể cả khi đã có 3 Judge). |

### 🟡 Soft Warnings (Cảnh báo nhẹ - CẦN GIÁM SÁT)
Vẫn cho phép Release (`PASS`) nhưng đính kèm cảnh báo cho team DevOps/Analyst.

| Chỉ số | Ngưỡng (Threshold) | Lưu ý |
| :--- | :--- | :--- |
| **Avg Latency** | Tăng không quá **20%** | Nếu chậm hơn nhưng chất lượng tốt hơn nhiều, có thể chấp nhận. |
| **Cost per Eval** | Tăng không quá **15%** | Theo dõi để cân đối ngân sách vận hành hàng tháng. |

---

## 📈 Quy trình Operational Monitoring
1. **Benchmark**: Chạy toàn bộ Golden Dataset trên Agent mới.
2. **Delta Analysis**: So sánh với phiên bản Stable gần nhất.
3. **Auto-Gate Decision**: `ReleaseGate` đưa ra phán quyết dựa trên các quy tắc trên.
4. **Audit**: Lưu lại `reports/summary.json` để thực hiện Failure Analysis khi cần thiết.
