from unittest import TestCase

from mock import Mock, call, patch

from base import SafeStatsd, logger


class TestSafeStatsd(TestCase):
    """
    Tests for SafeStatsd.
    """
    def test_init_with_accepted_level(self):
        """
        SafeStatsd should have the correct level if instasiated with
        acceptable level.
        """
        test_statsd = SafeStatsd(log_level='info')
        self.assertEqual(
            test_statsd.logging_function, logger.info
        )

    def test_init_with_bad_level(self):
        """
        SafeStatsd should have "exception" level if instasiated with
        unacceptable level.
        """
        test_statsd = SafeStatsd(log_level='fantasy')
        self.assertEqual(
            test_statsd.logging_function, logger.exception
        )

    @patch('base.logger')
    def test_exception_free_call(self, mock_logger):
        """
        Exceptions should not be raised inside the context manager, instead
        we log the error.
        """
        ERROR_MESSAGE = 'I am pretend statsd error'
        mock_logger.fake = Mock()
        test_statsd = SafeStatsd(log_level='fake')
        with test_statsd._exception_free_call():
            raise Exception(ERROR_MESSAGE)
        self.assertEqual(
            mock_logger.fake.call_args_list,
            [call('I am pretend statsd error')]
        )

    @patch('base.statsd')
    def test_increment(self, mock_statsd):
        """
        Test increment passing to statsd increment.
        """
        safe_statsd = SafeStatsd()
        safe_statsd.increment(
            'metric',
            value=5,
            tags=['tag1', 'tag2'],
            sample_rate=21
        )
        mock_statsd.increment.assert_called_with(
            'metric', 5, ['tag1', 'tag2'], 21
        )

    @patch('base.statsd')
    def test_event(self, mock_statsd):
        """
        Test event passing to (statsd.event).
        """
        safe_statsd = SafeStatsd()
        safe_statsd.event(
            'event_title',
            'event_text',
            alert_type='Error',
            aggregation_key='aggregation_key',
            source_type_name='source_type_name',
            date_happened='data_here', priority=1,
            tags=['list', 'of', 'tags'], hostname='holvi.something'
        )
        mock_statsd.event.assert_called_with(
            'event_title',
            'event_text',
            'Error',
            'aggregation_key',
            'source_type_name',
            'data_here', 1,
            ['list', 'of', 'tags'],
            'holvi.something'
        )

    @patch('base.statsd')
    def test_timing(self, mock_statsd):
        """
        Test timing event passing to statsd.timing
        """
        safe_statsd = SafeStatsd()
        safe_statsd.timing(
            metric='metric_name',
            value=123,
            tags=['some', 'ragged', 'tags'],
            sample_rate=20
        )
        mock_statsd.timing.assert_called_with(
            'metric_name',
            123,
            ['some', 'ragged', 'tags'],
            20
        )
