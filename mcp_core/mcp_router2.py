from tool_registry import Tools
from ai.groq_client import decide_tool

def mcp_router2(repo_path, user_message):
    message = user_message.lower()

    # ✅ UI-trigger detection (VERY IMPORTANT)
    if any(x in message for x in [
        "selected code",
        "this file",
        "this function",
        "explain this"
    ]):
        tool_name = "repo_qa"
    else:
        tool_name = decide_tool(user_message)

    print(f"DEBUG: Tool Selected -> {tool_name}")

    tool = Tools.get(tool_name, Tools["repo_qa"])

    try:
        # ✅ EXECUTION
        if tool_name == "repo_qa":
            result = tool(repo_path, user_message)
        else:
            result = tool(repo_path)

        # ✅ HANDLE EMPTY RESULTS
        if not result or str(result).strip() == "":
            return {
                "type": tool_name,
                "data": "No meaningful data found for this request."
            }

    except Exception as e:
        print("ERROR:", e)
        return {
            "type": "error",
            "data": f"{tool_name} failed: {str(e)}"
        }

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
        