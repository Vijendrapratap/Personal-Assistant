# Knowledge Base (Vector DB)

Alfred uses **Qdrant** as the Vector Database to store and retrieve knowledge.

## Qdrant Setup
The system expects a Qdrant instance running. You can run it using Docker:

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

## Environment Variables
Ensure the following variables are set in your `.env` file:
- `QDRANT_URL`: URL of the Qdrant instance (default: `http://localhost:6333`)
- `OPENAI_API_KEY`: API Key for generating embeddings.

## Ingestion
To add documents to the knowledge base:
1. Use the `/upload-knowledge` API endpoint.
2. The system will save the file to `user_data/` and trigger an ingestion process (to be implemented fully with `agno.knowledge`).

## Collections
- **alfred_knowledge**: Stores general documents and user-uploaded content.
