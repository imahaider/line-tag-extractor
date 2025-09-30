import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
from io import BytesIO
import base64

# ---------- Page setup
st.set_page_config(page_title="P&IDs Line-Tags Extractor", page_icon="📄", layout="wide")

# ---------- CSS: only buttons styled
st.markdown("""
<style>
/* Keep your existing layout/title/footer intact; only buttons below */
.btn-solid {
  display: inline-block;
  width: 100%;
  text-align: center;
  padding: 0.75rem 1.25rem;
  font-weight: 700;
  font-size: 1rem;
  border-radius: 12px;
  border: 1px solid transparent;
  text-decoration: none;
  cursor: pointer;
}

/* Download buttons: green #6EB819 */
.btn-green { background-color: #6EB819; border-color: #6EB819; color: #fff; }
.btn-green:hover { background-color: #5ea114; border-color: #5ea114; }

/* Extract Tags (form submit) stable selector */
div[data-testid="formSubmitButton"] > button {
  background-color: #FD602E !important;  /* orange */
  border-color: #FD602E !important;
  color: #fff !important;
  width: 100%;
  padding: 0.75rem 1.25rem !important;
  font-weight: 700 !important;
  font-size: 1rem !important;
  border-radius: 12px !important;
}
div[data-testid="formSubmitButton"] > button:hover { filter: brightness(0.95); }
</style>
""", unsafe_allow_html=True)

# ---------- Header (unchanged)
st.markdown('<div class="app-title">P&IDs Line-Tags Extractor</div>', unsafe_allow_html=True)
st.caption("Developed by Muhammad Ali Haider")

# ---------- Sidebar (unchanged)
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

# ---------- Main controls (Extract via form submit for reliable styling)
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)
with st.form("extract_form", clear_on_submit=False):
    run = st.form_submit_button("Extract Tags", use_container_width=True)

results_placeholder = st.empty()
all_tags = []

# Helper to create same-sized download buttons in green #6EB819
def download_button_like_primary(data_bytes: bytes, filename: str, label: str, mime: str) -> None:
    b64 = base64.b64encode(data_bytes).decode()
    href = f"data:{mime};base64,{b64}"
    st.markdown(f'<a class="btn-solid btn-green" href="{href}" download="{filename}">{label}</a>', unsafe_allow_html=True)

# ---------- Processing (unchanged)
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
        st.success(f"Extraction complete. {len(all_tags)} tag(s) found.")

        # ---------- Downloads: same size/shape as Extract, green #6EB819 ----------
        if export_fmt == "XLSX":
            out = BytesIO()
            df.to_excel(out, index=False)
            out.seek(0)
            download_button_like_primary(
                data_bytes=out.getvalue(),
                filename="line_number_tags.xlsx",
                label="⬇ Download XLSX",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        elif export_fmt == "CSV":
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            download_button_like_primary(
                data_bytes=csv_bytes,
                filename="line_number_tags.csv",
                label="⬇ Download CSV",
                mime="text/csv",
            )
        else:
            txt_bytes = "\n".join(df["Line Number Tags"].astype(str).tolist()).encode("utf-8")
            download_button_like_primary(
                data_bytes=txt_bytes,
                filename="line_number_tags.txt",
                label="⬇ Download TXT",
                mime="text/plain",
            )
    else:
        results_placeholder.info("No tags found in the uploaded PDFs.")
else:
    results_placeholder.info("Upload PDFs and click Extract tags to see results here.")

# ---------- Footer (unchanged)
st.markdown('<div class="footer">© 2025 Muhammad Ali Haider. All rights reserved.</div>', unsafe_allow_html=True)
