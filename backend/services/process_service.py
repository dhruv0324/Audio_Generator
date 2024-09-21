import os
import random
import subprocess
from pydub import AudioSegment
import yt_dlp
import whisper
import json
from backend.utils.utils import format_timestamp, append_srt_chunk, save_srt_chunk, convert_srt_time_to_seconds, mark_link_as_processed, is_link_processed

# Function to download video and convert to wav with 16000 Hz and mono
def download_and_convert_to_wav(youtube_url, output_dir, video_num):
    try:
        print(f"Downloading: {youtube_url}")

        # Set up yt-dlp options to download audio only
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, f'video_{video_num}.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }]
        }

        # Download and extract audio using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        # Locate the downloaded file
        downloaded_file = [f for f in os.listdir(output_dir) if f.endswith('.wav')][-1]
        wav_file_path = os.path.join(output_dir, downloaded_file)

        # Convert to mono and 16000 Hz using ffmpeg
        final_wav_file_path = wav_file_path.replace('.wav', '_mono_16000.wav')
        subprocess.run([
            'ffmpeg', '-i', wav_file_path, '-ac', '1', '-ar', '16000', final_wav_file_path
        ], check=True)

        print(f"Converted and saved to: {final_wav_file_path}")
        os.remove(wav_file_path)  # Remove original wav

        return final_wav_file_path

    except Exception as e:
        print(f"An error occurred for {youtube_url}: {e}")
        return None
    
def format_playlist_url(video_url):
    # Format a YouTube video URL into a playlist URL.
    
    # Check if the URL contains a playlist ID
    if 'list=' in video_url:
        # Extract the playlist ID from the URL
        playlist_id = video_url.split('list=')[1]
        # Return the formatted playlist URL
        return f"https://www.youtube.com/playlist?list={playlist_id}"
    
    # Return the original URL if no playlist ID is found
    return video_url  

def extract_video_links_from_playlist(playlist_url):
    # Extract video links from a formatted YouTube playlist URL.
    
    # Format the URL before extracting video links
    formatted_url = format_playlist_url(playlist_url)
    video_links = []
    
    # Define options for yt-dlp
    ydl_opts = {
        'extract_flat': True,  # Extract only video information, do not download
        'force_generic_extractor': True,  # Use the generic extractor
    }

    # Create a yt-dlp instance with the specified options
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Extract information from the playlist without downloading
            info = ydl.extract_info(formatted_url, download=False)
            
            # Collect the video URLs from the extracted information
            video_links = [entry['url'] for entry in info.get('entries', [])]
                
        except Exception as e:
            # Print any errors that occur during extraction
            print(f"An error occurred: {e}")

    # Return the list of extracted video links
    return video_links
    
# Function to generate SRT using Whisper ASR with language support
def generate_srt_file(audio_file_path, output_dir, language):
    try:
        model = whisper.load_model("base")
        
        # Set language for transcription based on user choice
        language_map = {
            'english': 'en',
            'hindi': 'hi',
            'german': 'de'
        }

        if language.lower() not in language_map:
            print(f"Unsupported language selected: {language}. Defaulting to English.")
            language = 'english'
        
        print(f"Generating captions in {language.capitalize()} for {audio_file_path}...")
        
        # Transcribe audio using Whisper with the selected language
        result = model.transcribe(audio_file_path, language=language_map[language.lower()])
        
        # Save captions to an SRT file
        srt_file_path = os.path.join(output_dir, os.path.basename(audio_file_path).replace('.wav', '.srt'))
        with open(srt_file_path, 'w', encoding='utf-8') as srt_file:
            for segment in result['segments']:
                start = segment['start']
                end = segment['end']
                text = segment['text']
                srt_file.write(f"{segment['id'] + 1}\n")
                srt_file.write(f"{format_timestamp(start)} --> {format_timestamp(end)}\n")
                srt_file.write(f"{text}\n\n")
        return srt_file_path

    except Exception as e:
        print(f"An error occurred during SRT generation: {e}")
        return None
    
    
