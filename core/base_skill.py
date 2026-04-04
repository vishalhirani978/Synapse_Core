from abc import ABC, abstractmethod

class BaseSkill(ABC):
    @abstractmethod
    def execute(self, **kwargs):
        raise NotImplementedError("Each skill must implement execute!")
