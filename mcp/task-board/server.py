"""task-board -- the simplest useful MCP server, and the one to copy first.

Four operations over a list of tasks, chosen so that each takes a different
path through MCP Bridge:

    add_task(title)      ordinary call, runs immediately
    list_tasks()         a read; never held
    complete_task(id)    an ordinary write
    delete_all_tasks()   classified DESTRUCTIVE -- the bridge holds it for an
                         operator instead of running it

The last one is why there are four. `cli.mcp_operation_class.classify_tool`
matches a word list against the name and the first docstring line, and
`delete` is on it; `destructive` is one of the three classes `is_sensitive`
treats as needing approval. So calling it puts a real entry in the admin
console's sensitive-actions queue rather than emptying anything, which is the
only way that queue gets something to decide.

State lives in a file, not a module-level list. In memory, an id returned by
one call refers to something no other call can read back, and the whole store
vanishes on restart -- which proves the bridge works and nothing else. This
container has its own writable layer; it survives a restart but not a
`docker rm`.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# 0.0.0.0, not FastMCP's 127.0.0.1 default: this runs in its own container and
# is reached by managed-mcp-bridge over the docker network, not by a process
# sharing its loopback.
mcp = FastMCP("task-board", host="0.0.0.0")

_STORE = Path(os.environ.get("TASK_BOARD_STORE_PATH", "/data/tasks.json"))
# FastMCP answers from a thread pool, so two concurrent writes can interleave
# a read-modify-write and lose one. A lock is cheaper than reasoning about
# whether that happens in practice.
_LOCK = threading.Lock()


def _read() -> list[dict]:
    try:
        raw = json.loads(_STORE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return raw if isinstance(raw, list) else []


def _write(tasks: list[dict]) -> None:
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    _STORE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


@mcp.tool()
def add_task(title: str) -> dict:
    """Records a new task and returns it with the id assigned to it."""
    title = (title or "").strip()
    if not title:
        return {"ok": False, "error": "title must not be empty"}
    with _LOCK:
        tasks = _read()
        task = {
            "id": max((t.get("id", 0) for t in tasks), default=0) + 1,
            "title": title[:500],
            "done": False,
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        tasks.append(task)
        _write(tasks)
    return {"ok": True, "task": task, "count": len(tasks)}


@mcp.tool()
def list_tasks() -> dict:
    """Returns every task on the board, open and completed.

    A read, so the bridge never holds it -- worth calling right after a
    held operation to see that ordinary work is unaffected while something
    waits for a decision.
    """
    tasks = _read()
    return {
        "ok": True,
        "tasks": tasks,
        "open": sum(1 for t in tasks if not t.get("done")),
        "count": len(tasks),
    }


@mcp.tool()
def complete_task(task_id: int) -> dict:
    """Marks one task as done and returns the updated task."""
    with _LOCK:
        tasks = _read()
        for task in tasks:
            if task.get("id") == task_id:
                task["done"] = True
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
                _write(tasks)
                return {"ok": True, "task": task}
    return {"ok": False, "error": f"no task with id {task_id}"}


@mcp.tool()
def delete_all_tasks() -> dict:
    """Deletes every task on the board.

    Classified destructive by the name and this first line, so an operator
    decides it before anything happens. A refusal here is the platform
    working, not a fault -- the request appears under Security, and the call
    only proceeds once it has been allowed.
    """
    with _LOCK:
        tasks = _read()
        removed = len(tasks)
        _write([])
    return {"ok": True, "deleted": removed, "count": 0}


if __name__ == "__main__":
    mcp.run(transport="sse")
