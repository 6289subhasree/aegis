import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app import db as db_module
from app.main import app


@pytest.fixture()
def session(monkeypatch):
    engine = db_module.make_engine("sqlite:///:memory:")
    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr("app.main.init_db", lambda: None)
    
    from app import models  # noqa: F401
    db_module.Base.metadata.create_all(bind=engine)
    
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    s = TestingSession()
    monkeypatch.setattr(db_module, "SessionLocal", TestingSession)
    yield s
    s.close()


@pytest.fixture()
def client(session):
    def override():
        yield session

    app.dependency_overrides[db_module.get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()
