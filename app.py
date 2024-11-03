import asyncio
from typing import AsyncGenerator, List
import streamlit as st
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.agent.agent import create_agent
from src.tools.weather import get_weather, get_coolest_cities
from src.tools.single_stock_and_fixed_savings import analyze_single_stock_and_fixed_savings
from src.config import SYSTEM_PROMPT

AGENT = None

def init_agent():
    """Initialize the agent if not already done."""
    global AGENT
    if AGENT is None:
        AGENT = create_agent()
    return AGENT

async def process_agent_message(
    message: str,
    messages: List[dict]
) -> AsyncGenerator[str, None]:
    """Process messages through the agent with streaming support."""
    agent_app = init_agent()
    
    try:
        messages_state = {"messages": [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=message)]}
        
        # Process through the agent
        for chunk in agent_app.stream(messages_state, stream_mode="values"):
            response = chunk["messages"][-1]
            
            if isinstance(response, AIMessage):
                if response.content:
                    yield response.content
                
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        yield f"\nUsing tool: {tool_call['name']}"
                        yield f"Arguments: {tool_call['args']}"
                        
                        tool = globals().get(tool_call['name'])
                        if tool:
                            args = tool_call['args']
                            # Special case for financial analysis
                            if tool_call['name'] == 'analyze_single_stock_and_fixed_savings':
                                args = {
                                    **args,
                                    'monthly_investment': float(args['monthly_investment']),
                                    'stock_allocation': float(args.get('stock_allocation', 1.0)),
                                    'savings_rate': float(args.get('savings_rate', 0.045))
                                }
                            result = tool.invoke(args)
                            yield f"{tool_call['name']} result: {result}"
                            
    except Exception as e:
        yield f"An error occurred: {str(e)}"

async def main():
    st.set_page_config(
        page_title="AI Assistant with Financial and Weather Tools",
        page_icon="🤖",
        layout="wide"
    )

    st.markdown("# AI Assistant with Financial and Weather Tools 🤖💱🌤️")

    # Initialize session state for messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Add example prompts section
    st.markdown("### Try these example prompts:")
    example_prompts = [
        "What's the weather like in New York?",
        "I started investing at age 20 with $10000 per month, stop investing at age 30. Meanwhile my friend started investing $15000 per month at age 30, and continues to invest till age 60 if average annual return for both cases is 13.6% compare both scenarios.",
        "Analyze my portfolio if i invest in AAPL, MSFT",
        "Can I buy a house with $100000 salary, $700,000 house price and 3.5% interest rate, 30 year fixed mortgage?"
    ]
    
    cols = st.columns(len(example_prompts))
    for col, prompt in zip(cols, example_prompts):
        if col.button(prompt, key=f"example_{prompt}"):
            st.session_state.prompt = prompt
            st.rerun()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Fix the chat input - remove the value parameter as it's not supported
    if "prompt" in st.session_state:
        prompt = st.chat_input(
            "Ask about weather, investments, or use any of our tools...",
            key="chat_input"
        )
        del st.session_state.prompt  # Fix typo in 'prompt' deletion
    else:
        prompt = st.chat_input(
            "Ask about weather, investments, or use any of our tools...",
            key="chat_input"
        )

    if prompt:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Stream the response
            async for chunk in process_agent_message(prompt, st.session_state.messages):
                full_response += chunk + "\n\n"
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Sidebar with tools documentation
    with st.sidebar:
        st.markdown("### Available Tools")
        st.markdown("""
        - **Weather Tools**: 
            - Get current weather
            - Find cool cities
        - **Financial Tools**:
            - Calculate option profits
            - Analyze compound interest
            - Evaluate stock and savings strategies
        """)
        
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()

if __name__ == "__main__":
    asyncio.run(main())