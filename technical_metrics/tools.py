"""
Holvi specific vendor agnostic metrics tools.
"""
from contextlib import contextmanager
from statsd import safe_statsd


@contextmanager
def metered_request(request_metric_name):
    """
    Context manager for metered requests.
    This context manager will send metrics to the events:
    1. Request made (increment).
    2. Success: Response received (increment).
    3. Time (Request made-> Request end).
    4. Request fail (increment).
    5. Request fail detail: event.
    request_metric_name: a string to describe the vendor. This metric name
    will be used for datadog. Metric name format agreed to be:
    "repository.capability.detail.vendor"
    example of a request_metric_name: "bakgw.cdd.kyb.compass"
    """
    try:
        safe_statsd.increment('%s.request' % request_metric_name)
        with safe_statsd.timed('%s.time' % request_metric_name):
            yield
    except Exception as error:
        safe_statsd.increment('%s.error' % request_metric_name)
        safe_statsd.event(
            '%s.error.details' % request_metric_name,
            error.message,
            alert_type='error'
        )
        raise error
    else:
        safe_statsd.increment('%s.success' % request_metric_name)
        return
