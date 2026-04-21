"""
Mock rag_answer.py cho Lab 14
Không dùng Chroma, không dùng LLM thật.
Chỉ mô phỏng retrieval + answer generation.
"""

from typing import Dict, List, Any


DOC_CONTEXTS = {
    "access_control_sop": (
        "Access Control SOP: Level 1 áp dụng cho nhân viên mới 30 ngày đầu. "
        "Level 2 cho nhân viên chính thức đã qua thử việc. "
        "Level 3 cần Line Manager + IT Admin + IT Security phê duyệt. "
        "Level 4 cần IT Manager + CISO. "
        "Quyền tạm thời trong sự cố P1 tối đa 24 giờ."
    ),
    "hr_leave_policy": (
        "HR Leave Policy: Nhân viên dưới 3 năm có 12 ngày phép năm. "
        "Nghỉ ốm trên 3 ngày cần giấy tờ y tế. "
        "Nhân viên sau probation có thể remote tối đa 2 ngày mỗi tuần. "
        "Onsite bắt buộc là Thứ 3 và Thứ 5."
    ),
    "it_helpdesk_faq": (
        "IT Helpdesk FAQ: Reset mật khẩu qua portal SSO hoặc liên hệ Helpdesk ext. 9000. "
        "Tài khoản bị khóa sau 5 lần đăng nhập sai. "
        "Công ty sử dụng Cisco AnyConnect cho VPN."
    ),
    "refund_policy_v4": (
        "Refund Policy v4: Điều kiện hoàn tiền gồm sản phẩm lỗi do nhà sản xuất, "
        "gửi yêu cầu trong 7 ngày, hàng chưa sử dụng hoặc chưa mở seal. "
        "Hàng digital và đơn Flash Sale không được hoàn tiền."
    ),
    "sla_p1_2026": (
        "SLA P1 2026: Ticket P1 cần first response trong 15 phút, "
        "resolution trong 4 giờ, cập nhật stakeholder mỗi 30 phút."
    ),
}


def _dense_retrieve(query: str) -> List[str]:
    q = query.lower()

    if any(k in q for k in ["remote", "nghỉ", "ốm", "phép", "thai sản", "onsite"]):
        return ["it_helpdesk_faq", "hr_leave_policy", "access_control_sop"]

    if any(k in q for k in ["mật khẩu", "password", "vpn", "helpdesk", "laptop", "mailbox", "email"]):
        return ["access_control_sop", "it_helpdesk_faq", "hr_leave_policy"]

    if any(k in q for k in ["hoàn tiền", "refund", "flash sale", "store credit", "digital", "seal"]):
        return ["it_helpdesk_faq", "refund_policy_v4", "sla_p1_2026"]

    if any(k in q for k in ["p1", "incident", "sla", "critical", "resolution", "stakeholder"]):
        return ["access_control_sop", "sla_p1_2026", "it_helpdesk_faq"]

    if any(k in q for k in ["access", "quyền", "ciso", "level", "it-access", "jira"]):
        return ["it_helpdesk_faq", "access_control_sop", "sla_p1_2026"]

    return ["access_control_sop", "hr_leave_policy", "it_helpdesk_faq"]


def _hybrid_retrieve(query: str) -> List[str]:
    q = query.lower()

    if any(k in q for k in ["remote", "nghỉ", "ốm", "phép", "thai sản", "onsite"]):
        return ["hr_leave_policy", "it_helpdesk_faq", "access_control_sop"]

    if any(k in q for k in ["mật khẩu", "password", "vpn", "helpdesk", "laptop", "mailbox", "email"]):
        return ["it_helpdesk_faq", "access_control_sop", "hr_leave_policy"]

    if any(k in q for k in ["hoàn tiền", "refund", "flash sale", "store credit", "digital", "seal"]):
        return ["refund_policy_v4", "it_helpdesk_faq", "sla_p1_2026"]

    if any(k in q for k in ["p1", "incident", "sla", "critical", "resolution", "stakeholder"]):
        return ["sla_p1_2026", "access_control_sop", "it_helpdesk_faq"]

    if any(k in q for k in ["access", "quyền", "ciso", "level", "it-access", "jira"]):
        return ["access_control_sop", "it_helpdesk_faq", "sla_p1_2026"]

    return ["access_control_sop", "hr_leave_policy", "it_helpdesk_faq"]


