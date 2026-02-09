from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts
from agent.tools.agent_tools import (rag_summarize, get_weather,
                                                  get_user_location, get_user_id,
                                                  get_current_month, fetch_external_data,
                                                  fill_context_for_report)
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch

class ReactAgent:
    def __init__(self, lang="zh"):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(lang),
            tools = [rag_summarize, get_weather, get_user_location, get_user_id,
                    get_current_month, fetch_external_data,
                    fill_context_for_report],
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )

    def execute_stream(self, query: str):
        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }

        # 第三个参数context就是上下文runtime中的信息，就是我们做提示词切换的标记 如果加上别的标记的话记得在这里先初始化一下
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]
            # 只向前端输出模型的最终回复，避免工具调用参数泄露
            if isinstance(latest_message, AIMessage) and latest_message.content:
                yield latest_message.content.strip() + "\n"

if __name__ == '__main__':
    agent = ReactAgent()

    for chunk in agent.execute_stream("给我生成我的使用报告"):
        print(chunk, end="", flush=True)
