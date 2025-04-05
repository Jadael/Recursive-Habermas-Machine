import numpy as np
import requests
import json
from sklearn.metrics.pairwise import cosine_similarity

class OllamaEmbeddingHelper:
    """Helper class to use Ollama for embeddings if available"""
    
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.embedding_model = "nomic-embed-text" # Default embedding model
        self.available = self._check_availability()
    
    def _check_availability(self):
        """Check if Ollama is available and has an embedding model"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code != 200:
                return False
                
            # Check if an embedding model is available
            models = response.json().get("models", [])
            embedding_models = [m for m in models if "embed" in m.get("name", "").lower()]
            
            if embedding_models:
                self.embedding_model = embedding_models[0].get("name")
                return True
                
            # Try nomic-embed
            try:
                test_response = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.embedding_model, "prompt": "test"},
                    timeout=2
                )
                return test_response.status_code == 200
            except:
                return False
                
        except:
            return False
    
    def get_embedding(self, text):
        """Get embedding vector for a text using Ollama"""
        if not self.available or not text:
            return None
            
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.embedding_model, "prompt": text},
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"Error getting embedding: Status code {response.status_code}")
                return None
                
            embedding = response.json().get("embedding")
            return np.array(embedding) if embedding else None
            
        except Exception as e:
            print(f"Error getting embedding: {str(e)}")
            return None
    
    def compute_semantic_similarity(self, text1, text2):
        """Compute semantic similarity between two texts"""
        if not self.available:
            return 0.0
            
        try:
            emb1 = self.get_embedding(text1)
            emb2 = self.get_embedding(text2)
            
            if emb1 is None or emb2 is None:
                return 0.0
                
            return cosine_similarity([emb1], [emb2])[0][0]
            
        except Exception as e:
            print(f"Error computing similarity: {str(e)}")
            return 0.0
    
    def rank_by_similarity(self, target_text, candidate_texts):
        """Rank candidate texts by similarity to a target text"""
        if not self.available or not candidate_texts:
            return [(t, 0.0) for t in candidate_texts]
            
        try:
            target_emb = self.get_embedding(target_text)
            if target_emb is None:
                return [(t, 0.0) for t in candidate_texts]
                
            similarities = []
            for text in candidate_texts:
                emb = self.get_embedding(text)
                if emb is not None:
                    sim = cosine_similarity([target_emb], [emb])[0][0]
                    similarities.append((text, sim))
                else:
                    similarities.append((text, 0.0))
                    
            return sorted(similarities, key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            print(f"Error ranking by similarity: {str(e)}")
            return [(t, 0.0) for t in candidate_texts]
    
    def find_most_diverse_subset(self, texts, n=3):
        """Find a diverse subset of texts using embeddings"""
        if not self.available or len(texts) <= n:
            return texts
            
        try:
            # Get embeddings for all texts
            embeddings = []
            text_with_embeddings = []
            
            for text in texts:
                emb = self.get_embedding(text)
                if emb is not None:
                    embeddings.append(emb)
                    text_with_embeddings.append((text, emb))
                    
            if len(text_with_embeddings) <= n:
                return [t for t, _ in text_with_embeddings]
                
            # Greedy selection for maximum diversity
            selected = []
            selected_embeddings = []
            
            # Start with a random text
            import random
            first_idx = random.randint(0, len(text_with_embeddings) - 1)
            selected.append(text_with_embeddings[first_idx][0])
            selected_embeddings.append(text_with_embeddings[first_idx][1])
            
            # Remove the selected text
            remaining = text_with_embeddings.copy()
            del remaining[first_idx]
            
            # Greedily select the most diverse text
            while len(selected) < n and remaining:
                # Find the text with maximum minimum distance to already selected texts
                max_min_dist = -1
                max_idx = -1
                
                for i, (text, emb) in enumerate(remaining):
                    min_dist = float('inf')
                    for sel_emb in selected_embeddings:
                        dist = 1 - cosine_similarity([emb], [sel_emb])[0][0]  # Convert similarity to distance
                        min_dist = min(min_dist, dist)
                        
                    if min_dist > max_min_dist:
                        max_min_dist = min_dist
                        max_idx = i
                
                if max_idx >= 0:
                    selected.append(remaining[max_idx][0])
                    selected_embeddings.append(remaining[max_idx][1])
                    del remaining[max_idx]
                else:
                    break
                    
            return selected
            
        except Exception as e:
            print(f"Error finding diverse subset: {str(e)}")
            # Fall back to random selection
            return random.sample(texts, min(n, len(texts)))
