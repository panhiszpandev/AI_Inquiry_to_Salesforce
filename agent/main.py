import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agent.agent import Agent
from agent.tools.save_field import SaveFieldTool
from agent.tools.finish_conversation import FinishConversationTool


def main():
    inquiry_data = {}
    tools = [
        SaveFieldTool(inquiry_data),
        FinishConversationTool(inquiry_data),
    ]
    agent = Agent(tools=tools, verbose="--verbose" in sys.argv)
    agent.run()


if __name__ == "__main__":
    main()
