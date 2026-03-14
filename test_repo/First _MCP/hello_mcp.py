# Import the FastMCP class from the mcp library
from mcp.server.fastmcp import FastMCP

# 1. Create our MCP Server. We will call it "My First Server"
mcp = FastMCP("My First Server")

# 2. Let's create a tool for the AI to use!
# The @mcp.tool() part tells the server that this function is an AI tool.
@mcp.tool()
def calculate_dog_years(human_years: int) -> str:
    """Calculate how old a dog is in dog years. (1 human year = 7 dog years)"""
    dog_years = human_years * 7
    return f"A dog that is {human_years} human years old is {dog_years} in dog years!"

# 3. Finally, start the server!
if __name__ == "__main__":
    mcp.run()
