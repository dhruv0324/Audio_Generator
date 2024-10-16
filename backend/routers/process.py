from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from backend.services.process_service import process_youtube_links
from backend.services.transfer_service import transfer_data
from backend.services.deletion_service import delete_temp_files_folder
from backend.services.wordcloud_service import generate_wordcloud
from backend.services.histogram_service import generate_histograms
from backend.services.fetch_service import fetch_video_folders, fetch_language_folders
import os

router = APIRouter()

# Define the route to process YouTube links from a file
@router.post("/process/")
async def process_file(file: UploadFile = File(...), language: str = Form(...)):
    # Define where to store the uploaded file temporarily
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)  # Ensure the upload directory exists
    
    # Save the uploaded file to the upload directory
    file_path = os.path.join(upload_dir, file.filename)
    try:
        with open(file_path, "wb") as f:
            f.write(file.file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")
    
    # Ensure the language is valid
    supported_languages = ["english", "hindi", "german"]
    if language.lower() not in supported_languages:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}. Supported languages are {supported_languages}")

    # Call the service to process the file
    try:
        result, status_code = process_youtube_links(file_path, language.lower())
        if status_code == 200:
            # Extract unique_id from the result if present
            unique_id = result.get("unique_id", None)
            # Return a success response with metadata and unique_id
            return JSONResponse(status_code=200, content={
                "message": "File processed successfully",
                "result": result,
                "unique_id": unique_id  # Include the unique_id in the response
            })
        else:
            raise HTTPException(status_code=500, detail=f"Error: {result.get('message', 'Failed to process the file.')}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {e}")
    finally:
        # Clean up the uploaded file after processing
        if os.path.exists(file_path):
            os.remove(file_path)
            
                        
# Define the route to transfer data from temp_files to audio_files
@router.post("/transfer/")
async def transfer_data_files(request: Request):
    try:
        body = await request.json()
        unique_id = body.get("unique_id")

        if not unique_id:
            raise HTTPException(status_code=400, detail="Unique ID is required")

        # Now pass the unique_id to the transfer_data function
        result = transfer_data(unique_id)
        if result["status"] == "success":
            return JSONResponse(status_code=200, content=result)
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transferring data: {e}")

# Define the route to delete the temp_files folder
@router.delete("/delete_temp/")
async def delete_temp_folder(request: Request):
    try:
        body = await request.json()
        unique_id = body.get("unique_id")

        if not unique_id:
            raise HTTPException(status_code=400, detail="Unique ID is required")

        # Now pass the unique_id to the delete_temp_files_folder function
        result = delete_temp_files_folder(unique_id)
        if result["status"] == "success":
            return JSONResponse(status_code=200, content=result)
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting temp_files folder: {e}")
    
BASE_DIR = "audio_files"
@router.get("/wordcloud/")
async def get_wordcloud(language: str, video_code: str = None):
    # Construct the directory path based on the presence of video_code
    if video_code:
        # Use the specific video folder
        language_path = os.path.join(BASE_DIR, language.lower(), video_code)
    else:
        # Use the language folder
        language_path = os.path.join(BASE_DIR, language.lower())
    
    wordcloud_image = generate_wordcloud(language_path, language.lower())
    
    if wordcloud_image is None:
        raise HTTPException(status_code=404, detail="Base directory does not exist.")
    
    return wordcloud_image

@router.get("/histograms/")
async def get_histograms(language: str, video_code: str = None):
    # Construct the directory path based on the presence of video_code
    if video_code:
        # Use the specific video folder
        language_path = os.path.join(BASE_DIR, language.lower(), video_code)
    else:
        # Use the language folder
        language_path = os.path.join(BASE_DIR, language.lower())
    
    img_buffer = generate_histograms(language_path, language.lower())
    
    if img_buffer is None:
        return {"error": "Base directory not found"}
    
    return StreamingResponse(img_buffer, media_type="image/png")

# Endpoint to fetch video folder names for a given language
@router.get("/video_folders/")
async def get_video_folders(language: str):
    try:
        video_folders = fetch_video_folders(language.lower(), BASE_DIR)
        if "error" in video_folders:
            raise HTTPException(status_code=404, detail=video_folders["error"])
        return {"video_folders": video_folders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching video folders: {e}")

# Endpoint to fetch language folder names
@router.get("/language_folders/")
async def get_language_folders():
    try:
        language_folders = fetch_language_folders(BASE_DIR)
        if "error" in language_folders:
            raise HTTPException(status_code=404, detail=language_folders["error"])
        return {"language_folders": language_folders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching language folders: {e}")