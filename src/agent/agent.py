from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from src.tools.weather import get_weather, get_coolest_cities
from src.tools.options import calculate_option_profit
from src.tools.compound_interest import calculate_compound_interest
from src.tools.single_stock_and_fixed_savings import analyze_single_stock_and_fixed_savings
from src.tools.tool_401k import calculate_401k_retirement
from src.tools.home_affordability import calculate_home_affordability
from src.tools.loan import calculate_loan
from src.tools.financial_freedom import calculate_financial_freedom
from src.config import SYSTEM_PROMPT, MODEL_NAME

def create_agent():
    tools = [
        calculate_option_profit,
        get_weather,
        get_coolest_cities,
        calculate_compound_interest,
        analyze_single_stock_and_fixed_savings,
        calculate_401k_retirement,
        calculate_home_affordability,
        calculate_loan,
        calculate_financial_freedom
    ]

    tool_node = ToolNode(tools)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
    ])
    
    model = ChatOllama(model=MODEL_NAME)
    model_with_tools = model.bind_tools(tools).bind(prompt=prompt)

    def should_continue(state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        return END

    def call_model(state: MessagesState):
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")

    return workflow.compile() 