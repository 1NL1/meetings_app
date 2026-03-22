from datetime import UTC, datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_meeting(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/meetings/",
        json={
            "title": "Sprint Planning",
            "date": datetime.now(UTC).isoformat(),
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Sprint Planning"


@pytest.mark.asyncio
async def test_list_meetings(client: AsyncClient, auth_headers: dict):
    for title in ["Meeting 1", "Meeting 2"]:
        await client.post(
            "/meetings/",
            json={
                "title": title,
                "date": datetime.now(UTC).isoformat(),
            },
            headers=auth_headers,
        )
    response = await client.get("/meetings/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_validate_saves_markdown(client: AsyncClient, auth_headers: dict):
    # Create a meeting
    create_resp = await client.post(
        "/meetings/",
        json={
            "title": "Validation Test",
            "date": datetime.now(UTC).isoformat(),
        },
        headers=auth_headers,
    )
    meeting_id = create_resp.json()["id"]

    # Validate with markdown
    response = await client.put(
        f"/meetings/{meeting_id}/validate",
        json={"report_markdown": "# Édité"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["report_validated"] is True
    assert data["report_markdown"] == "# Édité"
