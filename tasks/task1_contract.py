from environment import JudicialEnv, JudicialAction

class ContractTask:
    name = "task1_contract"
    difficulty = "easy"
    description = "Resolve a contract dispute. Agent must identify breach and assign liability."

    def __init__(self):
        self.env = JudicialEnv(domain="contract", difficulty="easy")

    def run(self, agent_fn) -> float:
        obs = self.env.reset()
        action = agent_fn(obs)
        _, reward, done, info = self.env.step(action)
        return max(0.0, min(1.0, reward))