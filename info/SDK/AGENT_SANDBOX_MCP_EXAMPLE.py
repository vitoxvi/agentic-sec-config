import os

from agents import Agent, Runner

from mcp_sandbox_openai_sdk import (
    FSAccess,
    MCPManifest,
    MCPServers,
    Permission,
    Registry,
    SandboxedMCPStdio,
)

# If there exists a manifest.json file, then you can use it.
# Since this manifest pracice is not yet widespread, we define it inline here.
manifest = MCPManifest(
    name="Filesystem Server",
    description="A server that access the local filesystem and allows interaction with all sorts of files.",
    registry=Registry.NPM,
    package_name="@modelcontextprotocol/server-filesystem",
    permissions=[
        Permission.MCP_AC_FILESYSTEM_READ,
        Permission.MCP_AC_FILESYSTEM_WRITE,
        Permission.MCP_AC_FILESYSTEM_DELETE,
    ],
)


async def main():
    async with MCPServers(
        SandboxedMCPStdio(
            manifest=manifest,
            runtime_args=[os.path.abspath("./")],
            runtime_permissions=[FSAccess(os.path.abspath("./"))],
        )
    ) as servers:
        agent = Agent(
            name="MCP Sandbox Test",
            model="gpt-5-mini",
            mcp_servers=servers,
        )

        prompt = f"""
            Read the files in the {os.path.abspath("./")} directory and
            list all the found files and directories of the first level.
            Do not decend recursively.
            Use the provided mcp servers to access the filesystem.
        """
        result = await Runner.run(
            agent,
            input=prompt,
        )
        print(result.final_output)


if __name__ == "__main__":
    import asyncio

    print("Execute Sandbox Demo")
    asyncio.run(main())
