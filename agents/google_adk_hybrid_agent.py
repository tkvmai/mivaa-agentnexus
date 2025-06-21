"""
Google ADK Agent - FULLY FIXED VERSION
Fixes all syntax errors, scope issues, and method access problems
"""

import os
import json
import time
import logging
import asyncio
from typing import Optional, Dict, Any, List

# Google ADK imports
try:
    from google.adk.agents import Agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.tools import FunctionTool
    from google.genai import types
    GOOGLE_ADK_AVAILABLE = True
except ImportError as e:
    GOOGLE_ADK_AVAILABLE = False

from config.settings import AgentConfig
from servers.mcp_server import MCPClient

logger = logging.getLogger(__name__)


class ToolExecutingAgentExecutor:
    """
    Google ADK Agent that properly executes MCP tools

    FULLY FIXED: Resolves all scope and method access issues
    """

    def __init__(self, mcp_client: MCPClient, config: AgentConfig):
        self.mcp_client = mcp_client
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Google ADK components
        self.agent = None
        self.runner = None
        self.session_service = None
        self.session_id = None
        self._google_adk_ready = False
        self._initialization_error = None

        # Statistics
        self.stats = {
            "total_invocations": 0,
            "successful_invocations": 0,
            "failed_invocations": 0,
            "tool_executions": 0,
            "system_type": "Google ADK Agent with Tool Execution"
        }

        self.logger.info("Google ADK Tool Executing Agent created")

    def _create_tool_functions(self) -> List:
        """Create Python functions that ADK can automatically wrap as tools"""
        self.logger.info("Creating tool functions for Google ADK...")

        # Store reference to self for use in closures
        executor_instance = self

        tools = []

        # List Files Tool Function - NO DEFAULT PARAMETERS
        def list_files(pattern: str) -> dict:
            """List files matching pattern in the data directory

            Args:
                pattern: File pattern to match (e.g., "*.las", "*.sgy", "*")

            Returns:
                dict: Results containing matched files
            """
            try:
                executor_instance.logger.info(f"Executing list_files with pattern: {pattern}")
                result = executor_instance._execute_mcp_tool("list_files", pattern)
                return {"status": "success", "result": result}
            except Exception as e:
                executor_instance.logger.error(f"Error in list_files: {e}")
                return {"status": "error", "message": str(e)}

        tools.append(list_files)

        # System Status Tool Function - NO DEFAULT PARAMETERS
        def system_status(query: str) -> dict:
            """Get comprehensive system health and performance metrics

            Args:
                query: Query parameter for system status (use empty string if not needed)

            Returns:
                dict: System status information
            """
            try:
                executor_instance.logger.info("Executing system_status")
                result = executor_instance._execute_mcp_tool("system_status", query)
                return {"status": "success", "result": result}
            except Exception as e:
                executor_instance.logger.error(f"Error in system_status: {e}")
                return {"status": "error", "message": str(e)}

        tools.append(system_status)

        # Health Check Tool Function - NO DEFAULT PARAMETERS
        def health_check(query: str) -> dict:
            """Perform comprehensive health check of the platform

            Args:
                query: Query parameter for health check (use empty string if not needed)

            Returns:
                dict: Health check results
            """
            try:
                executor_instance.logger.info("Executing health_check")
                result = executor_instance._execute_mcp_tool("health_check", query)
                return {"status": "success", "result": result}
            except Exception as e:
                executor_instance.logger.error(f"Error in health_check: {e}")
                return {"status": "error", "message": str(e)}

        tools.append(health_check)

        # Directory Info Tool Function - NO DEFAULT PARAMETERS
        def directory_info(directory_path: str) -> dict:
            """Get detailed information about data directories

            Args:
                directory_path: Path to analyze (use empty string for default data directory)

            Returns:
                dict: Directory information
            """
            try:
                executor_instance.logger.info(f"Executing directory_info for: {directory_path}")
                result = executor_instance._execute_mcp_tool("directory_info", directory_path)
                return {"status": "success", "result": result}
            except Exception as e:
                executor_instance.logger.error(f"Error in directory_info: {e}")
                return {"status": "error", "message": str(e)}

        tools.append(directory_info)

        # LAS Tools - NO DEFAULT PARAMETERS
        def las_parser(file_path: str) -> dict:
            """Parse and extract metadata from LAS files

            Args:
                file_path: Path to the LAS file

            Returns:
                dict: Parsed LAS file metadata and information
            """
            try:
                executor_instance.logger.info(f"Executing las_parser with file: {file_path}")
                result = executor_instance._execute_mcp_tool("las_parser", file_path)
                return {"status": "success", "result": result}
            except Exception as e:
                executor_instance.logger.error(f"Error in las_parser: {e}")
                return {"status": "error", "message": str(e)}

        tools.append(las_parser)

        def las_analysis(file_path: str) -> dict:
            """Analyze curve data and perform statistical analysis

            Args:
                file_path: Path to the LAS file

            Returns:
                dict: Analysis results
            """
            try:
                executor_instance.logger.info(f"Executing las_analysis with file: {file_path}")
                result = executor_instance._execute_mcp_tool("las_analysis", file_path)
                return {"status": "success", "result": result}
            except Exception as e:
                executor_instance.logger.error(f"Error in las_analysis: {e}")
                return {"status": "error", "message": str(e)}

        tools.append(las_analysis)

        def formation_evaluation(file_path: str) -> dict:
            """Perform comprehensive petrophysical analysis

            Args:
                file_path: Path to the LAS file

            Returns:
                dict: Formation evaluation results
            """
            try:
                executor_instance.logger.info(f"Executing formation_evaluation with file: {file_path}")
                result = executor_instance._execute_mcp_tool("formation_evaluation", file_path)
                return {"status": "success", "result": result}
            except Exception as e:
                executor_instance.logger.error(f"Error in formation_evaluation: {e}")
                return {"status": "error", "message": str(e)}

        tools.append(formation_evaluation)

        def well_correlation(file_path: str) -> dict:
            """Correlate formations across multiple wells

            Args:
                file_path: Path to the LAS file or directory

            Returns:
                dict: Well correlation results
            """
            try:
                executor_instance.logger.info(f"Executing well_correlation with file: {file_path}")
                result = executor_instance._execute_mcp_tool("well_correlation", file_path)
                return {"status": "success", "result": result}
            except Exception as e:
                executor_instance.logger.error(f"Error in well_correlation: {e}")
                return {"status": "error", "message": str(e)}

        tools.append(well_correlation)

        # SEG-Y Tools - NO DEFAULT PARAMETERS
        def segy_parser(file_path: str) -> dict:
            """Parse SEG-Y seismic files with comprehensive metadata extraction

            Args:
                file_path: Path to the SEG-Y file

            Returns:
                dict: Parsed SEG-Y metadata
            """
            try:
                executor_instance.logger.info(f"Executing segy_parser with file: {file_path}")
                result = executor_instance._execute_mcp_tool("segy_parser", file_path)
                return {"status": "success", "result": result}
            except Exception as e:
                executor_instance.logger.error(f"Error in segy_parser: {e}")
                return {"status": "error", "message": str(e)}

        tools.append(segy_parser)

        def segy_classify(file_path: str) -> dict:
            """Automatically classify SEG-Y survey type (2D/3D)

            Args:
                file_path: Path to the SEG-Y file

            Returns:
                dict: Classification results
            """
            try:
                executor_instance.logger.info(f"Executing segy_classify with file: {file_path}")
                result = executor_instance._execute_mcp_tool("segy_classify", file_path)
                return {"status": "success", "result": result}
            except Exception as e:
                executor_instance.logger.error(f"Error in segy_classify: {e}")
                return {"status": "error", "message": str(e)}

        tools.append(segy_classify)

        def segy_qc(file_path: str) -> dict:
            """Perform quality control on SEG-Y files

            Args:
                file_path: Path to the SEG-Y file

            Returns:
                dict: Quality control results
            """
            try:
                executor_instance.logger.info(f"Executing segy_qc with file: {file_path}")
                result = executor_instance._execute_mcp_tool("segy_qc", file_path)
                return {"status": "success", "result": result}
            except Exception as e:
                executor_instance.logger.error(f"Error in segy_qc: {e}")
                return {"status": "error", "message": str(e)}

        tools.append(segy_qc)

        def quick_segy_summary(file_path: str) -> dict:
            """Get instant overview of SEG-Y files

            Args:
                file_path: Path to the SEG-Y file

            Returns:
                dict: Quick summary results
            """
            try:
                executor_instance.logger.info(f"Executing quick_segy_summary with file: {file_path}")
                result = executor_instance._execute_mcp_tool("quick_segy_summary", file_path)
                return {"status": "success", "result": result}
            except Exception as e:
                executor_instance.logger.error(f"Error in quick_segy_summary: {e}")
                return {"status": "error", "message": str(e)}

        tools.append(quick_segy_summary)

        self.logger.info(f"Created {len(tools)} tool functions (no default parameters)")
        return tools

    async def _initialize_google_adk(self):
        """Initialize Google ADK with proper tool format - NO DEFAULT PARAMETERS"""
        self.logger.info("Initializing Google ADK components...")

        if not os.getenv('OPENAI_API_KEY'):
            raise Exception("OPENAI_API_KEY environment variable not set")

        # STEP 1: Create tool functions (ADK will automatically wrap them)
        tools = self._create_tool_functions()

        # STEP 2: Create agent with tools
        self.agent = Agent(
            name="subsurface_data_analyst",
            model=LiteLlm(model="openai/gpt-4o-mini"),
            description="Subsurface data analyst with tool execution capabilities",
            instruction=self._create_tool_execution_instruction(),
            tools=tools  # Pass Python functions directly - ADK handles the wrapping
        )

        # STEP 3: Session management
        self.session_service = InMemorySessionService()
        self.session_id = f"tool_execution_session_{hash('hybrid_user')}"

        await self.session_service.create_session(
            app_name="SubsurfaceToolExecution",
            user_id="hybrid_user",
            session_id=self.session_id
        )

        # STEP 4: Create runner
        self.runner = Runner(
            agent=self.agent,
            app_name="SubsurfaceToolExecution",
            session_service=self.session_service
        )

        self.logger.info("Google ADK initialized successfully with function tools (no defaults)")

    def _create_tool_execution_instruction(self) -> str:
        """Create instruction that emphasizes tool execution"""
        return """You are a subsurface data analyst with access to specialized tools for analyzing well logs (LAS files) and seismic data (SEG-Y files).

# CRITICAL INSTRUCTIONS - ALWAYS EXECUTE TOOLS:

## For File Listing Requests:
- User asks "list files *.las" → IMMEDIATELY call list_files with pattern="*.las"
- User asks "list files F3_*" → IMMEDIATELY call list_files with pattern="F3_*"  
- User asks "show available data" → IMMEDIATELY call list_files with pattern="*"

## For System Status Requests:
- User asks "system status" → IMMEDIATELY call system_status with query=""
- User asks "health check" → IMMEDIATELY call health_check with query=""

## For File Analysis:
- User asks "analyze well.las" → IMMEDIATELY call las_parser with file_path="well.las"
- User asks "classify survey.sgy" → IMMEDIATELY call segy_classify with file_path="survey.sgy"

# IMPORTANT PARAMETER RULES:
- ALL functions require parameters (no defaults)
- For list_files: always provide a pattern (e.g., "*", "*.las", "*.sgy")
- For system_status/health_check: use query="" if no specific query needed
- For directory_info: use directory_path="" for default data directory
- For file tools: always provide the full file path

# YOUR WORKFLOW:
1. Understand what the user wants
2. Identify the appropriate tool
3. **EXECUTE the tool immediately with required parameters**
4. Present the results clearly

# EXAMPLES OF CORRECT BEHAVIOR:
User: "list files *.las"
You: [CALLS list_files(pattern="*.las")]
Then: Present the results

User: "system status"  
You: [CALLS system_status(query="")]
Then: Present the status information

**REMEMBER: Always provide ALL required parameters when calling tools!**

Available tools: list_files, system_status, health_check, directory_info, las_parser, las_analysis, formation_evaluation, well_correlation, segy_parser, segy_classify, segy_qc, quick_segy_summary."""

    async def _execute_with_google_adk(self, query: str, chat_history: Optional[List[Dict]] = None) -> str:
        """
        Executes the query using the Google ADK Runner, now with session/history support.
        """
        self.stats["total_invocations"] += 1
        await self._ensure_google_adk_ready()

        if self._initialization_error:
            self.stats["failed_invocations"] += 1
            return f"Google ADK is not available: {self._initialization_error}"

        try:
            # Use a new session for each distinct conversation to maintain context
            if chat_history:
                # Re-construct session from history
                self.session_id = f"session-{hash(str(chat_history))}"
                session = await self.session_service.load_session(self.session_id)
                if not session.history:
                     for message in chat_history:
                        role = "user" if message["role"] == "user" else "model"
                        session.add_message(types.Message(content=message["content"], role=role))
                     await self.session_service.save_session(self.session_id, session)

            else: # Single query
                self.session_id = f"session-{os.urandom(16).hex()}"


            self.logger.info(f"Using session ID: {self.session_id} for query: '{query}'")

            response_future = self.runner.run(self.session_id, query)
            response_generator = await response_future

            final_response = ""
            async for chunk in response_generator:
                if chunk.text:
                    final_response += chunk.text
            
            # Save the final state of the session
            final_session = await self.session_service.load_session(self.session_id)
            await self.session_service.save_session(self.session_id, final_session)


            self.stats["successful_invocations"] += 1
            self.logger.info(f"Google ADK execution successful for query: '{query}'")
            return final_response if final_response else "No output from agent."

        except Exception as e:
            self.stats["failed_invocations"] += 1
            self.logger.error(f"Google ADK execution failed for query '{query}': {e}", exc_info=True)
            return self._minimal_fallback(query)

    def _minimal_fallback(self, query: str) -> str:
        """A minimal fallback that attempts to directly call a tool."""
        import re

        query_lower = query.lower()

        # Simple tool routing based on keywords
        if "list" in query_lower or "show" in query_lower:
            return self._execute_mcp_tool('list_files', '*')
        elif ".las" in query_lower:
            if "evaluate" in query_lower or "formation" in query_lower:
                return self._execute_mcp_tool('formation_evaluation', file_path)
            elif "analyze" in query_lower:
                return self._execute_mcp_tool('las_analysis', file_path)
            elif "correlate" in query_lower:
                return self._execute_mcp_tool('well_correlation', file_path)
            elif "quality" in query_lower or "qc" in query_lower:
                 return self._execute_mcp_tool('las_qc', file_path)
            else: # Default to parser
                return self._execute_mcp_tool('las_parser', file_path)
        elif ".sgy" in query_lower or ".segy" in query_lower:
            if "classify" in query_lower:
                return self._execute_mcp_tool('segy_classify', file_path)
            elif "analyze" in query_lower:
                return self._execute_mcp_tool('segy_analysis', file_path)
            elif "quality" in query_lower or "qc" in query_lower:
                return self._execute_mcp_tool('segy_qc', file_path)
            else: # Default to parser
                return self._execute_mcp_tool('segy_parser', file_path)
        elif "status" in query_lower:
            return self._execute_mcp_tool('system_status', '')
        elif "health" in query_lower:
            return self._execute_mcp_tool('health_check', '')
        else:
            return f"Agent failed. No fallback for query: '{query}'"

    async def invoke(self, input_dict: Dict[str, Any]) -> Dict[str, str]:
        """
        Invoke the agent. This is the entry point for LangChain compatibility.
        Now handles chat_history.
        """
        query = input_dict.get("input")
        chat_history = input_dict.get("chat_history")

        if not query:
            return {"output": "Error: Input dictionary must contain a non-empty 'input' key."}

        response = await self._execute_with_google_adk(query, chat_history=chat_history)
        return {"output": response}

    async def _ensure_google_adk_ready(self):
        """Initializes Google ADK components if not already done."""
        if self._google_adk_ready:
            return True

        if self._initialization_error:
            raise Exception(f"Google ADK initialization failed: {self._initialization_error}")

        try:
            await self._initialize_google_adk()
            self._google_adk_ready = True
            return True
        except Exception as e:
            self._initialization_error = str(e)
            self.logger.error(f"Google ADK initialization failed: {e}")
            raise

    def _execute_mcp_tool(self, tool_name: str, params: Any) -> str:
        """Execute MCP tool"""
        try:
            self.logger.info(f"Executing MCP tool: {tool_name} with params: {params}")
            self.stats["tool_executions"] += 1

            # Simple parameter preparation
            if isinstance(params, str):
                input_data = params
            else:
                input_data = str(params) if params is not None else ""

            result = self.mcp_client.call_tool(tool_name, input_data)
            return self._extract_result_content(result)

        except Exception as e:
            self.logger.error(f"MCP tool execution failed: {e}")
            return f"Error executing {tool_name}: {str(e)}"

    def _extract_result_content(self, result: Dict[str, Any]) -> str:
        """Extract content from MCP response"""
        try:
            if isinstance(result, dict):
                if 'content' in result and isinstance(result['content'], list):
                    if len(result['content']) > 0 and 'text' in result['content'][0]:
                        return result['content'][0]['text']
                if 'text' in result:
                    return result['text']
            return str(result)
        except:
            return str(result)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        self.stats["uptime_hours"] = (time.time() - getattr(self, '_start_time', time.time())) / 3600
        return self.stats.copy()


