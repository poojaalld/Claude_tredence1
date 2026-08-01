from anthropic import Anthropic
from config import API_KEY
from prompts import SYSTEM_PROMPT

# ----------------------------------------------------
# Initialize Claude Client
# ----------------------------------------------------

client = Anthropic(api_key=API_KEY)

print("=" * 60)
print(" Enterprise Banking AI Assistant")
print("=" * 60)

# ----------------------------------------------------
# Get User Input
# ----------------------------------------------------

conversation = []

while True:

    query = input("You: ")

    if query.lower() == "exit":
        break

    conversation.append(
        {
            "role": "user",
            "content": query
        }
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        system=SYSTEM_PROMPT,
        max_tokens=1000,
        messages=conversation
    )

    answer = response.content[0].text

    print("\nClaude:\n")
    print(answer)

    conversation.append(
        {
            "role": "assistant",
            "content": answer
        }
    )