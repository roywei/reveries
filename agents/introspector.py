class IntrospectorAgent:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    def reflect_on_output(self, thread_id, output):
        instructions = f"Reflect on the output: {output}"
        return self.coordinator.run(thread_id, instructions)
