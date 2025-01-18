import fitz  # PyMuPDF
import re
import pandas as pd
from zipfile import ZipFile, BadZipFile
from io import BytesIO
import streamlit as st

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        if isinstance(pdf_path, BytesIO):
            doc = fitz.open(stream=pdf_path.read(), filetype="pdf")
        elif isinstance(pdf_path, str):
            doc = fitz.open(pdf_path)
        else:
            st.error("Unsupported file type.")
            return ""
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text()
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
    return text

# Function to extract emails from text
def extract_emails_from_text(text):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    return emails

# Function to create a DataFrame of emails with company names
def create_email_dataframe(emails):
    data = [{"Email": email, "Company": email.split('@')[-1].split('.')[0]} for email in emails]
    df = pd.DataFrame(data)
    return df

# Function to extract emails from PDFs in a zip file
def extract_emails_from_zip(zip_path):
    all_emails = []
    try:
        with ZipFile(zip_path, 'r') as zip_ref:
            pdf_files = [f for f in zip_ref.namelist() if f.endswith('.pdf')]
            for pdf_file in pdf_files:
                with zip_ref.open(pdf_file) as pdf_ref:
                    pdf_data = BytesIO(pdf_ref.read())
                    text = extract_text_from_pdf(pdf_data)
                    emails = extract_emails_from_text(text)
                    all_emails.extend(emails)
    except BadZipFile as e:
        st.error(f"Invalid ZIP file: {e}")
    except Exception as e:
        st.error(f"Error processing ZIP file: {e}")
    return all_emails

# Function to extract emails and create DataFrame
def extract_and_create_dataframe(file):
    if isinstance(file, str):  # Handle path for direct PDFs
        text = extract_text_from_pdf(file)
    elif isinstance(file, BytesIO):  # Handle BytesIO for uploaded PDFs
        text = extract_text_from_pdf(file)
    else:
        st.error("Unsupported file type.")
        return None
        
    if text:
        extracted_emails = extract_emails_from_text(text)
    else:
        st.error("No text was extracted from the file.")
        return None

    email_df = create_email_dataframe(extracted_emails)
    email_df = email_df.drop_duplicates(subset="Email")
    return email_df

# Streamlit app layout
st.title('Email Extractor from PDFs or Zip Files')
st.sidebar.title('Menu')
uploaded_file = st.sidebar.file_uploader("Upload a PDF or ZIP file", type=['pdf', 'zip'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.zip'):
            email_df = extract_and_create_dataframe(uploaded_file)
            if email_df is not None and not email_df.empty:
                st.write("### Extracted Email Data")
                st.dataframe(email_df)

                csv = email_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Email CSV",
                    data=csv,
                    file_name='filtered_emails.csv',
                    mime='text/csv',
                )
        elif uploaded_file.name.endswith('.pdf'):
            email_df = extract_and_create_dataframe(uploaded_file)
            if email_df is not None and not email_df.empty:
                st.write("### Extracted Email Data")
                st.dataframe(email_df)

                csv = email_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Email CSV",
                    data=csv,
                    file_name='filtered_emails.csv',
                    mime='text/csv',
                )
        else:
            st.error("Unsupported file type.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
