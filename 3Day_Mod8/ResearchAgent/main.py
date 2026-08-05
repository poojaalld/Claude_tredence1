from search import search_web
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

question = input("Ask anything: ")

results = search_web(question)

context = ""

for r in results:

    context += f"""

Title:

{r['title']}

Content:

{r['content']}

URL:

{r['url']}

"""

prompt = f"""

Use ONLY the search results below.

Question:

{question}

Search Results:

{context}

Provide a comparison.

Also cite URLs.

"""

response = client.messages.create(

model="claude-haiku-4-5-20251001",

max_tokens=800,

messages=[

{

"role":"user",

"content":prompt

}

]

)

print(response.content[0].text)