def _generate_answer(query: str, doc_ids: List[str], style: str = "dense") -> str:
    q = query.lower()
    primary = doc_ids[0] if doc_ids else None

    if primary == "hr_leave_policy":
        if "remote" in q:
            return (
                "Nhân viên có thể remote theo chính sách nội bộ."
                if style == "dense"
                else "Nhân viên sau probation có thể remote tối đa 2 ngày mỗi tuần."
            )
        if "ốm" in q:
            return (
                "Nghỉ ốm có thể cần giấy tờ y tế."
                if style == "dense"
                else "Nếu nghỉ ốm trên 3 ngày liên tiếp thì cần giấy tờ y tế từ bệnh viện."
            )
        if "phép" in q:
            return (
                "Số ngày phép năm phụ thuộc vào kinh nghiệm."
                if style == "dense"
                else "Nhân viên dưới 3 năm kinh nghiệm có 12 ngày nghỉ phép năm."
            )

    if primary == "it_helpdesk_faq":
        if "mật khẩu" in q or "password" in q:
            return (
                "Bạn có thể reset mật khẩu qua hệ thống hoặc liên hệ helpdesk."
                if style == "dense"
                else "Bạn có thể reset mật khẩu qua portal SSO hoặc liên hệ Helpdesk qua ext. 9000."
            )
        if "vpn" in q:
            return (
                "Công ty dùng phần mềm VPN nội bộ."
                if style == "dense"
                else "Công ty sử dụng Cisco AnyConnect cho VPN."
            )

    if primary == "refund_policy_v4":
        if "digital" in q:
            return (
                "Một số mặt hàng không được refund."
                if style == "dense"
                else "Không. Hàng kỹ thuật số như license key hoặc subscription không được hoàn tiền."
            )
        if "flash sale" in q:
            return (
                "Đơn khuyến mãi có thể không được refund."
                if style == "dense"
                else "Không. Đơn hàng Flash Sale không được áp dụng hoàn tiền."
            )
        return (
            "Có thể hoàn tiền nếu đáp ứng điều kiện theo chính sách."
            if style == "dense"
            else "Điều kiện hoàn tiền gồm: sản phẩm lỗi do nhà sản xuất, yêu cầu trong 7 ngày và hàng chưa sử dụng hoặc chưa mở seal."
        )

    if primary == "sla_p1_2026":
        if "15 phút" in q or "phản hồi" in q:
            return (
                "P1 cần được phản hồi rất nhanh."
                if style == "dense"
                else "Ticket P1 cần first response trong vòng 15 phút."
            )
        return (
            "P1 có thời gian xử lý ngắn."
            if style == "dense"
            else "Ticket P1 có thời gian resolution là 4 giờ."
        )

    if primary == "access_control_sop":
        if "24 giờ" in q or "tạm thời" in q:
            return (
                "Quyền tạm thời chỉ được cấp trong thời gian ngắn."
                if style == "dense"
                else "Trong sự cố P1, quyền truy cập tạm thời có thể được cấp tối đa 24 giờ."
            )
        if "level 3" in q:
            return (
                "Level 3 cần nhiều bên phê duyệt."
                if style == "dense"
                else "Level 3 cần Line Manager, IT Admin và IT Security phê duyệt."
            )
        return (
            "Nhân viên mới được cấp quyền truy cập cơ bản."
            if style == "dense"
            else "Nhân viên mới trong 30 ngày đầu được cấp Level 1 - Read Only."
        )

    return "Tôi chưa tìm thấy thông tin rõ ràng trong tài liệu hiện có để trả lời chính xác câu hỏi này."


def rag_answer(
    query: str,
    retrieval_mode: str = "dense",
    top_k_search: int = 3,
    top_k_select: int = 2,
    use_rerank: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    if retrieval_mode == "dense":
        retrieved_doc_ids = _dense_retrieve(query)[:top_k_search]
        style = "dense"
    elif retrieval_mode == "hybrid":
        retrieved_doc_ids = _hybrid_retrieve(query)[:top_k_search]
        style = "hybrid"
    else:
        retrieved_doc_ids = _dense_retrieve(query)[:top_k_search]
        style = "dense"

    selected_doc_ids = retrieved_doc_ids[:top_k_select]

    chunks_used = []
    for doc_id in selected_doc_ids:
        chunks_used.append(
            {
                "text": DOC_CONTEXTS.get(doc_id, ""),
                "metadata": {
                    "source": doc_id,
                    "section": "mock_section",
                },
                "score": 1.0,
            }
        )

    answer = _generate_answer(query, selected_doc_ids, style=style)
    sources = selected_doc_ids

    if verbose:
        print("=" * 60)
        print(f"Query: {query}")
        print(f"Mode: {retrieval_mode}")
        print("Retrieved:", retrieved_doc_ids)
        print("Selected:", selected_doc_ids)
        print("Answer:", answer)

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "chunks_used": chunks_used,
        "config": {
            "retrieval_mode": retrieval_mode,
            "top_k_search": top_k_search,
            "top_k_select": top_k_select,
            "use_rerank": use_rerank,
        },
    }


if __name__ == "__main__":
    q = "Ai phải phê duyệt để cấp quyền Level 3?"
    print("\n--- Dense ---")
    print(rag_answer(q, retrieval_mode="dense", verbose=True))
    print("\n--- Hybrid ---")
    print(rag_answer(q, retrieval_mode="hybrid", verbose=True))