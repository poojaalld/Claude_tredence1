import sys

import anthropic
from anthropic import Anthropic
from config import API_KEY
from prompts import SYSTEM_PROMPT
from logger import logger

sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252, which can't print every character Claude might use

# Keep the last ~10 user/assistant turns and drop older history beyond that,
# so a long session never grows the request past the model's context window.
MAX_MESSAGES = 20

# ----------------------------------------------------
# Initialize Claude Client
# ----------------------------------------------------

client = Anthropic(api_key=API_KEY)

print("=" * 60)
print(" Enterprise Banking AI Assistant")
print("=" * 60)
print()
print("This is a system-design conversation: Claude is acting as a Senior")
print("Solution Architect for an enterprise digital banking platform")
print("(Angular, Spring Boot, Java 21, Kafka, PostgreSQL, Redis, Docker,")
print("Kubernetes), following Clean Architecture, SOLID, and OWASP.")
print()
print("Ask for architecture decisions, service designs, or trade-offs —")
print('e.g. "Design a fraud-detection service for real-time transaction')
print(' monitoring" or "How should we handle idempotency for payment')
print(' retries?"')
print()
print("Type 'exit' to end the session.")
print("=" * 60)

logger.info("Application started")

# ----------------------------------------------------
# Get User Input
# ----------------------------------------------------

conversation = []

while True:

    query = input("You: ")

    if query.lower() == "exit":
        logger.info("Session ended by user")
        break

    conversation.append(
        {
            "role": "user",
            "content": query
        }
    )
    logger.info(f"User: {query}")

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            system=SYSTEM_PROMPT,
            max_tokens=1000,
            messages=conversation
        )
#with client.messages.stream(
#model="claude-haiku-4-5-20251001",
#max_tokens=1000,
#messages=[
 #   {'role':user,
  #   "content": query}
#])as stream:
#for text in stream.text_stream:
 #   print(text, end="", flush=True)


    
    except anthropic.AuthenticationError:
        print("\nClaude: Authentication failed — check ANTHROPIC_API_KEY in .env.\n")
        logger.error("Authentication error calling Claude API")
        conversation.pop()  # drop the unanswered user turn so history stays consistent
        continue
    except anthropic.RateLimitError:
        print("\nClaude: Rate limited — please wait a moment and try again.\n")
        logger.error("Rate limit error calling Claude API")
        conversation.pop()
        continue
    except anthropic.APIConnectionError:
        print("\nClaude: Could not reach the Claude API — check your network connection.\n")
        logger.error("Connection error calling Claude API")
        conversation.pop()
        continue
    except anthropic.APIStatusError as e:
        print(f"\nClaude: API error ({e.status_code}) — {e.message}\n")
        logger.error(f"API error calling Claude API: {e.status_code} {e.message}")
        conversation.pop()
        continue

    answer = response.content[0].text

    print("\nClaude:\n")
    print(answer)

    conversation.append(
        {
            "role": "assistant",
            "content": answer
        }
    )
    preview = answer if len(answer) <= 200 else answer[:200] + "..."
    logger.info(f"Claude ({len(answer)} chars): {preview}")

    if len(conversation) > MAX_MESSAGES:
        # Drop the oldest user/assistant pair — keeps strict user/assistant
        # alternation intact while bounding how much history gets resent.
        conversation = conversation[2:]
        logger.info("Trimmed oldest turn from conversation history")
