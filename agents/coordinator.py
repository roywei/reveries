from .prompts.system_prompts import COORDINATOR_INSTRUCTIONS


class CoordinatorAgent:
    def __init__(self, client, model="gpt-4-1106-preview"):
        self.client = client
        self.model = model
        self.assistant = self.create_assistant()

    def create_assistant(self):
        return self.client.beta.assistants.create(
            name="CoordinatorAgent",
            instructions=COORDINATOR_INSTRUCTIONS,
            model=self.model,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "callPlanner",
                        "description": "call Planner to breakdown task into step by step plan, recap the plan or update the plan",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "callExecutor",
                        "description": "call exectuor to write code or call external APIs to complete a single step/task",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "callIntrospector",
                        "description": "call Introspector to review, reflect, and analyze the currenct sitation, provide feedback and help with next action",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "callMemorizer",
                        "description": "call Memorizer to retrieve and provide context for current problem or update the knowledge base for future use",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                },
            ],
        )

    def create_thread(self):
        return self.client.beta.threads.create()

    def run(self, thread_id, instructions):
        return self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant.id,
            instructions=instructions,
        )

    def retrieve_run(self, thread_id, run_id):
        return self.client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run_id
        )

    def post_message(self, thread_id, content, role="user"):
        return self.client.beta.threads.messages.create(
            thread_id=thread_id, role=role, content=content
        )

    def list_messages(self, thread_id):
        return self.client.beta.threads.messages.list(thread_id=thread_id)
