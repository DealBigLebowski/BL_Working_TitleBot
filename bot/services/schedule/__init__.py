import asyncio
from typing import Optional

import aioschedule

from . import jobs


# TODO: use apscheduler?
class ScheduleService(aioschedule.Scheduler):
    def __init__(self, *, pending_jobs_interval: int = 60) -> None:
        super().__init__()
        self.pending_jobs_interval = pending_jobs_interval
        self.pending_jobs_task: Optional[asyncio.Task] = None

    async def _run_pending_jobs(self):
        while True:
            await asyncio.sleep(self.pending_jobs_interval)
            await self.run_pending()

    async def setup(self):
        self.pending_jobs_task = asyncio.create_task(self._run_pending_jobs())

    async def dispose(self):
        if self.pending_jobs_task and not self.pending_jobs_task.done():
            self.pending_jobs_task.cancel()

        self.pending_jobs_task = None
