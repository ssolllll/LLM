import asyncio
import logging

from config import Configuration
from server import Server
from llm_client import LLMClient
from chat_session import ChatSession


async def main() -> None:
    """Initialize and run the chat session."""
    try:
        # Load configuration
        config = Configuration()
        
        # Load server configuration
        server_config = config.load_config("servers_config.json")
        
        # Initialize servers
        servers = [
            Server(name, srv_config)
            for name, srv_config in server_config["mcpServers"].items()
        ]
        
        logging.info(f"Loaded {len(servers)} servers from configuration")
        for server in servers:
            logging.info(f"  - {server.name}")
        
        # Initialize LLM client
        llm_client = LLMClient()
        
        # Start chat session
        chat_session = ChatSession(servers, llm_client)
        await chat_session.start()
        
    except FileNotFoundError as e:
        logging.error(f"Configuration file not found: {e}")
        print("Please ensure 'servers_config.json' exists in the current directory.")
    except Exception as e:
        logging.error(f"Failed to start application: {e}")
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())