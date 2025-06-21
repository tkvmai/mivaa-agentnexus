from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
import uuid
import atexit
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Config, load_config
from main import SubsurfaceDataPlatform

SESSIONS_FILE = project_root / "data" / "sessions.json"

app = FastAPI(title="Subsurface Data Management Platform API")

# New structure: { "convo_id": {"history": [...], "last_updated": "iso_timestamp"}, ... }
conversations: Dict[str, Dict[str, Any]] = {}

def load_sessions():
    global conversations
    if SESSIONS_FILE.exists():
        with open(SESSIONS_FILE, 'r') as f:
            try:
                content = f.read()
                if content:
                    loaded_conversations = json.loads(content)
                    seven_days_ago = datetime.utcnow() - timedelta(days=7)
                    
                    # Filter out sessions that have not been updated in the last 7 days
                    conversations = {
                        cid: cdata for cid, cdata in loaded_conversations.items()
                        if "last_updated" in cdata and datetime.fromisoformat(cdata["last_updated"]) > seven_days_ago
                    }
                    
                    # After filtering, save the cleaned-up data back to the file
                    save_sessions()
                else:
                    conversations = {}
            except (json.JSONDecodeError, TypeError):
                conversations = {}
    else:
        conversations = {}

def save_sessions():
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(conversations, f, indent=4)

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

    history = conversations.get(conversation_id, {}).get("history", [])
    
    # Add the current user query to the history for this turn
    history.append({"role": "user", "content": query})

    try:
        # Call the agent with the original simple format (no session parameters) - now async
        response_text = await agent.run(query)

        # Update history with the agent's response for the next turn
        history.append({"role": "assistant", "content": response_text})

        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        conversations[conversation_id] = {
            "history": history,
            "last_updated": datetime.utcnow().isoformat()
        }
        save_sessions() # Save after every update
        
        return {"history": history, "conversation_id": conversation_id}
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing query for conversation {conversation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the query.")

@app.get("/api/sessions")
async def get_sessions():
    """
    Returns all active sessions, formatted for the frontend.
    """
    session_list = []
    for cid, cdata in conversations.items():
        history = cdata.get("history", [])
        if history:
            session_list.append({
                "id": cid,
                "title": history[0].get("content", "New Session"),
                "timestamp": cdata.get("last_updated"),
                "history": history
            })
    # Sort by most recently updated
    session_list.sort(key=lambda s: s["timestamp"], reverse=True)
    return session_list

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
        # Check if platform and MCP client are available
        if not platform:
            raise HTTPException(status_code=500, detail="Platform not initialized")
            
        if not platform.mcp_client:
            raise HTTPException(status_code=500, detail="MCP Client not initialized")
            
        mcp_client = platform.mcp_client
        
        # Test the connection first
        try:
            tools_response = mcp_client.get_tools()
            if "error" in tools_response:
                raise HTTPException(status_code=500, detail=f"MCP server connection failed: {tools_response['error']}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"MCP server not accessible: {str(e)}")
        
        # Now try to list files
        raw_result = mcp_client.call_tool("list_files", "*")
        
        # Check if the tool call failed
        if isinstance(raw_result, dict) and "error" in raw_result:
            raise HTTPException(status_code=500, detail=f"list_files tool failed: {raw_result['error']}")
        
        # Use the robust unwrapping function to get the clean content
        final_content = unwrap_mcp_response(raw_result)
        
        # Ensure the final result is in the format the frontend expects
        if isinstance(final_content, dict) and 'content' in final_content:
            return final_content
        else:
            # If unwrapping fails to find the expected dict, return a default
            return {"content": []}

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in list_files: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """
    Initialize platform and conversations
    """
    load_sessions()
    # The main platform object, which holds the agent, still needs to be initialized.
    # We will ensure it's initialized without starting the sub-servers.
    platform.initialize_agent_only()
    # Store the initialized agent in the application state so it's available to endpoints
    app.state.agent = platform.agent
    if not app.state.agent:
        # This is a critical failure, we should log it.
        # Note: a proper logger should be configured for a real application.
        import logging
        logging.getLogger(__name__).critical("CRITICAL: Agent could not be initialized and is not available in app state!")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up resources
    """
    save_sessions()

atexit.register(save_sessions)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 