from operator import add
from typing import Annotated, List, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
import os
# Load environment variables
load_dotenv()


class InputState(TypedDict):
    article: str


class OutputState(TypedDict):
    agent_output: str


class OverallState(InputState, OutputState):
    messages: Annotated[List[BaseMessage], add]

import random

@tool
def get_market_value(player_name: str):
    """Gets current market value of a player"""
    try:
        fake_market_value_db = {
            "Lionel Messi": "€50 million",
            "Cristiano Ronaldo": "€30 million",
        }
        return random.choice(["€50 million","€30 million"])
        
    except Exception as e:
        print(e)

def create_market_value_agent():
    tools_market_value = [get_market_value]
    # model_market_value = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools_market_value)
    from langchain_openai import AzureChatOpenAI
    model_market_value = AzureChatOpenAI(temperature = 0.1, deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")).bind_tools(tools_market_value)

    async def call_model_market_value(state: OverallState):
        local_messages = state.get("messages", [])
        if not local_messages:
            human_message = HumanMessage(content=state["article"])
            local_messages.append(human_message)

        system_message = SystemMessage(
            content="""You are an agent tasked with determining the market value of a player.
use the provided tool.'"""
        )

        response = await model_market_value.ainvoke([system_message] + local_messages)

        state["agent_output"] = response.content
        state["messages"] = local_messages + [response]

        return state

    def should_continue(state: OverallState) -> Literal["tools", END]:
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    market_value_graph = StateGraph(OverallState, input=InputState, output=OutputState)
    market_value_graph.add_node("call_model_market_value", call_model_market_value)
    market_value_graph.add_node("tools", ToolNode(tools_market_value))
    market_value_graph.add_edge(START, "call_model_market_value")
    market_value_graph.add_conditional_edges("call_model_market_value", should_continue)
    market_value_graph.add_edge("tools", "call_model_market_value")

    return market_value_graph.compile()
