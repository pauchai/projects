"""Tests for the Projects MCP server."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mcp_tools.servers.projects.server import list_projects, create_project


class TestListProjects:
    def test_returns_list_of_projects(self) -> None:
        mock_response = [
            {
                "project_id": "p1",
                "title": "Alpha",
                "description": "A project",
                "owner_id": "u1",
                "required_skills": ["python"],
                "status": "draft",
                "created_at": "2025-01-01T00:00:00",
            },
        ]

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get.return_value.json.return_value = mock_response

        with patch("mcp_tools.servers.projects.server.httpx.Client", return_value=mock_client):
            result = list_projects(user_id="u1")

        assert len(result) == 1
        assert result[0]["project_id"] == "p1"
        mock_client.get.assert_called_once()
        call_kwargs = mock_client.get.call_args.kwargs
        assert call_kwargs["params"] == {"owner_id": "u1"}
        assert call_kwargs["headers"]["X-User-ID"] == "u1"

    def test_raises_on_http_error(self) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("server error")

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get.return_value = mock_response

        with patch("mcp_tools.servers.projects.server.httpx.Client", return_value=mock_client):
            with pytest.raises(Exception, match="server error"):
                list_projects(user_id="u1")


class TestCreateProject:
    def test_creates_project_with_minimal_args(self) -> None:
        mock_response = {
            "project_id": "p1",
            "title": "Alpha",
            "description": "A project",
            "owner_id": "u1",
            "required_skills": [],
            "max_members": None,
            "status": "draft",
            "created_at": "2025-01-01T00:00:00",
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.post.return_value.json.return_value = mock_response

        with patch("mcp_tools.servers.projects.server.httpx.Client", return_value=mock_client):
            result = create_project(
                user_id="u1",
                title="Alpha",
                description="A project",
            )

        assert result["project_id"] == "p1"
        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["json"] == {
            "title": "Alpha",
            "description": "A project",
        }
        assert call_kwargs["headers"]["X-User-ID"] == "u1"

    def test_creates_project_with_all_args(self) -> None:
        mock_response = {
            "project_id": "p2",
            "title": "Beta",
            "description": "Desc",
            "owner_id": "u2",
            "required_skills": ["python", "react"],
            "max_members": 5,
            "status": "draft",
            "created_at": "2025-01-01T00:00:00",
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.post.return_value.json.return_value = mock_response

        with patch("mcp_tools.servers.projects.server.httpx.Client", return_value=mock_client):
            result = create_project(
                user_id="u2",
                title="Beta",
                description="Desc",
                required_skills=["python", "react"],
                max_members=5,
                project_id="p2",
            )

        assert result["max_members"] == 5
        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["json"] == {
            "title": "Beta",
            "description": "Desc",
            "required_skills": ["python", "react"],
            "max_members": 5,
            "project_id": "p2",
        }

    def test_raises_on_http_error(self) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("server error")

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.post.return_value = mock_response

        with patch("mcp_tools.servers.projects.server.httpx.Client", return_value=mock_client):
            with pytest.raises(Exception, match="server error"):
                create_project(
                    user_id="u1",
                    title="Alpha",
                    description="A project",
                )