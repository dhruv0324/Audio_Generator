import time
import streamlit as st
import requests

# Define the backend API URLs
BACKEND_URL_PROCESS = "http://localhost:8080/process/"
BACKEND_URL_TRANSFER = "http://localhost:8080/transfer/"
BACKEND_URL_DELETE = "http://localhost:8080/delete_temp/"
BACKEND_URL_WORDCLOUD = "http://localhost:8080/wordcloud/"
BACKEND_URL_HISTOGRAM = "http://localhost:8080/histograms/"  

# App title and description
st.title("Audio Data Generator 🎥➡️📝")

st.markdown(""" 
    Welcome to the Audio Data Generator! This app helps you create audio chunks 
    and corresponding SRT files from multiple YouTube videos. It's perfect for building a dataset 
    of audio segments with accurate transcriptions. Simply upload a text file containing YouTube links, select your desired language, 
    and let our app do the rest.
""")

# Initialize session state for word cloud
if 'wordcloud' not in st.session_state:
    st.session_state.wordcloud = None

# Fetch the word cloud only if it has not been fetched yet
if st.session_state.wordcloud is None:
    try:
        response = requests.get(BACKEND_URL_WORDCLOUD)
        if response.status_code == 200:
            st.session_state.wordcloud = response.content  # Store word cloud image in session state
        else:
            st.error("Could not retrieve word cloud. Please try again later.")
    except Exception as e:
        st.error(f"An error occurred while fetching the word cloud: {e}")

# Display the word cloud if available
if st.session_state.wordcloud:
    st.header("Word Cloud")
    st.image(st.session_state.wordcloud, caption="Generated Word Cloud", use_column_width=True)

# Initialize session state for histogram
if 'histogram' not in st.session_state:
    st.session_state.histogram = None

# Fetch the histogram only if it has not been fetched yet
if st.session_state.histogram is None:
    try:
        response = requests.get(BACKEND_URL_HISTOGRAM)
        if response.status_code == 200:
            st.session_state.histogram = response.content  # Store histogram image in session state
        else:
            st.error("Could not retrieve histogram. Please try again later.")
    except Exception as e:
        st.error(f"An error occurred while fetching the histogram: {e}")

# Display the histogram if available
if st.session_state.histogram:
    st.header("Histogram")
    st.image(st.session_state.histogram, caption="Generated Histogram", use_column_width=True)

# Instructions
st.header("How to use:")
st.markdown(""" 
    1. Prepare a .txt file with one YouTube link per line.
    2. Upload your file using the file uploader below.
    3. Select the language for transcription from the dropdown menu.
    4. Click the 'Submit' button to process your links.
    5. You will get a success message after successful processing.
    6. Click 'Yes' if you want to store the generated results and 'No' to delete them.
    7. Reload the page if you wish to process more files. 
""")

# Initialize session state variables to track file processing and unique_id
if 'file_processed' not in st.session_state:
    st.session_state.file_processed = False

if 'unique_id' not in st.session_state:
    st.session_state.unique_id = None

# New session state variables for file and language
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None

if 'language' not in st.session_state:
    st.session_state.language = ""

# File uploader for .txt file
st.session_state.uploaded_file = st.file_uploader("Upload a text file with YouTube links", type=["txt"])

# Dropdown for language selection
st.session_state.language = st.selectbox("Select a language for transcription", ["", "English", "Hindi", "German"])

# Button to trigger processing
if st.session_state.uploaded_file is not None and st.session_state.language != "":
    if st.button("Submit", key="submit_button"):
        # Convert file to bytes to send it to FastAPI
        file_bytes = st.session_state.uploaded_file.read()

        # Create a dictionary for the POST request with the file and form data
        files = {"file": (st.session_state.uploaded_file.name, file_bytes)}
        data = {"language": st.session_state.language.lower()}

        # Make the API request to the FastAPI backend
        try:
            with st.spinner('Processing your request...'):
                response = requests.post(BACKEND_URL_PROCESS, files=files, data=data)

            # Check the status of the response
            if response.status_code == 200:
                result = response.json()
                st.success("File processed successfully! 🎉")

                # Store the unique_id in session state
                st.session_state.unique_id = result.get("unique_id")
                st.session_state.file_processed = True  # Update session state after successful processing

                st.write(f"Unique ID: {st.session_state.unique_id}")  # Display the unique ID on the frontend

            else:
                st.error(f"Error: {response.json()['message']} ❌")

        except Exception as e:
            st.error(f"An error occurred: {e} ❌")

else:
    st.warning("Please upload a valid .txt file and select a language before submitting.")

# Only show the Yes/No buttons after successful file processing
if st.session_state.file_processed:
    st.write("Would you like to store the generated chunks?")

    # Create styled columns for the Yes/No buttons
    col1, col2 = st.columns([1, 1])

    with col1:
        # Button for Yes (Transfer Data)
        if st.button("Yes", key="yes_button"):
            try:
                with st.spinner("Transferring chunks..."):
                    transfer_response = requests.post(BACKEND_URL_TRANSFER, json={"unique_id": st.session_state.unique_id})
                    if transfer_response.status_code == 200:
                        st.success("Chunks transferred successfully! 🎉\n Please reload the page if you wish to process more files!")
                    else:
                        st.error(f"Error: {transfer_response.json()['message']} ❌")
            except Exception as e:
                st.error(f"An error occurred during transfer: {e} ❌")

    with col2:
        # Button for No (Delete Temp Folder)
        if st.button("No", key="no_button"):
            try:
                with st.spinner("Deleting temp folder..."):
                    delete_response = requests.delete(BACKEND_URL_DELETE, json={"unique_id": st.session_state.unique_id})
                    if delete_response.status_code == 200:
                        st.success("Temp folder deleted successfully! 🗑️\n Please reload the page if you wish to process more files!")
                    else:
                        st.error(f"Error: {delete_response.json()['message']} ❌")
            except Exception as e:
                st.error(f"An error occurred during deletion: {e} ❌")

# Add some styling
st.markdown(""" 
    <style>
    .stButton>button {
        color: #ffffff;
        background-color: #4CAF50;
        border-radius: 5px;
        font-size: 16px;
        padding: 10px 20px;
        margin: 5px;
    }
    .stSelectbox {
        color: #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)
