from openai import OpenAI
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from datetime import datetime
from model.models import InteraccionesChatbot
from database.db import db

# OPEN API Key
USER_PROVIDED_OPENAI_KEY = "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"

openai_client = None
api_key = USER_PROVIDED_OPENAI_KEY
if api_key:
    openai_client = OpenAI(api_key=api_key)
else:
    print("CRITICAL: OpenAI API Key not provided. Chatbot will not function.")

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        if not openai_client:
            current_app.logger.error("OpenAI client not initialized. Missing OPENAI_API_KEY.")
            return jsonify({'error': 'Chatbot no está configurado correctamente. Falta la clave API.'}), 503

        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Pregunta vacía'}), 400
        
        if not current_user.is_authenticated:
            return jsonify({
                'response': "Por favor inicia sesión para acceder a todas las funciones del chatbot.",
                'sources': [],
                'requires_auth': True
            })

        system_message = (
            "Eres KONECTAi, un asistente virtual amigable y servicial para una plataforma de voluntariado inclusivo. "
            "Tu objetivo es responder preguntas generales sobre la plataforma y el voluntariado de manera conversacional. "
            "Ya no tienes acceso directo a la base de datos de actividades específicas, así que si te preguntan por detalles muy concretos de programas que no conocerías de forma general, indica amablemente que no puedes buscar en la base de datos pero puedes ofrecer ayuda general sobre voluntariado o la plataforma. "
            "Mantén un tono conversacional y evita sonar como un robot. Sé conciso pero completo."
        )

        try:
            completion = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": query} # Pass the user's query directly
                ],
                temperature=0.7,
                max_tokens=250
            )
            llm_response = completion.choices[0].message.content.strip()
        except Exception as e:
            current_app.logger.error(f"OpenAI API call failed: {str(e)}")
            return jsonify({'error': 'Error al comunicarse con el servicio de IA. Inténtalo más tarde.'}), 500
        
        interaccion = InteraccionesChatbot(
            id_usuario=current_user.id_usuario,
            pregunta_usuario=query,
            respuesta_chatbot=llm_response,
            fecha=datetime.now()
        )
        db.session.add(interaccion)
        db.session.commit()
        
        return jsonify({
            'response': llm_response,
            'sources': [],
            'requires_auth': False 
        })
        
    except Exception as e:
        current_app.logger.error(f"Error en chatbot: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500
