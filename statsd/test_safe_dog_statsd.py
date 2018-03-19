import copy
from unittest import TestCase
from datetime import datetime
from datadog import statsd as original_statsd
from mock import Mock, call, patch

from statsd.base import DEFAULT_SAFEGUARDED_METHODS, SafeDogStatsd, logger
from statsd import safe_statsd


SIMPLE_STATSD_METRIC_KWARGS = {
    'metric': 'vault.capability.detail.something_happened',
    'value': 2020,
    'tags': ['tag1', 'tag2', 'tag3'],
    'sample_rate': 0.1
}


EXPECTED_CALLS_FIXTURES = {
    # ['method_name', 'call_args', '._report(call_args)]
    'increment': copy.deepcopy(SIMPLE_STATSD_METRIC_KWARGS),
    'decrement': copy.deepcopy(SIMPLE_STATSD_METRIC_KWARGS),
    'gauge': copy.deepcopy(SIMPLE_STATSD_METRIC_KWARGS),
    'histogram': copy.deepcopy(SIMPLE_STATSD_METRIC_KWARGS),
    'distribution': copy.deepcopy(SIMPLE_STATSD_METRIC_KWARGS),
    'timing': copy.deepcopy(SIMPLE_STATSD_METRIC_KWARGS),
    'set': copy.deepcopy(SIMPLE_STATSD_METRIC_KWARGS),
    'timed': {
        'metric': 'vault.capability.detail.something_happened',
        'tags': ['tag1', 'tag2', 'tag3'],
        'sample_rate': 0.1
    },
    'event': {
        'title': 'testing title',
        'text': 'description here',
        'alert_type': 'error',
        'aggregation_key': 'agg_key',
        'source_type_name': 'source_type',
        'date_happened': 123456,
        'priority': 1,
        'tags': ['tag1', 'tag2', 'tag3'],
        'hostname': 'vault'
    },
    'service_check': {
        'check_name': 'health_check_1',
        'status': 'healthy',
        'tags': ['tag1', 'tag2', 'tag3'],
        'timestamp': 1234567,
        'hostname': 'vault',
        'message': 'I am healthy'
    }
}


class TestSafeDogStatsd(TestCase):
    """
    Tests for SafeDogStatsd.
    """
    def test_init_with_accepted_level(self):
        """
        SafeDogStatsd should have the correct level if instasiated with
        acceptable level.
        """
        test_statsd = SafeDogStatsd(log_level='info')
        self.assertEqual(
            test_statsd.logging_function, logger.info
        )

    def test_init_with_bad_level(self):
        """
        SafeDogStatsd should have "exception" level if instasiated with
        unacceptable level.
        """
        test_statsd = SafeDogStatsd(log_level='fantasy')
        self.assertEqual(
            test_statsd.logging_function, logger.exception
        )

    def test_default_methods_acceptable(self):
        """
        Sanity check for base DEFAULT_SAFEGUARDED_METHODS
        if statsd datadog got changed or our default safeguarded methods are
        referenceing something that does not exists.
        """
        from datadog.dogstatsd.base import DogStatsd
        for prop in DEFAULT_SAFEGUARDED_METHODS:
            method = getattr(DogStatsd, prop)
            if not callable(method):
                raise AttributeError('%s is not callable', prop)

    def test_exception_free_call(self):
        """
        A function decorated with the wrapper
        _exception_free_call
        should never raise exception, instead it would log the exception.
        """
        with patch('statsd.base.logger.info') as mock_logger:
            safe_statsd = SafeDogStatsd(
                log_level='info',
                safeguarded_methods=''
            )

        funky_method = Mock(
            autospec=True, side_effect=ValueError('Funky statsd error'),
            __name__='functools_require_this'
        )
        safe_funky_method = safe_statsd._exception_free_call(funky_method)
        safe_funky_method('some event here')
        mock_logger.assert_called_once_with('Funky statsd error')

    def test_safeguard_method(self):
        """
        safeguard_method should replace the method with another
        safe version of that method.
        """
        with patch('statsd.base.logger') as mock_logger:
            safe_statsd = SafeDogStatsd(log_level='meltdown')
        safe_statsd.test_method = Mock(
            autospec=True, side_effect=ValueError('Funky statsd error'),
            __name__='functools_require_this'
        )
        with self.assertRaisesRegexp(ValueError, 'Funky statsd error'):
            safe_statsd.test_method()

        safe_statsd._safeguard_method('test_method')
        safe_statsd.test_method('I am safe now!')
        mock_logger.meltdown.assert_called_once_with('Funky statsd error')

    def test_safeguard_method_non_existant_method(self):
        """
        If a method does not exist, the logic should not break.
        """
        with patch('statsd.base.logger') as mock_logger:
            safe_statsd = SafeDogStatsd(log_level='meltdown')
            safe_statsd._safeguard_method('not_a_method')

        mock_logger.meltdown.assert_called_once_with(
            '%s is not a statsd property', 'not_a_method'
        )

    def test_safeguard_method_non_callable_property(self):
        """
        If a method does not exist, the logic should not break.
        """
        with patch('statsd.base.logger') as mock_logger:
            safe_statsd = SafeDogStatsd(log_level='meltdown')
            safe_statsd._safeguard_method('SAFEGUARDED_METHODS')

        mock_logger.meltdown.assert_called_once_with(
            '%s is not a statsd method', 'SAFEGUARDED_METHODS'
        )

    def test_class_functions(self):
        """
        Sanity check: A call from the safe wrapper should be equal to
        a call from the original library.
        If you add new functions or if statsd is updated, please
        change the fixture accordingly.
        """
        for method, call_args in EXPECTED_CALLS_FIXTURES.items():
            with patch('datadog.statsd._send_to_server') as mock_original_send:
                mock_original_send.clear_mock()
                getattr(original_statsd, method)(**call_args)

            with patch('statsd.safe_statsd'
                       '._send_to_server') as mock_safe_class_send:
                mock_safe_class_send.clear_mock()
                getattr(original_statsd, method)(**call_args)

            self.assertEqual(
                mock_original_send.call_args_list,
                mock_safe_class_send.call_args_list
            )

    def test_all_methods_are_covered_by_tests(self):
        """
        Test that the default methods in base module are all covered
        in the fixture to be tested.
        """
        methods_tested = [
            method for method, _ in EXPECTED_CALLS_FIXTURES.items()
        ]
        self.assertEqual(
            methods_tested.sort(),
            DEFAULT_SAFEGUARDED_METHODS.sort()
        )
