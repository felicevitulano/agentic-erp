import logging
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.models.database import Base, engine
from app.api.auth_routes import router as auth_router
from app.api.chat_routes import router as chat_router
from app.api.dashboard_routes import router as dashboard_router
from app.api.sales_routes import router as sales_router
from app.api.finance_routes import router as finance_router
from app.api.hr_routes import router as hr_router
from app.api.operations_routes import router as operations_router
from app.api.marketing_routes import router as marketing_router


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger("agentic_erp")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Avvio Agentic ERP...")
    if not getattr(app, "_skip_lifespan", False):
        Base.metadata.create_all(bind=engine)
        _seed_admin()
    yield
    logger.info("Arresto Agentic ERP...")


def _seed_admin():
    from app.models import SessionLocal, User
    from app.auth.jwt import hash_password

    settings = get_settings()
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == settings.admin_username).first()
        if not existing:
            admin = User(
                username=settings.admin_username,
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                full_name="Amministratore",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logger.info(f"Utente admin '{settings.admin_username}' creato.")
    finally:
        db.close()


settings = get_settings()

app = FastAPI(
    title="Agentic ERP",
    description="Gestionale Aziendale Multi-Agente per Think Next S.r.l.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(dashboard_router)
app.include_router(sales_router)
app.include_router(finance_router)
app.include_router(hr_router)
app.include_router(operations_router)
app.include_router(marketing_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "agentic-erp"}
