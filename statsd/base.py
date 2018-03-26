# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from functools import wraps

from datadog.dogstatsd.base import DogStatsd

logger = logging.getLogger(__name__)


DEFAULT_SAFEGUARDED_METHODS = [
    'increment', 'decrement', 'gauge', 'histogram',
    'distribution', 'timing', 'timed', 'set', 'event', 'service_check'
]


class SafeDogStatsd(DogStatsd):
    """
    Safe wrapper around datadog statsd library.
    Class methods will try to call statsd without raising any exception
    if that call fails.
    """
    def __init__(self, log_level='exception',
                 safeguarded_methods=DEFAULT_SAFEGUARDED_METHODS,
                 *args, **kwargs):
        """
        Instantiate a new object with the error level specified.
        The level fallback on exception if the logger provided is unusable
        """
        super(SafeDogStatsd, self).__init__(*args, **kwargs)
        try:
            self.logging_function = getattr(logger, log_level)
        except AttributeError:
            self.logging_function = getattr(logger, 'exception')
        self.SAFEGUARDED_METHODS = safeguarded_methods
        self._safeguard_methods(self.SAFEGUARDED_METHODS)

    def _exception_free_call(self, func):
        """
        Call the function without raising its exceptions.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as error:
                self.logging_function(str(error))
        return wrapper

    def _safeguard_method(self, method_name):
        """
        Replace a method with a safe copy that does not raise exceptions.
        This will wrap the property provided with _exception_free_call wrapper
        """
        if not hasattr(self, method_name):
            self.logging_function('%s is not a statsd property', method_name)
            return
        method = getattr(self, method_name)
        if not callable(method):
            self.logging_function('%s is not a statsd method', method_name)
            return

        decorated_prop = self._exception_free_call(method)
        setattr(self, method_name, decorated_prop)

    def _safeguard_methods(self, methods_names):
        """
        Replace methods with a safe copy that does not raise exceptions.
        param methods_names: List of methods names.
        """
        for method_name in methods_names:
            self._safeguard_method(method_name=method_name)
