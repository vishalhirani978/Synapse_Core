from core.base_skill import BaseSkill

class DummySkill(BaseSkill):
    def execute(self, **kwargs):
        return "Synapse Core: Connection Established."
