# #!/usr/bin/env python3
# """
# A live, hostable uAgent that integrates with the ASI:One network.
# It uses a MeTTa knowledge graph and a multi-step planner to execute
# optimal cross-border financial transactions.
# """
# import os
# import json
# import requests
# import dotenv
# import uuid
# from hyperon import MeTTa

# # Import uagents components
# from uagents import Agent, Context, Model, Protocol

# # Import our knowledge graph and RAG modules
# from knowledge import initialize_financial_knowledge_graph
# from financerag import FinancialRAG

# from uagents_core.contrib.protocols.chat import (
#     ChatAcknowledgement,
#     ChatMessage,
#     TextContent,
#     chat_protocol_spec,
# )

# chat_proto = Protocol(spec=chat_protocol_spec)
# # --- Initialization ---
# dotenv.load_dotenv()
# metta = MeTTa()
# initialize_financial_knowledge_graph(metta)
# financial_rag = FinancialRAG(metta)

# BASE_URL = "https://api.asi1.ai/v1"
# API_KEY = os.getenv("ASI_ONE_API_KEY")
# MODEL = "asi1-fast-agentic"
# print(f"may api key:",API_KEY)
# # --- Tool Definitions (Local Python Functions) ---
# # These are the capabilities of our agent.

# def fetch_and_update_realtime_rates() -> str:
#     """
#     Fetches the latest currency conversion rates and updates the agent's knowledge graph.
#     """
#     print("\n[TOOL LOG] Fetching real-time rates from external API...")
#     mock_api_response = {
#         "INR-ETH": 1 / 285000.0, "ETH-USD": 3550.0,
#         "INR-MATIC": 1 / 58.0, "MATIC-USD": 0.72,
#     }
#     for pair, rate in mock_api_response.items():
#         from_curr, to_curr = pair.split('-')
#         financial_rag.update_rate(from_curr, to_curr, rate)
#     return json.dumps({"status": "success", "message": "Knowledge graph updated with latest market rates."})

# def find_best_conversion_path(from_currency: str, to_currency: str) -> str:
#     """Finds the most cost-effective intermediate currency for a conversion."""
#     print(f"\n[TOOL LOG] Finding best path from {from_currency} to {to_currency}...")
#     path = financial_rag.find_best_path(from_currency.upper(), to_currency.upper())
#     if path: return json.dumps({"status": "success", "best_path_via": path})
#     return json.dumps({"status": "error", "message": "No valid conversion path found."})

# def convert_and_transfer(from_currency: str, to_currency: str, from_address: str, to_address: str, amount: float) -> str:
#     """Simulates a conversion using the latest rates from the knowledge graph."""
#     rate = financial_rag.get_exchange_rate(from_currency.upper(), to_currency.upper())
#     if rate is None: return json.dumps({"status": "error", "message": f"No rate found for {from_currency}->{to_currency}."})
#     output_amount = amount * rate
#     print(f"\n[TOOL LOG] Converting {amount:.2f} {from_currency} to {output_amount:.6f} {to_currency}...")
#     return json.dumps({"status": "success", "amount_in": amount, "amount_out": output_amount})


# # --- Tool Schemas for the Model ---
# update_rates_func = {"type": "function","function": {"name": "fetch_and_update_realtime_rates","description": "Use this tool first to get the latest market conversion rates before making any decisions.","parameters": {"type": "object","properties": {},"required": []}}}
# find_best_path_func = {"type": "function","function": {"name": "find_best_conversion_path","description": "After getting rates, use this tool to find the cheapest conversion path.","parameters": {"type": "object","properties": {"from_currency": {"type": "string","description": "The source currency code (e.g., 'INR')."},"to_currency": {"type": "string","description": "The final target currency code (e.g., 'USD')."}},"required": ["from_currency", "to_currency"]}}}
# convert_func = {"type": "function","function": {"name": "convert_and_transfer","description": "Converts an amount from a source to a target currency. Use this for each step of the path.","parameters": {"type": "object","properties": {"from_currency": {"type": "string","description": "The source currency for this specific conversion step (e.g., 'INR', 'ETH')."},"to_currency": {"type": "string","description": "The target currency for this specific conversion step (e.g., 'ETH', 'USD')."},"from_address": {"type": "string","description": "Sender's account identifier."},"to_address": {"type": "string","description": "Receiver's account identifier."},"amount": {"type": "number","description": "The amount in the source currency to be converted."}},"required": ["from_currency", "to_currency", "from_address", "to_address", "amount"]}}}


