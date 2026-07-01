from redis import Redis
from rq import Queue

from app.core.config import settings

# Parse redis:// URL into a connection RQ can use.
redis_connection = Redis.from_url(settings.redis_url)

# Single default queue for document-processing jobs.
task_queue = Queue("document_processing", connection=redis_connection)
