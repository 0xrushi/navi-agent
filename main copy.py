from langchain_ollama.chat_models import ChatOllama

from langchain_core.tools import tool

from langgraph.prebuilt import ToolNode
import uuid
import mibian
import numpy as np
from datetime import datetime, timedelta
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.prebuilt import ToolExecutor
from langchain_core.tools import BaseTool
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import StateGraph, END, START


class State(TypedDict):
    messages: Annotated[Sequence[tuple[str, str]], "The messages in the conversation"]
    
class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable
        
    def __call__(self, state, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            user_id = configuration.get("user_id", None)
            
            # Convert the messages to the correct format
            messages = []
            if isinstance(state["messages"], tuple):
                # Handle single message tuple
                role, content = state["messages"]
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
            elif isinstance(state["messages"], list):
                # Handle list of message tuples
                for role, content in state["messages"]:
                    if role == "user":
                        messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        messages.append(AIMessage(content=content))
            
            # Invoke with the properly formatted messages
            result = self.runnable.invoke(messages)
            
            # Handle tool calls specifically
            if hasattr(result, 'tool_calls') and result.tool_calls:
                return {
                    "messages": result,
                    "next": "tools"
                }
            
            # Re-prompt if empty response
            if not hasattr(result, 'content') or not result.content or (
                isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                if isinstance(state["messages"], tuple):
                    state = {"messages": [state["messages"], ("user", "Respond with a real output.")]}
                else:
                    state = {"messages": state["messages"] + [("user", "Respond with a real output.")]}
                continue
            else:
                break
        return {"messages": result, "next": "end"}

def create_tool_node_with_fallback(tools: list[BaseTool]):
    tool_node = ToolNode(tools)
    
    def tool_node_with_fallback(state):
        messages = state["messages"]
        try:
            # Execute all tool calls
            if hasattr(messages, 'tool_calls') and messages.tool_calls:
                tool_results = []
                for tool_call in messages.tool_calls:
                    args = tool_call.args if hasattr(tool_call, 'args') else {}
                    name = tool_call.name if hasattr(tool_call, 'name') else tool_call.get('name')
                    
                    # Find the matching tool
                    tool = next((t for t in tools if t.name == name), None)
                    if tool:
                        result = tool.invoke(args)
                        tool_results.append(result)
                    else:
                        tool_results.append(f"Tool {name} not found")
                return {"messages": tool_results}
            return {"messages": "No tool calls to execute"}
        except Exception as e:
            import traceback
            return {"messages": f"Error executing tool: {str(e)}\n{traceback.format_exc()}"}
    
    return tool_node_with_fallback

def tools_condition(state):
    """Determine if we should use tools or end the conversation."""
    messages = state["messages"]
    has_tool_calls = (hasattr(messages, 'tool_calls') and messages.tool_calls)
    if has_tool_calls:
        return "tools"
    return "end"

@tool
def get_weather(location: str):
    """Call to get the current weather."""
    if location.lower() in ["sf", "san francisco"]:
        return "It's 60 degrees and foggy."
    else:
        return "It's 90 degrees and sunny."


@tool
def get_coolest_cities():
    """Get a list of coolest cities"""
    return "nyc, sf"

@tool
def calculate_option_profit(
    current_price: float,
    strike_price: float,
    days_to_expiry: int,
    option_type: str,
    initial_price: float,
    contracts: int = 1,
    interest_rate: float = 0.05
) -> str:
    """Calculate option profit/loss matrix for different price points and dates.
    
    Args:
        current_price: Current stock price (e.g., 100.50)
        strike_price: Option strike price (e.g., 105.00)
        days_to_expiry: Number of days until option expiration (e.g., 30)
        option_type: Type of option - must be 'p' for put or 'c' for call
        initial_price: Option premium paid per share (e.g., 1.50)
        contracts: Number of option contracts (optional, default: 1)
        interest_rate: Annual interest rate as decimal (optional, default: 0.05 for 5%)
    
    Returns:
        A detailed analysis of potential profit/loss scenarios
    
    Example:
        calculate_option_profit(
            current_price=100.50,
            strike_price=105.00,
            days_to_expiry=30,
            option_type='c',
            initial_price=1.50
        )
    """
    # Validate inputs
    if option_type not in ['p', 'c']:
        return "Error: option_type must be 'p' for put or 'c' for call"
    
    if current_price <= 0 or strike_price <= 0 or days_to_expiry < 0 or initial_price < 0:
        return "Error: prices and days must be positive numbers"
    
    if contracts < 1:
        return "Error: number of contracts must be at least 1"
    
    # Calculate implied volatility
    c = mibian.BS([current_price, strike_price, interest_rate, days_to_expiry], 
                  putPrice=initial_price if option_type == 'p' else None,
                  callPrice=initial_price if option_type == 'c' else None)
    implied_volatility = c.impliedVolatility

    total_cost = initial_price * 100 * contracts

    # Generate price range (±15% from current price)
    price_range = 0.15
    min_price = current_price * (1 - price_range)
    max_price = current_price * (1 + price_range)
    stock_prices = np.arange(min_price, max_price, current_price * 0.01)
    dates = [datetime.now() + timedelta(days=i) for i in range(days_to_expiry + 1)]

    data = np.zeros((len(stock_prices), len(dates)))

    for i, price in enumerate(stock_prices):
        for j, date in enumerate(dates):
            days_left = (dates[-1] - date).days

            if days_left == 0:
                option_value = max(strike_price - price, 0) if option_type == 'p' else max(price - strike_price, 0)
            else:
                c = mibian.BS([price, strike_price, interest_rate, days_left], volatility=implied_volatility)
                option_value = c.putPrice if option_type == 'p' else c.callPrice

            profit_loss = (option_value * 100 * contracts) - total_cost
            data[i, j] = round(profit_loss)

    # Format results
    result = f"Option Analysis:\n"
    result += f"Initial price: ${initial_price:.2f}\n"
    result += f"Total cost: ${total_cost:.2f}\n"
    result += f"Break-even at expiry: ${strike_price - initial_price if option_type == 'p' else strike_price + initial_price:.2f}\n"
    result += f"Implied Volatility: {implied_volatility:.2f}%\n\n"
    result += "Profit/Loss Matrix (rows=prices, columns=days):\n"
    result += str(np.flipud(data))
    
    return result

# tools = [get_weather, get_coolest_cities, calculate_option_profit]
# tool_node = ToolNode(tools)


# model_with_tools = ChatOllama(model="qwen2.5:14b").bind_tools(tools)

# print(model_with_tools.invoke("What would be my profit/loss matrix for a call option with current price of 100?"))


# Create the tools list
tools = [
    calculate_option_profit,
    get_weather,
    get_coolest_cities
]

# Create the model with tools
model_with_tools = ChatOllama(
    model="qwen2.5:14b",
    format="json"
).bind_tools(tools)

# Build the graph
def build_graph():
    builder = StateGraph(State)
    
    # Add nodes
    builder.add_node("assistant", Assistant(model_with_tools))
    builder.add_node("tools", create_tool_node_with_fallback(tools))
    
    # Add edges
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
        {
            "tools": "tools",
            "end": END
        }
    )
    builder.add_edge("tools", "assistant")
    
    return builder

# Usage example
if __name__ == "__main__":
    builder = build_graph()
    graph = builder.compile()
    
    config = {
        "configurable": {
            "user_id": "user123",
            "thread_id": str(uuid.uuid4()),
        }
    }
    
    # Test the options calculation
    initial_message = ("user", 
        "Calculate profit for a call option with:\n"
        "- Strike price: $100\n"
        "- Current price: $105\n"
        "- Days to expiry: 30\n"
        "- Initial premium: $2\n"
        "- Option type: call"
    )
    
    try:
        events = graph.stream(
            {"messages": initial_message},
            config,
            stream_mode="values"
        )
        
        for event in events:
            if isinstance(event.get("messages"), list):
                for message in event["messages"]:
                    print(message)
            else:
                print(event.get("messages"))
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(traceback.format_exc())