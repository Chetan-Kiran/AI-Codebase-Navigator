from tool_registry import Tools
from ai.groq_client import decide_tool

def mcp_router2(repo_path, user_message):
    # 1. NEW: Detection logic for UI-triggered "Explain" requests
    # This prevents the AI from incorrectly choosing 'risk_analysis' for code snippets
    is_selection_request = (
        "Explain this selected code" in user_message or 
        "Explain this specific" in user_message or
        "Explain this file" in user_message
    )

    if is_selection_request:
        tool_name = "repo_qa"
    else:
        # Ask the AI only for general chat questions
        raw_decision = decide_tool(user_message).lower().strip()
        
        # 2. Robust mapping to handle AI chatter (e.g., "I choose risk_analysis")
        if "risk" in raw_decision: tool_name = "risk_analysis"
        elif "summary" in raw_decision: tool_name = "commit_summary"
        elif "diff" in raw_decision: tool_name = "diff_analysis"
        elif "bug" in raw_decision: tool_name = "bug_origin"
        else: tool_name = "repo_qa"

    print(f"DEBUG: Final Decision -> {tool_name}")

    # 3. Get the tool from registry
    tool = Tools.get(tool_name)

    if not tool:
        # Fallback to repo_qa if the specific tool is missing
        tool = Tools.get("repo_qa")
        tool_name = "repo_qa"

    try:
        # 4. Execute tool
        if tool_name == "repo_qa":
            result = tool(repo_path, user_message)
        else:
            result = tool(repo_path)
            
        if result is None:
            return {"type": "error", "data": f"Tool '{tool_name}' returned no data."}

    except Exception as e:
        print(f"Tool Execution Error: {e}")
        return {"type": "error", "data": f"Failed to run {tool_name}: {str(e)}"}
    
    return {
        "type": tool_name,
        "data": result
    }

# def mcp_router2(repo_path, user_message):

#     tool_name = decide_tool(user_message).lower().strip()

#     if "risk" in tool_name: tool_name = "risk_analysis"
#     elif "summary" in tool_name: tool_name = "commit_summary"
#     elif "diff" in tool_name: tool_name = "diff_analysis"
#     elif "bug" in tool_name: tool_name = "bug_origin"
#     else: tool_name = "repo_qa" # <--- DEFAULT FALLBACK

#     print(f"Decided tool: {tool_name}")  # Debug print to check the decided tool
#     tool = Tools.get(tool_name)

#     print("AI selected tool:", tool_name)

#     if not tool:
#         return {"type": "error", "data": "I couldn't find the right tool to explain that."}
    
#     if tool_name == "repo_qa":
#         result = tool(repo_path, user_message)
#     else:
#         result = tool(repo_path)
#     #handel fall back if tool execution fails or returns None
#     if result is None:
#         return {"error": f"Tool '{tool_name}' execution failed."}
    
#     return {
#         "type": tool_name,
#         "data": result
#     }
        