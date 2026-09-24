from fastapi.testclient import TestClient

from app.main import app


def test_login_and_protected_report():
    client = TestClient(app)
    login = client.post("/auth/login", json={"email": "admin@skillsprint.local", "password": "ChangeMe123!"})
    assert login.status_code == 200
    report = client.get("/reports/overview", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert report.status_code == 200
    assert "documents" in report.json()


def test_report_rejects_anonymous_access():
    assert TestClient(app).get("/reports/overview").status_code == 401


def test_saved_plan_supports_evidence_progress_and_recommendations():
    client = TestClient(app)
    token = client.post("/auth/login", json={"email": "admin@skillsprint.local", "password": "ChangeMe123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    plans = client.get("/plans", headers=headers).json()
    assert plans
    plan = plans[0]
    evidence = client.get(f"/plans/{plan['id']}/evidence", headers=headers)
    assert evidence.status_code == 200
    assert len(evidence.json()) == len(plan["payload"]["modules"])
    module = plan["payload"]["modules"][0]
    progress = client.post(f"/plans/{plan['id']}/progress", headers=headers, json={
        "module_id": module["module_id"], "completed": True, "checklist_complete": True,
        "task_complete": True, "quiz_score": 85, "assessment_score": 85,
    })
    assert progress.status_code == 200
    assert progress.json()["payload"]["modules"][0]["progress"]["completed"] is True
