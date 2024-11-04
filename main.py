from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.agent.agent import create_agent
from src.config import SYSTEM_PROMPT

def main():
    app = create_agent()
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    print("Welcome! You can chat with me about the weather or cool cities. Type 'quit' to exit.")
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'quit':
            break
            
        messages.append(HumanMessage(content=user_input))
        
        try:
            for chunk in app.stream({"messages": messages}, stream_mode="values"):
                response = chunk["messages"][-1]
                
                if isinstance(response, AIMessage):
                    if response.content:
                        print("\nAssistant:", response.content)
                    
                    if hasattr(response, 'tool_calls') and response.tool_calls:
                        for tool_call in response.tool_calls:
                            print(f"\nUsing tool: {tool_call['name']}")
                            print(f"Arguments: {tool_call['args']}")
                            
                            # Get the tool function from globals from the name string of the tool
                            tool_func = globals().get(tool_call['name'])
                            if tool_func:
                                args = tool_call['args']
                                # Special handling for analyze_single_stock_and_fixed_savings
                                if tool_call['name'] == 'analyze_single_stock_and_fixed_savings':
                                    args = {
                                        **args,
                                        'monthly_investment': float(args['monthly_investment']),
                                        'stock_allocation': float(args.get('stock_allocation', 1.0)),
                                        'savings_rate': float(args.get('savings_rate', 0.045))
                                    }
                                
                                # Invoke the tool function
                                result = tool_func.invoke(args)
                                print(f"Result: {result}")
                
                messages.extend(chunk["messages"])
                
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            continue

if __name__ == "__main__":
    main()