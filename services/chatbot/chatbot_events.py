from flask_socketio import SocketIO, emit
from flask_login import current_user
# We need to ensure VectorStore is initialized, and a way to access/initialize it.
# Assuming get_vector_store is available or can be made available similarly to chatbot_route.py
# For simplicity in this subtask, we'll assume vector_store gets initialized.
# A better approach might involve passing the app context or a shared service.

# If VectorStore is in the same directory, this should work.
from .vector_store import VectorStore

socketio = SocketIO()
vector_store_instance = None # Renamed to avoid conflict if 'vector_store' is a module name

def get_socket_vector_store():
    global vector_store_instance
    if vector_store_instance is None:
        # This initialization might need current_app if VectorStore's __init__ uses it.
        # This is a potential issue if current_app is not available here directly.
        # For the subtask, we'll proceed assuming it can be instantiated.
        # In a real app, ensure context is handled or VS is passed around.
        try:
            vector_store_instance = VectorStore()
        except Exception as e:
            print(f"Error initializing VectorStore in chatbot_events: {e}")
            # Handle error appropriately, maybe by disabling chat features that need it
            # For now, if it fails, a None check will prevent further errors.
            vector_store_instance = None
    return vector_store_instance

# Simulated LLM call function (redefined for this subtask, ideally this would be shared)
def simulated_llm_call_socket(prompt):
    return f"LLM (socket-simulado) responde: {prompt}"

@socketio.on('chat_message')
def handle_chat_message(data):
    try:
        query = data.get('query', '').strip() if data else ''
        
        if not query:
            emit('chat_error', {'message': 'Pregunta vacía'})
            return
        
        current_vs = get_socket_vector_store()

        if not current_user.is_authenticated:
            # For unauthenticated users via SocketIO
            llm_prompt_socket = f"El usuario no autenticado (via SocketIO) preguntó: '{query}'. Por favor, responde de forma general o anímale a iniciar sesión."
            llm_response_text_socket = simulated_llm_call_socket(llm_prompt_socket)
            emit('chat_response', {
                'response': llm_response_text_socket,
                'requires_auth': True
            })
            return
        
        # Authenticated user flow via SocketIO
        if not current_vs:
            emit('chat_error', {'message': 'El servicio de búsqueda no está disponible en este momento.'})
            return

        results = current_vs.search(query)
        
        llm_prompt_context_socket = "Sin contexto adicional de la base de conocimientos."
        if results:
            context_str_socket = "\n".join([doc.page_content for doc in results])
            llm_prompt_context_socket = f"Contexto de la base de conocimientos (SocketIO):\n{context_str_socket}"

        llm_prompt_socket = f"Pregunta del usuario (SocketIO): '{query}'\n\n{llm_prompt_context_socket}\n\nResponde."
        
        llm_response_text_socket = simulated_llm_call_socket(llm_prompt_socket)

        # Note: SocketIO chat interactions are typically not saved to InteraccionesChatbot
        # in this structure, as that's handled by the HTTP endpoint. If they should be,
        # similar db logic from chatbot_route.py would be needed here (requiring db access).

        emit('chat_response', {
            'response': llm_response_text_socket,
            'sources': [doc.metadata for doc in results] if results else []
        })
        
    except Exception as e:
        # Consider logging the error server-side as well
        import traceback
        print(f"Error in handle_chat_message (SocketIO): {str(e)}\n{traceback.format_exc()}")
        emit('chat_error', {'message': f'Error procesando tu pregunta vía SocketIO: {str(e)}'})
