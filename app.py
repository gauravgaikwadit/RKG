import fitz  # PyMuPDF
import re
import pandas as pd
from zipfile import ZipFile
from io import BytesIO
import streamlit as st

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    text = ""
    if isinstance(pdf_path, BytesIO):
        doc = fitz.open(stream=pdf_path, filetype="pdf")
    else:
        doc = fitz.open(pdf_path)
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text += page.get_text()
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
def extract_emails_from_zip(zip_file):
    all_emails = []
    with ZipFile(zip_file) as zip_ref:
        pdf_files = [f for f in zip_ref.namelist() if f.endswith('.pdf')]
        if not pdf_files:
            st.warning("No PDF files found in the zip.")
            return []
        
        total_files = len(pdf_files)
        progress = st.progress(0)  # Initialize progress
        for index, pdf_file in enumerate(pdf_files):
            with zip_ref.open(pdf_file) as pdf_ref:
                pdf_data = BytesIO(pdf_ref.read())
                text = extract_text_from_pdf(pdf_data)
                emails = extract_emails_from_text(text)
                all_emails.extend(emails)
            progress.progress((index + 1) / total_files)
    return all_emails

# Function to extract emails from zip and create DataFrame
def extract_and_create_dataframe(zip_file):
    extracted_emails = extract_emails_from_zip(zip_file)
    if not extracted_emails:
        return pd.DataFrame()
    email_df = create_email_dataframe(extracted_emails)
    email_df = email_df.drop_duplicates(subset="Email")
    return email_df

# Streamlit App
st.title("Extract Emails from Uploaded Zip File")

# File upload
uploaded_zip = st.file_uploader("Choose a ZIP file", type="zip")

if uploaded_zip is not None:
    email_df = extract_and_create_dataframe(uploaded_zip)
    if email_df.empty:
        st.warning("No emails extracted from the uploaded file.")
    else:
        st.write("Filtered Email DataFrame:")
        st.dataframe(email_df)

        # Optionally save to a CSV file
        csv_data = email_df.to_csv(index=False)
        st.download_button("Download CSV", csv_data, file_name='filtered_emails.csv', mime='text/csv')

    # Search functionality
    search_query = st.text_input("Search for Email Domain/Company", "")
    if search_query:
        filtered_df = email_df[email_df['Company'].str.contains(search_query, case=False)]
        st.write("Filtered Emails:")
        st.dataframe(filtered_df)
