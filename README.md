<<<<<<< HEAD
# Audio_Generator
=======
uvicorn main:app --workers 4 --port 8080

cd frontend
streamlit run app.py --server.port 8501

cd /path/to/your/Audio-Data-Generator
docker build -t audio_gen .
docker run -d --name audio_gen -p 8080:8080 -p 8501:8501 audio_gen
docker start audio_gen
docker logs -f audio_gen
# Optional: Check running containers
docker ps
# Optional: Stop the container
docker stop audio_gen
# Optional: Remove the container
docker rm audio_gen

http://localhost:8080
http://localhost:8501


uvicorn backend.main:app --host 0.0.0.0 --port 8080
>>>>>>> b668e41 (Final)
