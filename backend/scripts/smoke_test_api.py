from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    client = TestClient(app)

    health = client.get("/api/health")
    queue = client.get("/api/packages/")
    detail = client.get("/api/packages/pkg_1001")
    decision = client.post(
        "/api/packages/pkg_1001/decisions",
        json={
            "reviewer": "aria.han",
            "final_decision": "approve",
            "reviewer_comment": "Smoke test approval path.",
            "override_reason": "Manual verification complete.",
        },
    )

    print("GET /api/health ->", health.status_code, health.json())
    print("GET /api/packages/ ->", queue.status_code)
    print("GET /api/packages/pkg_1001 ->", detail.status_code)
    print("POST /api/packages/pkg_1001/decisions ->", decision.status_code, decision.json())


if __name__ == "__main__":
    main()
