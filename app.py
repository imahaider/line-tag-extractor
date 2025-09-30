import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
from io import BytesIO

# Streamlit app title
st.title("PDF Line Tag Extractor")
st.caption("Created by Muhammad Ali Haider")

# File uploader
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

# Regex for line tags
tag_pattern = r'(?:\d+(?:\s*-\s*\d+/\d+)?)\s*"\s*-[A-Za-z0-9]+-[A-Za-z0-9]+-\d{3,}-[A-Za-z0-9]+(?:-[A-Za-z]+)?'

if uploaded_files:
    all_tags = []
    
    # Process each uploaded PDF
    for uploaded_file in uploaded_files:
        # Read the PDF from memory
        pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in pdf:
            text = page.get_text("text")
            if text:
                # Clean text: remove extra spaces, normalize hyphens
                text = re.sub(r'\s*\n\s*', ' ', text).replace('–', '-').replace('—', '-')
                tags = re.findall(tag_pattern, text)
                all_tags.extend(tags)
        pdf.close()

    # Remove duplicates
    all_tags = list(set(all_tags))

    if all_tags:
        # Display tags
        st.write("Extracted Line Tags:")
        st.write(all_tags)

        # Create DataFrame and offer Excel download
        df = pd.DataFrame(all_tags, columns=["Line Number Tags"])
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        st.download_button(
            label="Download Excel",
            data=output,
            file_name="line_number_tags.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.write("No tags found in the uploaded PDFs.")
