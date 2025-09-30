import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
from io import BytesIO
import base64

# ---------- Page setup
st.set_page_config(page_title="P&IDs Line-Tags Extractor", page_icon="📄", layout="wide")

# ---------- CSS: exact colors and identical button specs
st.markdown("""
<style>
:root{
  --orange:#FD602E;   /* Extract button color */
  --green:#6EB819;    /* Download buttons color */
  --btn-pad-y:0.75rem;
  --btn-pad-x:1.25rem;
  --btn-radius:12px;
  --btn-font-size:1rem;
  --btn-font-weight:700;
}

/* Layout and title */
.block-container {padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1200px;}
.block-container > *:first-child { margin-top: 0 !important; }
.app-title{
  font-weight: 800; font-size: 2.1rem; line-height: 1.2;
  background: linear-gradient(90deg,#0ea5e9,#22c55e,#a855f7);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  margin: 0 0 .45rem 0; word-break: break-word; overflow-wrap: anywhere;
}
.footer{color:rgba(49,51,63,.55); font-size:.85rem; text-align:center; margin-top:2rem;}

/* Uniform spec for both Extract and Download buttons */
.btn-solid{
  display: inline-block;
  width: 100%;
  text-align: center;
  padding: var(--btn-pad-y) var(--btn-pad-x);
  font-weight: var(--btn-font-weight);
  font-size: var(--btn-font-size);
  border-radius: var(--btn-radius);
  border: 1px solid transparent;
  text-decoration: none;
  cursor: pointer;
  transition: filter .15s ease;
  user-select: none;
}

/* Color variants */
.btn-orange{ background-color: var(--orange); border-color: var(--orange); color: #fff; }
.btn-orange:hover{ filter: brightness(.95); }

.btn-green{ background-color: var(--green); border-color: var(--green); color: #fff; }
.btn-green:hover{ filter: brightness(.95); }

/* Force the native Streamlit Extract button to match spec and color exactly */
#extract_btn_wrap button{
  width: 100%;
  background-color: var(--orange) !important;  /* #FD602E */
  border-color: var(--orange) !important;
  color: #fff !important;
  padding: var(--btn-pad-y) var(--btn-pad-x) !important;
  font-weight: var(--btn-font-weight) !important;
  font-size: var(--btn-font-size) !important;
  border-radius: var(--btn-radius) !important;
}
#extract_btn_wrap button:hover{ filter: brightness(.95); }

/* Focus ring for accessibility on anchor buttons */
a.btn-solid:focus-visible{
  outline: 3px solid rgba(14,165,233,.5); outline-offset: 2px;
}
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
    default_pattern = r'(?:\\d+(?:\\s*-\\s*\\d+/\\d+)?)\\s*"\\s*-[A-Za-z0-9]+-[A-Za-z0-9]+-\\d{3,}-[A-Za-z0-9]+(?:-[A-Za-z]+)?'
    tag_pattern = st.text_area("Line-tag regex", value=default_pattern, height=90)

# ---------- Main controls
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

# Wrap Extract button so we can style it to #FD602E and keep identical spec
st.markdown('<div id="extract_btn_wrap">', unsafe_allow_html=True)
run = st.button("Extract Tags", use_container_width=True, type="primary")
st.markdown('</div>', unsafe_allow_html=True)

results_placeholder = st.empty()
all_tags = []

# Helper to render download buttons as same size and style (green)
def download_button_like_streamlit(data_bytes: bytes, filename: str, label: str, mime: str) -> None:
    b64 = base64.b64encode(data_bytes).decode()
    href = f"data:{mime};base64,{b64}"
    st.markdown(f'<a class="btn-solid btn-green" href="{href}" download="{filename}">{label}</a>', unsafe_allow_html=True)

if uploaded_files and run:
    flags = 0 if case_sensitive else re.IGNORECASE
    rx = re.compile(tag_pattern, flags=flags)

    for uploaded_file in uploaded_files:
        data = uploaded_file.getvalue()
        pdf = fitz.open(stream=data, filetype="pdf")
        for page in pdf:
            text = page.get_text("text")
            if text:
                text = re.sub(r'\\s*\\n\\s*', ' ', text).replace('–', '-').replace('—', '-')
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

        # Downloads — same size and design as Extract, in #6EB819
        if export_fmt == "XLSX":
            out = BytesIO()
            df.to_excel(out, index=False)
            out.seek(0)
            download_button_like_streamlit(
                data_bytes=out.getvalue(),
                filename="line_number_tags.xlsx",
                label="⬇ Download XLSX",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        elif export_fmt == "CSV":
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            download_button_like_streamlit(
                data_bytes=csv_bytes,
                filename="line_number_tags.csv",
                label="⬇ Download CSV",
                mime="text/csv",
            )
        else:
            txt_bytes = "\\n".join(df["Line Number Tags"].astype(str).tolist()).encode("utf-8")
            download_button_like_streamlit(
                data_bytes=txt_bytes,
                filename="line_number_tags.txt",
                label="⬇ Download TXT",
                mime="text/plain",
            )
    else:
        results_placeholder.info("No tags found in the uploaded PDFs.")
else:
    results_placeholder.info("Upload PDFs and click Extract tags to see results here.")

# ---------- Footer
st.markdown('<div class="footer">© 2025 Muhammad Ali Haider. All rights reserved.</div>', unsafe_allow_html=True)
