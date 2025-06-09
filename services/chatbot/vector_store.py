import chromadb
from chromadb.utils import embedding_functions
from model.models import Actividades
from flask import current_app # Assuming Flask is set up with an app context

class VectorStore:
    def __init__(self):
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2" # Using the specified lightweight model
        )
        # Path for the persistent ChromaDB database, relative to the project root or where the app runs
        self.persist_directory = "services/chatbot/chroma_db_persistent"

        # Initialize the Chroma client for persistent storage
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        # Get or create the collection
        self.collection_name = "actividades_collection_light" # New name to avoid conflicts
        self.db_collection = self._get_or_create_collection() # Changed attribute name to db_collection

        # Populate the database with activities if it's empty
        self._populate_db_if_empty()

    def _get_or_create_collection(self):
        # Gets or creates a ChromaDB collection.
        return self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function
        )

    def _populate_db_if_empty(self):
        # Populates the ChromaDB collection with activities if it's currently empty.
        if self.db_collection.count() == 0:
            # This requires an active Flask app context to query the database
            # Ensure this is called within a context or the app is running
            if not current_app:
                print("Warning: Flask app context not available. Skipping DB population for VectorStore.")
                return

            with current_app.app_context():
                actividades = Actividades.query.all()
                if not actividades:
                    print("No activities found to populate the vector store.")
                    return

                documents = []
                metadatas = []
                ids = []
                for i, a in enumerate(actividades):
                    org = a.organizacion.nombre_org if hasattr(a, 'organizacion') and a.organizacion else "Sin organización"

                    discapacidades_list = []
                    if hasattr(a, 'discapacidades') and a.discapacidades:
                        discapacidades_list = [d.nombre for d in a.discapacidades if d and hasattr(d, 'nombre')]
                    discapacidades_str = ", ".join(discapacidades_list) if discapacidades_list else "No especificadas"

                    documents.append(
                        f"Actividad: {a.nombre}\n"
                        f"Descripción: {a.descripcion}\n"
                        f"Organización: {org}\n"
                        f"Discapacidades: {discapacidades_str}"
                    )
                    metadatas.append({"type": "actividad", "id_actividad": a.id_actividad})
                    # Create unique IDs for ChromaDB entries
                    ids.append(f"actividad_{a.id_actividad}_{i}")

                if documents:
                    self.db_collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    print(f"Populated vector store with {len(documents)} documents.")
                else:
                    print("No documents generated to populate vector store.")


    def search(self, query, k=3, threshold=0.65):
        # Searches the vector store for documents similar to the query.
        results = self.db_collection.query(
            query_texts=[query],
            n_results=k,
            include=['metadatas', 'documents', 'distances'] # Explicitly include what's needed
        )

        processed_results = []
        if results and results.get('documents') and results['documents'][0]:
            for i, doc_content in enumerate(results['documents'][0]):
                distance = float('inf') # Default to max distance
                if results.get('distances') and results['distances'][0] and i < len(results['distances'][0]):
                    distance = results['distances'][0][i]

                # Convert distance to a similarity score (0 to 1, higher is better)
                # For normalized embeddings (like all-MiniLM-L6-v2), score = 1 - distance
                score = 1 - distance

                if score >= threshold:
                    # Mimic the structure of Langchain's Document object for compatibility
                    # The original chatbot_route.py expects an object with 'page_content' and 'metadata' attributes.
                    metadata_item = {}
                    if results.get('metadatas') and results['metadatas'][0] and i < len(results['metadatas'][0]):
                        metadata_item = results['metadatas'][0][i]

                    doc_obj = type('Document', (object,), {
                        'page_content': doc_content,
                        'metadata': metadata_item,
                        'score': score # Adding score as it might be useful
                    })
                    processed_results.append(doc_obj)

        return processed_results
