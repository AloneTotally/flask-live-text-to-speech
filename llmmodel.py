from langchain_ollama import ChatOllama

llm = ChatOllama(
    # model="llama3.2",
    model='llama3-groq-tool-use'
)

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
    item_name = " ".join(w.capitalize() for w in item_name.split())
    if item_name in menu:  # Assuming `menu` is a predefined dictionary with food items
        if item_name in orders:
            orders[item_name]["quantity"] += quantity
            orders[item_name]["special_requests"].append(special_requests)
        else:
            orders[item_name] = {
                "quantity": quantity,
                "special_requests": [special_requests],
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
- If the input involves placing, viewing, or canceling an order, use the following tools:
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
'Milkshake': 5.0"""

memory = MemorySaver()
agent_executor = create_react_agent(llm, tools=tools, checkpointer=memory, state_modifier=template)
config = {"configurable": {"thread_id": "testinglololololololol"}}
# Use the agent
# for chunk in agent_executor.stream(
#     {"messages": [HumanMessage(content="What food do you have?")]}, config
# ):
#     print(chunk)
#     print("----")

for chunk in agent_executor.stream(
    {"messages": [HumanMessage(content="Yes, i want to order a lemon soda.")]}, config
):
    print(chunk)
    print("----")
