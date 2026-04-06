from environment import JudicialEnv, JudicialAction

class TortTask:
    name = "task2_tort"
    difficulty = "medium"
    description = "Resolve a tort/negligence case with conflicting evidence and witnesses."

    def __init__(self):
        self.env = JudicialEnv(domain="tort", difficulty="medium")

    def run(self, agent_fn) -> float:
        obs = self.env.reset()
        action = agent_fn(obs)
        _, reward, done, info = self.env.step(action)
        return max(0.0, min(1.0, reward))