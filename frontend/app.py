import streamlit as st
import requests

BACKEND_URL_PROCESS = "http://localhost:8080/process/"
BACKEND_URL_TRANSFER = "http://localhost:8080/transfer/"
BACKEND_URL_DELETE = "http://localhost:8080/delete_temp/"
BACKEND_URL_WORDCLOUD = "http://localhost:8080/wordcloud/"
BACKEND_URL_HISTOGRAM = "http://localhost:8080/histograms/"
BACKEND_URL_LANGUAGES = "http://localhost:8080/language_folders/"
BACKEND_URL_VIDEOS = "http://localhost:8080/video_folders/"

# App title and description
st.title("Audio Data Generator 🎥➡️📝")

st.markdown(""" 
    Welcome to the Audio Data Generator! This app helps you create audio chunks 
    and corresponding SRT files from multiple YouTube videos. Simply upload a text file containing YouTube links, 
    select your desired language, and let our app do the rest.

    In addition to generating audio chunks and SRT files, this app also offers **visualization features** like **word clouds** and **histograms** to help you analyze the text data. These visualizations allow you to see the most common words and the distribution of filler versus non-filler words.
""")

st.header("How to use the Visualizations (optional):") 
st.markdown(""" 
    1. **Select Language:** Choose the language from the dropdown menu for which you want to generate visualizations.
    2. **Optional Video Selection:** If you want to generate visualizations for a specific video, you can select a video from the dropdown (this step is optional).
    3. **Generate Word Cloud and Histogram:** Click the 'Generate Visualization' button to generate a **word cloud** and **histogram** based on the transcription data.
        - The **Word Cloud** will visually display the most frequent words used in the transcription.
        - The **Histogram** will show the distribution of **filler** and **non-filler** words in the transcription.
    4. You can analyze these visualizations to get insights into word frequencies and content patterns within the transcribed audio.
""")


# Session state management for dropdowns (only run on page reload)
if 'languages' not in st.session_state:
    # Function to fetch languages
    def get_languages():
        try:
            response = requests.get(BACKEND_URL_LANGUAGES)
            if response.status_code == 200:
                return response.json().get("language_folders", [])
            else:
                st.error("Could not retrieve language options. Please try again later.")
                return []
        except Exception as e:
            st.error(f"Error fetching languages: {e}")
            return []
    
    # Fetch languages only once on page load
    st.session_state.languages = get_languages()
    st.session_state.selected_language = ""

# Dropdown for language selection
selected_language = st.selectbox("Select your language", [""] + st.session_state.languages)

# Fetch videos only if a language is selected and it's a new selection
if selected_language and (st.session_state.selected_language != selected_language):
    st.session_state.selected_language = selected_language

    # Function to fetch videos for the selected language
    def get_videos(language):
        try:
            response = requests.get(f"{BACKEND_URL_VIDEOS}?language={language}")
            if response.status_code == 200:
                return response.json().get("video_folders", [])
            else:
                st.error("Could not retrieve video options. Please try again later.")
                return []
        except Exception as e:
            st.error(f"Error fetching videos: {e}")
            return []

    # Fetch videos and store in session state
    st.session_state.videos = get_videos(selected_language)

# Dropdown for video selection (optional)
if selected_language:
    selected_video = st.selectbox("Select your video (optional)", [""] + st.session_state.videos)

# Visualizations
if selected_language:
    if st.button("Generate Visualisations"):
        if selected_video == "":
            # Only language selected
            wordcloud_response = requests.get(f"{BACKEND_URL_WORDCLOUD}?language={selected_language.lower()}")
            histogram_response = requests.get(f"{BACKEND_URL_HISTOGRAM}?language={selected_language.lower()}")

            if wordcloud_response.status_code == 200:
                st.image(wordcloud_response.content, caption="Generated Wordcloud")
            else:
                st.error("Error generating wordcloud.")

            if histogram_response.status_code == 200:
                st.image(histogram_response.content, caption="Generated Histogram")
            else:
                st.error("Error generating histogram.")
        else:
            # Both language and video selected
            wordcloud_response = requests.get(
                f"{BACKEND_URL_WORDCLOUD}?language={selected_language.lower()}&video_code={selected_video}"
            )
            histogram_response = requests.get(
                f"{BACKEND_URL_HISTOGRAM}?language={selected_language.lower()}&video_code={selected_video}"
            )

            if wordcloud_response.status_code == 200:
                st.image(wordcloud_response.content, caption="Generated Wordcloud")
            else:
                st.error("Error generating wordcloud.")

            if histogram_response.status_code == 200:
                st.image(histogram_response.content, caption="Generated Histogram")
            else:
                st.error("Error generating histogram.")

# Instructions and File Upload Section
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

# File uploader for .txt file
uploaded_file = st.file_uploader("Upload a text file with YouTube links", type=["txt"])

# Dropdown for language selection in file processing section
file_language = st.selectbox("Select a language for transcription", ["", "English", "Hindi", "German"])

# Button to trigger processing
if uploaded_file and file_language != "":
    if st.button("Submit", key="submit_button"):
        # Convert file to bytes to send it to FastAPI
        file_bytes = uploaded_file.read()

        # Create a dictionary for the POST request with the file and form data
        files = {"file": (uploaded_file.name, file_bytes)}
        data = {"language": file_language.lower()}

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
