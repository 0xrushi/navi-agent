import gradio as gr
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.agent.agent import create_agent
from src.config import SYSTEM_PROMPT

def process_message(message, history):
    app = create_agent()
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    # Add chat history to messages
    for human, ai in history:
        messages.append(HumanMessage(content=human))
        messages.append(AIMessage(content=ai))
    
    # Add current message
    messages.append(HumanMessage(content=message))
    
    try:
        response_parts = []
        for chunk in app.stream({"messages": messages}, stream_mode="values"):
            response = chunk["messages"][-1]
            
            if isinstance(response, AIMessage):
                if response.content:
                    response_parts.append(response.content)
                
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        tool_info = f"\nUsing tool: {tool_call['name']}\nArguments: {tool_call['args']}"
                        response_parts.append(tool_info)
                        
                        tool_func = globals().get(tool_call['name'])
                        if tool_func:
                            args = tool_call['args']
                            if tool_call['name'] == 'analyze_single_stock_and_fixed_savings':
                                args = {
                                    **args,
                                    'monthly_investment': float(args['monthly_investment']),
                                    'stock_allocation': float(args.get('stock_allocation', 1.0)),
                                    'savings_rate': float(args.get('savings_rate', 0.045))
                                }
                            
                            result = tool_func.invoke(args)
                            response_parts.append(f"Result: {result}")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"An error occurred: {str(e)}"

def main():
    example_prompts = [
        "I started investing at age 20 with $10000 per month, stop investing at age 30. Meanwhile my friend started investing $15000 per month at age 30, and continues to invest till age 60 if average annual return for both cases is 13.6% compare both scenarios.",
        "Analyze my portfolio if i invest in AAPL, MSFT",
        "Can I buy a house with $100000 salary, $700,000 house price and 3.5% interest rate, 30 year fixed mortgage?"
    ]

    chat_interface = gr.ChatInterface(
        fn=process_message,
        title="AI Assistant",
        description="Chat with me about the weather or cool cities!",
        examples=example_prompts,
    )
    
    chat_interface.launch(share=True)

if __name__ == "__main__":
    main()