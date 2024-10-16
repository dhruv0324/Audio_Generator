import os

def fetch_language_folders(base_dir):
    # Check if the base directory exists
    if not os.path.exists(base_dir):
        return {"error": "Base directory not found."}
    
    # Get a list of all subfolders (language folders) inside the base directory
    language_folders = [folder for folder in os.listdir(base_dir) 
                        if os.path.isdir(os.path.join(base_dir, folder))]
    
    # Return the list of language folder names
    return language_folders

import os

def fetch_video_folders(language, base_dir):
    # Construct the path to the language folder
    language_folder_path = os.path.join(base_dir, language.lower())
    
    # Check if the language folder exists
    if not os.path.exists(language_folder_path):
        return {"error": f"Language folder '{language}' not found."}

    # Get a list of all subfolders (video codes) inside the language folder
    video_folders = [folder for folder in os.listdir(language_folder_path) 
                     if os.path.isdir(os.path.join(language_folder_path, folder))]

    # Return the list of video folder names
    return video_folders