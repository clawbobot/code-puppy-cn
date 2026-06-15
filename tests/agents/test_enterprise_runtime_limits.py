import asyncio

import pytest

from code_puppy.agents._runtime import _await_agent_task


@pytest.mark.asyncio
async def test_enterprise_timeout_cannot_be_suppressed_by_agent_task():
    async def suppress_cancellation():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            return "suppressed"

    task = asyncio.create_task(suppress_cancellation())
    with pytest.raises(asyncio.TimeoutError):
        await _await_agent_task(task, 0.01)


@pytest.mark.asyncio
async def test_enterprise_timeout_returns_completed_result():
    task = asyncio.create_task(asyncio.sleep(0, result="ok"))
    assert await _await_agent_task(task, 1) == "ok"
