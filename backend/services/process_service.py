import os
import random
import subprocess
from pydub import AudioSegment
import yt_dlp
import whisper
import json
from backend.utils.utils import format_timestamp, append_srt_chunk, save_srt_chunk, convert_srt_time_to_seconds, mark_link_as_processed, is_link_processed, extract_video_id

# Function to download video and convert to wav with 16000 Hz and mono
def download_and_convert_to_wav(youtube_url, output_dir):
    try:
        print(f"Downloading: {youtube_url}")

        # Extract the video ID for naming purposes
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return None

        # Set up yt-dlp options to download audio only
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, f'{video_id}.%(ext)s'),
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
    if 'list=' in video_url:
        playlist_id = video_url.split('list=')[1]
        return f"https://www.youtube.com/playlist?list={playlist_id}"
    return video_url

def extract_video_links_from_playlist(playlist_url):
    formatted_url = format_playlist_url(playlist_url)
    video_links = []
    ydl_opts = {
        'extract_flat': True,
        'force_generic_extractor': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(formatted_url, download=False)
            video_links = [entry['url'] for entry in info.get('entries', [])]
        except Exception as e:
            print(f"An error occurred: {e}")

    return video_links

# Function to generate SRT using Whisper ASR with language support
def generate_srt_file(audio_file_path, output_dir, language):
    try:
        model = whisper.load_model("base")
        language_map = {'english': 'en', 'hindi': 'hi', 'german': 'de'}

        if language.lower() not in language_map:
            print(f"Unsupported language selected: {language}. Defaulting to English.")
            language = 'english'
        
        print(f"Generating captions in {language.capitalize()} for {audio_file_path}...")
        result = model.transcribe(audio_file_path, language=language_map[language.lower()])

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
                'audio_filepath': os.path.join(*os.path.normpath(chunk_audio_path).split(os.path.sep)[os.path.normpath(chunk_audio_path).split(os.path.sep).index('temp_files'):]).replace('\\', '/'),
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
                'audio_filepath': os.path.join(*os.path.normpath(chunk_audio_path).split(os.path.sep)[os.path.normpath(chunk_audio_path).split(os.path.sep).index('temp_files'):]).replace('\\', '/'),
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
    main_op_dir = 'audio_files'
    output_dir = 'temp_files'
    os.makedirs(main_op_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    processed_links_file = os.path.join(main_op_dir, 'processed_links.txt')
    temp_links_file = os.path.join(output_dir, 'temp_links.txt')
    

    try:
        with open(file_path, 'r') as file:
            links = [line.strip() for line in file.readlines() if line.strip()]

        language_folder = os.path.join(output_dir, language.lower())
        os.makedirs(language_folder, exist_ok=True)

        processed_videos = []

        for link in links:
            if is_link_processed(link, processed_links_file):
                print(f"Link already processed: {link}")
                processed_videos.append({'status': 'already_processed', 'link': link})
                continue

            video_links = extract_video_links_from_playlist(link) if "list" in link else [link]

            for video_link in video_links:
                video_id = extract_video_id(video_link)
                if not video_id:
                    print(f"Failed to extract video ID for {video_link}")
                    continue

                video_dir = os.path.join(language_folder, video_id)
                os.makedirs(video_dir, exist_ok=True)

                print(f"Processing video {video_id}: {video_link}")

                audio_file = download_and_convert_to_wav(video_link, video_dir)

                if audio_file:
                    srt_file = generate_srt_file(audio_file, video_dir, language)
                    if srt_file:
                        print(f"Generated SRT in {language.capitalize()}: {srt_file}")
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
                                'link': video_link,
                                'metadata_file': metadata_file_path
                            })
                        
                        os.remove(audio_file)
                        os.remove(srt_file)
                        mark_link_as_processed(video_link, temp_links_file)
                    else:
                        print(f"Failed to generate SRT for {audio_file}")
                        return {"status": "error", "message": f"Failed to generate SRT for {audio_file}"}, 500
                else:
                    print(f"Failed to process {link}")
                    return {"status": "error", "message": f"Failed to process {link}"}, 500

        return {"status": "success", "processed_videos": processed_videos}, 200

    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        return {"status": "error", "message": f"The file {file_path} was not found."}, 404
    except Exception as e:
        print(f"An error occurred while processing the file: {e}")
        return {"status": "error", "message": str(e)}, 500