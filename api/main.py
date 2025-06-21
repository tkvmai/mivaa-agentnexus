from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import json
from pathlib import Path

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

# Initialize platform
config = load_config()
platform = SubsurfaceDataPlatform(config)
platform.initialize()

class QueryRequest(BaseModel):
    query: str

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
async def process_query(request: QueryRequest):
    try:
        response = await platform.agent.run(request.query)
        return {"response": response}
    except Exception as e:
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