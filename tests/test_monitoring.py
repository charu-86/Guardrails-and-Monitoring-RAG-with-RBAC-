import pytest
from monitoring.logger import Logger
from monitoring.metrics import MetricsCollector
from monitoring.analytics import Analytics

class TestLogger:
    @pytest.fixture
    def logger(self):
        return Logger()

    def test_logger_creation(self, logger):
        assert logger is not None

    def test_info_log(self, logger):
        logger.info("Test info message")

    def test_warning_log(self, logger):
        logger.warning("Test warning message")

    def test_error_log(self, logger):
        logger.error("Test error message")

    def test_audit_log(self, logger):
        # Audit returns None, just make sure it executes cleanly
        logger.audit(
            event_type="ACCESS",
            user="admin",
            resource="document1",
            action="read",
            success=True
        )
        assert True


class TestMetricsCollector:
    @pytest.fixture(scope="module")
    def metrics(self):
        try:
            return MetricsCollector()
        except ValueError:
            # Handle prometheus duplicate registration in tests if necessary
            pass

    def test_metrics_creation(self, metrics):
        assert metrics is not None

    def test_record_query(self, metrics):
        metrics.record_query()

    def test_record_latency(self, metrics):
        metrics.record_latency(1.5)

    def test_record_tokens(self, metrics):
        metrics.record_tokens(prompt_tokens=10, completion_tokens=20)

    def test_record_guardrail_trigger(self, metrics):
        metrics.record_guardrail_trigger("pii_detected")

    def test_record_rbac_denial(self, metrics):
        metrics.record_rbac_denial(user_role="viewer", permission="manage_users")


class TestAnalytics:
    @pytest.fixture
    def analytics(self):
        return Analytics()

    def test_analytics_creation(self, analytics):
        assert analytics is not None

    def test_record_and_summarize(self, analytics):
        analytics.record_query(
            query="test query", 
            response="test response", 
            user="user1", 
            latency=1.0, 
            tokens_used={"prompt": 10, "completion": 20}, 
            guardrails_triggered=[]
        )
        summary = analytics.get_summary()
        assert summary['total_queries'] >= 1
        assert summary['avg_latency'] > 0

    def test_get_guardrail_report(self, analytics):
        analytics.record_query("q1", "r1", "u1", 1.0, {}, ["pii"])
        analytics.record_query("q2", "r2", "u1", 1.0, {}, ["pii"])
        analytics.record_query("q3", "r3", "u1", 1.0, {}, ["toxicity"])
        
        report = analytics.get_guardrail_report()
        assert report['breakdown']['pii'] >= 2
        assert report['breakdown']['toxicity'] >= 1

    def test_get_token_usage_report(self, analytics):
        analytics.record_query("q1", "r1", "u1", 1.0, {"prompt": 10, "completion": 20}, [])
        report = analytics.get_token_usage_report()
        assert 'total_prompt_tokens' in report
        assert 'total_completion_tokens' in report
        assert 'total_tokens' in report
        assert report['total_tokens'] >= 30

    def test_empty_summary(self, analytics):
        empty_analytics = Analytics()
        summary = empty_analytics.get_summary()
        assert summary['total_queries'] == 0
