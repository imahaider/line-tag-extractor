import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
from io import BytesIO

# ---------- Configurable password for regex editor
REGEX_PASSWORD = st.secrets.get("REGEX_PASSWORD", "haider2410")

# ---------- Page setup
st.set_page_config(page_title="P&IDs Line-Tags Extractor", page_icon="📄", layout="wide")

# ---------- Styling (buttons + title fix)
st.markdown("""
<style>
.block-container {padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1200px;}
.app-title{
  font-weight: 800; font-size: 2.7rem; line-height: 1.2;
  background: linear-gradient(90deg,#0ea5e9,#22c55e,#a855f7);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  margin: 0 0 .45rem 0; word-break: break-word; overflow-wrap: anywhere;
}
.footer{color:rgba(49,51,63,.55); font-size:.85rem; text-align:center; margin-top:2rem;}

/* Extract Tags button (orange, unchanged) */
div[data-testid="stButton"] > button[kind="primary"] {
    background-color: #FD602E !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    border: none !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    font-size: 1rem !important;
    width: 100% !important;
}

/* Download buttons (green #6EB819) */
div[data-testid="stDownloadButton"] > button {
    background-color: #6EB819 !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    border: none !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    font-size: 1rem !important;
    width: 100% !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    filter: brightness(0.95);
}
</style>
""", unsafe_allow_html=True)

# ---------- Header
st.markdown('<div class="app-title">P&IDs Line-Tags Extractor</div>', unsafe_allow_html=True)
st.caption("Developed by Muhammad Ali Haider")

# ---------- Sidebar
with st.sidebar:
    st.header("About")
    st.write("Upload one or more PDFs. The app extracts line-tags with preview and export.")
    st.markdown("---")
    st.subheader("Export")
    export_fmt = st.segmented_control("File Format", ["XLSX", "CSV", "TXT"], default="XLSX")
    st.markdown("---")
    st.subheader("Settings")
    case_sensitive = st.toggle("Case Sensitive", value=False)
    sort_output = st.toggle("Sort Results Alphabetically", value=True)
    show_duplicates = st.toggle("Keep Duplicates", value=False)

    # Starts-with filter (existing)
    prefix_filter = st.text_input(
        "Line-Tag starts with (optional)",
        placeholder="e.g., 1/2, 3\", or 1-1/2"
    )

    # NEW contains filter (optional)
    contains_filter = st.text_input(
        "Find tags containing (optional)",
        placeholder="e.g., LC-456 or 1370X or -V"
    )

    # ---------- Regex Pattern (password protected at the very end)
    st.markdown("---")
    st.subheader("Line-Tag General Pattern")

    if "regex_unlocked" not in st.session_state:
        st.session_state.regex_unlocked = False

    if not st.session_state.regex_unlocked:
        pw = st.text_input("Enter password to set-up", type="password", key="regex_pw")
        unlock = st.button("Unlock Editor", key="unlock_btn", use_container_width=True)
        if unlock:
            if pw == REGEX_PASSWORD:
                st.session_state.regex_unlocked = True
                st.success("Regex editor unlocked")
            else:
                st.error("Incorrect password")
        default_pattern = r'(?:\d+(?:\s*-\s*\d+/\d+)?)\s*"\s*-[A-Za-z0-9]+-[A-Za-z0-9]+-\d{3,}-[A-Za-z0-9]+(?:-[A-Za-z]+)?'
        tag_pattern = default_pattern
    else:
        relock = st.button("Lock regex editor", key="lock_btn", use_container_width=True)
        if relock:
            st.session_state.regex_unlocked = False
        default_pattern = r'(?:\d+(?:\s*-\s*\d+/\d+)?)\s*"\s*-[A-Za-z0-9]+-[A-Za-z0-9]+-\d{3,}-[A-Za-z0-9]+(?:-[A-Za-z]+)?'
        tag_pattern = st.text_area("Line-tag regex", value=default_pattern, height=90)

# ---------- Main area
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)
run = st.button("Extract Line-Tags", use_container_width=True, type="primary")

results_placeholder = st.empty()
all_tags = []

if uploaded_files and run:
    flags = 0 if case_sensitive else re.IGNORECASE
    rx = re.compile(tag_pattern, flags=flags)

    for uploaded_file in uploaded_files:
        data = uploaded_file.getvalue()
        pdf = fitz.open(stream=data, filetype="pdf")
        for page in pdf:
            text = page.get_text("text")
            if text:
                text = re.sub(r'\s*\n\s*', ' ', text).replace('–', '-').replace('—', '-')
                matches = rx.findall(text)
                all_tags.extend(matches)
        pdf.close()

    # Apply startswith filter (if provided)
    if prefix_filter:
        all_tags = [t for t in all_tags if (t.startswith(prefix_filter) if case_sensitive
                    else t.lower().startswith(prefix_filter.lower()))]

    # Apply contains filter (if provided)
    if contains_filter:
        all_tags = [t for t in all_tags if (contains_filter in t if case_sensitive
                    else contains_filter.lower() in t.lower())]

    if not show_duplicates:
        seen, deduped = set(), []
        for t in all_tags:
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        all_tags = deduped

    if sort_output:
        all_tags = sorted(all_tags, key=lambda x: str(x).lower())

    if all_tags:
        df = pd.DataFrame(all_tags, columns=["Line Number Tags"])
        results_placeholder.dataframe(df, use_container_width=True, hide_index=True)
        st.success(f"Extraction complete — {len(all_tags)} tag(s) found.")

        # --- Download buttons (already styled green via CSS)
        if export_fmt == "XLSX":
            out = BytesIO()
            df.to_excel(out, index=False)
            out.seek(0)
            st.download_button(
                "Download XLSX",
                out,
                "line_number_tags.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="xlsx_dl"
            )
        elif export_fmt == "CSV":
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV", csv, "line_number_tags.csv", "text/csv",
                use_container_width=True, key="csv_dl"
            )
        else:
            txt = "\n".join(df["Line Number Tags"].astype(str).tolist()).encode("utf-8")
            st.download_button(
                "Download TXT", txt, "line_number_tags.txt", "text/plain",
                use_container_width=True, key="txt_dl"
            )
    else:
        results_placeholder.info("No tags found in the uploaded PDFs.")
else:
    results_placeholder.info("Upload PDFs and click Extract tags to see results here.")

# ---------- Footer
st.markdown('<div class="footer">© 2025 Muhammad Ali Haider. All rights reserved.</div>', unsafe_allow_html=True)
