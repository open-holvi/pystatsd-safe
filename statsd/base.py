import logging
from contextlib import contextmanager
from datadog import statsd

logger = logging.getLogger(__name__)


class SafeStatsd(object):
    """
    Safe wrapper around datadog statsd library.
    Class methods will try to call statsd without raising any exception
    if that call fails.
    """
    def __init__(self, log_level='exception'):
        """
        Instantiate a new object with the error level specified.
        The level fallback on exception if the logger provided is unusable
        """
        try:
            self.logging_function = getattr(logger, log_level)
        except AttributeError:
            self.logging_function = getattr(logger, 'exception')

    @contextmanager
    def _exception_free_call(self):
        try:
            yield
        except Exception as error:
            self.logging_function(str(error))

    def increment(self, metric, value=1, tags=None, sample_rate=1):
        """
        Safely increment a counter, optionally setting a value, tags and a
        sample rate.
        >>> safe_statsd.increment('page.views')
        >>> safe_statsd.increment('files.transferred', 124)
        """
        with self._exception_free_call():
            statsd.increment(metric, value, tags, sample_rate)

    def event(self, title, text, alert_type=None, aggregation_key=None,
              source_type_name=None, date_happened=None, priority=None,
              tags=None, hostname=None):
        """
        Safely send an event. Attributes are the same as the Event API.
            http://docs.datadoghq.com/api/
        >>> statsd.event('Man down!', 'This server needs assistance.')
        >>> statsd.event('The web server restarted', 'The web server is up again', alert_type='success')  # NOQA
        """
        with self._exception_free_call():
            statsd.event(
                title, text, alert_type, aggregation_key,
                source_type_name, date_happened, priority,
                tags, hostname
            )

    def timing(self, metric, value, tags=None, sample_rate=1):
        """
        Record a timing, optionally setting tags and a sample rate.
        >>> statsd.timing("query.response.time", 1234)
        """
        with self._exception_free_call():
            statsd.timing(metric, value, tags, sample_rate)

