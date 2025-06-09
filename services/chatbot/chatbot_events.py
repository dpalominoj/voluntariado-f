from flask_socketio import SocketIO, emit
from flask_login import current_user
from services.chatbot.vector_store import VectorStore

socketio = SocketIO()
vector_store = None

def get_vector_store():
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store

@socketio.on('chat_message')
def handle_chat_message(data):
    try:
        query = data.get('query', '').strip() if data else ''
        
        if not query:
            emit('chat_error', {'message': 'Pregunta vacía'})
            return
        
        if not current_user.is_authenticated:
            emit('chat_response', {
                'response': "Por favor inicia sesión para usar el chatbot completo.",
                'requires_auth': True
            })
            return
        
        results = vector_store.search(query)
        
        if not results:
            emit('chat_response', {
                'response': "No encontré información relevante en nuestra plataforma.",
                'sources': []
            })
            return
        
        response = "Encontramos esta información:\n\n" + "\n\n".join(
            f"{i+1}. {doc.page_content}" for i, doc in enumerate(results)
        )
        
        emit('chat_response', {
            'response': response,
            'sources': [doc.metadata for doc in results]
        })
        
    except Exception as e:
        emit('chat_error', {'message': f'Error procesando tu pregunta: {str(e)}'})
