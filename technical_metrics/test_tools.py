from unittest import TestCase
from mock import Mock, patch, call
from technical_metrics import metered_request


@patch('technical_metrics.tools.safe_statsd')
class TestMeteredRequest(TestCase):
    """
    Test metered request context manager.
    """
    def setUp(self):
        self.REQUEST_METRIC_NAME = 'repo.capability.detail.vendor'
        self.REQUEST_METRIC_FULL_NAME = (
            '%s.%s' % ('repo', self.REQUEST_METRIC_NAME)
        )
        self.REQUEST_MADE_METRIC = 'repo.capability.detail.vendor.request'
        self.RESPONSE_RECEIVED_METRIC = (
            'repo.capability.detail.vendor.success'
        )
        self.REQUEST_FAILED_METRIC = 'repo.capability.detail.vendor.error'
        self.REQUEST_FAILED_METRIC_EVENT = (
            'repo.capability.detail.vendor.error.details'
        )
        self.REQUEST_RESPONSE_TIME = 'repo.capability.detail.vendor.time'

    def test_statsd_metered_request_reporting_success_request(
            self,
            mock_statsd):
        """
        Successful requests in statsd_metered_request blocks should cause
        three events:
        1. Request made (increment).
        2. Response received (increment).
        3. Time (Request made-> Request end).
        """
        fake_request = Mock()
        with metered_request(self.REQUEST_METRIC_NAME) as _:
            fake_request()
        fake_request.assert_any_call()
        EXPECTED_INCREMENT_CALLS = [
            call(self.REQUEST_MADE_METRIC),
            call(self.RESPONSE_RECEIVED_METRIC)
        ]
        statsd_increment = mock_statsd.increment
        self.assertEqual(
            statsd_increment.call_args_list,
            EXPECTED_INCREMENT_CALLS
        )

        statsd_timing = mock_statsd.timed
        timing_event_name = statsd_timing.call_args[0][0]
        self.assertEqual(
            self.REQUEST_RESPONSE_TIME, timing_event_name
        )

    def test_statsd_metered_request_reporting_fail_request(self, mock_statsd):
        """
        Failed requests in statsd_metered_request blocks should cause
        three events:
        1. Request made (increment).
        2. Time (Request made-> Request end).
        3. Request fail (increment).
        4. Request fail event.
        """
        from requests.exceptions import Timeout
        ERROR_MESSAGE = 'timed out while querying'
        fake_request = Mock(side_effect=Timeout(ERROR_MESSAGE))
        with self.assertRaisesRegexp(Timeout, ERROR_MESSAGE):
            with metered_request(self.REQUEST_METRIC_NAME):
                fake_request()
        fake_request.assert_any_call()
        EXPECTED_INCREMENT_CALLS = [
            call(self.REQUEST_MADE_METRIC),
            call(self.REQUEST_FAILED_METRIC)
        ]
        statsd_increment = mock_statsd.increment
        self.assertEqual(
            statsd_increment.call_args_list,
            EXPECTED_INCREMENT_CALLS
        )

        mock_statsd.timing.assert_not_called()
        statsd_event = mock_statsd.event
        statsd_event.assert_called_once_with(
            self.REQUEST_FAILED_METRIC_EVENT,
            ERROR_MESSAGE,
            alert_type='error'
        )
