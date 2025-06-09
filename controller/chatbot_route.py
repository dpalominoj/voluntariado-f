from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from datetime import datetime
from model.models import InteraccionesChatbot
from database.db import db
from services.chatbot.vector_store import VectorStore

chatbot_bp = Blueprint('chatbot', __name__)

vector_store = None

def get_vector_store():
    global vector_store
    if vector_store is None:
        vector_store = VectorStore() # Initialize if not already
    return vector_store

RESPUESTAS_GENERALES = [
    "Puedo ayudarte con información sobre Programas o Actividades de voluntariado.",
    "Por favor inicia sesión para acceder a todas las funciones del chatbot.",
    "No tengo información sobre ello en nuestra plataforma."
]

# Simulated LLM call function
def simulated_llm_call(prompt):
    # In a real scenario, this would involve API calls, etc.
    # For now, just prepend to the prompt or a part of it.
    return f"LLM (simulado) responde: {prompt}"

@chatbot_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Pregunta vacía'}), 400
        
        current_vector_store = get_vector_store() # Ensure vector_store is initialized

        if not current_user.is_authenticated:
            # For unauthenticated users, perhaps a simpler LLM call or a canned response
            # For now, let's assume we want them to log in for full LLM features.
            # Or, we could give a generic LLM response without vector search.
            llm_prompt = f"El usuario no autenticado preguntó: '{query}'. Por favor, responde de forma general o anímale a iniciar sesión para obtener respuestas más detalladas."
            llm_response_text = simulated_llm_call(llm_prompt)
            return jsonify({
                'response': llm_response_text, # RESPUESTAS_GENERALES[1]
                'sources': [],
                'requires_auth': True # Keep this to prompt login on client-side
            })
        
        # Authenticated user flow
        results = current_vector_store.search(query)
        
        llm_prompt_context = "Sin contexto adicional de la base de conocimientos."
        if results:
            context_str = "\n".join([doc.page_content for doc in results])
            llm_prompt_context = f"Contexto de la base de conocimientos:\n{context_str}"

        # Construct prompt for LLM
        llm_prompt = f"Pregunta del usuario: '{query}'\n\n{llm_prompt_context}\n\nPor favor, responde a la pregunta del usuario basándote en el contexto proporcionado, si es relevante. Si no, usa tu conocimiento general."
        
        # Simulated LLM call
        llm_response_text = simulated_llm_call(llm_prompt)
        
        # Save interaction
        interaccion = InteraccionesChatbot(
            id_usuario=current_user.id_usuario,
            pregunta_usuario=query,
            respuesta_chatbot=llm_response_text, # Store LLM response
            fecha=datetime.now()
        )
        db.session.add(interaccion)
        db.session.commit()
        
        return jsonify({
            'response': llm_response_text,
            'sources': [doc.metadata for doc in results] if results else []
        })
        
    except Exception as e:
        current_app.logger.error(f"Error en chatbot: {str(e)}")
        # Log the full traceback for better debugging
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Error interno del servidor procesando la solicitud del chatbot'}), 500