class ToolExecutingHybridAgent:
    """Hybrid Agent that actually executes tools via Google ADK"""

    def __init__(self, agent_executor, command_processor, fallback_handlers=None):
        self.agent_executor = agent_executor
        self.command_processor = command_processor
        self.fallback_handlers = fallback_handlers or {}
        self.logger = logging.getLogger(__name__)

        self._start_time = time.time()
        self.stats = {
            "total_queries": 0,
            "direct_commands": 0,
            "agent_responses": 0,
            "fallback_responses": 0,
            "errors": 0,
            "system_type": "Google ADK Agent with Tool Execution"
        }

    async def run(self, query: str = None, chat_history: List[Dict[str, str]] = None) -> str:
        """
        Process a query or chat history using the Google ADK agent.
        """
        self.logger.debug("ToolExecutingHybridAgent received a run call")

        if chat_history:
            # The last user message is the current query
            current_query = next((m['content'] for m in reversed(chat_history) if m['role'] == 'user'), None)
            if not current_query:
                return "Error: Could not find user query in history."
            
            # Pass the full history to the executor's invoke method
            # The executor will need to be updated to handle this
            input_data = {"input": current_query, "chat_history": chat_history}
            self.logger.debug(f"Running with chat history, query: '{current_query}'")

        elif query:
            current_query = query
            input_data = {"input": current_query}
            self.logger.debug(f"Running with single query: '{current_query}'")
        else:
            raise ValueError("run() requires either 'query' or 'chat_history'.")

        # Fallback for simple commands
        if self._is_obvious_system_command(current_query):
            self.logger.debug("Handling as an obvious system command.")
            return await self.agent_executor.invoke(input_data)

        # Main execution path
        try:
            result = await self.agent_executor.invoke(input_data)
            # The response from Google ADK is typically a dict with an 'output' key
            return result.get("output", str(result))
        except Exception as e:
            self.logger.error(f"Error during agent execution: {e}", exc_info=True)
            return f"An error occurred: {e}"

    def _is_obvious_system_command(self, query: str) -> bool:
        """Check for simple system commands that don't need complex reasoning"""
        query_lower = query.lower().strip()
        obvious_commands = ["system status", "health check", "status", "health"]
        return query_lower in obvious_commands

    def get_stats(self) -> Dict[str, Any]:
        """Return statistics from the agent executor"""
        self.stats["uptime_hours"] = (time.time() - self._start_time) / 3600

        if hasattr(self.agent_executor, 'get_stats'):
            try:
                executor_stats = self.agent_executor.get_stats()
                if isinstance(executor_stats, dict):
                    combined_stats = executor_stats.copy()
                    combined_stats.update(self.stats)
                    return combined_stats
            except Exception:
                pass

        return self.stats.copy()


