from environment import JudicialEnv, JudicialAction

class PropertyTask:
    name = "task3_property"
    difficulty = "hard"
    description = "Resolve a property/inheritance dispute with adversarial ambiguous facts."

    def __init__(self):
        self.env = JudicialEnv(domain="property", difficulty="hard")

    def run(self, agent_fn) -> float:
        obs = self.env.reset()
        action = agent_fn(obs)
        _, reward, done, info = self.env.step(action)
        return max(0.0, min(1.0, reward))