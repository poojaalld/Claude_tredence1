from .retriever import Retriever
from .reranker import ScoreReranker
from .context_builder import ContextBuilder


class RetrievalPipeline:

    def __init__(

            self,

            index_path,

            metadata_path,

            embedding_dimension

    ):

        self.retriever = Retriever(

            index_path,

            metadata_path,

            embedding_dimension

        )

        self.reranker = ScoreReranker()

        self.builder = ContextBuilder()

    ##################################################

    def retrieve_context(

            self,

            question,

            top_k=5

    ):

        results = self.retriever.retrieve(

            question,

            top_k

        )

        results = self.reranker.rerank(

            results

        )

        context = self.builder.build(

            results

        )

        return context
