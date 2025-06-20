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
        result = mcp_client.call_tool("list_files", "*")

        # The tool returns a dictionary with a 'text' key containing a JSON string.
        # We need to parse this before sending it to the frontend.
        if 'text' in result and isinstance(result['text'], str):
            # Parse the JSON string to get the actual content
            content = json.loads(result['text'])
            return content  # This will be {"content": [...]}
        elif 'content' in result:
             # Handle case where it might already be parsed
             return result
        else:
             # If the format is unexpected, return an empty list for now.
             return {"content": []}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 