from typing import Callable
from AIwardrobe.utils.prompt_loader import load_report_prompts, load_system_prompts
from langchain.agents import AgentState
from langchain.agents.middleware import wrap_tool_call, before_model, dynamic_prompt, ModelRequest
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.runtime import Runtime
from langgraph.types import Command
from AIwardrobe.utils.logger_handler import logger


@wrap_tool_call
async def monitor_tool(
        # LangGraph tool call envelope
        request: ToolCallRequest,
        # Next handler in the chain
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:                      # Log tool invocations and outcomes

    logger.info(f"[tool monitor] invoking tool: {request.tool_call['name']}")
    logger.info(f"[tool monitor] args: {request.tool_call['args']}")

    try:
        result = await handler(request)
        logger.info(f"[tool monitor] tool {request.tool_call['name']} succeeded")

        if request.tool_call['name'] == "fill_context_for_report":          # Flip runtime flag for report prompt mode
            request.runtime.context["report"] = True

        return result

    except Exception as e:
        logger.error(f"[tool monitor] tool {request.tool_call['name']} failed: {e}")
        raise e

@before_model
def log_before_model(
        state: AgentState,                  # Agent message list and scratch state
        runtime: Runtime,                   # Execution context (e.g. report flag)
):     # Log before each model call
    logger.info(f"[log_before_model] calling model with {len(state['messages'])} message(s)")

    logger.debug(f"[log_before_model]{type(state['messages'][-1]).__name__} | {state['messages'][-1].content.strip()}")

    return None


@dynamic_prompt
def report_prompt_switch(request: ModelRequest):
    is_report = request.runtime.context.get("report", False)

    if is_report:
        logger.info("[report_prompt_switch] switched to report prompt mode")
        return load_report_prompts()

    return load_system_prompts()