# # --- uAgent Definition ---

# # 1. Define the message model for incoming queries
# class TransactionRequest(Model):
#     text: str

# # 2. Create the agent instance
# agent = Agent(
#     name="financial_transaction_agent",
#     port=8000,
#     seed="financial_agent_secret_phrase",
#     endpoint=["http://127.0.0.1:8000/submit"],
# )

# # 3. The main message handler - this is where your core logic lives now
# @agent.on_message(model=TransactionRequest)
# async def handle_transaction_request(ctx: Context, sender: str, msg: TransactionRequest):
#     ctx.logger.info(f"Received transaction request from {sender}: '{msg.text}'")
    
#     session_id = str(uuid.uuid4())
#     headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "X-Session-Id": session_id}
    
#     messages = [
#         {"role": "system", "content": "You are an intelligent financial agent. Your goal is to execute a currency conversion from INR to USD. You MUST follow this plan: 1. Call `fetch_and_update_realtime_rates` to get current data. 2. Call `find_best_conversion_path` to choose the optimal route. 3. Create a plan to call `convert_and_transfer` for each leg of the journey (e.g., INR->best_path, and best_path->USD). You must reason about the amounts for each step."},
#         {"role": "user", "content": msg.text}
#     ]
    
#     available_tools = {
#         "fetch_and_update_realtime_rates": fetch_and_update_realtime_rates,
#         "find_best_conversion_path": find_best_conversion_path,
#         "convert_and_transfer": convert_and_transfer
#     }
    
#     max_turns = 5
#     turn_count = 0

#     while turn_count < max_turns:
#         turn_count += 1
#         ctx.logger.info(f"--- Agent Turn {turn_count} ---")

#         try:
#             payload = {"model": MODEL, "messages": messages, "tools": [update_rates_func, find_best_path_func, convert_func], "use_planner": True}
#             response = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload)
#             response.raise_for_status()
#             response_json = response.json()

#             if "choices" not in response_json or not response_json["choices"]:
#                 await ctx.send(sender, {"error": response_json.get("message", "No choices returned.")})
#                 return
            
#             response_message = response_json["choices"][0]["message"]
#             messages.append(response_message)
            
#             if not response_message.get("tool_calls"):
#                 final_answer = response_message.get('content')
#                 ctx.logger.info(f"--- Final Response --- \nAssistant: {final_answer}")
#                 await ctx.send(sender, {"response": final_answer})
#                 return

#             tool_outputs = []
#             for call in response_message["tool_calls"]:
#                 func_name = call["function"]["name"]
#                 args_str = call["function"].get("arguments", "{}")
#                 args = json.loads(args_str)
#                 tool_to_call = available_tools.get(func_name)
                
#                 if tool_to_call: result = tool_to_call(**args)
#                 else: result = json.dumps({"status": "error", "message": f"Unknown tool: {func_name}"})
                
#                 tool_outputs.append({"tool_call_id": call["id"], "role": "tool", "name": func_name, "content": result})

#             messages.extend(tool_outputs)

#         except Exception as e:
#             ctx.logger.error(f"An error occurred: {e}")
#             await ctx.send(sender, {"error": str(e)})
#             return



# # 4. Run the agent
# if __name__ == "__main__":
#     agent.include(chat_proto, publish_manifest=True)
#     agent.run()

