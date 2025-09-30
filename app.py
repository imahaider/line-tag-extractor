import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
from io import BytesIO
import base64

st.set_page_config(page_title="P&IDs Line-Tags Extractor", page_icon="📄", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
/* Title + footer */
.block-container {padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1200px;}
.app-title{
  font-weight: 800; font-size: 2.1rem; line-height: 1.2;
  background: linear-gradient(90deg,#0ea5e9,#22c55e,#a855f7);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  margin: 0 0 .45rem 0;
}
.footer{color:rgba(49,51,63,.55); font-size:.85rem; text-align:center; margin-top:2rem;}

/* Uniform button design */
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

/* Colors */
.btn-orange { background-color: #FD602E; border-color: #FD602E; color: #fff; }
.btn-orange:hover { background-color: #e65529; border-color: #e65529; }

.btn-green { background-color: #6EB819; border-color: #6EB819; color: #fff; }
.btn-green:hover { background-color: #5ea114; border-color: #5ea114; }

/* Style native Extract button */
#extract_btn_wrap button {
  width: 100%;
  background-color: #FD602E !important;
  border-color: #FD602E !important;
  color: #fff !important;
  padding: 0.75rem 1.25rem !important;
  font-weight: 700 !important;
  font-size: 1rem !important;
  border-radius: 12px !important;
}
#extract_btn_wrap button:hover { filter: brightness(0.95); }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown('<div class="app-title">P&IDs Line-Tags Extractor</div>', unsafe_allow_html=True)
st.caption("Developed by Muhammad Ali Haider")

# ---------- Sidebar ----------
with st.sidebar:
    export_fmt = st.segmented_control("Export Format", ["XLSX", "CSV", "TXT"], default="XLSX")
    case_sensitive = st.toggle("Case sensitive regex", value=False)
    sort_output = st.toggle("Sort results alphabetically", value=True)
    show_duplicates = st.toggle("Keep duplicates", value=False)
    prefix_filter = st.text_input("Starts with (optional)")
    st.subheader("Regex Pattern (optional)")
    default_pattern = r'(?:\d+(?:\s*-\s*\d+/\d+)?)\s*"\s*-[A-Za-z0-9]+-[A-Za-z0-9]+-\d{3,}-[A-Za-z0-9]+(?:-[A-Za-z]+)?'
    tag_pattern = st.text_area("Line-tag regex", value=default_pattern, height=90)

# ---------- Main ----------
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

st.markdown('<div id="extract_btn_wrap">', unsafe_allow_html=True)
run = st.button("Extract Tags", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

results_placeholder = st.empty()

def download_anchor(data_bytes, filename, label, mime):
    """Uniform green button for downloads"""
    b64 = base64.b64encode(data_bytes).decode()
    href = f"data:{mime};base64,{b64}"
    st.markdown(f'<a class="btn-solid btn-green" href="{href}" download="{filename}">{label}</a>', unsafe_allow_html=True)

if uploaded_files and run:
    flags = 0 if case_sensitive else re.IGNORECASE
    rx = re.compile(tag_pattern, flags=flags)
    all_tags = []
    for uploaded_file in uploaded_files:
        data = uploaded_file.getvalue()
        pdf = fitz.open(stream=data, filetype="pdf")
        for page in pdf:
            text = page.get_text("text")
            if text:
                text = re.sub(r'\s*\n\s*', ' ', text).replace('–', '-').replace('—', '-')
                all_tags.extend(rx.findall(text))
        pdf.close()

    if prefix_filter:
        all_tags = [t for t in all_tags if str(t).startswith(prefix_filter)]
    if not show_duplicates:
        all_tags = list(dict.fromkeys(all_tags))  # dedupe preserve order
    if sort_output:
        all_tags = sorted(all_tags, key=lambda x: str(x).lower())

    if all_tags:
        df = pd.DataFrame(all_tags, columns=["Line Number Tags"])
        results_placeholder.dataframe(df, use_container_width=True, hide_index=True)

        if export_fmt == "XLSX":
            out = BytesIO(); df.to_excel(out, index=False); out.seek(0)
            download_anchor(out.getvalue(), "line_number_tags.xlsx", "⬇ Download XLSX",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        elif export_fmt == "CSV":
            csv_bytes = df.to_csv(index=False).encode()
            download_anchor(csv_bytes, "line_number_tags.csv", "⬇ Download CSV", "text/csv")
        else:
            txt_bytes = "\n".join(df["Line Number Tags"]).encode()
            download_anchor(txt_bytes, "line_number_tags.txt", "⬇ Download TXT", "text/plain")
    else:
        results_placeholder.info("No tags found in the uploaded PDFs.")
else:
    results_placeholder.info("Upload PDFs and click Extract Tags to see results here.")

# ---------- Footer ----------
st.markdown('<div class="footer">© 2025 Muhammad Ali Haider. All rights reserved.</div>', unsafe_allow_html=True)
