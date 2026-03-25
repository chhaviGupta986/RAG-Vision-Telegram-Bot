# LangChain overview

LangChain is the easy way to start building completely custom agents and applications powered by LLMs. With under 10 lines of code, you can connect to OpenAI, Anthropic, Google, and more. LangChain provides a prebuilt agent architecture and model integrations to help you get started quickly and seamlessly incorporate LLMs into your agents and applications.

## LangChain vs. LangGraph vs. Deep Agents

If you are looking to build an agent, we recommend you start with Deep Agents which comes “batteries-included”, with modern features like automatic compression of long conversations, a virtual filesystem, and subagent-spawning for managing and isolating context.
Deep Agents are implementations of LangChain agents. If you don’t need these capabilities or would like to customize your own for your agents and autonomous applications, start with LangChain.
Use LangGraph, our low-level agent orchestration framework and runtime, when you have more advanced needs that require a combination of deterministic and agentic workflows and heavy customization.
LangChain agents are built on top of LangGraph in order to provide durable execution, streaming, human-in-the-loop, persistence, and more. You do not need to know LangGraph for basic LangChain agent usage.
We recommend you use LangChain if you want to quickly build agents and autonomous applications.
​
Create an agent

### pip install -qU langchain "langchain[anthropic]"

from langchain.agents import create_agent

def get_weather(city: str) -> str:
"""Get weather for a given city."""
return f"It's always sunny in {city}!"

agent = create_agent(
model="claude-sonnet-4-6",
tools=[get_weather],
system_prompt="You are a helpful assistant",
)

## Run the agent

agent.invoke(
{"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)
See the Installation instructions and Quickstart guide to get started building your own agents and applications with LangChain.
Use LangSmith to trace requests, debug agent behavior, and evaluate outputs. Set LANGSMITH_TRACING=true and your API key to get started.
​
