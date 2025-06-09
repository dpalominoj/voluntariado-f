# from langchain.vectorstores import Chroma
# no funciona: from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from model.models import Actividades, Organizaciones, Discapacidades
from flask import current_app

class VectorStore:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.db = self._create_db()

    def _create_db(self):
        with current_app.app_context():
            actividades = Actividades.query.all()
            documents = []
            metadatas = []
            for a in actividades:
                # Obtener organización relacionada si existe
                org = a.organizacion.nombre_org if hasattr(a, 'organizacion') and a.organizacion else "Sin organización"
                # Obtener discapacidades relacionadas si existen
                discapacidades = ", ".join([d.nombre for d in a.discapacidades]) if hasattr(a, 'discapacidades') and a.discapacidades else "No especificadas"
                # Puedes agregar más campos relevantes aquí si lo deseas
                documents.append(
                    f"Actividad: {a.nombre}\n"
                    f"Descripción: {a.descripcion}\n"
                    f"Organización: {org}\n"
                    f"Discapacidades: {discapacidades}"
                )
                metadatas.append({"type": "actividad", "id": a.id_actividad})
            return Chroma.from_texts(
                texts=documents,
                embedding=self.embeddings,
                metadatas=metadatas,
                persist_directory="app/services/chatbot/chroma_db"
            )

    def search(self, query, k=3, threshold=0.65):
        results = self.db.similarity_search_with_score(query, k=k)
        return [doc for doc, score in results if score >= threshold]
