import os
import shutil

# In deletion_service.py
def delete_temp_files_folder(temp_dir='temp_files'):
    try:
        # Check if temp_files directory exists
        if os.path.exists(temp_dir):
            # Use shutil.rmtree to delete the directory and its contents
            shutil.rmtree(temp_dir)
            return {"status": "success", "message": f"Deleted the entire folder: {temp_dir}"}
        else:
            return {"status": "error", "message": f"Folder {temp_dir} does not exist."}
    except Exception as e:
        return {"status": "error", "message": f"An error occurred while deleting the folder {temp_dir}: {e}"}
