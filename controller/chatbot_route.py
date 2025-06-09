from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from datetime import datetime
from model.models import InteraccionesChatbot
from database.db import db
from services.chatbot.vector_store import VectorStore

chatbot_bp = Blueprint('chatbot', __name__)

vector_store = VectorStore()

RESPUESTAS_GENERALES = [
    "Puedo ayudarte con información sobre Programas o Actividades de voluntariado.",
    "Por favor inicia sesión para acceder a todas las funciones del chatbot.",
    "No tengo información sobre ello en nuestra plataforma."
]

@chatbot_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Pregunta vacía'}), 400
        
        if not current_user.is_authenticated:
            return jsonify({
                'response': RESPUESTAS_GENERALES[1],
                'sources': [],
                'requires_auth': True
            })
        
        results = vector_store.search(query)
        
        if not results:
            return jsonify({
                'response': RESPUESTAS_GENERALES[2],
                'sources': []
            })
        
        response = "Encontramos esta información:\n\n" + "\n\n".join(
            f"{i+1}. {doc.page_content}\n(ID: {doc.metadata['id']}, Tipo: {doc.metadata['type']})"
            for i, doc in enumerate(results)
        )
        
        interaccion = InteraccionesChatbot(
            id_usuario=current_user.id_usuario,
            pregunta_usuario=query,
            respuesta_chatbot=response,
            fecha=datetime.now()
        )
        db.session.add(interaccion)
        db.session.commit()
        
        return jsonify({
            'response': response,
            'sources': [doc.metadata for doc in results]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error en chatbot: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500
