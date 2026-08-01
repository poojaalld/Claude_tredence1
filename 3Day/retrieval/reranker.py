"""
Simple Score-Based Reranker
"""


class ScoreReranker:

    def __init__(

            self,

            threshold=0.35

    ):

        self.threshold = threshold

    def rerank(

            self,

            results

    ):

        filtered = []

        for item in results:

            if item["score"] >= self.threshold:

                filtered.append(item)

        filtered.sort(

            key=lambda x: x["score"],

            reverse=True

        )

        return filtered