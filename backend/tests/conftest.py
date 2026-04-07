import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.models import database as db_module
from app.models.database import Base, get_db
from app.models.user import User
from app.auth.jwt import hash_password, create_access_token

# Single in-memory engine shared across all tests
_test_engine = create_engine(
    "sqlite:///file:test_db?mode=memory&cache=shared&uri=true",
    connect_args={"check_same_thread": False},
    echo=False,
)
_TestSession = sessionmaker(bind=_test_engine, expire_on_commit=False)

# Patch module-level references so any code importing from database.py
# that directly uses engine/SessionLocal also hits the test DB
db_module.engine = _test_engine
db_module.SessionLocal = _TestSession


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def db_session():
    session = _TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session):
    user = User(
        username="testuser",
        email="test@thinknext.it",
        password_hash=hash_password("testpass"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def client(db_session, test_user):
    from app.main import app

    def override_get_db():
        # Each request gets a fresh session on the same in-memory engine
        session = _TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app._skip_lifespan = True

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}