# Updated function with proper handling of the last chunk's metadata
def chunk_audio_and_srt(audio_file_path, srt_file_path, output_dir, language):
    # Create directories for caption chunks and audio chunks
    caption_chunk_dir = os.path.join(output_dir, 'caption_chunks')
    audio_chunk_dir = os.path.join(output_dir, 'audio_chunks')
    os.makedirs(caption_chunk_dir, exist_ok=True)
    os.makedirs(audio_chunk_dir, exist_ok=True)

    # Set language map
    language_map = {
        'english': 'en',
        'hindi': 'hi',
        'german': 'de'
    }

    # Parse SRT file to get timestamp segments with captions
    caption_segments = []
    with open(srt_file_path, 'r', encoding='utf-8') as srt_file:
        lines = srt_file.readlines()
        for i in range(0, len(lines), 4):  # Each caption segment consists of 4 lines in SRT
            start_time = convert_srt_time_to_seconds(lines[i+1].split(' --> ')[0].strip())
            end_time = convert_srt_time_to_seconds(lines[i+1].split(' --> ')[1].strip())
            text = lines[i+2].strip()  # Get the caption text
            caption_segments.append((start_time, end_time, text))

    # Load the audio file
    audio = AudioSegment.from_wav(audio_file_path)

    # Initialize counters for naming files
    chunk_index = 1

    # Initialize an empty list to store chunk metadata
    chunk_metadata = []

    # Randomly chop the audio based on captions and the time constraint
    current_chunk_audio = AudioSegment.empty()
    current_chunk_captions = []
    chunk_duration_limit = random.randint(16, 29)  # Generate initial random chunk duration
    silence_threshold = 3  # 3-second threshold for silence handling

    for idx, (segment_start, segment_end, text) in enumerate(caption_segments):
        segment_audio = audio[segment_start * 1000:segment_end * 1000]
        current_chunk_audio += segment_audio
        current_chunk_captions.append((segment_start, segment_end, text))

        # Check the gap between this segment's end and the next segment's start
        next_segment_start = caption_segments[idx + 1][0] if idx + 1 < len(caption_segments) else None
        if next_segment_start:
            gap_duration = next_segment_start - segment_end
        else:
            gap_duration = None  # No next segment means no gap

        # If the gap is short (below the threshold), include the gap in the current chunk
        if gap_duration is not None and gap_duration <= silence_threshold:
            current_chunk_audio += audio[segment_end * 1000:next_segment_start * 1000]  # Append short silence
            segment_end = next_segment_start  # Extend segment end time

        # Check if the accumulated audio chunk is within the random chunk duration limit
        current_chunk_duration = len(current_chunk_audio) / 1000  # Duration in seconds
        if current_chunk_duration >= chunk_duration_limit or current_chunk_duration > 29:
            # Save the audio chunk
            chunk_audio_path = os.path.join(audio_chunk_dir, f"{chunk_index}.wav")
            current_chunk_audio.export(chunk_audio_path, format="wav")

            # Save the corresponding SRT chunk with captions
            chunk_srt_path = os.path.join(caption_chunk_dir, f"{chunk_index}.srt")
            save_srt_chunk(current_chunk_captions, chunk_srt_path)

            # Append chunk metadata
            chunk_metadata.append({
                'audio_filepath': os.path.join(*os.path.normpath(chunk_audio_path).split(os.path.sep)[os.path.normpath(chunk_audio_path).split(os.path.sep).index('audio_files'):]).replace('\\', '/'),
                'duration': current_chunk_duration,
                'text': ' '.join(caption.strip() for start, end, caption in current_chunk_captions),
                'lang_id': language_map.get(language.lower(), 'en')
            })

            # Log success message
            print(f"Chunk {chunk_index} created successfully!")

            # Reset for the next chunk and generate a new random chunk duration limit
            current_chunk_audio = AudioSegment.empty()
            current_chunk_captions = []
            chunk_duration_limit = random.randint(16, 29)  # New random chunk duration
            chunk_index += 1

    # Handle any leftover audio and captions (final chunk)
    if len(current_chunk_audio) > 0:
        leftover_duration = len(current_chunk_audio) / 1000

        if 16 <= leftover_duration <= 29:
            # Save the final audio chunk
            chunk_audio_path = os.path.join(audio_chunk_dir, f"{chunk_index}.wav")
            current_chunk_audio.export(chunk_audio_path, format="wav")

            # Save the corresponding SRT chunk
            chunk_srt_path = os.path.join(caption_chunk_dir, f"{chunk_index}.srt")
            save_srt_chunk(current_chunk_captions, chunk_srt_path)

            # Append metadata for the final chunk
            chunk_metadata.append({
                'audio_filepath': os.path.join(*os.path.normpath(chunk_audio_path).split(os.path.sep)[os.path.normpath(chunk_audio_path).split(os.path.sep).index('audio_files'):]).replace('\\', '/'),
                'duration': leftover_duration,
                'text': ' '.join(caption.strip() for start, end, caption in current_chunk_captions),
                'lang_id': language_map.get(language.lower(), 'en')
            })

            # Log success message
            print(f"Final chunk {chunk_index} created successfully!")

        else:
            # If the last segment is shorter than 16 seconds, append it to the previous chunk
            if chunk_index > 1:
                prev_audio_file = os.path.join(audio_chunk_dir, f"{chunk_index - 1}.wav")
                prev_audio = AudioSegment.from_wav(prev_audio_file)
                prev_audio += current_chunk_audio
                prev_audio.export(prev_audio_file, format="wav")

                # Append SRT chunk to previous file
                prev_srt_file = os.path.join(caption_chunk_dir, f"{chunk_index - 1}.srt")
                append_srt_chunk(prev_srt_file, current_chunk_captions)

                # Update the metadata of the previous chunk
                chunk_metadata[-1]['duration'] += leftover_duration  # Extend previous chunk's duration
                chunk_metadata[-1]['text'] += ' ' + ' '.join(caption.strip() for start, end, caption in current_chunk_captions)  # Append text

                # Log success message for appending to the previous chunk
                print(f"Appended remaining audio to chunk {chunk_index - 1} successfully!")

    return chunk_metadata

