"""
APScheduler Configuration and Setup.
Configures timezone-aware job scheduling with market-specific timing.
"""

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.scheduler.jobs.kr_analysis_job import run_kr_analysis
from app.scheduler.jobs.us_analysis_job import run_us_analysis
from app.scheduler.jobs.cache_warmup_job import run_kr_cache_warmup, run_us_cache_warmup
from app.scheduler.runner import JobRunner

# Timezone
KST = pytz.timezone("Asia/Seoul")


class SchedulerManager:
    """Manages APScheduler lifecycle and job configuration."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=KST)
        self.runner = JobRunner()
        self.settings = get_settings()

    def configure_jobs(self) -> None:
        """Configure all scheduled jobs with market-specific timing."""
        if not self.settings.scheduler_enabled:
            print("⚠️  Scheduler disabled in settings")
            return

        # KR Market Analysis Job - 16:10 KST after KOSPI close
        # Monday-Friday (weekdays only)
        self.scheduler.add_job(
            func=self._run_kr_job,
            trigger=CronTrigger(
                hour=16,
                minute=10,
                day_of_week="0-4",  # Mon-Fri
                timezone=KST
            ),
            id="kr_analysis",
            name="KR Market Analysis",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,  # 5 minutes grace period
        )

        # US Market Analysis Job - 07:10 KST using previous day NYSE data
        # Tuesday-Saturday (after US Mon-Fri closes in KST time)
        self.scheduler.add_job(
            func=self._run_us_job,
            trigger=CronTrigger(
                hour=7,
                minute=10,
                day_of_week="1-5",  # Tue-Sat
                timezone=KST
            ),
            id="us_analysis",
            name="US Market Analysis",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,  # 5 minutes grace period
        )

        # Cache Pre-warming Jobs (Step 26: Performance Optimization)
        # KR Cache Warmup: Mon-Fri 15:50 KST (20min before analysis)
        self.scheduler.add_job(
            func=self._run_kr_cache_warmup,
            trigger=CronTrigger(
                hour=15,
                minute=50,
                day_of_week="0-4",  # Mon-Fri
                timezone=KST,
            ),
            id="kr_cache_warmup",
            name="KR Cache Pre-warming",
            replace_existing=True,
            max_instances=1,
        )

        # US Cache Warmup: Tue-Sat 06:50 KST
        self.scheduler.add_job(
            func=self._run_us_cache_warmup,
            trigger=CronTrigger(
                hour=6,
                minute=50,
                day_of_week="1-5",  # Tue-Sat
                timezone=KST,
            ),
            id="us_cache_warmup",
            name="US Cache Pre-warming",
            replace_existing=True,
            max_instances=1,
        )

        print("✅ Scheduler jobs configured:")
        print("   🇰🇷 KR Analysis: Mon-Fri 16:10 KST")
        print("   🇺🇸 US Analysis: Tue-Sat 07:10 KST")
        print("   📦 KR Cache Warmup: Mon-Fri 15:50 KST")
        print("   📦 US Cache Warmup: Tue-Sat 06:50 KST")

    async def _run_kr_job(self) -> None:
        """KR job wrapper with isolation."""
        await self.runner.run("KR_ANALYSIS", run_kr_analysis)

    async def _run_us_job(self) -> None:
        """US job wrapper with isolation."""
        await self.runner.run("US_ANALYSIS", run_us_analysis)

    async def _run_kr_cache_warmup(self) -> None:
        """KR cache warmup wrapper."""
        await self.runner.run("KR_CACHE_WARMUP", run_kr_cache_warmup)

    async def _run_us_cache_warmup(self) -> None:
        """US cache warmup wrapper."""
        await self.runner.run("US_CACHE_WARMUP", run_us_cache_warmup)

    def start(self) -> None:
        """Start the scheduler."""
        if not self.settings.scheduler_enabled:
            print("⚠️  Scheduler disabled - not starting")
            return

        self.configure_jobs()
        self.scheduler.start()
        print("🚀 APScheduler started with KST timezone")

        # Log next run times
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            next_run = job.next_run_time
            if next_run:
                print(
                    f"   📅 {job.name}: next run "
                    f"{next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}"
                )

    def shutdown(self) -> None:
        """Shutdown the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            print("⏹️  APScheduler shutdown complete")

    def get_job_status(self) -> dict:
        """Get current job status for monitoring."""
        if not self.scheduler.running:
            return {"status": "stopped", "jobs": []}

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": (
                    job.next_run_time.isoformat() if job.next_run_time else None
                ),
                "trigger": str(job.trigger),
            })

        return {
            "status": "running",
            "timezone": str(KST),
            "jobs": jobs
        }


# Global scheduler instance
_scheduler_manager: SchedulerManager = None


def get_scheduler_manager() -> SchedulerManager:
    """Get singleton scheduler manager instance."""
    global _scheduler_manager
    if _scheduler_manager is None:
        _scheduler_manager = SchedulerManager()
    return _scheduler_manager
