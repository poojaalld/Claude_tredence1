"""
Claude Client

Wrapper around Anthropic Messages API
"""

from anthropic import Anthropic

from chatbot.config import ANTHROPIC_API_KEY


class ClaudeClient:

    def __init__(self):

        self.client = Anthropic(
            api_key=ANTHROPIC_API_KEY
        )

        self.model = "claude-haiku-4-5-20251001"

    def generate(

            self,

            system_prompt,

            user_prompt,

            temperature=0,

            max_tokens=1000

    ):

        response = self.client.messages.create(

            model=self.model,

            system=system_prompt,

            temperature=temperature,

            max_tokens=max_tokens,

            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]

        )

        return response.content[0].text