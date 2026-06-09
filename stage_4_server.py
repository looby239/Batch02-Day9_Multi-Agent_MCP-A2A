import asyncio
import json
import os
import sys

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

sys.path.insert(0, os.path.dirname(__file__))

from stages.stage_4_milti_agent.main import create_graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Execute the Stage 4 Multi-Agent Graph and stream the internal states 
    (Agent interactions and tool calls) back to the client using Server-Sent Events.
    """
    async def event_generator():
        graph = create_graph()
        inputs = {
            "question": req.message,
            "law_analysis": "",
            "needs_tax": False,
            "needs_compliance": False,
            "needs_privacy": False,
            "tax_result": "",
            "compliance_result": "",
            "privacy_analysis": "",
            "final_answer": "",
        }

        try:
            async for chunk in graph.astream(inputs, stream_mode="updates"):
                for node_name, state_update in chunk.items():
                    # Check which node finished and extract what it produced
                    detail = ""
                    if node_name == "analyze_law":
                        detail = state_update.get("law_analysis", "")
                    elif node_name == "call_tax_specialist":
                        detail = state_update.get("tax_result", "")
                    elif node_name == "call_compliance_specialist":
                        detail = state_update.get("compliance_result", "")
                    elif node_name == "privacy_agent":
                        detail = state_update.get("privacy_analysis", "")
                    elif node_name == "aggregate":
                        detail = state_update.get("final_answer", "")
                    
                    # Yield event
                    event_data = {
                        "node": node_name,
                        "status": "completed",
                        "content": detail
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                    
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    print("Starting Stage 4 UI Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
