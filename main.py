import asyncio
import json
import os
import time
from engine.runner import BenchmarkRunner
from agent.main_agent import MainAgent
from engine.release_gate import ReleaseGate
from dotenv import load_dotenv
import json
import re
from openai import AsyncOpenAI
import google.generativeai as genai
from engine.retrieval_eval import RetrievalEvaluator
from engine.llm_judge import LLMJudge

load_dotenv()



class ExpertEvaluator:
    def __init__(self):
        self.retrieval_evaluator = RetrievalEvaluator()

    async def score(self, case, resp):
        """
        Đánh giá Retrieval (Hit Rate, MRR) 
        Phần Faithfulness/Relevancy sẽ do LLMJudge xử lý ở bước sau hoặc gộp tại đây.
        """
        expected_ids = case.get('expected_retrieval_ids', [])
        retrieved_ids = resp.get('retrieved_ids', [])

        hit_rate = self.retrieval_evaluator.calculate_hit_rate(expected_ids, retrieved_ids)
        mrr = self.retrieval_evaluator.calculate_mrr(expected_ids, retrieved_ids)

        return {
            "retrieval": {
                "hit_rate": hit_rate,
                "mrr": mrr
            }
        }

async def run_benchmark_with_results(agent_instance, agent_version: str, judge_engine: LLMJudge):
    print(f"\n🚀 Khởi động Benchmark cho {agent_version}...")

    if not os.path.exists("data/golden_set.jsonl"):
        print(f"❌ Thiếu data/golden_set.jsonl")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    runner = BenchmarkRunner(agent_instance, ExpertEvaluator(), judge_engine)
    results = await runner.run_all(dataset)

    total = len(results)

    # Tính trung bình các chỉ số chi tiết từ các Judge
    avg_faithfulness = sum(
        (r["judge"]["individual_scores"]["gpt-4o"]["criteria"]["faithfulness"] + 
         r["judge"]["individual_scores"]["gemini-2.5-pro"]["criteria"]["faithfulness"]) / 2
        for r in results
    ) / total

    summary = {
        "metadata": {
            "version": agent_version, 
            "total": total, 
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "metrics": {
            "avg_score": sum(r["judge"]["final_score"] for r in results) / total,
            "hit_rate": sum(r["ragas"]["retrieval"]["hit_rate"] for r in results) / total,
            "faithfulness": avg_faithfulness,
            "agreement_rate": sum(r["judge"]["agreement_rate"] for r in results) / total,
            "conflicts": sum(1 for r in results if r["judge"].get("conflict", False))
        }
    }
    return results, summary

async def main():
    # 1. Khởi tạo Judge Engine từ file của bạn
    judge_engine = LLMJudge()

    # 2. Khởi tạo các phiên bản Agent
    agent_v1 = MainAgent(version="v1") 
    agent_v2 = MainAgent(version="v2")

    # 3. Chạy đánh giá
    v1_results, v1_summary = await run_benchmark_with_results(agent_v1, "Agent_V1_Base", judge_engine)
    v2_results, v2_summary = await run_benchmark_with_results(agent_v2, "Agent_V2_Optimized", judge_engine)
    
    if not v1_summary or not v2_summary:
        return

    # 4. Phân tích Delta (Regression Gate)
    print("\n📊 --- KẾT QUẢ SO SÁNH (REGRESSION) ---")
    score_v1 = v1_summary["metrics"]["avg_score"]
    score_v2 = v2_summary["metrics"]["avg_score"]
    delta = score_v2 - score_v1
    
    print(f"V1 Score: {score_v1:.2f} | V2 Score: {score_v2:.2f}")
    print(f"Delta Score: {'+' if delta >= 0 else ''}{delta:.2f}")
    print(f"Agreement Rate: {v2_summary['metrics']['agreement_rate']:.2f}")

    # Ghi báo cáo
    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    # 5. Quyết định Release Gate
    THRESHOLD = 0.2
    if delta >= THRESHOLD:
        print("✅ QUYẾT ĐỊNH: CHẤP NHẬN BẢN CẬP NHẬT (APPROVE)")
    else:
        print("❌ QUYẾT ĐỊNH: TỪ CHỐI (BLOCK RELEASE) - Cải thiện không đáng kể.")

if __name__ == "__main__":
    asyncio.run(main())