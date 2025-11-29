"""
Ollama API client for LLM inference.

Provides both streaming and non-streaming interfaces to local Ollama models.
Supports both prompted models (instruct/chat-tuned) and base models (for finetuning).
"""

import json
import re
import requests
from typing import Optional, Dict, Any, Iterator, Callable


class OllamaClient:
    """
    Client for interacting with Ollama API.

    Supports two modes:
    1. Prompted models: Use with instruct or chat-tuned models (e.g., deepseek-r1, llama3.1)
    2. Base models: Use with base models for finetuning workflows (e.g., Comma-v0.1)
    """

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "deepseek-r1:14b"):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            default_model: Default model to use for generation
        """
        self.base_url = base_url
        self.default_model = default_model
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if Ollama is available and responsive."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> list:
        """
        Get list of available models.

        Returns:
            List of model names, or empty list if unavailable
        """
        if not self.available:
            return []

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m.get("name") for m in models]
        except:
            pass

        return []

    def generate(self,
                prompt: str,
                model: Optional[str] = None,
                stream: bool = False,
                temperature: float = 0.7,
                top_p: float = 0.9,
                top_k: int = 40,
                max_tokens: Optional[int] = None,
                stop: Optional[list] = None,
                callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Generate text from prompt (non-streaming or with callback).

        Args:
            prompt: Input prompt text
            model: Model name (uses default if None)
            stream: Whether to stream response
            temperature: Sampling temperature (0.0 to 2.0)
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling parameter
            max_tokens: Maximum tokens to generate (None = model default)
            stop: List of stop sequences
            callback: Optional callback function for streaming (receives each token)

        Returns:
            Complete generated text

        Example:
            >>> client = OllamaClient()
            >>> response = client.generate("Explain quantum computing", temperature=0.2)
            >>> print(response)
        """
        if not self.available:
            raise ConnectionError("Ollama is not available")

        model = model or self.default_model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k
            }
        }

        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        if stop:
            payload["stop"] = stop

        try:
            if stream and callback:
                # Streaming mode with callback
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    stream=True,
                    timeout=120
                )

                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if 'response' in data:
                                token = data['response']
                                full_response += token
                                callback(token)
                        except json.JSONDecodeError:
                            continue

                return full_response

            else:
                # Non-streaming mode
                payload["stream"] = False
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=120
                )

                if response.status_code == 200:
                    return response.json().get("response", "")
                else:
                    raise RuntimeError(f"Ollama API error: {response.status_code}")

        except requests.exceptions.Timeout:
            raise TimeoutError("Ollama request timed out")
        except Exception as e:
            raise RuntimeError(f"Ollama generation error: {str(e)}")

    def generate_stream(self,
                       prompt: str,
                       model: Optional[str] = None,
                       temperature: float = 0.7,
                       top_p: float = 0.9,
                       top_k: int = 40,
                       stop: Optional[list] = None) -> Iterator[str]:
        """
        Generate text with streaming (returns iterator).

        Args:
            prompt: Input prompt text
            model: Model name (uses default if None)
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling parameter
            stop: List of stop sequences

        Yields:
            Individual tokens as they're generated

        Example:
            >>> client = OllamaClient()
            >>> for token in client.generate_stream("Write a haiku"):
            ...     print(token, end="", flush=True)
        """
        if not self.available:
            raise ConnectionError("Ollama is not available")

        model = model or self.default_model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k
            }
        }

        if stop:
            payload["stop"] = stop

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=120
            )

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if 'response' in data:
                            yield data['response']
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            raise RuntimeError(f"Ollama streaming error: {str(e)}")

    def clean_response(self, response: str, model: Optional[str] = None) -> str:
        """
        Clean model-specific artifacts from response.

        Some models (like DeepSeek-R1) include reasoning tags that should be stripped.

        Args:
            response: Raw model response
            model: Model name (for model-specific cleaning)

        Returns:
            Cleaned response text
        """
        # DeepSeek-R1 specific: Remove <think>...</think> tags
        if model and "deepseek" in model.lower():
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)

        return response.strip()

    def generate_json(self,
                     prompt: str,
                     model: Optional[str] = None,
                     temperature: float = 0.2,
                     max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Generate JSON response with retry logic.

        Attempts to extract valid JSON from model response, with multiple retries if needed.

        Args:
            prompt: Input prompt (should request JSON output)
            model: Model name (uses default if None)
            temperature: Sampling temperature (lower is more deterministic)
            max_retries: Maximum number of retry attempts

        Returns:
            Parsed JSON dict, or None if all attempts fail

        Example:
            >>> client = OllamaClient()
            >>> prompt = 'Return JSON: {"ranking": [1,2,3]}'
            >>> result = client.generate_json(prompt, temperature=0.1)
            >>> print(result['ranking'])
        """
        for attempt in range(max_retries):
            try:
                response = self.generate(prompt, model=model, temperature=temperature)

                # Try to extract JSON from response
                match = re.search(r'({[\s\S]*?})', response)
                if match:
                    json_str = match.group(1)
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        # Try ast.literal_eval as fallback
                        import ast
                        try:
                            return ast.literal_eval(json_str)
                        except:
                            continue

            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"JSON generation failed after {max_retries} attempts: {e}")
                continue

        return None

    def test_connection(self) -> bool:
        """
        Test connection to Ollama and verify default model is available.

        Returns:
            True if connected and model available, False otherwise
        """
        if not self.available:
            return False

        models = self.list_models()
        return self.default_model in models


# Convenience functions for backward compatibility

def ollama_generate(prompt: str,
                   model: str = "deepseek-r1:14b",
                   base_url: str = "http://localhost:11434",
                   temperature: float = 0.7,
                   stream: bool = False) -> str:
    """
    Simple generation function (backward compatible with existing code).

    Args:
        prompt: Input prompt
        model: Model name
        base_url: Ollama API URL
        temperature: Sampling temperature
        stream: Whether to stream (ignored, always non-streaming)

    Returns:
        Generated text
    """
    client = OllamaClient(base_url=base_url, default_model=model)
    return client.generate(prompt, temperature=temperature)


def ollama_generate_json(prompt: str,
                         model: str = "deepseek-r1:14b",
                         base_url: str = "http://localhost:11434",
                         temperature: float = 0.2,
                         max_retries: int = 3) -> Optional[Dict]:
    """
    Simple JSON generation function (backward compatible).

    Args:
        prompt: Input prompt requesting JSON
        model: Model name
        base_url: Ollama API URL
        temperature: Sampling temperature
        max_retries: Number of retry attempts

    Returns:
        Parsed JSON dict or None
    """
    client = OllamaClient(base_url=base_url, default_model=model)
    return client.generate_json(prompt, model=model, temperature=temperature, max_retries=max_retries)
