import json
import os
from dotenv import load_dotenv

from agent.openrouter_client import OpenRouterClient
from agent.config import DEFAULT_MODEL, MAX_TOOL_ITERATIONS, SYSTEM_PROMPT_PATH

load_dotenv()


class Agent:
    def __init__(self, tools: list, verbose: bool = False):
        self.verbose = verbose
        self.client = OpenRouterClient(model=os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL))
        self.tools = tools
        self.tool_schemas = [tool.to_schema() for tool in tools]
        self.tool_map = {tool.name: tool for tool in tools}
        self.messages = []
        self._load_system_prompt()

    def _load_system_prompt(self):
        if os.path.exists(SYSTEM_PROMPT_PATH):
            with open(SYSTEM_PROMPT_PATH) as f:
                self.messages.append({"role": "system", "content": f.read().strip()})

    def run(self):
        print("Agent: Hello! I'm here to help connect you with our investment advisory team. May I start with your name?")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            if not user_input:
                continue
            self._step(user_input)

    def _step(self, user_input: str):
        for tool in self.tools:
            tool.reset()

        self.messages.append({"role": "user", "content": user_input})

        for iteration in range(MAX_TOOL_ITERATIONS):
            if self.verbose:
                print(f"[verbose] iteration {iteration + 1}")

            active_schemas = [s for tool, s in zip(self.tools, self.tool_schemas) if not tool.disabled]
            message = self.client.complete(self.messages, tools=active_schemas or None)
            self.messages.append(message)

            tool_calls = message.get("tool_calls")

            if not tool_calls:
                print(f"Agent: {message.get('content', '')}")
                return

            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                tool = self.tool_map.get(tool_name)

                if self.verbose:
                    print(f"[verbose] → {tool_name}({tool_args})")

                result = tool.run(**tool_args) if tool else {"error": f"Tool '{tool_name}' not found."}

                if self.verbose:
                    print(f"[verbose] ← {result}")

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result),
                })
