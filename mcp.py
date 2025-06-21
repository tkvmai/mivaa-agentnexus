from servers.mcp_server import MCPServerManager
from config.settings import load_config, validate_config
from utils.logging_setup import setup_logging
import logging

def main():
    """
    Independent entrypoint for running the MCP Server.
    """
    # Load configuration
    config = load_config()

    # Setup logging
    setup_logging(config.logging)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting standalone MCP Server...")

    # Validate configuration
    if not validate_config(config):
        logger.error("Invalid configuration for MCP server. Exiting.")
        return

    # Initialize and start the MCP server
    mcp_server = MCPServerManager(config.mcp, config.data)
    try:
        mcp_server.start()
        logger.info(f"MCP Server started successfully on {mcp_server.url}")
        # Keep the main thread alive while the server runs in its thread
        while True:
            import time
            time.sleep(3600) 
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down MCP Server...")
        mcp_server.stop()
    except Exception as e:
        logger.critical(f"A critical error occurred: {e}", exc_info=True)
        mcp_server.stop()

if __name__ == "__main__":
    main() 