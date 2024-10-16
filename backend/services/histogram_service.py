import io
import matplotlib.pyplot as plt
from collections import Counter
import os
import json
import string
from nltk.corpus import stopwords

# Your clean_text function remains the same
def clean_text(text, language):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    stop_words = set(stopwords.words(language))
    words = text.split()
    cleaned_words = [word for word in words if word not in stop_words]
    removed_stopwords = [word for word in words if word in stop_words]
    return ' '.join(cleaned_words), ' '.join(removed_stopwords)

def generate_histograms(base_dir, language):
    if not os.path.exists(base_dir):
        return None

    all_cleaned_text = []
    all_stopwords = []

    # Check if the base_dir is a video folder (check if metadata.json exists)
    metadata_path = os.path.join(base_dir, 'metadata.json')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                cleaned_text, stopwords_text = clean_text(data['text'], language)
                all_cleaned_text.append(cleaned_text)
                all_stopwords.append(stopwords_text)
    else:
        # If it's a language folder, iterate through video folders
        for video_folder in os.listdir(base_dir):
            video_path = os.path.join(base_dir, video_folder)
            metadata_path = os.path.join(video_path, 'metadata.json')
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    for line in f:
                        data = json.loads(line)
                        cleaned_text, stopwords_text = clean_text(data['text'], language)
                        all_cleaned_text.append(cleaned_text)
                        all_stopwords.append(stopwords_text)

    combined_cleaned_text = ' '.join(all_cleaned_text)
    combined_stopwords = ' '.join(all_stopwords)
    
    word_freq = Counter(combined_cleaned_text.split())
    stopword_freq = Counter(combined_stopwords.split())
    
    top_words = dict(word_freq.most_common(20))
    top_stopwords = dict(stopword_freq.most_common(20))
    
    # Create a figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))
    
    # Histogram for cleaned words
    ax1.bar(top_words.keys(), top_words.values())
    ax1.set_title('Top 20 Most Common Words (Stopwords Removed)')
    ax1.set_xlabel('Words')
    ax1.set_ylabel('Frequency')
    ax1.tick_params(axis='x', rotation=45)
    
    # Histogram for stopwords
    ax2.bar(top_stopwords.keys(), top_stopwords.values())
    ax2.set_title('Top 20 Most Common Stopwords')
    ax2.set_xlabel('Stopwords')
    ax2.set_ylabel('Frequency')
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Save the plot to a BytesIO buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    img_buffer.seek(0)
    
    plt.close(fig)  # Close the figure to free up memory
    
    return img_buffer
