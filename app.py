import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
from io import BytesIO
import base64

# ---------- Page setup
st.set_page_config(page_title="P&IDs Line-Tags Extractor", page_icon="📄", layout="wide")

# ---------- Styling (title + footer + button styles)
st.markdown("""
<style>
.block-container {padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1200px;}
.block-container > *:first-child { margin-top: 0 !important; }
.app-title{
  font-weight: 800; font-size: 2.1rem; line-height: 1.2;
  background: linear-gradient(90deg,#0ea5e9,#22c55e,#a855f7);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  margin: 0 0 .45rem 0; word-break: break-word; overflow-wrap: anywhere;
}
.btn-green {
  display: inline-block;
  padding: 0.6rem 1rem;
  border-radius: 0.5rem;
  font-weight: 600;
  text-decoration: none;
  background: #16a34a;
  color: #ffffff;
  border: 1px solid #16a34a;
}
.btn-green:hover { background: #15803d; border-color: #15803d; }
.footer{color:rgba(49,51,63,.55); font-size:.85rem; text-align:center; margin-top:2rem;}
</style>
""", unsafe_allow_html=True)

# ---------- Header
st.markdown('<div class="app-title">P&IDs Line-Tags Extractor</div>', unsafe_allow_html=True)
st.caption("Developed by Muhammad Ali Haider")

# ---------- Sidebar
with st.sidebar:
    st.header("About")
    st.write("Upload one or more PDFs. The app extracts line-tags using a regex, with preview and export.")
    st.markdown("---")

    st.subheader("Settings")

    st.subheader("Export")
    export_fmt = st.segmented_control("Format", ["XLSX", "CSV", "TXT"], default="XLSX")

    st.markdown("---")
    case_sensitive = st.toggle("Case sensitive regex", value=False)
    sort_output = st.toggle("Sort results alphabetically", value=True)
    show_duplicates = st.toggle("Keep duplicates", value=False)
    prefix_filter = st.text_input("Starts with (optional)", placeholder="e.g., 12-34/5 or 100")

    st.markdown("---")
    st.subheader("Regex Pattern (optional)")
    default_pattern = r'(?:\d+(?:\s*-\s*\d+/\d+)?)\s*"\s*-[A-Za-z0-9]+-[A-Za-z0-9]+-\d{3,}-[A-Za-z0-9]+(?:-[A-Za-z]+)?'
    tag_pattern = st.text_area("Line-tag regex", value=default_pattern, height=90)

# ---------- Main area
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)
run = st.button("Extract tags", use_container_width=True, type="primary")

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

    if prefix_filter:
        all_tags = [t for t in all_tags if str(t).startswith(prefix_filter)]

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

        # ---------- Downloads ----------
        if export_fmt == "XLSX":
            out = BytesIO()
            df.to_excel(out, index=False)
            out.seek(0)

            # Convert to base64 for custom button
            b64 = base64.b64encode(out.getvalue()).decode()
            href = f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}'

            # Custom green download button
            st.markdown(
                f'<a class="btn-green" href="{href}" download="line_number_tags.xlsx">⬇ Download XLSX</a>',
                unsafe_allow_html=True
            )

        elif export_fmt == "CSV":
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "line_number_tags.csv", "text/csv", use_container_width=True)
        else:
            txt = "\n".join(df["Line Number Tags"].astype(str).tolist()).encode("utf-8")
            st.download_button("Download TXT", txt, "line_number_tags.txt", "text/plain", use_container_width=True)

    else:
        results_placeholder.info("No tags found in the uploaded PDFs.")
else:
    results_placeholder.info("Upload PDFs and click Extract tags to see results here.")

# ---------- Footer
st.markdown('<div class="footer">© 2025 Muhammad Ali Haider. All rights reserved.</div>', unsafe_allow_html=True)
