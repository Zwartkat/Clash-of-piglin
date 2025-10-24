import esper
from components.ai.ai_controlled import AiControlled

class AiSystem(esper.Processor):
    def __init__(self):
        super().__init__()
        
    def process(self, dt):
        for ent, ai in esper.get_component(AiControlled):
            ai.behavior.execute_action(ent)