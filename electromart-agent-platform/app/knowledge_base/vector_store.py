import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.core.config import settings
from app.core.logs import get_logger
from app.services.data_service import get_data_service
import json

logger = get_logger()


class VectorStore:
    """
    Vector store manager for document embeddings and similarity search.
    Implements RAG architecture for agent knowledge retrieval.
    """

    def __init__(self):
        """Initialize ChromaDB client and embedding function"""
        # Create persist directory
        Path(settings.CHROMA_PERSIST_DIRECTORY).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self.client = chromadb.Client(
            Settings(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                anonymized_telemetry=False
            )
        )

        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )

        # Initialize collections for different knowledge domains
        self.collections = {}
        self._initialize_collections()

        logger.info("Vector store initialized successfully")

    def _initialize_collections(self):
        """Initialize or get existing collections for different agents"""
        collection_names = [
            "products",
            "technical_support",
            "return_policy",
            "shipping_policy",
            "promotions",
            "store_info",
            "loyalty_program"
        ]

        for name in collection_names:
            try:
                collection = self.client.get_or_create_collection(
                    name=name,
                    embedding_function=self.embedding_function,
                    metadata={"hnsw:space": "cosine"}
                )
                self.collections[name] = collection
                logger.info(f"Collection '{name}' initialized with {collection.count()} documents")
            except Exception as e:
                logger.error(f"Error initializing collection '{name}': {e}")

    def populate_collections(self):
        """
        Populate all collections with data from data service.
        Should be called on first startup or when data is updated.
        """
        data_service = get_data_service()

        # Populate products collection
        self._populate_products(data_service.get_all_products())

        # Populate technical support collection
        self._populate_knowledge_base(
            "technical_support",
            data_service.get_technical_support_kb()
        )

        # Populate return policy collection
        self._populate_knowledge_base(
            "return_policy",
            data_service.get_return_policy_kb()
        )

        # Populate shipping policy collection
        self._populate_knowledge_base(
            "shipping_policy",
            data_service.get_shipping_policy_kb()
        )

        # Populate promotions collection
        self._populate_promotions(data_service.get_all_promotions())

        # Populate store info collection
        self._populate_knowledge_base(
            "store_info",
            data_service.get_store_info_kb()
        )

        # Populate loyalty program collection
        self._populate_knowledge_base(
            "loyalty_program",
            data_service.get_loyalty_program_kb()
        )

        logger.info("All collections populated successfully")

    def _populate_products(self, products: List[Dict[str, Any]]):
        """Populate products collection"""
        collection = self.collections.get("products")
        if not collection:
            logger.error("Products collection not found")
            return

        # Check if already populated
        if collection.count() > 0:
            logger.info("Products collection already populated, skipping")
            return

        documents = []
        metadatas = []
        ids = []

        for product in products:
            # Create searchable document text
            specs_text = " ".join([f"{k}: {v}" for k, v in product.get('specs', {}).items()])
            doc_text = (
                f"Product: {product.get('name', '')} "
                f"Brand: {product.get('brand', '')} "
                f"Category: {product.get('category', '')} "
                f"Price: ${product.get('price', 0)} "
                f"Description: {product.get('description', '')} "
                f"Specifications: {specs_text} "
                f"Stock: {product.get('stock_status', '')}"
            )

            documents.append(doc_text)
            metadatas.append({
                "id": product.get('id', ''),
                "name": product.get('name', ''),
                "category": product.get('category', ''),
                "brand": product.get('brand', ''),
                "price": str(product.get('price', 0)),
                "stock_status": product.get('stock_status', ''),
                "data": json.dumps(product)
            })
            ids.append(product.get('id', ''))

        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} products to vector store")

    def _populate_knowledge_base(self, collection_name: str, articles: List[Dict[str, Any]]):
        """Populate knowledge base collection"""
        collection = self.collections.get(collection_name)
        if not collection:
            logger.error(f"Collection '{collection_name}' not found")
            return

        # Check if already populated
        if collection.count() > 0:
            logger.info(f"Collection '{collection_name}' already populated, skipping")
            return

        documents = []
        metadatas = []
        ids = []

        for article in articles:
            # Create searchable document text
            doc_text = (
                f"Question: {article.get('question', '')} "
                f"Answer: {article.get('answer', '')} "
                f"Category: {article.get('category', '')} "
                f"Tags: {', '.join(article.get('tags', []))}"
            )

            documents.append(doc_text)
            metadatas.append({
                "id": article.get('id', ''),
                "question": article.get('question', ''),
                "category": article.get('category', ''),
                "tags": json.dumps(article.get('tags', [])),
                "data": json.dumps(article)
            })
            ids.append(article.get('id', ''))

        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} articles to '{collection_name}' collection")

    def _populate_promotions(self, promotions: List[Dict[str, Any]]):
        """Populate promotions collection"""
        collection = self.collections.get("promotions")
        if not collection:
            logger.error("Promotions collection not found")
            return

        # Check if already populated
        if collection.count() > 0:
            logger.info("Promotions collection already populated, skipping")
            return

        documents = []
        metadatas = []
        ids = []

        for promo in promotions:
            # Create searchable document text
            doc_text = (
                f"Promotion: {promo.get('name', '')} "
                f"Description: {promo.get('description', '')} "
                f"Code: {promo.get('code', '')} "
                f"Discount: {promo.get('discount_value', 0)}% "
                f"Categories: {', '.join(promo.get('applicable_categories', []))} "
                f"Status: {promo.get('status', '')} "
                f"Requirements: {promo.get('requirements', '')}"
            )

            documents.append(doc_text)
            metadatas.append({
                "id": promo.get('id', ''),
                "name": promo.get('name', ''),
                "code": promo.get('code', ''),
                "status": promo.get('status', ''),
                "data": json.dumps(promo)
            })
            ids.append(promo.get('id', ''))

        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} promotions to vector store")

    def query_collection(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query a specific collection for relevant documents.

        Args:
            collection_name: Name of the collection to query
            query_text: Query text for similarity search
            n_results: Number of results to return
            where_filter: Optional metadata filter

        Returns:
            Query results with documents, metadatas, and distances
        """
        collection = self.collections.get(collection_name)
        if not collection:
            logger.error(f"Collection '{collection_name}' not found")
            return {"documents": [], "metadatas": [], "distances": []}

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_filter
            )
            return results
        except Exception as e:
            logger.error(f"Error querying collection '{collection_name}': {e}")
            return {"documents": [], "metadatas": [], "distances": []}

    def search_products(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search products using semantic similarity.

        Args:
            query: Search query
            n_results: Number of results to return

        Returns:
            List of relevant products
        """
        results = self.query_collection("products", query, n_results)
        products = []

        if results.get("metadatas") and results["metadatas"][0]:
            for metadata in results["metadatas"][0]:
                try:
                    product_data = json.loads(metadata.get("data", "{}"))
                    products.append(product_data)
                except json.JSONDecodeError:
                    logger.error("Error decoding product data")

        return products

    def search_knowledge_base(
        self,
        query: str,
        collection_name: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base using semantic similarity.

        Args:
            query: Search query
            collection_name: KB collection to search
            n_results: Number of results to return

        Returns:
            List of relevant knowledge base articles
        """
        results = self.query_collection(collection_name, query, n_results)
        articles = []

        if results.get("metadatas") and results["metadatas"][0]:
            for metadata in results["metadatas"][0]:
                try:
                    article_data = json.loads(metadata.get("data", "{}"))
                    articles.append(article_data)
                except json.JSONDecodeError:
                    logger.error("Error decoding article data")

        return articles

    def get_collection_count(self, collection_name: str) -> int:
        """Get document count for a collection"""
        collection = self.collections.get(collection_name)
        return collection.count() if collection else 0


# Global vector store instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """
    Get or create the global vector store instance.

    Returns:
        VectorStore: Global vector store instance
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        # Populate on first access if empty
        if _vector_store.get_collection_count("products") == 0:
            _vector_store.populate_collections()
    return _vector_store


def initialize_vector_store():
    """Initialize and populate vector store on startup"""
    global _vector_store
    _vector_store = VectorStore()
    _vector_store.populate_collections()
    logger.info("Vector store initialized and populated")
