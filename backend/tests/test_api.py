def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_customer_and_interaction_flow(client, fake):
    r = client.post("/api/customers", json={"name": "Rahul", "company": "ABC Corp", "industry": "SaaS"})
    assert r.status_code == 201
    cid = r.json()["id"]
    bank = r.json()["bank_id"]
    assert bank in fake.banks and bank.startswith("dealmind-") and str(cid) != bank

    r = client.post(f"/api/customers/{cid}/interactions", json={"content": "Rahul asked about SOC 2 compliance.", "kind": "email"})
    assert r.status_code == 201
    assert r.json()["retained"] is True
    assert "SOC 2" in fake.retained[0][1] and "Rahul" in fake.retained[0][1]

    r = client.post(f"/api/customers/{cid}/memory/recall", json={"query": "security"})
    assert "SOC 2" in r.json()["memories"][0]["text"]

    r = client.post(f"/api/customers/{cid}/prepare", json={})
    body = r.json()
    assert body["memory_used"] is True and body["source"] == "hindsight" and "SOC 2" in body["answer"]

    r = client.post(f"/api/customers/{cid}/prepare", json={"use_memory": False})
    assert r.json()["source"] == "generic-template"

    r = client.post(f"/api/customers/{cid}/followup", json={})
    assert r.json()["source"] == "hindsight"

    r = client.post(f"/api/customers/{cid}/ask", json={"question": "What does Rahul care about?"})
    assert r.status_code == 200 and r.json()["memory_used"]


def test_empty_customer_uses_generic_template(client, fake):
    cid = client.post("/api/customers", json={"name": "Asha", "company": "X"}).json()["id"]
    body = client.post(f"/api/customers/{cid}/prepare", json={}).json()
    assert body["memory_used"] is False and body["source"] == "generic-template"


def test_retain_failure_is_reported_and_retryable(client, fake):
    cid = client.post("/api/customers", json={"name": "A", "company": "B"}).json()["id"]
    fake.fail_retain = True
    r = client.post(f"/api/customers/{cid}/interactions", json={"content": "hello"})
    assert r.status_code == 201 and r.json()["retained"] is False and "boom" in r.json()["retain_error"]
    fake.fail_retain = False
    iid = r.json()["id"]
    r = client.post(f"/api/interactions/{iid}/retry")
    assert r.json()["retained"] is True


def test_validation_and_404(client, fake):
    assert client.post("/api/customers", json={"name": "", "company": "x"}).status_code == 422
    assert client.get("/api/customers/99999").status_code == 404


def test_demo_customer_idempotent(client, fake):
    a = client.post("/api/demo/customer").json()
    b = client.post("/api/demo/customer").json()
    assert a["id"] == b["id"] and a["name"] == "Rahul" and a["company"] == "ABC Corp"
    script = client.get("/api/demo/script").json()
    assert len(script["steps"]) == 5


def test_delete_customer(client, fake):
    cid = client.post("/api/customers", json={"name": "Z", "company": "Y"}).json()["id"]
    assert client.delete(f"/api/customers/{cid}").status_code == 204
    assert client.get(f"/api/customers/{cid}").status_code == 404


def test_memory_status(client, fake):
    st = client.get("/api/memory/status").json()
    assert st["configured"] is True and st["reachable"] is True


def test_timestamps_are_timezone_aware(client, fake):
    cid = client.post("/api/customers", json={"name": "T", "company": "Z"}).json()["id"]
    r = client.post(f"/api/customers/{cid}/interactions", json={"content": "hi"}).json()
    assert r["occurred_at"].endswith("Z") or r["occurred_at"].endswith("+00:00")
    assert fake.retained[0][2]["timestamp"].tzinfo is not None


def test_each_customer_gets_a_unique_bank(client, fake):
    a = client.post("/api/customers", json={"name": "A", "company": "X"}).json()
    b = client.post("/api/customers", json={"name": "B", "company": "X"}).json()
    assert a["bank_id"] != b["bank_id"]
    client.post(f"/api/customers/{a['id']}/interactions", json={"content": "only A knows this"})
    # B's memory must be empty even though A has memories
    assert client.post(f"/api/customers/{b['id']}/memory/recall", json={"query": "x"}).json()["memories"] == []