# Main function to process the YouTube links and create folders with language input
def process_youtube_links(file_path, language):
    # Step 1: Create 'audio_files' directory if not present
    output_dir = 'audio_files'
    os.makedirs(output_dir, exist_ok=True)

    # Step 2: Create or load 'processed_links.txt'
    processed_links_file = os.path.join(output_dir, 'processed_links.txt')

    try:
        with open(file_path, 'r') as file:
            links = [line.strip() for line in file.readlines() if line.strip()]

        # Step 3: Create a language folder based on user input (lowercase)
        language_folder = os.path.join(output_dir, language.lower())
        os.makedirs(language_folder, exist_ok=True)

        processed_videos = []  # List to store info about processed videos

        # Step 4: Process each link and create separate directories
        for link in links:
            # Skip link if already processed
            if is_link_processed(link, processed_links_file):
                print(f"Link already processed: {link}")
                # Mark as already processed in response
                processed_videos.append({
                    'status': 'already_processed',
                    'link': link
                })
                continue

            # If it's a playlist, extract video links
            if "list" in link:
                video_links = extract_video_links_from_playlist(link)
            else:
                video_links = [link]

            for video_link in video_links:
                # Find the next available "video_x" folder number
                existing_videos = [d for d in os.listdir(language_folder) if d.startswith("video_")]
                video_nums = [int(v.split("_")[1]) for v in existing_videos] if existing_videos else []
                next_video_num = max(video_nums, default=0) + 1
                video_dir = os.path.join(language_folder, f"video_{next_video_num}")
                os.makedirs(video_dir, exist_ok=True)

                print(f"Processing video {next_video_num}: {video_link}")

                # Download and convert to wav
                audio_file = download_and_convert_to_wav(video_link, video_dir, next_video_num)

                if audio_file:
                    # Generate SRT file using Whisper with selected language
                    srt_file = generate_srt_file(audio_file, video_dir, language)

                    if srt_file:
                        print(f"Generated SRT in {language.capitalize()}: {srt_file}")
                        
                        # Get metadata file after chunking of audio and SRT
                        chunk_metadata = chunk_audio_and_srt(audio_file, srt_file, video_dir, language)

                        if chunk_metadata:
                            # Create JSON metadata file
                            metadata_file_path = os.path.join(video_dir, 'metadata.json')
                            with open(metadata_file_path, 'w', encoding='utf-8') as metadata_file:
                                for chunk in chunk_metadata:
                                    json.dump(chunk, metadata_file, ensure_ascii=False)
                                    metadata_file.write('\n')
                    
                            print(f"Created metadata file: {metadata_file_path}")
                            processed_videos.append({
                                'status': 'processed',
                                'video_number': next_video_num,
                                'link': video_link,
                                'metadata_file': metadata_file_path
                            })

                        # Remove original .wav and .srt files after successful chunking
                        os.remove(audio_file)
                        os.remove(srt_file)

                        # Mark the link as processed
                        mark_link_as_processed(link, processed_links_file)
                    else:
                        print(f"Failed to generate SRT for {audio_file}")
                        return {"status": "error", "message": f"Failed to generate SRT for {audio_file}"}, 500
                else:
                    print(f"Failed to process {link}")
                    return {"status": "error", "message": f"Failed to process {link}"}, 500

        # Return a successful response with metadata
        return {
            "status": "success",
            "processed_videos": processed_videos
        }, 200

    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        return {"status": "error", "message": f"The file {file_path} was not found."}, 404
    except Exception as e:
        print(f"An error occurred while processing the file: {e}")
        return {"status": "error", "message": str(e)}, 500