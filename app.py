import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
from io import BytesIO

# ---------------- Page setup
st.set_page_config(page_title="P&IDs Line-Tags Extractor", page_icon="📄", layout="wide")

# ---------------- Light, modern styling
st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px;}
.app-title {
  font-weight: 800; font-size: 2.2rem; line-height: 1.1;
  background: linear-gradient(90deg,#0ea5e9,#22c55e,#a855f7);
  -webkit-background-clip: text; background-clip: text; color: transparent; margin-bottom: .25rem;
}
.app-subtitle {color: rgba(49,51,63,.7); font-size: .95rem; margin-bottom: 1.25rem;}
.card {border: 1px solid rgba(49,51,63,.15); border-radius: 16px; padding: 1rem 1.1rem; background: #fff;}
.card h4 {margin: .2rem 0 .8rem 0;}
.footer {color: rgba(49,51,63,.55); font-size: .85rem; text-align:center; margin-top: 2rem;}
</style>
""", unsafe_allow_html=True)

# ---------------- Header
st.markdown('<div class="app-title">P&IDs Line-Tags Extractor</div>', unsafe_allow_html=True)
st.caption("Developed by Muhammad Ali Haider")

# ---------------- Sidebar - controls
with st.sidebar:
    st.header("Settings")
    st.write("Tune extraction and output.")
    case_sensitive = st.toggle("Case sensitive regex", value=False)
    sort_output = st.toggle("Sort results alphabetically", value=True)
    show_duplicates = st.toggle("Keep duplicates", value=False)
    prefix_filter = st.text_input("Starts with (optional)", placeholder='e.g., "12-34/5" or "100"')
    st.markdown("---")
    st.subheader("Export")
    export_fmt = st.segmented_control("Format", ["XLSX", "CSV", "TXT"], default="XLSX")
    st.markdown("---")
    st.subheader("About")
    st.write("Upload one or more PDFs. The app extracts line-tags with a pattern and lets you preview and download.")

# ---------------- Upload + pattern
col_left, col_right = st.columns([1.05, 1])

with col_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Upload PDF files")
    uploaded_files = st.file_uploader("Select PDFs", type="pdf", accept_multiple_files=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card" style="margin-top: 1rem;">', unsafe_allow_html=True)
    st.subheader("Regex Pattern")
    # Your original pattern, shown for transparency with option to tweak
    default_pattern = r'(?:\d+(?:\s*-\s*\d+/\d+)?)\s*"\s*-[A-Za-z0-9]+-[A-Za-z0-9]+-\d{3,}-[A-Za-z0-9]+(?:-[A-Za-z]+)?'
    tag_pattern = st.text_area("Line-tag regex", value=default_pattern, height=90, help="Edit if you need to adapt to other formats.")
    st.markdown("</div>", unsafe_allow_html=True)

    run = st.button("Extract tags", use_container_width=True, type="primary")

with col_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Preview")
    results_placeholder = st.empty()

    all_tags = []

    if uploaded_files and run:
        flags = 0 if case_sensitive else re.IGNORECASE
        rx = re.compile(tag_pattern, flags=flags)

        # Progress + status
        total_pages = 0
        for f in uploaded_files:
            # quick pass to count pages
            pdf = fitz.open(stream=f.read(), filetype="pdf")
            total_pages += pdf.page_count
            pdf.close()
        # Need to reopen since we consumed the stream above
        progress = st.progress(0)
        done_pages = 0

        # Re-read actual file bytes now for processing
        for uploaded_file in uploaded_files:
            data = uploaded_file.getvalue()
            pdf = fitz.open(stream=data, filetype="pdf")
            for page in pdf:
                text = page.get_text("text")
                if text:
                    # Normalize newlines and long dashes to hyphen
                    text = re.sub(r'\s*\n\s*', ' ', text).replace('–', '-').replace('—', '-')
                    matches = rx.findall(text)
                    all_tags.extend(matches)
                done_pages += 1
                progress.progress(min(done_pages / max(total_pages, 1), 1.0))
            pdf.close()

        # Optional prefix filter
        if prefix_filter:
            all_tags = [t for t in all_tags if str(t).startswith(prefix_filter)]

        # Deduplicate unless user wants duplicates
        if not show_duplicates:
            # preserve first occurrence order
            seen = set()
            deduped = []
            for t in all_tags:
                if t not in seen:
                    seen.add(t)
                    deduped.append(t)
            all_tags = deduped

        # Sort if chosen
        if sort_output:
            all_tags = sorted(all_tags, key=lambda x: str(x).lower())

        if all_tags:
            df = pd.DataFrame(all_tags, columns=["Line Number Tags"])
            results_placeholder.dataframe(df, use_container_width=True, hide_index=True)
            st.toast(f"Extraction complete. {len(all_tags)} tag(s) found.")
        else:
            results_placeholder.info("No tags found in the uploaded PDFs.")
    else:
        results_placeholder.info("Upload PDFs and click Extract tags to see results here.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Export section
st.markdown('<div class="card" style="margin-top: 1rem;">', unsafe_allow_html=True)
st.subheader("Download")

if 'df' in locals() and not df.empty:
    if export_fmt == "XLSX":
        out = BytesIO()
        df.to_excel(out, index=False)
        out.seek(0)
        st.download_button("Download XLSX", out, "line_number_tags.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    elif export_fmt == "CSV":
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "line_number_tags.csv", "text/csv", use_container_width=True)
    else:
        txt = "\n".join(df["Line Number Tags"].astype(str).tolist()).encode("utf-8")
        st.download_button("Download TXT", txt, "line_number_tags.txt", "text/plain", use_container_width=True)
else:
    st.write("Results will be available for download after extraction.")

st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Footer
st.markdown('<div class="footer">© 2025 Muhammad Ali Haider. All rights reserved.</div>', unsafe_allow_html=True)
