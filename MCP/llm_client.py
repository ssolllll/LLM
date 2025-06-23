import httpx
import logging
from typing import Any, List, Dict


class LLMClient:
    """
    Manages communication with an Ollama server using the standard /api/chat endpoint.
    
    NOTE: This requires a modern version of Ollama that supports the /api/chat endpoint.
    If you get a 404 Not Found error, you MUST update your Ollama installation.
    """

    def __init__(self, model: str = "qwen3:latest", ollama_base_url: str = "http://localhost:11434") -> None:
        """
        Initializes the LLM client to connect to an Ollama server.

        Args:
            model: The name of the Ollama model to use (e.g., 'llama3.2:3b').
            ollama_base_url: The base URL of the Ollama server.
        """
        self.model = model
        self.ollama_url = f"{ollama_base_url}/api/chat"  # Using the standard /api/chat endpoint
        logging.info(f"LLMClient initialized for model '{self.model}' at '{self.ollama_url}'")

    def get_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Get a response from the local Ollama LLM using the /api/chat endpoint.

        Args:
            messages: A list of message dictionaries, representing the conversation history.

        Returns:
            The LLM's response as a string.

        Raises:
            httpx.RequestError: If the request to the LLM fails.
        """
        headers = {
            "Content-Type": "application/json",
        }

        # Payload structure for Ollama's /api/chat endpoint (non-streaming)
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,  # Ensure a single response object
            "options": {
                "temperature": 0.7,
                "top_p": 1,
            },
        }

        try:
            # Added a timeout for potentially long-running local models
            with httpx.Client(timeout=120.0) as client:
                logging.info(f"Sending request to Ollama with model: {self.model}")
                response = client.post(self.ollama_url, headers=headers, json=payload)
                
                # Check for any client or server errors (4xx or 5xx)
                response.raise_for_status()
                
                data = response.json()

                # As per the documentation for non-streaming chat, the content is here:
                # data -> message -> content
                if "message" in data and "content" in data["message"]:
                    return data["message"]["content"]
                else:
                    # Handle cases where the response format is unexpected
                    logging.error(f"Unexpected response format from Ollama: {data}")
                    return "Error: Received an unexpected response format from the model."

        except httpx.HTTPStatusError as e:
            # This block will now catch the 404 error if Ollama is still not updated
            status_code = e.response.status_code
            error_message = f"HTTP Status {status_code}: {e.response.text}"
            logging.error(f"Error getting LLM response from Ollama: {error_message}", exc_info=True)
            if status_code == 404:
                return (
                    "FATAL ERROR: Ollama server responded with 404 Not Found. "
                    "This means your Ollama version is too old and does not support the /api/chat endpoint. "
                    "Please update Ollama to the latest version."
                )
            return f"I encountered an HTTP error: {status_code}. Please check the logs."

        except httpx.RequestError as e:
            logging.error("Error getting LLM response from Ollama", exc_info=True)
            return (
                f"I encountered a network error connecting to Ollama: {str(e)}. "
                "Please ensure Ollama is running and accessible."
            )