"""
Entry point for the RQ worker process.

Run with:  python -m app.worker

On Windows, RQ's default Worker can't be used because it relies on os.fork(),
which doesn't exist there — so we fall back to SimpleWorker (runs jobs in the
same process, no fork). On Linux/Docker the regular Worker is used.
"""

import os

from rq import SimpleWorker, Worker

from app.core.queue import redis_connection, task_queue


def main() -> None:
    # os.fork only exists on Unix-like systems.
    worker_class = Worker if hasattr(os, "fork") else SimpleWorker
    worker = worker_class([task_queue], connection=redis_connection)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
