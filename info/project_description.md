Team members:  Julian Maximilian Göhre, Vito Emanuel Steiner
[Written with AI]
Agentic AI for Secure Configuration Management
Motivation
Configuration errors are one of the most common sources of security vulnerabilities in IT systems. While the underlying software and infrastructure may be robust, incorrect setup or access permissions can create loopholes for attackers. These mistakes often stem from the human factor: repetitive, error-prone workflows that lack consistent oversight.
Our project aims to explore how Agentic AI can support and partially automate such workflows to improve both efficiency and security.
Project Idea
We propose building a simplified corporate environment consisting of one or two database systems. This environment will simulate typical security-relevant workflows such as access control and configuration.
Important Note: The term MCP-Server refers not only to external Servers communication with by MCP but also to internal components (e.g. localhost or service in project) which are addressed by the MCP Protocol. 
Core Workflow
The project will use multiple AI agents with distinct responsibilities that interact through MCP and coordinate their tasks:
1.	Policy definition: A written access policy defines which team has access to which database tables (e.g., finance team → transaction, accounts, stock; sales team → customer, order; warehouse team → stock, procurement).
2.	Error injection: We will intentionally introduce configuration errors to simulate real-world mistakes.
3.	Agent tasks:
o	Auditor Agent: audits the database configuration against the written policy.
o	Reporter Agent: writes a detailed audit report and automatically sends it (e.g., via email).
o	Fixer Agent: reconfigures the database using Config-as-Code principles.
Extensions (if feasible)
•	Additional systems beyond databases: For example, a simulated cloud storage bucket or external module to broaden the applicability of Agentic AI beyond a single tool. Could be done using a docker container. 
•	Enhanced reporting: Have one agent write a detailed audit report in natural language and another agent generate a visual summary (e.g., access matrix, charts).
•	Automatic onboarding/offboarding: Manage user lifecycle events by automatically granting or revoking permissions according to policy.
•	Multi-agent specialization: Experiment with coordination patterns where different agents handle policy interpretation, auditing, reporting, and remediation separately.
Architectural Requirements (A)
•	A1 – Modular Structure:
o	Use MCP to connect the AI agents with tools (database, email, config-as-code, optional extensions).
o	Separate modules for policy definition, auditing, reporting, visualization, and reconfiguration.
•	A2 – Security Protection:
o	Define and enforce clear access permissions in advance.
o	Ensure that agents operate with restricted rights (least-privilege principle).
o	Adopt mechanisms for secure resource access (MCP Sandbox SDK).
Project Structure and Roadmap (B)
•	B1 – Modular and Incremental:
o	Start with a minimal local database and simple access policy.
o	Have a roadmap developed by a LLM. 
o	Extend step by step: add reporting, then reconfiguration, then onboarding and visualization.
o	Optional: integrate additional systems beyond the database.
•	B2 – AI Beyond Coding:
o	Use AI for breaking down tasks and defining module interfaces.
o	Support in software design and testing (audit scenarios).
o	Optimize performance and extend tool integration.
Expected Outcome
By the end of the project, we expect to demonstrate how Agentic AI can automate security-critical configuration workflows. The system should be able to detect misconfigurations, document them in both technical and executive-friendly formats, and take corrective action in a controlled, auditable manner.
Extensions will show how the approach scales to multiple systems and user lifecycle management.

