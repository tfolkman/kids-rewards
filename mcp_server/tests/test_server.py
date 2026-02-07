import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from server import mcp


def test_server_loads_all_tools():
    tools = asyncio.run(mcp._tool_manager.get_tools())
    assert len(tools) >= 50
    expected = [
        "login",
        "get_current_user",
        "list_store_items",
        "list_chores",
        "get_parent_dashboard",
        "get_kid_dashboard",
        "submit_chore",
        "approve_chore_submission",
        "create_pet",
        "get_points_rules",
    ]
    for name in expected:
        assert name in tools, f"Missing tool: {name}"


def test_tool_descriptions_exist():
    tools = asyncio.run(mcp._tool_manager.get_tools())
    for name, tool in tools.items():
        assert tool.description, f"Tool {name} has no description"


def test_login_tool_has_required_params():
    tools = asyncio.run(mcp._tool_manager.get_tools())
    login_tool = tools["login"]
    schema = login_tool.parameters
    assert "username" in schema.get("properties", {})
    assert "password" in schema.get("properties", {})
