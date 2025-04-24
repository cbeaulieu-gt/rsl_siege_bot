
import requests
from typing import Optional

class GPT:
    """
    A class to interact with the ChatGPT API using an API token.
    """

    def __init__(self, api_token: str):
        """
        Initializes the GPT class with the provided API token.

        Args:
            api_token (str): The API token for authenticating with the ChatGPT API.
        """
        self.api_token = api_token
        self.session_id: Optional[str] = None
        self.instructions: Optional[str] = None
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def set_instructions(self, instructions: str) -> None:
        """
        Sets the baseline instructions for all requests sent to ChatGPT.

        Args:
            instructions (str): The baseline prompt to use for all requests.
        """
        self.instructions = instructions

    def send_request(self, message: str) -> str:
        """
        Sends a message to the ChatGPT API and returns the response.

        Args:
            message (str): The body of the message to send.

        Returns:
            str: The response from the ChatGPT API.
        """
        if not self.api_token:
            raise ValueError("API token is not set.")
        
        if not self.instructions:
            raise ValueError("Instructions are not set. Use set_instructions() first.")

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": self.instructions},
                {"role": "user", "content": message}
            ]
        }

        response = requests.post(self.api_url, headers=headers, json=payload)

        if response.status_code != 200:
            raise RuntimeError(f"API request failed with status code {response.status_code}: {response.text}")

        response_data = response.json()
        return response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

    def initialize_session(self) -> None:
        """
        Initializes a new chat session. If a session already exists, it disposes of the previous session.
        """
        self.session_id = None  # Dispose of the previous session
        self.session_id = "new_session"  # Placeholder for session initialization logic
