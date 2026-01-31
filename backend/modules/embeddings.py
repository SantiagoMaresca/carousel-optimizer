"""
CLIP embeddings generation for image similarity analysis.
"""

import asyncio
from typing import List, Dict, Optional
import numpy as np
from PIL import Image
from pathlib import Path
import hashlib
import pickle
from functools import lru_cache

# Optional ML dependencies
try:
    import torch
    import open_clip
    HAS_ML_DEPS = True
except ImportError:
    torch = None
    open_clip = None
    HAS_ML_DEPS = False

from core.logger import get_ai_logger
from app.config import settings


logger = get_ai_logger()


class EmbeddingCache:
    """Simple in-memory cache for embeddings with LRU eviction."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: Dict[str, np.ndarray] = {}
        self.access_order: List[str] = []
    
    def get(self, key: str) -> Optional[np.ndarray]:
        """Get embedding from cache."""
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key].copy()
        return None
    
    def put(self, key: str, embedding: np.ndarray) -> None:
        """Put embedding in cache with LRU eviction."""
        if key in self.cache:
            # Update existing entry
            self.cache[key] = embedding.copy()
            self.access_order.remove(key)
            self.access_order.append(key)
        else:
            # Add new entry
            if len(self.cache) >= self.max_size:
                # Remove least recently used
                lru_key = self.access_order.pop(0)
                del self.cache[lru_key]
            
            self.cache[key] = embedding.copy()
            self.access_order.append(key)
    
    def clear(self) -> None:
        """Clear all cached embeddings."""
        self.cache.clear()
        self.access_order.clear()


class EmbeddingGenerator:
    """Generates CLIP embeddings for images with caching and batch processing."""
    
    def __init__(self, model_name: str = 'ViT-B-32', pretrained: str = 'openai'):
        self.model_name = model_name
        self.pretrained = pretrained
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') if HAS_ML_DEPS else 'cpu'
        self.cache = EmbeddingCache(max_size=100)
        
        logger.info("EmbeddingGenerator initialized", 
                   model_name=model_name, 
                   pretrained=pretrained,
                   device=str(self.device),
                   has_ml_deps=HAS_ML_DEPS)
    
    async def initialize(self) -> None:
        """Load the CLIP model at startup."""
        if not HAS_ML_DEPS:
            logger.warning("ML dependencies not available, using mock embeddings")
            return
            
        logger.info("Loading CLIP model...")
        
        try:
            # Load model in thread pool to avoid blocking
            model, _, preprocess = await asyncio.to_thread(
                open_clip.create_model_and_transforms,
                self.model_name,
                pretrained=self.pretrained,
                device=self.device
            )
            
            tokenizer = await asyncio.to_thread(
                open_clip.get_tokenizer,
                self.model_name
            )
            
            # Set to evaluation mode
            model.eval()
            
            self.model = model
            self.preprocess = preprocess
            self.tokenizer = tokenizer
            
            logger.info("CLIP model loaded successfully", 
                       parameters=sum(p.numel() for p in model.parameters()))
            
        except Exception as e:
            logger.error("Failed to load CLIP model", error=str(e))
            raise RuntimeError(f"Could not initialize CLIP model: {e}")
    
    def _get_image_hash(self, image_path: Path) -> str:
        """Generate hash for image caching."""
        try:
            with open(image_path, 'rb') as f:
                # Read first and last 1KB for fast hashing
                start = f.read(1024)
                f.seek(-1024, 2)
                end = f.read(1024)
            
            content = start + end + str(image_path.stat().st_size).encode()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return str(image_path)
    
    async def generate_embedding(self, image_path: Path) -> np.ndarray:
        """
        Generate CLIP embedding for a single image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Normalized embedding vector
        """
        # Return mock embedding if ML dependencies not available
        if not HAS_ML_DEPS:
            # Generate deterministic mock embedding based on file hash
            image_hash = self._get_image_hash(image_path)
            np.random.seed(hash(image_hash) % 2**32)
            mock_embedding = np.random.normal(0, 1, 512).astype(np.float32)
            mock_embedding = mock_embedding / np.linalg.norm(mock_embedding)
            return mock_embedding
            
        if not self.model:
            raise RuntimeError("Model not initialized. Call initialize() first.")
        
        # Check cache first
        image_hash = self._get_image_hash(image_path)
        cached_embedding = self.cache.get(image_hash)
        if cached_embedding is not None:
            logger.debug("Using cached embedding", image_path=str(image_path))
            return cached_embedding
        
        logger.debug("Generating new embedding", image_path=str(image_path))
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # Generate embedding
            with torch.no_grad():
                embedding = await asyncio.to_thread(
                    self.model.encode_image,
                    image_tensor
                )
                
                # Normalize embedding
                embedding = embedding / embedding.norm(dim=-1, keepdim=True)
                embedding_np = embedding.cpu().numpy().flatten()
            
            # Cache the result
            self.cache.put(image_hash, embedding_np)
            
            logger.debug("Embedding generated", 
                        image_path=str(image_path),
                        embedding_shape=embedding_np.shape,
                        embedding_norm=float(np.linalg.norm(embedding_np)))
            
            return embedding_np
            
        except Exception as e:
            logger.error("Failed to generate embedding", 
                        image_path=str(image_path), 
                        error=str(e))
            # Return zero embedding on failure
            return np.zeros(512, dtype=np.float32)
    
    async def generate_embeddings_batch(self, image_paths: List[Path]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple images efficiently.
        
        Args:
            image_paths: List of paths to image files
            
        Returns:
            List of normalized embedding vectors
        """
        if not self.model:
            raise RuntimeError("Model not initialized. Call initialize() first.")
        
        logger.info("Generating batch embeddings", image_count=len(image_paths))
        
        # Check cache for all images
        embeddings = []
        uncached_paths = []
        uncached_indices = []
        
        for i, image_path in enumerate(image_paths):
            image_hash = self._get_image_hash(image_path)
            cached_embedding = self.cache.get(image_hash)
            
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
                logger.debug("Using cached embedding", image_path=str(image_path))
            else:
                embeddings.append(None)  # Placeholder
                uncached_paths.append(image_path)
                uncached_indices.append(i)
        
        # Process uncached images in batches
        if uncached_paths:
            logger.info("Processing uncached images", count=len(uncached_paths))
            
            try:
                # Load all uncached images
                images = []
                valid_indices = []
                
                for i, path in enumerate(uncached_paths):
                    try:
                        image = Image.open(path).convert('RGB')
                        images.append(self.preprocess(image))
                        valid_indices.append(i)
                    except Exception as e:
                        logger.error("Failed to load image", image_path=str(path), error=str(e))
                        # Will be handled below
                
                if images:
                    # Stack images into batch tensor
                    batch_tensor = torch.stack(images).to(self.device)
                    
                    # Generate embeddings in batch
                    with torch.no_grad():
                        batch_embeddings = await asyncio.to_thread(
                            self.model.encode_image,
                            batch_tensor
                        )
                        
                        # Normalize embeddings
                        batch_embeddings = batch_embeddings / batch_embeddings.norm(dim=-1, keepdim=True)
                        batch_embeddings_np = batch_embeddings.cpu().numpy()
                    
                    # Store results and cache
                    for i, embedding_np in enumerate(batch_embeddings_np):
                        if i < len(valid_indices):
                            path_idx = valid_indices[i]
                            original_idx = uncached_indices[path_idx]
                            embeddings[original_idx] = embedding_np
                            
                            # Cache the result
                            image_hash = self._get_image_hash(uncached_paths[path_idx])
                            self.cache.put(image_hash, embedding_np)
                
                # Handle failed images with zero embeddings
                for i, embedding in enumerate(embeddings):
                    if embedding is None:
                        logger.warning("Using zero embedding for failed image", 
                                     image_path=str(image_paths[i]))
                        embeddings[i] = np.zeros(512, dtype=np.float32)
                
            except Exception as e:
                logger.error("Batch embedding generation failed", error=str(e))
                # Fill remaining with zero embeddings
                for i, embedding in enumerate(embeddings):
                    if embedding is None:
                        embeddings[i] = np.zeros(512, dtype=np.float32)
        
        logger.info("Batch embedding generation completed", 
                   image_count=len(image_paths),
                   cached_count=len(image_paths) - len(uncached_paths),
                   generated_count=len(uncached_paths))
        
        return embeddings
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.cache.cache),
            "max_size": self.cache.max_size,
            "hit_rate": 0.0  # Could be implemented with counters
        }
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self.cache.clear()
        logger.info("Embedding cache cleared")


# Global embedding generator instance
embedding_generator = EmbeddingGenerator()