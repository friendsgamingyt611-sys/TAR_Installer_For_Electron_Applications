from ..model import Action

def action(kind: str, **kwargs) -> Action:
    return Action(type=kind, **kwargs)
