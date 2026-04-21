import asyncio
from typing import Dict, Any, List

class LLMJudge:
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        # TODO: Định nghĩa rubrics chi tiết cho các tiêu chí: Accuracy, Professionalism, Safety
        self.rubrics = {
            "accuracy": "Chấm điểm từ 1-5 dựa trên độ chính xác so với Ground Truth...",
            "tone": "Chấm điểm từ 1-5 dựa trên sự chuyên nghiệp của ngôn ngữ..."
        }

    def _calculate_agreement_rate(self, scores: List[float]) -> float:
        """
        [Expert Task] Tính toán hệ số đồng thuận giữa các giám khảo.
        Công thức: 1 - (Chênh lệch tuyệt đối / Khoảng điểm tối đa)
        """
        if len(scores) < 2:
            return 1.0
        
        # Thang điểm 1-5 có biên độ là 4
        score_range = self.max_score - 1
        max_diff = max(scores) - min(scores)
        
        agreement = 1.0 - (max_diff / score_range)
        return round(max(0.0, agreement), 2)

    def _resolve_consensus(self, individual_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        [Expert Task] Xử lý xung đột và tổng hợp kết quả cuối cùng.
        """
        scores = list(individual_scores.values())
        avg_score = sum(scores) / len(scores)
        agreement_rate = self._calculate_agreement_rate(scores)
        
        max_diff = max(scores) - min(scores)
        has_conflict = max_diff > self.conflict_threshold
        
        return {
            "final_score": round(avg_score, 2),
            "agreement_rate": agreement_rate,
            "has_conflict": has_conflict,
            "individual_scores": individual_scores,
            "status": "Consensus Reached" if not has_conflict else "Conflict: Needs Review"
        }

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """
        EXPERT TASK: Gọi ít nhất 2 model (ví dụ GPT-4o và Claude).
        Tính toán sự sai lệch. Nếu lệch > 1 điểm, cần logic xử lý.
        """
        # Giả lập gọi 2 model
        score_a = 4
        score_b = 3
        
        avg_score = (score_a + score_b) / 2
        agreement = 1.0 if score_a == score_b else 0.5
        
        return {
            "final_score": avg_score,
            "agreement_rate": agreement,
            "individual_scores": {"gpt-4o": score_a, "claude-3-5": score_b}
        }

    async def check_position_bias(self, response_a: str, response_b: str):
        """
        Nâng cao: Thực hiện đổi chỗ response A và B để xem Judge có thiên vị vị trí không.
        """
        pass