#!/usr/bin/env python3

"""
A live, hostable uAgent that integrates with the ASI:One network using the Chat Protocol.
It uses a MeTTa knowledge graph and a multi-step planner to execute
optimal cross-border financial transactions.
"""
import os
import json
import requests
import dotenv
import uuid
from datetime import datetime
from hyperon import MeTTa

# Import uagents components
from uagents import Agent, Context, Protocol, Bureau
from uagents.setup import fund_agent_if_low

# Import the Chat Protocol components
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

# Import our knowledge graph and RAG modules
from knowledge import initialize_financial_knowledge_graph
from financerag import FinancialRAG

# --- Initialization ---
dotenv.load_dotenv()
metta = MeTTa()
initialize_financial_knowledge_graph(metta)
financial_rag = FinancialRAG(metta)

BASE_URL = "https://api.asi1.ai/v1"
API_KEY = os.getenv("ASI_ONE_API_KEY")
MODEL = "asi1-mini"

# --- Tool Definitions (Local Python Functions) ---
def fetch_and_update_realtime_rates() -> str:
    """
    Fetches the latest currency conversion rates and updates the agent's knowledge graph.
    """
    print("\n[TOOL LOG] Fetching real-time rates from external API...")
    mock_api_response = {
        "INR-ETH": 1 / 285000.0, "ETH-USD": 3550.0,
        "INR-MATIC": 1 / 58.0, "MATIC-USD": 0.72,
    }
    for pair, rate in mock_api_response.items():
        from_curr, to_curr = pair.split('-')
        financial_rag.update_rate(from_curr, to_curr, rate)
    return json.dumps({"status": "success", "message": "Knowledge graph updated with latest market rates."})

def find_best_conversion_path(from_currency: str, to_currency: str) -> str:
    """Finds the most cost-effective intermediate currency for a conversion."""
    print(f"\n[TOOL LOG] Finding best path from {from_currency} to {to_currency}...")
    path = financial_rag.find_best_path(from_currency.upper(), to_currency.upper())
    if path: return json.dumps({"status": "success", "best_path_via": path})
    return json.dumps({"status": "error", "message": "No valid conversion path found."})

def convert_and_transfer(from_currency: str, to_currency: str, from_address: str, to_address: str, amount: float) -> str:
    """Simulates a conversion using the latest rates from the knowledge graph."""
    rate = financial_rag.get_exchange_rate(from_currency.upper(), to_currency.upper())
    if rate is None: return json.dumps({"status": "error", "message": f"No rate found for {from_currency}->{to_currency}."})
    output_amount = amount * rate
    print(f"\n[TOOL LOG] Converting {amount:.2f} {from_currency} to {output_amount:.6f} {to_currency}...")
    return json.dumps({"status": "success", "amount_in": amount, "amount_out": output_amount})

# --- Tool Schemas for the Model ---
update_rates_func = {"type": "function","function": {"name": "fetch_and_update_realtime_rates","description": "Use this tool first to get the latest market conversion rates before making any decisions.","parameters": {"type": "object","properties": {},"required": []}}}
find_best_path_func = {"type": "function","function": {"name": "find_best_conversion_path","description": "After getting rates, use this tool to find the cheapest conversion path.","parameters": {"type": "object","properties": {"from_currency": {"type": "string","description": "The source currency code (e.g., 'INR')."},"to_currency": {"type": "string","description": "The final target currency code (e.g., 'USD')."}},"required": ["from_currency", "to_currency"]}}}
convert_func = {"type": "function","function": {"name": "convert_and_transfer","description": "Converts an amount from a source to a target currency. Use this for each step of the path.","parameters": {"type": "object","properties": {"from_currency": {"type": "string","description": "The source currency for this specific conversion step (e.g., 'INR', 'ETH')."},"to_currency": {"type": "string","description": "The target currency for this specific conversion step (e.g., 'ETH', 'USD')."},"from_address": {"type": "string","description": "Sender's account identifier."},"to_address": {"type": "string","description": "Receiver's account identifier."},"amount": {"type": "number","description": "The amount in the source currency to be converted."}},"required": ["from_currency", "to_currency", "from_address", "to_address", "amount"]}}}


