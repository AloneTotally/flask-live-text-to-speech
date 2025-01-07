from langchain_groq import ChatGroq
import os 
api_key = ''
with open('api-key.txt', 'r') as fin:
    api_key = fin.readline()
    print(api_key)

os.environ["GROQ_API_KEY"] = api_key
llm = ChatGroq(model="llama-3.1-8b-instant")

# llm = ChatOllama(
#     # model="llama3.2",
#     model='llama3-groq-tool-use'
# )

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.schema import HumanMessage


# Ordering part
# Testing ordering system
from langchain_core.tools import tool

# Simulated ordering system (in-memory dictionary for simplicity)
orders = {}
menu = {
    'Grilled Chicken Rice': 7.0,
    'Spicy Curry Noodles': 8.5,
    'Fried Egg Noodles': 6.5,
    'Cheese Sandwich': 4.5,
    'Beef Burger': 9.0,
    'Chocolate Cake': 5.5,
    'Crispy Chicken Wings': 6.0,
    'Fresh Garden Salad': 5.0,
    'Iced Coffee': 3.5,
    'Lemon Soda': 3.0,
    'Vegetable Soup': 6.0,
    'Spaghetti With Tomato Sauce': 7.5,
    'Vanilla Ice Cream': 4.0,
    'Chicken Wrap': 8.0,
    'Apple Pie': 4.5,
    'Mushroom Soup': 5.5,
    'Grilled Fish': 9.5,
    'Fruit Salad': 4.0,
    'Pepperoni Pizza': 10.0,
    'Milkshake': 5.0
}


@tool
def order_food(item_name: str, quantity: int, special_requests: str = ""):
    """
    Place or modify a food order.
    
    Args:
        item_name (str): The name of the food item.
        quantity (int): The quantity of the food item to order.
        special_requests (str): Additional requests (optional).
        
    Returns:
        str: Confirmation message or error.
    """
    print(f'item_name is {item_name}')
    print(f'quantity is {quantity}')
    print(f'special_requests is {special_requests}')

    item_name = " ".join(w.capitalize() for w in item_name.split())
    if item_name in menu:  # Assuming `menu` is a predefined dictionary with food items
        # if item_name in orders:
        #     orders[item_name]["quantity"] += quantity
        #     orders[item_name]["special_requests"].append(special_requests)
        # else:
        #     orders[item_name] = {
        #         "quantity": quantity,
        #         "special_requests": [special_requests],
        #     }
        # orders[item_name]["quantity"] += quantity
        # orders[item_name]["special_requests"] = orders[item_name]["special_requests"] + "," + special_requests
        orders[item_name] = {
            "quantity": quantity,
            "special_requests": special_requests,
        }

        return f"Order updated: {item_name} x{quantity} with requests: {special_requests or 'None'}."
    else:
        return f"Item '{item_name}' is not available in the menu."
@tool
def view_order():
    """
    View the current order summary.
    
    Returns:
        str: A summary of the current orders.
    """
    if not orders:
        return "No items have been ordered yet."
    order_summary = "\n".join(
        f"{item}: {details['quantity']} (Requests: {', '.join(details['special_requests']) or 'None'})"
        for item, details in orders.items()
    )
    return f"Current Orders:\n{order_summary}"

@tool
def cancel_order(item_name: str):
    """
    Cancel a specific item from the order.
    
    Args:
        item_name (str): The name of the food item to cancel.
        
    Returns:
        str: Confirmation message or error.
    """
    if item_name in orders:
        del orders[item_name]
        return f"Order for '{item_name}' has been canceled."
    else:
        return f"No order found for '{item_name}'."

@tool
def conclude_order():
    """
    Finalize and conclude the order process.
    """
    print("Order has been concluded.")


tools = [order_food, view_order, cancel_order]

template = f"""
You are a waiter for a food ordering system, and your output will go through text-to-speech.
Think step-by-step and use the tools when necessary to carry out the user's request.
If you are not able to get enough information using the tools, reply with 'I DON'T KNOW'.

### Instructions:
- Your purpose is to assist customers in a conversational manner. Use the menu context provided to answer food-related questions or assist with ordering.
- If the input can be answered without placing or modifying an order (e.g., greetings, general inquiries, or non-food-related topics), respond with a **friendly, conversational answer**. Ensure the answer is based on this prompt and avoid guessing. If unsure, state that you do not have the answer to the question.
- Always process input by reasoning step-by-step, checking if a tool is required, and ensuring each tool invocation aligns with user intent.

- Look for the exact item in the menu context and mention its price with the term "dollars".
- If the item is found, confirm that it is available and offer further assistance.
- If the item is not found in the context, state: "It does not exist on the menu." Do not guess or provide unrelated information.
- If the input involves placing, viewing, or canceling an order, use the following tools provided to you:
    - `order_food(item_name: str, quantity: int, special_requests: str)` to place or modify a food order.
    - `view_order()` to view the current order summary.
    - `cancel_order(item_name: str)` to cancel a specific item from the order.

- When canceling an order (`cancel_order`), gather the `item_name` to cancel.
- Note that when someone asks to modify a order, you need to cancel that current item and create a new order for the item to change to
- You should **only output the action once all required arguments have been gathered**.
- Do not use any technical formatting, item IDs, or unrelated information. Your response should sound natural and clear for verbal communication.
- Keep responses concise and do not go past three sentences.
- Once the person concludes the order, call the tool `conclude_order()`

Context:
'Grilled Chicken Rice': 7.00,
'Spicy Curry Noodles': 8.50,
'Fried Egg Noodles': 6.50,
'Cheese Sandwich': 4.50,
'Beef Burger': 9.00,
'Chocolate Cake': 5.50,
'Crispy Chicken Wings': 6.00,
'Fresh Garden Salad': 5.00,
'Iced Coffee': 3.50,
'Lemon Soda': 3.00,
'Vegetable Soup': 6.00,
'Spaghetti With Tomato Sauce': 7.50,
'Vanilla Ice Cream': 4.00,
'Chicken Wrap': 8.00,
'Apple Pie': 4.50,
'Mushroom Soup': 5.50,
'Grilled Fish': 9.50,
'Fruit Salad': 4.00,
'Pepperoni Pizza': 10.00,
'Milkshake': 5.00"""

