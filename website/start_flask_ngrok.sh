# Start the Flask application
python run.py &

# Wait for a few seconds to ensure the server is up
sleep 5

# Start ngrok to expose the local server
ngrok http 5000