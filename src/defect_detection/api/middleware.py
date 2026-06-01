import time

from fastapi import Request

from defect_detection.api.metrics import REQUEST_LATENCY_SECONDS, REQUESTS_TOTAL


async def prometheus_middleware(request: Request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time
    endpoint = request.url.path

    REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(response.status_code),
    ).inc()

    REQUEST_LATENCY_SECONDS.labels(
        method=request.method,
        endpoint=endpoint,
    ).observe(duration)

    return response
