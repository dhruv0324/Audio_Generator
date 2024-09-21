from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from backend.services.process_service import process_youtube_links
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
        result = process_youtube_links(file_path, language.lower())
        if result:
            # Return a success response with metadata
            return JSONResponse(status_code=200, content={"message": "File processed successfully", "result": result})
        else:
            raise HTTPException(status_code=500, detail="Failed to process the file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {e}")
    finally:
        # Clean up the uploaded file after processing
        if os.path.exists(file_path):
            os.remove(file_path)
