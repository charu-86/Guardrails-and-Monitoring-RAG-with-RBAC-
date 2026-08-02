import yaml
import pathlib
from prometheus_client import Counter, Histogram, Gauge, start_http_server

from prometheus_client import REGISTRY

class MetricsCollector:
    """Prometheus metrics collector for the RAG system."""
    
    _instance = None
    
    def __new__(cls, config=None):
        if cls._instance is None:
            cls._instance = super(MetricsCollector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config=None):
        if getattr(self, '_initialized', False):
            return
        self.config = config or self._load_config()
        monitoring_config = self.config.get('monitoring', {})
        
        prefix = monitoring_config.get('metrics_prefix', 'rag_system')
        
        # Helper to get or create metric safely
        def get_or_create(metric_cls, name, documentation, *args, **kwargs):
            try:
                return metric_cls(name, documentation, *args, **kwargs)
            except ValueError:
                return REGISTRY._names_to_collectors.get(name)

        self.query_total = get_or_create(
            Counter, f'{prefix}_query_total', 'Total number of queries', ['status', 'user_role']
        )
        
        self.query_latency_seconds = get_or_create(
            Histogram, f'{prefix}_query_latency_seconds', 'Query latency in seconds',
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.tokens_used = get_or_create(
            Counter, f'{prefix}_tokens_used', 'Number of tokens used', ['token_type']
        )
        
        self.guardrail_triggers = get_or_create(
            Counter, f'{prefix}_guardrail_triggers', 'Number of times guardrails were triggered', ['trigger_type']
        )
        
        self.active_users = get_or_create(
            Gauge, f'{prefix}_active_users', 'Number of active users'
        )
        
        self.rbac_denials = get_or_create(
            Counter, f'{prefix}_rbac_denials', 'Number of RBAC denials', ['user_role', 'permission']
        )
        self._initialized = True

    def _load_config(self):
        """Load configuration from config/config.yaml."""
        config_path = pathlib.Path(__file__).parent.parent / 'config' / 'config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error loading config from {config_path}: {e}")
        return {}

    def start_server(self, port=None):
        """Start the Prometheus HTTP server."""
        if port is None:
            monitoring_config = self.config.get('monitoring', {})
            port = monitoring_config.get('metrics_port', 8001)
        start_http_server(port)

    def record_query(self, status='success', user_role='viewer'):
        """Record a query event."""
        self.query_total.labels(status=status, user_role=user_role).inc()

    def record_latency(self, duration_seconds: float):
        """Record query latency."""
        self.query_latency_seconds.observe(duration_seconds)

    def record_tokens(self, prompt_tokens: int, completion_tokens: int):
        """Record token usage."""
        self.tokens_used.labels(token_type='prompt').inc(prompt_tokens)
        self.tokens_used.labels(token_type='completion').inc(completion_tokens)

    def record_guardrail_trigger(self, trigger_type: str):
        """Record a guardrail trigger event."""
        self.guardrail_triggers.labels(trigger_type=trigger_type).inc()

    def record_rbac_denial(self, user_role: str, permission: str):
        """Record an RBAC denial event."""
        self.rbac_denials.labels(user_role=user_role, permission=permission).inc()

    def increment_active_users(self):
        """Increment the active users gauge."""
        self.active_users.inc()

    def decrement_active_users(self):
        """Decrement the active users gauge."""
        self.active_users.dec()
