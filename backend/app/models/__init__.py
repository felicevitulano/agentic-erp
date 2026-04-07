from app.models.database import Base, engine, SessionLocal, get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.audit import AuditLog, Notification
from app.models.sales import Contact, Opportunity, Contract, SAL
from app.models.finance import Fattura
from app.models.hr import Collaboratore, Presenza, Assenza
from app.models.operations import Progetto, Task, Timesheet
from app.models.marketing import Contenuto, ContattoEvento

__all__ = [
    "Base", "engine", "SessionLocal", "get_db",
    "User", "Conversation", "Message",
    "AuditLog", "Notification",
    "Contact", "Opportunity", "Contract", "SAL",
    "Fattura",
    "Collaboratore", "Presenza", "Assenza",
    "Progetto", "Task", "Timesheet",
    "Contenuto", "ContattoEvento",
]
