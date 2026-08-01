"""
Context Builder

Converts retrieved chunks into a prompt context.
"""


class ContextBuilder:

    def build(

            self,

            retrieved_chunks

    ):

        context = []

        for i, chunk in enumerate(

                retrieved_chunks,

                start=1

        ):

            text = f"""
Document {i}

Source : {chunk['filename']}

Chunk : {chunk['chunk_id']}

Similarity : {chunk['score']:.3f}

Content

{chunk['text']}
"""

            context.append(text)

        return "\n\n".join(context)