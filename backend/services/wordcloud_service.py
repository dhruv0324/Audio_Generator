import os
import json
import string
import io
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
from fastapi.responses import StreamingResponse

# Function to clean and preprocess text
def clean_text(text, language):
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove stopwords
    stop_words = set(stopwords.words(language))
    cleaned_words = [word for word in text.split() if word not in stop_words]
    
    # Join words back into a single string
    return ' '.join(cleaned_words)

# Function to generate word cloud
def generate_wordcloud(base_dir, language, max_words=50):
    # Check if the base directory exists
    if not os.path.exists(base_dir):
        return None  # Return None if the directory does not exist

    all_text = []

    # If the base_dir is a video folder (check if metadata.json exists)
    metadata_path = os.path.join(base_dir, 'metadata.json')
    if os.path.exists(metadata_path):
        # Read the metadata file line by line (each line is a separate JSON object)
        with open(metadata_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                cleaned_text = clean_text(data['text'], language)  # Clean the text
                all_text.append(cleaned_text)  # Append the cleaned text to the list
    else:
        # If it's a language folder, iterate through video folders
        for video_folder in os.listdir(base_dir):
            video_path = os.path.join(base_dir, video_folder)
            metadata_path = os.path.join(video_path, 'metadata.json')
            
            # Check if metadata.json exists in the folder
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    # Read the metadata file line by line (each line is a separate JSON object)
                    for line in f:
                        data = json.loads(line)
                        cleaned_text = clean_text(data['text'], language)  # Clean the text
                        all_text.append(cleaned_text)  # Append the cleaned text to the list

    # Combine all the cleaned text into a single string
    combined_text = ' '.join(all_text)

    # Generate the word cloud from the top max_words
    wordcloud = WordCloud(width=800, height=400, max_words=max_words, background_color='white').generate(combined_text)

    # Create a BytesIO buffer to save the image
    img_buffer = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')  # Remove the axis
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    img_buffer.seek(0)  # Move to the beginning of the BytesIO buffer

    return StreamingResponse(img_buffer, media_type="image/png")
