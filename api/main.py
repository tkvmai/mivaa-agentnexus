from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import json
from pathlib import Path
from typing import List, Optional
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Config, load_config
from main import SubsurfaceDataPlatform

app = FastAPI(title="Subsurface Data Management Platform API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for conversations
conversations = {}

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

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Retrieve history or start a new one
        history = conversations.get(conversation_id, [])
        
        # Add user's new query to history
        history.append({"role": "user", "content": request.query})
        
        # The agent now receives the whole history
        # Note: We need to ensure the agent's `run` method can handle a `chat_history` argument.
        # This might require changes in `main.py` or the agent class itself.
        response_content = await platform.agent.run(chat_history=history)

        # Add assistant's response to history
        history.append({"role": "assistant", "content": response_content})
        
        # Store the updated history
        conversations[conversation_id] = history
        
        return QueryResponse(
            response=response_content,
            conversation_id=conversation_id,
            history=[Message.parse_obj(msg) for msg in history]
        )
    except Exception as e:
        # It's useful to log the exception here
        print(f"Error in process_query: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 