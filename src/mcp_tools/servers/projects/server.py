"""MCP server for project management — exposes list_projects and create_project."""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Transport: streamable-http so opencode (or any HTTP client) can reach it.
# Mount at /mcp — the standard path for MCP over HTTP.
HOST = os.environ.get("MCP_API_HOST", "http://localhost:8000")
SERVICE_TOKEN = os.environ.get("MCP_SERVICE_TOKEN", "")

if not SERVICE_TOKEN:
    raise RuntimeError("MCP_SERVICE_TOKEN environment variable is not set")


def _headers(user_id: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {SERVICE_TOKEN}",
        "X-User-ID": user_id,
    }


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP("Projects", json_response=True)


@mcp.tool()
def list_projects(user_id: str) -> list[dict[str, Any]]:
    """List all projects owned by the specified user.

    Args:
        user_id: ID of the user whose projects to list.

    Returns:
        List of project summaries with project_id, title, description,
        owner_id, required_skills, status, created_at.
    """
    params = {"owner_id": user_id}
    with httpx.Client(base_url=HOST, timeout=15.0) as client:
        resp = client.get("/internal/projects", params=params, headers=_headers(user_id))
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def create_project(
    user_id: str,
    title: str,
    description: str,
    required_skills: list[str] | None = None,
    max_members: int | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    """Create a new project for the specified user.

    Args:
        user_id: ID of the user who will own the project.
        title: Project title (3-200 characters).
        description: Project description (max 5000 characters).
        required_skills: Optional list of skill tags.
        max_members: Optional maximum number of members.
        project_id: Optional custom project ID. If omitted, the API
            generates one.

    Returns:
        Created project with project_id, title, description, owner_id,
        required_skills, max_members, status, created_at.
    """
    body: dict[str, Any] = {
        "title": title,
        "description": description,
    }
    if project_id is not None:
        body["project_id"] = project_id
    if required_skills is not None:
        body["required_skills"] = required_skills
    if max_members is not None:
        body["max_members"] = max_members

    with httpx.Client(base_url=HOST, timeout=15.0) as client:
        resp = client.post(
            "/internal/projects",
            json=body,
            headers=_headers(user_id),
        )
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    mcp.run(transport="streamable-http", mount_path="/mcp")