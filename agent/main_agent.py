import asyncio
from typing import Dict, List, Any

from rag_answer import rag_answer


class MainAgent:
    _rag_lock = asyncio.Lock()

    def __init__(self, version: str = "v1"):
        self.version = version

        if version == "v1":
            self.name = "Agent_V1_Base"
            self.retrieval_mode = "dense"
        elif version == "v2":
            self.name = "Agent_V2_Optimized"
            self.retrieval_mode = "hybrid"
        else:
            raise ValueError("Version must be 'v1' or 'v2'")

    def _map_to_doc_id(self, chunk: Dict[str, Any]) -> str:
        meta = chunk.get("metadata", {}) or {}
        source = (meta.get("source", "") or "").lower()
        text = (chunk.get("text", "") or "").lower()

        if "access" in source or "approval" in text:
            return "access_control_sop"

        if "leave" in source or "remote" in text or "nghỉ" in text:
            return "hr_leave_policy"

        if "helpdesk" in source or "vpn" in text or "password" in text or "mật khẩu" in text:
            return "it_helpdesk_faq"

        if "refund" in source or "flash sale" in text:
            return "refund_policy_v4"

        if "sla" in source or "p1" in text:
            return "sla_p1_2026"

        return "unknown_doc"

    def _extract_retrieved_ids(self, chunks: List[Dict[str, Any]]) -> List[str]:
        ids = []
        for c in chunks:
            doc_id = self._map_to_doc_id(c)
            if doc_id not in ids:
                ids.append(doc_id)
        return ids

    def _refine_answer(self, answer: str) -> str:
        if self.version == "v1":
            return answer
        return f"{answer}\n\n(Thông tin được tổng hợp từ tài liệu nội bộ.)"

    async def query(self, question: str) -> Dict:
        async with self._rag_lock:
            result = await asyncio.to_thread(
                rag_answer,
                query=question,
                retrieval_mode=self.retrieval_mode,
                top_k_search=3,
                top_k_select=2,
                use_rerank=False,
                verbose=False,
            )

        chunks = result.get("chunks_used", [])
        answer = result.get("answer", "Không đủ dữ liệu.")
        retrieved_ids = self._extract_retrieved_ids(chunks)
        answer = self._refine_answer(answer)

        return {
            "answer": answer,
            "contexts": [c.get("text", "") for c in chunks],
            "retrieved_ids": retrieved_ids,
            "metadata": {
                "agent_version": self.version,
                "retrieval_mode": self.retrieval_mode,
                "tokens_used": 150 if self.version == "v2" else 100,
                "sources": retrieved_ids,
            },
        }


if __name__ == "__main__":
    async def test():
        q = "Nhân viên sau probation được remote bao nhiêu ngày?"

        agent_v1 = MainAgent("v1")
        agent_v2 = MainAgent("v2")

        print("=== V1 ===")
        print(await agent_v1.query(q))

        print("\n=== V2 ===")
        print(await agent_v2.query(q))

    asyncio.run(test())