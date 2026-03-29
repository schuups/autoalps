import asyncio
from fastmcp import Client

client = Client("http://localhost:8888/mcp")


async def list_tools():
    async with client:
        tools = await client.list_tools()
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")


async def get_systems():
    async with client:
        result = await client.call_tool("get_systems", {})
        print("Systems:", result)


async def main():
    await list_tools()
    print()
    await get_systems()


asyncio.run(main())
