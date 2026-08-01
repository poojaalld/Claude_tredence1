class PromptBuilder:

    def build(

            self,

            context,

            question

    ):

        prompt = f"""
Use ONLY the context below.

====================

CONTEXT

{context}

====================

QUESTION

{question}

====================

Provide:

1. Answer

2. Source Documents

3. Confidence

"""

        return prompt