"""Wraps Claude as a DeepEval judge model.

DeepEval's metrics (GEval, AnswerRelevancyMetric, FaithfulnessMetric, ...) need an
LLM to act as the *judge* - the model that reads a test case and scores it.
DeepEval defaults to OpenAI unless you hand it a custom DeepEvalBaseLLM. This
class is that custom model: it's the thing to point at when you want to show
participants "you can plug in any LLM as the judge, including the one you're
testing" - the four methods below are the entire contract.
"""

import os

from anthropic import Anthropic
from deepeval.models import DeepEvalBaseLLM


class ClaudeJudge(DeepEvalBaseLLM):
    # claude-haiku-4-5: fast/cheap, and - unlike the newer reasoning-first
    # Claude 5 family (sonnet-5/opus-5), which rejects `temperature` outright
    # ("temperature is deprecated for this model") - it still accepts
    # temperature=0, which makes it noticeably more consistent at following
    # deepeval's "reply with strict JSON" instructions than a creative judge.
    def __init__(self, model_name: str = "claude-haiku-4-5-20251001"):
        self.model_name = model_name
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        super().__init__(model_name)

    def load_model(self):
        return self.client

    def generate(self, prompt: str) -> str:
        response = self.model.messages.create(
            model=self.model_name,
            max_tokens=1024,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self) -> str:
        return self.model_name
