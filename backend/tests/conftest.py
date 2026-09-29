import os
import sys
import tempfile

# Use an isolated database + no real Hindsight for unit tests. Must be set before app import.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["HINDSIGHT_API_KEY"] = "test-key-not-real"
os.environ["HINDSIGHT_BASE_URL"] = "http://hindsight.test"
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services import hindsight_service as hs  # noqa: E402


class FakeHindsightClient:
    """TEST DOUBLE ONLY. Records calls so unit tests can run offline.
    It is never used by the running application."""

    def __init__(self):
        self.retained = []
        self.banks = []
        self.fail_retain = False

    def create_bank(self, bank_id, name=None, mission=None, **kw):
        self.banks.append(bank_id)

    def retain(self, bank_id, content, **kw):
        if self.fail_retain:
            raise RuntimeError("boom")
        self.retained.append((bank_id, content, kw))

    def recall(self, bank_id, query, **kw):
        texts = [c for b, c, _ in self.retained if b == bank_id]

        class R:
            def __init__(self, t):
                self.text, self.type = t, "world"

        class Res:
            results = [R(t) for t in texts]

        return Res()

    def reflect(self, bank_id, query, **kw):
        texts = [c for b, c, _ in self.retained if b == bank_id]

        class Res:
            text = "BRIEFING based on: " + " | ".join(texts)

        return Res()

    def get_version(self):
        class V:
            api_version = "test"

        return V()

    def delete_bank(self, bank_id):
        self.banks = [b for b in self.banks if b != bank_id]


@pytest.fixture()
def fake():
    f = FakeHindsightClient()
    hs.set_client_for_tests(f)
    yield f
    hs.reset_client()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
