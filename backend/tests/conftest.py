import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app import db as db_module
from app.main import app


@pytest.fixture()
def session():
    engine = db_module.make_engine("sqlite://")
    db_module.Base.metadata.drop_all(bind=engine)
    from app import models  # noqa: F401

    db_module.Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    s = Session()
    yield s
    s.close()


@pytest.fixture()
def client(session):
    def override():
        yield session

    app.dependency_overrides[db_module.get_db] = override
    # lifespan would create tables on the real engine; tests use the in-memory one
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
