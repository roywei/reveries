class ExecutorAgent:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    def execute_task(self, thread_id, task):
        # Invoke Coordinator to run the task
        instructions = f"Execute the task: {task}"
        return self.coordinator.run(thread_id, instructions)
