from app.agents.sales import SalesAgent
from app.agents.finance import FinanceAgent
from app.agents.hr import HRAgent
from app.agents.operations import OperationsAgent
from app.agents.marketing import MarketingAgent


def get_all_agents() -> list:
    """Restituisce tutte le classi agente registrate."""
    return [SalesAgent, FinanceAgent, HRAgent, OperationsAgent, MarketingAgent]