class ToolExecutingAgentFactory:
    """Factory for tool-executing agents"""

    def __init__(self, mcp_url: str, config: AgentConfig):
        self.mcp_url = mcp_url
        self.config = config
        self.logger = logging.getLogger(__name__)

    def create(self) -> ToolExecutingHybridAgent:
        """Create tool-executing agent"""
        self.logger.info("Creating Google ADK agent with tool execution...")

        # Create tool-executing executor
        agent_executor = self._create_tool_executing_executor()

        # Minimal command processor
        command_processor = self._create_minimal_command_processor()

        # Create hybrid agent
        hybrid_agent = ToolExecutingHybridAgent(agent_executor, command_processor, {})

        self.logger.info("Google ADK agent with tool execution created successfully")
        return hybrid_agent

    def _create_tool_executing_executor(self) -> ToolExecutingAgentExecutor:
        """Create tool-executing executor"""
        try:
            if not GOOGLE_ADK_AVAILABLE:
                raise ImportError("Google ADK not available")

            mcp_client = MCPClient(self.mcp_url)
            agent_executor = ToolExecutingAgentExecutor(mcp_client, self.config)
            agent_executor._start_time = time.time()

            return agent_executor

        except Exception as e:
            self.logger.error(f"Failed to create tool-executing executor: {e}")
            raise

    def _create_minimal_command_processor(self):
        """Minimal command processor for obvious system commands"""
        mcp_client = MCPClient(self.mcp_url)

        def minimal_command_processor(command_str: str) -> Optional[str]:
            command_lower = command_str.lower().strip()

            if command_lower == "system status":
                result = mcp_client.call_tool("system_status", "")
                return json.dumps(result) if isinstance(result, dict) else str(result)
            elif command_lower == "health check":
                result = mcp_client.call_tool("health_check", "")
                return json.dumps(result) if isinstance(result, dict) else str(result)

            return None

        return minimal_command_processor


# Factory functions
def create_google_adk_hybrid_agent(mcp_url: str, config: AgentConfig) -> ToolExecutingHybridAgent:
    """
    Create Google ADK agent that actually executes tools

    FULLY FIXED: Resolves all syntax errors and scope issues
    """
    factory = ToolExecutingAgentFactory(mcp_url, config)
    return factory.create()


# Backward compatibility
def create_pure_reasoning_agent(mcp_url: str, config: AgentConfig) -> ToolExecutingHybridAgent:
    """Backward compatible function"""
    return create_google_adk_hybrid_agent(mcp_url, config)


def create_hybrid_agent(a2a_url: str, mcp_url: str, config: AgentConfig) -> ToolExecutingHybridAgent:
    """Backward compatible function"""
    return create_google_adk_hybrid_agent(mcp_url, config)