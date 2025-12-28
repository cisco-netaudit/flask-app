"""
LLM Prompt Template for Generating Netaudit Checks (v2)
------------------------------------------------------

Copy and paste this template into a new chat with an LLM to generate
network audit checks for your Netaudit Flask app.

Replace all <PLACEHOLDER> fields with the desired values.
"""

CHECK_PROMPT_TEMPLATE = """
I want to create a new network audit check for my Flask app called Netaudit.

Framework Context:

1. Each check is a Python module containing a single class called CHECK_CLASS.

2. Each check class must define the following metadata variables:
   - NAME (str): Human-readable name of the check (auto-generated and refined)
   - VERSION (str): Version string (start with "1.0.0")
   - AUTHOR (str): Netaudit AI Assistant
   - TAGS (list[str]): Auto-generated tags based on the check purpose
   - DESCRIPTION (str): Refined, clear description of what the check validates
   - COMPLEXITY (int): Auto-determined complexity (1–5) based on number of handlers or command cycles

3. Execution Model:
   - Each check uses REQUESTS and RESULTS dictionaries.
   - REQUESTS defines the command to execute and the handler to process output.
   - RESULTS captures the final outcome.
   - Handlers are methods that process command output and update RESULTS and REQUESTS.
   - The main program will import the module and reads CHECK_CLASS, reads metadata and executes REQUESTS.

4. RESULTS (dict): Holds the result of the check
   RESULTS must be structured as:
   {
       "status": int,
       "observation": str,
       "comments": list[str]
   }

   Use the following status codes:
   - 0 → NOT_RUN (Check has not executed yet)
   - 1 → PASS (Check conditions fully satisfied)
   - 2 → FAIL (Check conditions violated)
   - 3 → WARN (Partial compliance, risk detected, or best-practice deviation)
   - 4 → INFO (Informational check (no pass/fail semantics))
   - 5 → ERROR (Execution/parsing error, command failed, unexpected output)
   - 6 → INCONCLUSIVE (Output insufficient or ambiguous)

   Choose the most accurate status based on findings.

5. REQUESTS (dict): Current work request to be executed by the main program
    REQUESTS must be structured as:
   {
       "device": self.device,
       "command": "<AUTO-INFERRED_COMMAND>",
       "handler": "handle_initial"
   }

6. Handlers:
   - Handlers are methods inside the class.
   - Signature:
       handler(self, device: str, command: str, output: str)
   - Use Python standard libraries only (especially `re`).
   - Update RESULTS inside handlers.
   - Clear REQUESTS (set to None) when the check is complete.

7. Initialization:
   - __init__(self, device, context=None)
   - The device is fixed at initialization and reused.
   - context may contain credentials, API objects, or external data.

8. Command Inference Rules:
   - Infer the CLI command from DESCRIPTION and TAGS.
   - Use industry-standard commands.
   - Examples:
       - Interfaces → "show interfaces"
       - Routing → "show ip route"
       - NTP → "show ntp status"
       - BGP → "show bgp summary"

9. Parsing Guidance:
   - Use regex (`re`) for structured parsing.
   - Handle unexpected or empty output gracefully.
   - Set status to ERROR or INCONCLUSIVE if parsing fails.

10. Comments Requirement:
    - RESULTS["comments"] must contain actionable, detailed guidance.
    - Include:
        - Evidence from output
        - Why it matters
        - Clear remediation steps or next actions
        - Example CLI/config snippets when possible

Template Reference:

class ExampleCheck:
    NAME = "Example Check"
    VERSION = "1.0.0"
    AUTHOR = "Netaudit AI Assistant"
    TAGS = ["Example"]
    DESCRIPTION = "Example audit check"
    COMPLEXITY = 1

    def __init__(self, device, context=None):
        self.device = device
        self.context = context or {}
        self.REQUESTS = {
            "device": self.device,
            "command": "show example",
            "handler": "handle_initial"
        }
        self.RESULTS = {
            "status": 0,
            "observation": "",
            "comments": []
        }

    def handle_initial(self, device, cmd, output):
        # Analyze output, update RESULTS, optionally append new REQUESTS
        pass

CHECK_CLASS = ExampleCheck

Task:

- Generate a full Python module for a check with these input parameters:
   - DESCRIPTION: <INSERT_DESCRIPTION_HERE>
   - SAMPLE OUTPUT (OPTIONAL): <INSERT_SAMPLE_OUTPUT_HERE>
- The LLM should:
   1. Refine or improve the CHECK NAME, TAGS, and DESCRIPTION to make them more meaningful and complete.
   2. Use the SAMPLE OUTPUT (if provided) as additional context for command inference, handler logic, and parsing examples.
   3. Infer the appropriate CLI command automatically from the refined DESCRIPTION and TAGS.
   4. Determine the check COMPLEXITY automatically on a scale of 1–5 based on the number of handlers or command cycles used.
   5. Include handler(s) for multi-level execution if needed.
   6. Use `re` and standard-library modules for parsing.
   7. Ensure RESULTS are correctly updated and REQUESTS are cleared when done.
   8. Ensure each RESULT comment provides clear, actionable remediation whenever possible.
   9. Use context (self.context) if the check requires credentials, API objects, or additional data.
- Return only Python code ready to save as a .py file.
"""
