import os
import shutil
import json

# Function to update metadata filepath
def update_metadata(temp_dir):
    for language in os.listdir(temp_dir):
        language_dir = os.path.join(temp_dir, language)
        if os.path.isdir(language_dir):
            for video_folder in os.listdir(language_dir):
                metadata_file_path = os.path.join(language_dir, video_folder, 'metadata.json')
                if os.path.exists(metadata_file_path):
                    with open(metadata_file_path, 'r+', encoding='utf-8') as metadata_file:
                        # Read all lines from metadata.json
                        lines = metadata_file.readlines()
                        # Update each line in metadata.json
                        updated_lines = []
                        for line in lines:
                            metadata = json.loads(line)
                            metadata['audio_filepath'] = metadata['audio_filepath'].replace(temp_dir, 'audio_files')
                            updated_lines.append(json.dumps(metadata, ensure_ascii=False))
                        # Write updated lines back to the file
                        metadata_file.seek(0)
                        metadata_file.truncate()  # Clear the file content
                        for updated_line in updated_lines:
                            metadata_file.write(updated_line + '\n')

# Function to move content from temp_files/temp_links.txt to audio_files/processed_links.txt
def transfer_processed_links(temp_links_file, processed_links_file):
    try:
        # Read from temp_links.txt
        if os.path.exists(temp_links_file):
            with open(temp_links_file, 'r') as temp_file:
                temp_links = temp_file.readlines()

            # If there are links to transfer
            if temp_links:
                # Append to processed_links.txt
                with open(processed_links_file, 'a') as processed_file:
                    processed_file.writelines(temp_links)

                # Delete temp_links.txt after transferring
                os.remove(temp_links_file)
                print(f"Successfully transferred links from {temp_links_file} to {processed_links_file} and deleted the temporary file.")
            else:
                print(f"No links to transfer from {temp_links_file}.")
        else:
            print(f"{temp_links_file} does not exist.")
    except Exception as e:
        print(f"An error occurred while transferring links: {e}")
        
        
# Function to transfer folders from temp_files to audio_files
def transfer_folders(temp_dir, main_dir):
    try:
        # Get the list of language folders inside temp_files
        language_folders = [folder for folder in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, folder))]

        for language in language_folders:
            temp_language_path = os.path.join(temp_dir, language)
            main_language_path = os.path.join(main_dir, language)

            # Check if the language folder already exists in audio_files
            if os.path.exists(main_language_path):
                # If the language folder exists, move only the video folders inside it
                for video_folder in os.listdir(temp_language_path):
                    temp_video_path = os.path.join(temp_language_path, video_folder)
                    main_video_path = os.path.join(main_language_path, video_folder)
                    
                    # Move video folder from temp_files to audio_files
                    shutil.move(temp_video_path, main_video_path)
                    print(f"Moved {video_folder} from {temp_language_path} to {main_language_path}.")

                # Remove the empty language folder from temp_files
                os.rmdir(temp_language_path)
                print(f"Deleted empty folder {temp_language_path}.")
            else:
                # If the language folder doesn't exist, move the entire language folder
                shutil.move(temp_language_path, main_language_path)
                print(f"Moved {language} folder to {main_dir}.")

        # After moving all language folders, remove the temp_files folder if it's empty
        if not os.listdir(temp_dir):
            os.rmdir(temp_dir)
            print(f"Deleted empty folder {temp_dir}.")

    except Exception as e:
        print(f"An error occurred while transferring folders: {e}")


def transfer_data(unique_id):
    try:
        # Define paths
        temp_links_file = os.path.join(f'temp_files_{unique_id}', 'temp_links.txt')
        processed_links_file = os.path.join('audio_files', 'processed_links.txt')
        temp_dir = f'temp_files_{unique_id}'
        main_dir = 'audio_files'

        # Step 1: Update metadata filepath
        update_metadata(temp_dir)

        # Step 2: Transfer processed links
        transfer_processed_links(temp_links_file, processed_links_file)

        # Step 3: Transfer folders
        transfer_folders(temp_dir, main_dir)

        return {"status": "success", "message": "Data transferred successfully."}
    except Exception as e:
        return {"status": "error", "message": f"An error occurred during data transfer: {e}"}