"""End-to-end API tests covering the full link lifecycle."""

from datetime import datetime, timedelta, timezone

LONG_URL = "https://example.com/a/very/long/url?with=query"


def test_healthcheck(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_link_generates_base62_code(client):
    response = client.post("/api/links", json={"original_url": LONG_URL})
    assert response.status_code == 201
    data = response.json()
    assert data["original_url"] == LONG_URL
    assert data["click_count"] == 0
    assert data["is_custom_alias"] is False
    assert len(data["code"]) == 6
    assert data["code"].isalnum()
    assert data["created_at"] is not None


def test_create_link_with_custom_alias(client):
    response = client.post(
        "/api/links",
        json={"original_url": LONG_URL, "custom_alias": "my-link"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "my-link"
    assert data["is_custom_alias"] is True


def test_create_link_alias_conflict_returns_409(client):
    payload = {"original_url": LONG_URL, "custom_alias": "taken"}
    assert client.post("/api/links", json=payload).status_code == 201
    conflict = client.post("/api/links", json=payload)
    assert conflict.status_code == 409


def test_create_link_rejects_invalid_url(client):
    response = client.post("/api/links", json={"original_url": "not-a-url"})
    assert response.status_code == 422


def test_create_link_rejects_invalid_alias(client):
    response = client.post(
        "/api/links",
        json={"original_url": LONG_URL, "custom_alias": "bad alias!"},
    )
    assert response.status_code == 422


def test_redirect_returns_307_and_counts_clicks(client):
    code = client.post("/api/links", json={"original_url": LONG_URL}).json()["code"]

    first = client.get(f"/{code}")
    assert first.status_code == 307
    assert first.headers["location"] == LONG_URL

    second = client.get(f"/{code}")
    assert second.status_code == 307

    stats = client.get(f"/api/links/{code}/stats").json()
    assert stats["click_count"] == 2
    assert stats["last_accessed_at"] is not None


def test_redirect_unknown_code_returns_404(client):
    response = client.get("/doesnotexist")
    assert response.status_code == 404


def test_stats_for_new_link(client):
    code = client.post("/api/links", json={"original_url": LONG_URL}).json()["code"]
    response = client.get(f"/api/links/{code}/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == code
    assert data["original_url"] == LONG_URL
    assert data["click_count"] == 0
    assert data["last_accessed_at"] is None
    assert data["is_expired"] is False


def test_stats_unknown_code_returns_404(client):
    assert client.get("/api/links/nope/stats").status_code == 404


def test_list_links(client):
    client.post("/api/links", json={"original_url": "https://example.com/one"})
    client.post("/api/links", json={"original_url": "https://example.com/two"})
    response = client.get("/api/links")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    urls = {item["original_url"] for item in data}
    assert urls == {"https://example.com/one", "https://example.com/two"}


def test_expired_link_returns_410_on_redirect(client):
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    created = client.post(
        "/api/links",
        json={"original_url": LONG_URL, "expires_at": past},
    )
    assert created.status_code == 201
    code = created.json()["code"]

    response = client.get(f"/{code}")
    assert response.status_code == 410

    stats = client.get(f"/api/links/{code}/stats").json()
    assert stats["is_expired"] is True
    assert stats["click_count"] == 0


def test_link_with_future_expiration_still_redirects(client):
    future = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    code = client.post(
        "/api/links",
        json={"original_url": LONG_URL, "expires_at": future},
    ).json()["code"]
    response = client.get(f"/{code}")
    assert response.status_code == 307


def test_delete_link(client):
    code = client.post("/api/links", json={"original_url": LONG_URL}).json()["code"]
    response = client.delete(f"/api/links/{code}")
    assert response.status_code == 204
    assert client.get(f"/{code}").status_code == 404
    assert client.get(f"/api/links/{code}/stats").status_code == 404


def test_delete_unknown_code_returns_404(client):
    assert client.delete("/api/links/nope").status_code == 404
