"""End-to-end test client for the Legal Multi-Agent System.

Sends a legal question to the Customer Agent and prints the response.
"""

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

CUSTOMER_AGENT_URL = os.getenv("CUSTOMER_AGENT_URL", "http://localhost:10100")

QUESTION = (
    "If a company breaks a contract and avoids taxes, "
    "what are the legal and regulatory consequences?"
)


async def main() -> None:
    print(f"Connecting to Customer Agent at {CUSTOMER_AGENT_URL}")
    print("Type your legal questions below. Type 'quit' or 'exit' to stop.")
    print("-" * 60)

    from a2a.types import AgentCard, Message, Part, Role, TextPart, MessageSendParams
    from a2a.types import SendMessageRequest
    from a2a.client import A2AClient
    from uuid import uuid4

    async with httpx.AsyncClient(
        timeout=300.0, 
        headers={"X-API-Key": os.getenv("A2A_API_KEY", "secret-123")}
    ) as http_client:
        # Resolve agent card
        card_url = f"{CUSTOMER_AGENT_URL}/.well-known/agent.json"
        try:
            card_resp = await http_client.get(card_url)
            card_resp.raise_for_status()
        except Exception as e:
            print(f"ERROR: Could not reach Customer Agent at {card_url}")
            print(f"  {e}")
            print("Make sure all services are running (./start_all.sh)")
            sys.exit(1)

        agent_card = AgentCard.model_validate(card_resp.json())
        print(f"Connected to agent: {agent_card.name} v{agent_card.version}")
        print("-" * 60)

        client = A2AClient(httpx_client=http_client, agent_card=agent_card)

        # Generate a stable context ID for this session so the Customer Agent remembers
        session_id = str(uuid4())

        while True:
            try:
                question = input("\nUser> ")
            except EOFError:
                break
                
            if not question.strip():
                continue
            if question.strip().lower() in ["quit", "exit"]:
                break

            message = Message(
                role=Role.user,
                parts=[Part(root=TextPart(text=question))],
                message_id=str(uuid4()),
            )
            request = SendMessageRequest(
                id=session_id, # Use session_id as the request id to keep context
                params=MessageSendParams(message=message),
            )

            print("Agent> (thinking...)")
            response = await client.send_message(request)

            # Parse response
            result_text = ""
            if hasattr(response, "root"):
                root = response.root
                if hasattr(root, "result"):
                    result = root.result
                    if hasattr(result, "artifacts") and result.artifacts:
                        for artifact in result.artifacts:
                            for part in artifact.parts:
                                p = part.root if hasattr(part, "root") else part
                                if hasattr(p, "text"):
                                    result_text += p.text
                    elif hasattr(result, "parts") and result.parts:
                        for part in result.parts:
                            p = part.root if hasattr(part, "root") else part
                            if hasattr(p, "text"):
                                result_text += p.text

            if result_text:
                print(f"Agent> {result_text}")
            else:
                print("Agent> [No text response received]")

if __name__ == "__main__":
    asyncio.run(main())