from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import process

app = FastAPI()

origins = [
    "http://localhost",  # Frontend running locally
    "http://localhost:8501",  # Streamlit default port
    "http://192.168.1.100:8501",  # IP of the Docker container running Streamlit
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router for processing
app.include_router(process.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the File Processing API!"}

