import os

# Function to extract video_id from url
def extract_video_id(youtube_url):
    try:
        if 'v=' in youtube_url:
            # Standard YouTube URL with video ID in 'v='
            return youtube_url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in youtube_url:
            # Shortened YouTube URL
            return youtube_url.split('youtu.be/')[1].split('?')[0]
        elif 'embed/' in youtube_url:
            # Embedded YouTube URL
            return youtube_url.split('embed/')[1].split('?')[0]
        else:
            raise ValueError(f"Cannot extract video ID from {youtube_url}")
    except Exception as e:
        print(f"Error extracting video ID: {e}")
        return None


# Function to check if the link has been processed
def is_link_processed(link, processed_links_file):
    if not os.path.exists(processed_links_file):
        open(processed_links_file, 'w').close()  # Create file if it doesn't exist
        return False

    with open(processed_links_file, 'r') as file:
        processed_links = [line.strip() for line in file.readlines()]

    return link in processed_links

# Function to add a link to the processed list
def mark_link_as_processed(link, processed_links_file):
    with open(processed_links_file, 'a') as file:
        file.write(link + '\n')
        
# Function to convert SRT time to seconds
def convert_srt_time_to_seconds(srt_time):
    hours, minutes, seconds = srt_time.split(':')
    seconds, milliseconds = seconds.split(',')
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000

# Function to format timestamps for SRT
def format_timestamp(seconds):
    millisec = int((seconds - int(seconds)) * 1000)
    return "{:02}:{:02}:{:02},{:03}".format(int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60), millisec)

# Function to append new captions to an existing SRT file
def append_srt_chunk(srt_file_path, captions):
    with open(srt_file_path, 'a', encoding='utf-8') as srt_file:
        current_index = sum(1 for _ in open(srt_file_path)) // 4  # Get the current number of captions
        for index, (start, end, text) in enumerate(captions):
            srt_file.write(f"{current_index + index + 1}\n")
            srt_file.write(f"{format_timestamp(start)} --> {format_timestamp(end)}\n")
            srt_file.write(f"{text}\n\n")
            
# Function to save a chunk of captions to an SRT file
def save_srt_chunk(captions, srt_file_path):
    with open(srt_file_path, 'w', encoding='utf-8') as srt_file:
        for index, (start, end, text) in enumerate(captions):
            srt_file.write(f"{index + 1}\n")
            srt_file.write(f"{format_timestamp(start)} --> {format_timestamp(end)}\n")
            srt_file.write(f"{text}\n\n")
            
