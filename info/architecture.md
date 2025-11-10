# Architecture Notes
- Manager pattern: main-auditor -> specialist agents
- MCP-first: all side effects via servers
- Least privilege and dry-run-first


# SDK OVERVIEW**

To install a certain level of guardrails around our project wer are using
- https://github.com/GuardiAgent/python-mcp-sandbox-openai-sdk 
which provides an SDK to use an MCP sandbox in conjunction with the openIA Agent SDK. 

The openAI Agent SDK which we are going to use is:
https://github.com/openai/openai-agents-python

To connect components inside the project and calling external services we will use the MCP Protocol. 
There’s an SDK for python: https://github.com/modelcontextprotocol/python-sdk


# ENVIRONEMTN Notes
- Use .env file to store environment variables
- Use .gitignore to avoid committing sensitive information
- Using uv manager to manage python project environment
- Using sqlite for local development database


