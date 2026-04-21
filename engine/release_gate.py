from typing import Dict, Tuple

class ReleaseGate:
    def __init__(self, thresholds: Dict = None):
        """
        Khởi tạo ReleaseGate với các ngưỡng (thresholds) mặc định.
        """
        self.thresholds = thresholds or {
            "score_delta_limit": -0.05,    # Giảm tối đa 5%
            "min_hit_rate": 0.75,          # Hit rate tối thiểu
            "min_agreement": 0.7,          # Agreement rate tối thiểu
            "latency_warn_limit": 0.2,     # Cảnh báo nếu latency tăng > 20%
            "cost_warn_limit": 0.15        # Cảnh báo nếu cost tăng > 15%
        }

    def evaluate(self, v1_summary: Dict, v2_summary: Dict) -> Dict:
        """
        Đánh giá bản cập nhật dựa trên so sánh metrics giữa V1 và V2.
        """
        v1_metrics = v1_summary.get("metrics", {})
        v2_metrics = v2_summary.get("metrics", {})

        # 1. Tính toán Deltas
        score_v1 = v1_metrics.get("avg_score", 0)
        score_v2 = v2_metrics.get("avg_score", 0)
        score_delta = (score_v2 - score_v1) / score_v1 if score_v1 > 0 else 0

        # Giả lập lancy/cost nếu chưa có trong metrics
        latency_v1 = v1_metrics.get("avg_latency", 0.5)
        latency_v2 = v2_metrics.get("avg_latency", 0.6)
        latency_delta = (latency_v2 - latency_v1) / latency_v1 if latency_v1 > 0 else 0

        # 2. Kiểm tra Hard Gates (Phải chặn)
        checks = []
        is_blocked = False
        reasons = []

        # Kiểm tra Score
        if score_delta < self.thresholds["score_delta_limit"]:
            is_blocked = True
            reasons.append(f"AI Score giảm quá sâu ({score_delta*100:.1f}%)")
        
        # Kiểm tra Hit Rate
        hit_rate = v2_metrics.get("hit_rate", 0)
        if hit_rate < self.thresholds["min_hit_rate"]:
            is_blocked = True
            reasons.append(f"Hit Rate quá thấp ({hit_rate:.2f} < {self.thresholds['min_hit_rate']})")

        # Kiểm tra Agreement Rate
        agreement = v2_metrics.get("agreement_rate", 0)
        if agreement < self.thresholds["min_agreement"]:
            is_blocked = True
            reasons.append(f"Agreement Rate không tin cậy ({agreement:.2f} < {self.thresholds['min_agreement']})")

        # 3. Kiểm tra Soft Warnings (Cảnh báo)
        warnings = []
        if latency_delta > self.thresholds["latency_warn_limit"]:
            warnings.append(f"Performance: Latency tăng {latency_delta*100:.1f}%")

        # Giả lập kiểm tra Cost
        # cost_delta = (v2_metrics.get("total_cost", 0) - v1_metrics.get("total_cost", 0)) ...

        return {
            "decision": "BLOCK" if is_blocked else "APPROVE",
            "is_blocked": is_blocked,
            "reasons": reasons,
            "warnings": warnings,
            "metrics_compared": {
                "score_delta": score_delta,
                "latency_delta": latency_delta
            }
        }
