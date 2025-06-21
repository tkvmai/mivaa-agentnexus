from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import json
from pathlib import Path
from typing import List, Optional, Dict
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Config, load_config
from main import SubsurfaceDataPlatform

app = FastAPI(title="Subsurface Data Management Platform API")

# In-memory storage for conversation histories
conversations: Dict[str, List[Dict[str, str]]] = {}

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://ddns.i2g.cloud:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize platform
config = load_config()
platform = SubsurfaceDataPlatform(config)
platform.initialize()

class Message(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    conversation_id: str
    history: List[Message]

def unwrap_mcp_response(data):
    """
    Recursively unwraps the deeply nested response from the MCP server
    until the actual content is found.
    """
    # Keep unwrapping as long as 'data' is a string that looks like JSON
    current_data = data
    while isinstance(current_data, str):
        try:
            current_data = json.loads(current_data)
        except json.JSONDecodeError:
            # If it's not a JSON string, we can't unwrap it further
            return current_data

    if isinstance(current_data, dict):
        if 'content' in current_data and isinstance(current_data['content'], list) and current_data['content'] and isinstance(current_data['content'][0], dict):
             # Outer wrapper: {'content': [{'type': 'text', ...}]}
            return unwrap_mcp_response(current_data['content'][0])
        elif 'text' in current_data:
             # Inner wrapper: {'text': '...'}
            return unwrap_mcp_response(current_data['text'])
        elif 'content' in current_data:
            # Final payload: {'content': [...]}
            return current_data

    return current_data # Fallback for unexpected formats

@app.post("/api/query")
async def process_query(query_request: QueryRequest, request: Request):
    """
    Processes a user query, maintaining conversation history.
    """
    agent = request.app.state.agent
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
        
    conversation_id = query_request.conversation_id
    query = query_request.query

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    history = conversations.get(conversation_id, [])
    
    # We pass the existing history to the agent, the new query is the main input
    try:
        response_text = await agent.run(
            query=query,
            chat_history=history, # Pass the history *before* the current query
            conversation_id=conversation_id
        )

        # Update history with the user query and the agent's response for the next turn
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": response_text})

        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        conversations[conversation_id] = history
        
        return {"history": history, "conversation_id": conversation_id}
        
    except Exception as e:
        logger.error(f"Error processing query for conversation {conversation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the query.")

@app.get("/api/status")
async def get_status(request: Request):
    try:
        status = platform.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files")
async def list_files():
    try:
        mcp_client = platform.get_mcp_server()
        raw_result = mcp_client.call_tool("list_files", "*")
        
        # Use the robust unwrapping function to get the clean content
        final_content = unwrap_mcp_response(raw_result)
        
        # Ensure the final result is in the format the frontend expects
        if isinstance(final_content, dict) and 'content' in final_content:
            return final_content
        else:
            # If unwrapping fails to find the expected dict, return a default
            return {"content": []}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """
    Initialize platform and conversations
    """
    # platform.initialize() # This is now handled by the dedicated MCP server
    conversations.clear()
    # The main platform object, which holds the agent, still needs to be initialized.
    # We will ensure it's initialized without starting the sub-servers.
    platform.initialize_agent_only()

@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up resources
    """
    conversations.clear()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 