from flask_socketio import SocketIO, emit
from flask import current_app, request as flask_request, session
import requests # For making HTTP requests to the /api/chat endpoint

# This socketio instance should be initialized with the Flask app (e.g., socketio.init_app(app) in main.py)
socketio = SocketIO()

@socketio.on('chat_message')
def handle_chat_message(data):
    try:
        query = data.get('query', '').strip() if data else ''
        
        if not query:
            emit('chat_error', {'message': 'Pregunta vacía'})
            return

        # The /api/chat endpoint is responsible for all logic including authentication.
        # This handler will simply proxy the request and response.

        # Cookies from the original request (that established SocketIO) should be forwarded.
        cookies = flask_request.cookies
        
        # Construct the full URL for the /api/chat endpoint.
        # flask_request.url_root provides the base URL (e.g., 'http://127.0.0.1:5000/')
        # Ensure 'api/chat' is appended correctly, avoiding double slashes if url_root ends with one.
        base_url = flask_request.url_root
        if base_url.endswith('/'):
            target_url = base_url + 'api/chat'
        else:
            target_url = base_url + '/api/chat'

        # Make the POST request to the /api/chat endpoint
        # It's important that the /api/chat endpoint can handle sessions/authentication based on these cookies.
        response = requests.post(target_url, json={'query': query}, cookies=cookies, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        
        chat_response_data = response.json()
        
        # Forward the exact JSON response from /api/chat to the client via SocketIO
        emit('chat_response', chat_response_data)

    except requests.exceptions.Timeout:
        current_app.logger.error(f"Chat API request timed out: {target_url}")
        emit('chat_error', {'message': 'La solicitud al chatbot tardó demasiado.'})
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Chat API request failed with HTTPError: {str(e)} - Response: {e.response.text if e.response else 'No response text'}")
        # Try to parse the JSON error from the API if possible, and forward it.
        # This allows the client to potentially receive structured error messages from the API.
        if e.response is not None:
            try:
                error_data = e.response.json()
                emit('chat_response', error_data) # Forward API's own error structure if it's a valid JSON response
                return # Avoid emitting the generic chat_error below
            except ValueError: # If response is not JSON or cannot be parsed
                pass # Fall through to generic error
        emit('chat_error', {'message': 'Error del servidor de chat al procesar la solicitud.'})
    except requests.exceptions.RequestException as e: # Catch other request-related errors (e.g., connection error)
        current_app.logger.error(f"Chat API request failed: {str(e)}")
        emit('chat_error', {'message': 'Error de comunicación con el servidor de chat.'})
    except Exception as e:
        # Log any other unexpected errors
        current_app.logger.error(f"Unexpected error in chat event handler: {str(e)}", exc_info=True)
        emit('chat_error', {'message': 'Ocurrió un error inesperado.'})
