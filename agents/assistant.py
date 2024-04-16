"""
Implementation of Agent
"""

import os
import json
import anthropic
from dotenv import load_dotenv

from tools import TOOLS, TOOL_EXPLAINATION, calculate
from prompts.system_prompts import COMMANDER_NARRATIVE, EXECUTOR_NARRATIVE

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL_NAME = "claude-3-opus-20240229"


class Host:
    """
    The host of artificial super intelligent,
    consists of commander and executor
    """

    def __init__(self, model=MODEL_NAME):
        self.model = model
        self.memory = []
        self.history = []
        self.components = []
        self.plan = []

    def convert_hisotry_to_messages(self):
        """
        Format the conversation history into a single readable string
        """
        formatted_output = ""
        for message in self.history:
            formatted_output += (
                f"[{message['role'].capitalize()}]: {message['content']}\n"
            )
        return formatted_output.strip()

    def process_tool_call(self, tool_name, tool_input):
        """
        Process the tool call based on the tool name
        """
        if tool_name == "code executor":
            raise NotImplementedError("Code executor tool is not implemented yet")
        elif tool_name == "calculator":
            return calculate(tool_input["expression"])
        else:
            raise ValueError(f"Unknown tool name: {tool_name}")

    def format_plan(self):
        """
        Format the plan into a readable string
        """
        formatted_output = ""
        for task in self.plan:
            dependencies = (
                ", ".join(task["dependencies"]) if task["dependencies"] else "None"
            )
            formatted_output += f"Task Name: {task['name']}\nDescription: {task['description']}\nState: {task['state']}\nDependencies: {dependencies}\n\n"
        return formatted_output.strip()

    def call_commander(self):
        """
        Call the commander to generate a long term plan or update the current plan
        """
        if len(self.plan) > 0:
            message = (
                self.convert_hisotry_to_messages()
                + "\nThe current plan is:"
                + self.format_plan()
            )
        else:
            message = self.convert_hisotry_to_messages()

        print("messages to commander is ", message)
        response = client.beta.tools.messages.create(
            model=self.model,
            max_tokens=4096,
            system=COMMANDER_NARRATIVE,
            messages=[{"role": "user", "content": message}],
        )

        response_data = next(
            (block.text for block in response.content if hasattr(block, "text")),
            None,
        )

        if "CONTINUE" in response_data:
            return "CONTINUE"
        # parse response data
        try:
            # extract json string from response data
            if "```json" in response_data:
                json_data = response_data.split("```json")[1].split("```")[0]
                data_dict = json.loads(json_data)
                # get rest of the message
                message = (
                    response_data.split("```json")[0] + response_data.split("```")[1]
                )
            else:
                data_dict = json.loads(response_data)
                message = ""

        except Exception as e:
            print("response data is", response_data)
            raise ValueError("Invalid response data from commander") from e

        print("data_dict is", data_dict)
        self.plan = data_dict.get("plan", [])
        self.history.append({"role": "Commander", "content": message})
        self.history.append(
            {"role": "Commander", "content": "instruction: " + data_dict["instruction"]}
        )
        self.history.append(
            {"role": "Commander", "content": "the plan is: " + data_dict["plan"]}
        )
        return response_data

    def chat(self):
        """
        Start a conversation with the host
        """
        while True:
            user_message = input("User: ")
            if user_message.lower() in ["quit", "exit", "bye"]:
                print("ending conversation")
                break
            if len(user_message) > 0:

                self.history.append({"role": "user", "content": user_message})
                # messages contains a single round of conversations
                # stisfy the alternating role API requirement
                messages = [
                    {"role": "user", "content": self.convert_hisotry_to_messages()}
                ]
                message = client.beta.tools.messages.create(
                    model=self.model,
                    system=EXECUTOR_NARRATIVE,
                    max_tokens=4096,
                    # convert all multi-party messages history as a single message
                    # claude api only allows alternative user and assistant roles
                    messages=messages,
                    tools=TOOLS,
                )

                # enter tool use loop
                if message.stop_reason == "tool_use":
                    print("\nTool Use Requested")
                    tool_use = next(
                        block for block in message.content if block.type == "tool_use"
                    )
                    tool_name = tool_use.name
                    tool_input = tool_use.input

                    print(f"\nTool Used: {tool_name}")
                    print(f"Tool Input: {tool_input}")
                    # assistant's thinking for the tool use
                    thinking = next(
                        (
                            block.text
                            for block in message.content
                            if hasattr(block, "text")
                        ),
                        None,
                    )
                    messages.append({"role": "assistant", "content": message.content})
                    self.history.append({"role": "Executor", "content": thinking})

                    if tool_name == "commander":
                        commander_response_string = self.call_commander()
                        messages.append(
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_use.id,
                                        "content": commander_response_string,
                                    }
                                ],
                            }
                        )
                        print(
                            "Inside tool use commander: history is now: ", self.history
                        )
                    else:
                        tool_result = self.process_tool_call(tool_name, tool_input)
                        print(f"\nTool Result: {tool_result}")
                        messages.append(
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_use.id,
                                        "content": tool_result,
                                    }
                                ],
                            }
                        )
                        self.history.append(
                            {
                                "role": "Tool use result (" + tool_name + ")",
                                "content": tool_result,
                            }
                        )
                        # final response after tool use
                        response = client.beta.tools.messages.create(
                            model=self.model,
                            max_tokens=4096,
                            system=EXECUTOR_NARRATIVE,
                            messages=messages,
                            tools=TOOLS,
                        )
                else:
                    # normal response
                    response = message

                final_response = next(
                    (
                        block.text
                        for block in response.content
                        if hasattr(block, "text")
                    ),
                    None,
                )
                self.history.append(
                    {
                        "role": "Executor",
                        "content": final_response if final_response else [],
                    }
                )
                print("End of executor turn")
                # check if commander want to say something
                commander_response = self.call_commander()
                if commander_response == "CONTINUE":
                    print("chat history is now:\n", self.convert_hisotry_to_messages())
                    continue
                print("chat history is now: \n", self.convert_hisotry_to_messages())


def main():
    """
    Main function to run the assistant
    """

    host = Host()
    host.chat()


if __name__ == "__main__":
    main()
