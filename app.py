"""
VeriSync Streamlit Application.
Web interface to verify forwarded VTU notices.
"""
import streamlit as st
from core.pipeline import verify_notice

st.set_page_config(
    page_title="VeriSync - VTU Notice Verifier",
    page_icon="🔍",
    layout="centered",
)

st.title("VeriSync: Is this VTU notice real?")
st.write(
    "Paste forwarded VTU circular text or WhatsApp message below to verify its authenticity against official circulars."
)

# Text area input
default_sample = (
    "VTU Notification: 3rd sem examinations scheduled from 5th Dec are postponed to 12th Dec 2026."
)
message = st.text_area(
    "Forwarded Notice Text:",
    value=default_sample,
    height=150,
    help="Paste the full text of the forwarded notice or circular excerpt.",
)

if st.button("Verify Notice", type="primary"):
    if not message.strip():
        st.warning("Please paste or type a notice text first.")
    else:
        with st.spinner("Analyzing notice and checking evidence..."):
            result = verify_notice(message)

        verdict = result["verdict"]

        # Green/red/yellow status box
        if verdict == "Verified":
            st.success("### Verdict: VERIFIED\nOfficial circular supports this notice.")
        elif verdict == "Contradicted":
            st.error("### Verdict: CONTRADICTED\nOfficial circular contradicts the claim in this notice.")
        else:
            st.warning("### Verdict: UNVERIFIED\nNo official circular found to confirm this claim, or suspicious elements detected.")

        # Forgery Flags
        flags = result.get("flags", [])
        if flags:
            st.subheader("🚩 Detected Flags")
            for flag in flags:
                severity = flag.get("severity", "soft").upper()
                rule = flag.get("rule", "Unknown")
                detail = flag.get("detail", "")
                st.caption(f"**[{severity}] {rule}**: {detail}")

        # Extracted Claim JSON
        st.subheader("📋 Extracted Claim")
        st.json(result.get("claim", {}))

        # Evidence Details
        st.subheader("📑 Evidence")
        evidence = result.get("evidence", {})
        col1, col2, col3 = st.columns(3)
        col1.metric("Circular No", evidence.get("circular_no") or "None")
        col2.metric("Source File", evidence.get("file") or "None")
        col3.metric("Page", str(evidence.get("page") if evidence.get("page") is not None else "None"))

        clause = evidence.get("clause")
        if clause:
            st.markdown(f"**Official Clause Cited:**\n> {clause}")
        else:
            st.write("No matching official clause cited.")
