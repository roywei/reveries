"""
Implementation of the host
"""

import os
import re
import json
import logging
import anthropic
from dotenv import load_dotenv

from tools import TOOLS, TOOL_EXPLAINATION, calculate
from prompts.system_prompts import COMMANDER_NARRATIVE, EXECUTOR_NARRATIVE

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL_NAME = "claude-3-opus-20240229"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Host:
    """
    The host of artificial super intelligent,
    consists of commander and executor
    """

    def __init__(self, model=MODEL_NAME, verbose=False, max_retry=2):
        self.model = model
        self.memory = []
        self.history = []
        self.components = []
        self.plan = []
        self.verbose = verbose
        self.max_retry = max_retry
        self.failed_commander_call = 0
        self.failed_executor_call = 0

    def convert_hisotry_to_messages(self):
        """
        Format the conversation history into a single readable string
        """
        # dump the history as a JSON string
        return json.dumps(self.history)

    def process_tool_call(self, tool_name, tool_input):
        """
        Process the tool call based on the tool name
        """
        if tool_name == "code executor":
            raise NotImplementedError("Code executor tool is not implemented yet")
        if tool_name == "calculator":
            return calculate(tool_input["expression"])
        raise ValueError(f"Unknown tool name: {tool_name}")

    def format_plan(self):
        """
        Format the plan into a readable string
        """
        return json.dumps(self.plan)

    def call_commander(self, additional_message=""):
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

        if additional_message:
            message += "\n" + additional_message

        if self.verbose:
            logger.info("Calling commander with message: %s", message)

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

        data_dict = self.find_and_parse_json(response_data)
        
        self.failed_commander_call = 0
        if "plan" in data_dict:
            self.plan = data_dict["plan"]
        self.history.append(data_dict)
        return data_dict

    def chat(self, user_message):
        """
        Start a conversation with the host
        """
        if len(user_message) > 0:
            self.history.append(
                {"from": "user", "to": "executor", "message": user_message}
            )

        # messages contains a single round of conversations
        # stisfy the alternating role API requirement and keep the speaking order flexible
        messages = [{"role": "user", "content": self.convert_hisotry_to_messages()}]
        message = client.beta.tools.messages.create(
            model=self.model,
            system=EXECUTOR_NARRATIVE,
            max_tokens=4096,
            messages=messages,
            tools=TOOLS,
        )

        # enter tool use loop
        if message.stop_reason == "tool_use":
            tool_use = next(
                block for block in message.content if block.type == "tool_use"
            )
            tool_name = tool_use.name
            tool_input = tool_use.input

            logger.info("\nTool Used: %s", tool_name)
            logger.info("Tool Input: %s", tool_input)

            messages.append({"role": "assistant", "content": message.content})
            tool_result = self.process_tool_call(tool_name, tool_input)
            logger.info("\nTool Result: %s", tool_result)
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
            # assistant's thinking for the tool use
            thinking = next(
                (block.text for block in message.content if hasattr(block, "text")),
                None,
            )
            self.history.append(
                {
                    "Tool use reason": thinking,
                    "Tool name": tool_name,
                    "Tool input": tool_input,
                    "Tool results": tool_result,
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
            (block.text for block in response.content if hasattr(block, "text")),
            None,
        )
        logger.info("End of executor turn")
        if self.verbose:
            logger.info("Final response from executor: %s", final_response)
        
        data_dict = self.find_and_parse_json(final_response)
        
        self.failed_executor_call = 0
        self.history.append(data_dict)
        # decide the next speaker
        next_speaker = data_dict.get("to")
        if next_speaker == "commander":
            self.call_commander()
        elif next_speaker == "user":
            return
        else:
            raise ValueError("Invalid next speaker", next_speaker)

    def find_and_parse_json(self, input_string):
        """
        Find and parse JSON object from the input string
        """
        if self.verbose:
            logger.info("Parsing JSON from input string: %s", input_string)
        try:
            # remove thinking in input string
            if "<thinking>" in input_string:
                input_string = input_string.split("</thinking>")[1].strip()
            if "```json" in input_string:
                input_string = input_string[input_string.find("```json")+len("```json"):input_string.rfind("```")]
            elif "{" in input_string:
                #for rest of the string extract eveyrthing after tht first { and before the last }
                # find first { and last } of the input string
                input_string = input_string[input_string.find("{"):input_string.rfind("}")+1]
            
            return json.loads(input_string)
        except Exception as e:
            # WIP: retry logic
            logger.warning("Invalid response data: %s", input_string)
            raise ValueError("Invalid response data from commander") from e
