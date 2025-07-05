# app/core/context/pen_context.py
import contextvars
import uuid
import time

search_id_var = contextvars.ContextVar("search_id", default=None)
search_start_time_var = contextvars.ContextVar("search_start_time", default=None)

def init_search_context() -> str:
    search_id = str(uuid.uuid4())
    search_id_var.set(search_id)
    search_start_time_var.set(time.perf_counter())
    return search_id

def get_search_id() -> str:
    return search_id_var.get()

def get_search_elapsed() -> float:
    start = search_start_time_var.get()
    return time.perf_counter() - start if start else -1