# --- uAgent Definition with Chat Protocol ---

# 1. Create the agent
agent = Agent(
    name="financial_transaction_agent",
    seed="financial_agent_secret_phrase",
)
fund_agent_if_low(agent.wallet.address())

# 2. Create the protocol instance using the standard chat specification
chat_proto = Protocol("FinancialTransactionChat", spec=chat_protocol_spec)

# 3. Define the main message handler for the chat protocol
@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    # Send an acknowledgement that we received the message
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))

    # Extract the text from the message content
    user_query = ""
    for item in msg.content:
        if isinstance(item, TextContent):
            user_query += item.text
    
    ctx.logger.info(f"Received transaction request from {sender}: '{user_query}'")

    # Start the multi-turn conversation with the planner
    session_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "X-Session-Id": session_id}
    
    messages = [
        {"role": "system", "content": "You are an intelligent financial agent. Your goal is to execute a currency conversion from INR to USD. You MUST follow this plan: 1. Call `fetch_and_update_realtime_rates` to get current data. 2. Call `find_best_conversion_path` to choose the optimal route. 3. Create a plan to call `convert_and_transfer` for each leg of the journey (e.g., INR->best_path, and best_path->USD). You must reason about the amounts for each step."},
        {"role": "user", "content": user_query}
    ]
    
    available_tools = {
        "fetch_and_update_realtime_rates": fetch_and_update_realtime_rates,
        "find_best_conversion_path": find_best_conversion_path,
        "convert_and_transfer": convert_and_transfer
    }
    
    max_turns = 5
    turn_count = 0

    while turn_count < max_turns:
        turn_count += 1
        ctx.logger.info(f"--- Agent Turn {turn_count} ---")

        try:
            payload = {"model": MODEL, "messages": messages, "tools": [update_rates_func, find_best_path_func, convert_func], "use_planner": True}
            response = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            response_json = response.json()

            if "choices" not in response_json or not response_json["choices"]:
                error_msg = f"API Error: {response_json.get('message', 'No choices returned from model.')}"
                await ctx.send(sender, ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid.uuid4(), content=[TextContent(text=error_msg), EndSessionContent()]))
                return
            
            response_message = response_json["choices"][0]["message"]
            messages.append(response_message)
            
            if not response_message.get("tool_calls"):
                final_answer = response_message.get('content', "Process complete.")
                ctx.logger.info(f"--- Final Response --- \nAssistant: {final_answer}")
                await ctx.send(sender, ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid.uuid4(), content=[TextContent(text=final_answer), EndSessionContent()]))
                return

            tool_outputs = []
            for call in response_message["tool_calls"]:
                func_name = call["function"]["name"]
                args_str = call["function"].get("arguments", "{}")
                args = json.loads(args_str)
                tool_to_call = available_tools.get(func_name)
                
                if tool_to_call:
                    result = tool_to_call(**args)
                else:
                    result = json.dumps({"status": "error", "message": f"Unknown tool: {func_name}"})
                
                tool_outputs.append({"tool_call_id": call["id"], "role": "tool", "name": func_name, "content": result})

            messages.extend(tool_outputs)

        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}"
            ctx.logger.error(error_msg)
            await ctx.send(sender, ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid.uuid4(), content=[TextContent(text=error_msg), EndSessionContent()]))
            return

# 4. Add a handler for acknowledgements (optional but good practice)
@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

# 5. Include the protocol in the agent
agent.include(chat_proto, publish_manifest=True)

# 6. Run the agent 
if __name__ == "__main__":
    agent.run()