import logging
import json
import yaml
import pathlib
import datetime
import traceback
import sys

# Optional import for sentry
try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

class JsonFormatter(logging.Formatter):
    """JSON formatter for logging."""
    
    def format(self, record):
        """Format the record as a JSON string."""
        log_record = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if they exist
        if hasattr(record, "extra"):
            log_record.update(record.extra)
            
        # Add exception info if present
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)


class Logger:
    """Configurable logger with JSON formatting and Sentry support."""
    
    def __init__(self, name='rag_system', config=None):
        self.name = name
        self.config = config or self._load_config()
        self.logger = logging.getLogger(name)
        
        # Default settings if config missing
        monitoring_config = self.config.get('monitoring', {})
        log_level_str = monitoring_config.get('log_level', 'INFO')
        self.logger.setLevel(getattr(logging, log_level_str.upper(), logging.INFO))
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers(monitoring_config)
            
        self._setup_sentry(monitoring_config)

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

    def _setup_handlers(self, config):
        """Setup logging handlers based on configuration."""
        formatter = JsonFormatter()
        
        # Stream Handler
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)
        
        # File Handler
        log_file = config.get('log_file', 'logs/rag_system.log')
        if log_file:
            log_path = pathlib.Path(log_file)
            # Create directory if it doesn't exist
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _setup_sentry(self, config):
        """Initialize Sentry if enabled."""
        if config.get('enable_sentry', False) and sentry_sdk:
            dsn = config.get('sentry_dsn')
            if dsn:
                sentry_sdk.init(dsn=dsn)
                self.logger.info("Sentry initialized.")

    def info(self, message, **kwargs):
        """Log info message with optional extra context."""
        self.logger.info(message, extra={'extra': kwargs} if kwargs else None)

    def warning(self, message, **kwargs):
        """Log warning message with optional extra context."""
        self.logger.warning(message, extra={'extra': kwargs} if kwargs else None)

    def error(self, message, exc_info=False, **kwargs):
        """Log error message with optional extra context and exception info."""
        self.logger.error(message, exc_info=exc_info, extra={'extra': kwargs} if kwargs else None)

    def debug(self, message, **kwargs):
        """Log debug message with optional extra context."""
        self.logger.debug(message, extra={'extra': kwargs} if kwargs else None)

    def audit(self, event_type, user=None, resource=None, action=None, success=True, details=None):
        """Log a structured audit event."""
        audit_record = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user": user,
            "resource": resource,
            "action": action,
            "success": success,
            "details": details or {}
        }
        self.logger.info("AUDIT_EVENT", extra={"audit": audit_record})
