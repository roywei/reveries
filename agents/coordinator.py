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
