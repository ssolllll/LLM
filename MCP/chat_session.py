import json
import logging
from typing import List

from server import Server
from llm_client import LLMClient


class ChatSession:
    """Orchestrates the interaction between user, LLM, and tools."""

    def __init__(self, servers: List[Server], llm_client: LLMClient) -> None:
        self.servers: List[Server] = servers
        self.llm_client: LLMClient = llm_client

    async def cleanup_servers(self) -> None:
        """Clean up all servers properly."""
        for server in reversed(self.servers):
            try:
                await server.cleanup()
            except Exception as e:
                logging.warning(f"Warning during final cleanup: {e}")

    async def process_llm_response(self, llm_response: str) -> str:
        """Process the LLM response and execute tools if needed.

        Args:
            llm_response: The response from the LLM.

        Returns:
            The result of tool execution or the original response.
        """
        try:
            tool_call = json.loads(llm_response)
            if "tool" in tool_call and "arguments" in tool_call:
                logging.info(f"Executing tool: {tool_call['tool']}")
                logging.info(f"With arguments: {tool_call['arguments']}")

                for server in self.servers:
                    tools = await server.list_tools()
                    if any(tool.name == tool_call["tool"] for tool in tools):
                        try:
                            result = await server.execute_tool(
                                tool_call["tool"], tool_call["arguments"]
                            )

                            if isinstance(result, dict) and "progress" in result:
                                progress = result["progress"]
                                total = result["total"]
                                percentage = (progress / total) * 100
                                logging.info(
                                    f"Progress: {progress}/{total} ({percentage:.1f}%)"
                                )

                            return f"Tool execution result: {result}"
                        except Exception as e:
                            error_msg = f"Error executing tool: {str(e)}"
                            logging.error(error_msg)
                            return error_msg

                return f"No server found with tool: {tool_call['tool']}"
            return llm_response
        except json.JSONDecodeError:
            return llm_response

    async def start(self) -> None:
        """Main chat session handler."""
        try:
            # Initialize all servers
            for server in self.servers:
                try:
                    await server.initialize()
                    logging.info(f"Server '{server.name}' initialized successfully")
                except Exception as e:
                    logging.error(f"Failed to initialize server '{server.name}': {e}")
                    await self.cleanup_servers()
                    return

            # Collect all available tools
            all_tools = []
            for server in self.servers:
                try:
                    tools = await server.list_tools()
                    all_tools.extend(tools)
                    logging.info(f"Server '{server.name}' has {len(tools)} tools available")
                except Exception as e:
                    logging.error(f"Failed to list tools for server '{server.name}': {e}")

            # Create tools description for LLM
            tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])
            
            # Log available tools for debugging
            if all_tools:
                logging.info(f"Total tools available: {len(all_tools)}")
                for tool in all_tools:
                    logging.info(f"  - {tool.name}: {tool.description}")
            else:
                logging.warning("No tools available!")

            system_message = (
                "You are a helpful assistant with access to these tools:\n\n"
                f"{tools_description}\n"
                "Choose the appropriate tool based on the user's question. "
                "If no tool is needed, reply directly.\n\n"
                "IMPORTANT: When you need to use a tool, you must ONLY respond with "
                "the exact JSON object format below, nothing else:\n"
                "{\n"
                '    "tool": "tool-name",\n'
                '    "arguments": {\n'
                '        "argument-name": "value"\n'
                "    }\n"
                "}\n\n"
                "After receiving a tool's response:\n"
                "1. Transform the raw data into a natural, conversational response\n"
                "2. Keep responses concise but informative\n"
                "3. Focus on the most relevant information\n"
                "4. Use appropriate context from the user's question\n"
                "5. Avoid simply repeating the raw data\n\n"
                "Please use only the tools that are explicitly defined above."
            )

            messages = [{"role": "system", "content": system_message}]
            
            print("Chat session started! Type 'quit' or 'exit' to end.")
            print("=" * 50)

            while True:
                try:
                    user_input = input("You: ").strip()
                    if user_input.lower() in ["quit", "exit"]:
                        logging.info("\nExiting...")
                        print("Goodbye!")
                        break

                    if not user_input:
                        continue

                    messages.append({"role": "user", "content": user_input})

                    # Get response from LLM
                    llm_response = self.llm_client.get_response(messages)
                    print(f"\nAssistant: {llm_response}")

                    # Process the response (check if it's a tool call)
                    result = await self.process_llm_response(llm_response)

                    if result != llm_response:
                        # Tool was executed, get final response
                        messages.append({"role": "assistant", "content": llm_response})
                        messages.append({"role": "system", "content": result})

                        final_response = self.llm_client.get_response(messages)
                        print(f"\nFinal response: {final_response}")
                        messages.append(
                            {"role": "assistant", "content": final_response}
                        )
                    else:
                        # No tool execution, just add the response
                        messages.append({"role": "assistant", "content": llm_response})

                except KeyboardInterrupt:
                    logging.info("\nExiting...")
                    print("\nGoodbye!")
                    break
                except Exception as e:
                    logging.error(f"Error in chat session: {e}")
                    print(f"An error occurred: {e}")

        finally:
            await self.cleanup_servers()