memory = MemorySaver()
agent_executor = create_react_agent(llm, tools=tools, checkpointer=memory, state_modifier=template)
config = {"configurable": {"thread_id": "idkwhatconfig"}}


# Use the agent
# for chunk in agent_executor.stream(
#     {"messages": [HumanMessage(content="What food do you have?")]}, config
# ):
    # print(chunk)
    # print("----")
    # print(chunk, flush=True, end="")
    

# query = input('User: ')
# prompt = PromptTemplate.from_template('''
#     You are a close friend offering support. 
#     Based on the user's query: "{query}", give a friendly, relatable response, sharing personal thoughts or experiences. 
#     If the query is unrelated or unfamiliar to you, smoothly shift the conversation to something you both enjoy or can relate to.
# ''')
# from langchain_ollama import OllamaLLM

# llm = OllamaLLM(model='llama3.2')
# response = (prompt | llm).stream({'query': query})
# for chunk in response:
#     print(chunk, flush=True, end="")

# for chunk in agent_executor.stream(
#     {"messages": [HumanMessage(content="Yes, i want to order a lemon soda.")]}, config
# ):
#     print(chunk)
#     print("----")



# import os
# os.system("")  # enables ansi escape characters in terminal

# COLOR = {
#     "HEADER": "\033[95m",
#     "BLUE": "\033[94m",
#     "GREEN": "\033[92m",
#     "RED": "\033[91m",
#     "ENDC": "\033[0m",
# }

# print(COLOR["GREEN"], "Testing Green!!", COLOR["ENDC"])
# from app import socketio

# async def run(usermsg):
#     returned_output = []
#     async for event in agent_executor.astream_events({"messages": [{"role": "user", "content": usermsg}]}, config=config, version="v2"):
#         # kind = event["event"]
#         # if kind == "on_chat_model_stream":
#         #     print(event, end="|", flush=True)
#         # print(COLOR["GREEN"], event, COLOR["ENDC"])  # Log all events to inspect their structure
#         if event["event"] == "on_chat_model_stream":
#             # print(event.get("data", {}).get("chunk", {}).get("content", ""), end="|", flush=True)
#             print(COLOR["HEADER"], event["data"]["chunk"].content, COLOR["ENDC"], end="|", flush=True)
#             socketio.emit('chat_model_stream', {'message': event["data"]["chunk"].content})
#             returned_output.append(['chat_model_stream', {'message': event["data"]["chunk"].content}])

#         elif event["event"] == "on_tool_start":  
#             print(COLOR["BLUE"], "tool is being called", COLOR["ENDC"])
#             socketio.emit('tool_start', {'message': 'tool to assist in ordering has been called'})
#             returned_output.append('tool_start', {'message': 'tool to assist in ordering has been called'})

#         elif event["event"] == "on_tool_end":  # Relax filter for debugging
#             print(COLOR["BLUE"], "tool calling has ended", COLOR["ENDC"])
#             socketio.emit('tool_end', {'message': 'tool to assist in ordering has been called'})
#             returned_output.append('tool_end', {'message': 'tool to assist in ordering has been called'})
    
#     # Return the final output from the task
#     final_result = {'status': 'done', 'message': 'Task is complete!', 'history': returned_output}
    
#     # Emit the final result after processing
#     socketio.emit('task_complete', final_result)
#     return returned_output

        # if event["metadata"].get("langgraph_node") == "tools":
        #     print(COLOR["BLUE"], event["data"]["chunk"].content, COLOR["ENDC"], end="|", flush=True)



# async def run_with_await(usermsg):
#     try:
#         logging.info(f"Running with user message: {usermsg}")
#         await run(usermsg)
#     except Exception as e:
#         logging.error(f"Error in run_with_await: {e}")
#         raise  # Optionally raise or handle the exception as needed
# asyncio.run(run("Can i order 1 beef burger, no special requests"))
# print(f"a is now {a}")