import asyncio

from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from AIwardrobe.model.factory import chat_model
from AIwardrobe.utils.prompt_loader import load_system_prompts
from AIwardrobe.utils.logger_handler import logger
from AIwardrobe.agent.tools.agent_tools import (rag_summarize, get_weather,
                                                  get_user_location, fetch_external_data,
                                                  get_agent_user_context)
from AIwardrobe.agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch

class ReactAgent:
    def __init__(self):
        self.tools = [
            rag_summarize,
            get_weather,
            get_user_location,
            fetch_external_data,
            get_agent_user_context,
        ]
        self.middleware = [monitor_tool, log_before_model, report_prompt_switch]

    def create_agent_for_lang(self, lang: str):
        """Create an agent for the given language; default English. ``lang`` is 'zh' or 'en'."""
        system_prompt = load_system_prompts(lang)
        return create_agent(
            model=chat_model,
            system_prompt=system_prompt,
            tools=self.tools,
            middleware=self.middleware,
        )

    async def execute_stream(self, query: str, lang: str = "en"):
        agent = self.create_agent_for_lang(lang)
        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }

        # Third arg ``context`` is runtime state (e.g. prompt switching); initialize new flags here if added
        async for chunk in agent.astream(
            input_dict,
            stream_mode="values",
            context={"report": False},
        ):
            latest_message = chunk["messages"][-1]
            if isinstance(latest_message, AIMessage):
                tool_calls = getattr(latest_message, "tool_calls", None) or []
                if tool_calls:
                    logger.info(f"[react_agent] model requested tool calls: {tool_calls}")

            # Stream only the model's final text to the client; hide tool-call payloads
            if isinstance(latest_message, AIMessage) and latest_message.content:
                yield latest_message.content.strip() + "\n"

if __name__ == '__main__':
    async def _main():
        agent = ReactAgent()
        async for chunk in agent.execute_stream("What is the weather in Shenzhen today?"):
            print(chunk, end="", flush=True)

    asyncio.run(_main())
