import streamlit as st
import requests

# Define the backend API URL
BACKEND_URL = "http://localhost:8080/process/"

# App title and description
st.title("Audio Data Generator 🎥➡️📝")

st.markdown("""
    Welcome to the Audio Data Generator! This app helps you create audio chunks 
    and corresponding SRT files from multiple YouTube videos. It's perfect for building a dataset 
    of audio segments with accurate transcriptions. Simply upload a text file containing YouTube links, select your desired language, 
    and let our app do the rest.
""")

# Instructions
st.header("How to use:")
st.markdown("""
    1. Prepare a .txt file with one YouTube link per line.
    2. Upload your file using the file uploader below.
    3. Select the language for transcription from the dropdown menu.
    4. Click the 'Submit' button to process your links.
    5. Wait for the results to appear!
""")

# File uploader for .txt file
uploaded_file = st.file_uploader("Upload a text file with YouTube links", type=["txt"])

# Dropdown for language selection
language = st.selectbox("Select a language for transcription", ["", "English", "Hindi", "German"])

# Button to trigger processing
if uploaded_file is not None and language != "":
    if st.button("Submit", key="submit_button"):
        # Convert file to bytes to send it to FastAPI
        file_bytes = uploaded_file.read()

        # Create a dictionary for the POST request with the file and form data
        files = {"file": (uploaded_file.name, file_bytes)}
        data = {"language": language.lower()}

        # Make the API request to the FastAPI backend
        try:
            with st.spinner('Processing your request...'):
                response = requests.post(BACKEND_URL, files=files, data=data)
            
            # Check the status of the response
            if response.status_code == 200:
                st.success("File processed successfully! 🎉")
            else:
                st.error(f"Error: {response.json()['detail']} ❌")
        except Exception as e:
            st.error(f"An error occurred: {e} ❌")
else:
    st.warning("Please upload a valid .txt file and select a language before submitting.")

# Add some styling
st.markdown("""
    <style>
    .stButton>button {
        color: #ffffff;
        background-color: #4CAF50;
        border-radius: 5px;
    }
    .stSelectbox {
        color: #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)