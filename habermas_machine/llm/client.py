"""
Ollama API client for the Habermas Machine.

This module handles all interactions with the Ollama API, including:
- Generating consensus candidate statements
- Predicting participant rankings
- Streaming responses with proper error handling

Copyright (C) 2025  Habermas Machine Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

import json
import logging
import requests
from typing import Optional, Callable, Dict, Any, Tuple
from threading import Event

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for interacting with the Ollama API.

    This client handles streaming responses, error recovery, and model-specific
    quirks (like DeepSeek-R1's <think> tags).
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize the Ollama client.

        Args:
            base_url: Base URL for the Ollama API (default: http://localhost:11434)
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.current_response: Optional[requests.Response] = None

    def generate_streaming(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        stop_event: Optional[Event] = None,
        on_token: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        Generate text using Ollama with streaming support.

        This method streams the response token-by-token, allowing for real-time
        display updates and early termination.

        Args:
            model: Name of the Ollama model to use (e.g., "deepseek-r1:14b")
            prompt: User prompt to send to the model
            system_prompt: Optional system prompt for instruction/context
            temperature: Sampling temperature (0.0-1.0)
                        Higher = more creative, lower = more deterministic
            top_p: Nucleus sampling parameter (0.0-1.0)
            top_k: Top-k sampling parameter (integer)
            stop_event: Threading event to signal early termination
            on_token: Callback function called for each token received
                     Signature: on_token(token: str) -> None
            on_complete: Callback function called when generation completes
                        Signature: on_complete(full_text: str) -> None

        Returns:
            The complete generated text, or None if an error occurred

        Example:
            >>> client = OllamaClient()
            >>> def print_token(token):
            ...     print(token, end='', flush=True)
            >>> text = client.generate_streaming(
            ...     model="deepseek-r1:14b",
            ...     prompt="Write a consensus statement...",
            ...     on_token=print_token
            ... )
        """
        try:
            # Prepare request payload
            payload: Dict[str, Any] = {
                "model": model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k
                }
            }

            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt

            # Make the API call
            self.current_response = requests.post(
                self.api_url,
                json=payload,
                stream=True,
                timeout=300  # 5 minute timeout
            )

            # Check response status
            if self.current_response.status_code != 200:
                logger.error(f"Ollama API error: Status {self.current_response.status_code}")
                return None

            # Stream the response
            full_response = ""
            for line in self.current_response.iter_lines():
                # Check for stop signal
                if stop_event and stop_event.is_set():
                    logger.info("Generation stopped by user")
                    break

                if line:
                    try:
                        data = json.loads(line)
                        if 'response' in data:
                            token = data['response']
                            full_response += token

                            # Call token callback if provided
                            if on_token:
                                on_token(token)

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to decode JSON from Ollama: {e}")
                        continue

            # Call completion callback if provided
            if on_complete:
                on_complete(full_response)

            return full_response

        except requests.exceptions.Timeout:
            logger.error("Ollama API request timed out")
            return None

        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Ollama API. Is Ollama running?")
            return None

        except Exception as e:
            logger.error(f"Error in generate_streaming: {e}", exc_info=True)
            return None

        finally:
            self.current_response = None

    def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40
    ) -> Optional[str]:
        """
        Generate text using Ollama (non-streaming version).

        This is a simpler interface for cases where streaming isn't needed.

        Args:
            model: Name of the Ollama model to use
            prompt: User prompt to send to the model
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter

        Returns:
            The complete generated text, or None if an error occurred
        """
        return self.generate_streaming(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k
        )

    def cancel_current_generation(self):
        """
        Cancel the currently running generation.

        This method attempts to close the current HTTP connection to stop
        an ongoing generation.
        """
        if self.current_response:
            try:
                self.current_response.close()
                logger.info("Current generation cancelled")
            except Exception as e:
                logger.warning(f"Error cancelling generation: {e}")

    def test_connection(self) -> bool:
        """
        Test if Ollama is accessible.

        Returns:
            True if Ollama is running and accessible, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> list:
        """
        List available models in Ollama.

        Returns:
            List of model names, or empty list if error occurred
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
