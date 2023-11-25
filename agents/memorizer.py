class MemorizerAgent:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    def update_knowledge_base(self, thread_id, updates):
        instructions = f"Update knowledge base with: {updates}"
        return self.coordinator.run(thread_id, instructions)
