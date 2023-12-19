from .prompts.system_prompts import COORDINATOR_INSTRUCTIONS, EXECUTROR_INSTRUCTIONS, PLANNER_INSTRUCTIONS, INTROSPECTOR_INSTRUCTIONS, MEMORIZER_INSTRUCTIONS
class CoordinatorAgent:
    def __init__(self, client, model="gpt-4-1106-preview"):
        self.client = client
        self.model = model
        self.coordinator = self.create_assistant()
        self.executor = self.client.beta.assistants.create(
            name = "executor",
            instructions=EXECUTROR_INSTRUCTIONS,
            model=self.model,
            tools=[{"type": "code_interpreter"}]
        )
        self.planner = self.client.beta.assistants.create(
            name = "planner",
            instructions=PLANNER_INSTRUCTIONS,
            model=self.model
        )
        self.introspector = self.client.beta.assistants.create(
            name = "introspector",
            instructions=INTROSPECTOR_INSTRUCTIONS,
            model=self.model
        )
        self.memorizer = self.client.beta.assistants.create(
            name = "memorizer",
            instructions=MEMORIZER_INSTRUCTIONS,
            model=self.model,
            tools=[ 
                {
                    "type": "function",
                    "function": {
                        "name": "retrieve_memory",
                        "description": "call Planner to breakdown task into step by step plan, recap the plan or update the plan",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                }
                ]
        )

    def create_assistant(self):
        return self.client.beta.assistants.create(
            name="coordinator",
            instructions=COORDINATOR_INSTRUCTIONS,
            model=self.model,
            tools=[
                 {
                    "type": "function",
                    "function": {
  "name": "call_next_agent",
  "parameters": {
    "type": "object",
    "properties": {
      "explaination": {
        "type": "string",
        "description": "Explain the reason to choose this agent to take the next action"
      },
      "agent": {
        "type": "string",
        "enum": [
          "Planner",
          "Executor",
          "Memorizer",
          "Introspector"
        ],
        "description": "The name of the agent to call, must be one of Planner, Executor, Memorizer, and Introspector."
      },
      "instructions": {
        "type": "string",
        "description": "Instructions for the agent been called"
      }
    },
    "required": [
      "explaination",
      "agent",
      "instructions"
    ]
  },
  "description": "Call the next agent, give instructions to that agent and explainations why choose this agent"
}
}],
        )

    def create_thread(self):
        return self.client.beta.threads.create()

    def run(self, thread_id, instructions):
        return self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant.id,
            instructions=instructions,
        )

    def handle_run(self, thread_id, run_id):
        run_status = self.retrieve_run(thread_id, run_id).status
        if run_status == 'requires_action':
             self.invoke_next_agent(thread_id, run_id) 

    def invoke_next_agent(self, thread_id, run_id):
        # Logic to determine which agent function to call
        # This could be based on the content of the messages in the thread
        # For example, parsing the latest messages to decide if we need to plan, execute, introspect, or memorize
        latest_message = self.get_latest_message(thread_id)
        tool_call_id = run_id.required_action.submit_tool_outputs. [0]
        function_name = run_id.required_action.submit_tool_outputs.tool_calls[0].function.name
print(function_name + "\n" + function_arguments["time_stamp"] + "\n" +function_arguments["subject"]  + "\n" +function_arguments["description"] + "\n" +function_arguments["people"] + "\n" + function_arguments["feelings"])
        if "plan" in latest_message.content.lower():
            self.call_planner(thread_id, run_id)
        elif "execute" in latest_message.content.lower():
            self.call_executor(thread_id, run_id)
        elif "reflect" in latest_message.content.lower():
            self.call_introspector(thread_id, run_id)
        elif "memorize" in latest_message.content.lower():
            self.call_memorizer(thread_id, run_id)
        
    def retrieve_run(self, thread_id, run_id):
        return self.client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run_id
        )

    def list_messages(self, thread_id):
        return self.client.beta.threads.messages.list(thread_id=thread_id)
