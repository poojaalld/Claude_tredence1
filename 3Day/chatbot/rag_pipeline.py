import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from retrieval.retrieval_pipeline import RetrievalPipeline

from chatbot.claude_client import ClaudeClient

from chatbot.rag_prompt import SYSTEM_PROMPT

from chatbot.response_formatter import PromptBuilder


class RAGPipeline:

    def __init__(self):

        self.retriever = RetrievalPipeline(

            index_path="vectorstore/indexes/faiss.index",

            metadata_path="vectorstore/indexes/metadata.pkl",

            embedding_dimension=1024

        )

        self.builder = PromptBuilder()

        self.claude = ClaudeClient()

    #####################################################

    def ask(

            self,

            question

    ):

        context = self.retriever.retrieve_context(

            question,

            top_k=5

        )

        prompt = self.builder.build(

            context,

            question

        )

        answer = self.claude.generate(

            SYSTEM_PROMPT,

            prompt

        )

        return answer