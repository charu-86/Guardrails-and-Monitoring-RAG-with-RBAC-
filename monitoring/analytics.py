import datetime
from collections import Counter
import statistics

class Analytics:
    """Analytics module for RAG system metrics and usage tracking."""
    
    def __init__(self):
        # Internal storage
        self.query_log = []
        self.guardrail_events = []
        self.latency_samples = []
        self.token_usage = []

    def record_query(self, query, response, user, latency, tokens_used, guardrails_triggered):
        """Record a complete query transaction."""
        timestamp = datetime.datetime.now()
        
        # Record the main query event
        self.query_log.append({
            'timestamp': timestamp,
            'query': query,
            'response': response,
            'user': user,
            'latency': latency,
            'tokens_used': tokens_used,
            'guardrails_triggered': guardrails_triggered
        })
        
        # Record latency
        self.latency_samples.append({
            'timestamp': timestamp,
            'latency': latency
        })
        
        # Record tokens
        if tokens_used:
            self.token_usage.append({
                'timestamp': timestamp,
                'prompt_tokens': tokens_used.get('prompt', 0),
                'completion_tokens': tokens_used.get('completion', 0)
            })
            
        # Record guardrails if any triggered
        if guardrails_triggered:
            for trigger in guardrails_triggered:
                self.guardrail_events.append({
                    'timestamp': timestamp,
                    'type': trigger
                })

    def _filter_by_time(self, records, time_window_minutes):
        """Filter records by timestamp within the given time window."""
        cutoff = datetime.datetime.now() - datetime.timedelta(minutes=time_window_minutes)
        return [r for r in records if r['timestamp'] >= cutoff]

    def get_summary(self, time_window_minutes=60) -> dict:
        """Get summary statistics for the given time window."""
        recent_queries = self._filter_by_time(self.query_log, time_window_minutes)
        
        total_queries = len(recent_queries)
        latencies = [q['latency'] for q in recent_queries if 'latency' in q]
        avg_latency = statistics.mean(latencies) if latencies else 0.0
        
        total_tokens = sum(q.get('tokens_used', {}).get('prompt', 0) + 
                           q.get('tokens_used', {}).get('completion', 0) 
                           for q in recent_queries)
                           
        guardrail_trigger_count = sum(len(q.get('guardrails_triggered', [])) for q in recent_queries)
        
        unique_users = len(set(q['user'] for q in recent_queries if q.get('user')))
        
        return {
            'total_queries': total_queries,
            'avg_latency': avg_latency,
            'total_tokens': total_tokens,
            'guardrail_trigger_count': guardrail_trigger_count,
            'unique_users': unique_users,
            'time_window_minutes': time_window_minutes
        }

    def get_query_analytics(self, top_n=10) -> dict:
        """Get analytics about queries."""
        if not self.query_log:
            return {'most_frequent_queries': [], 'avg_response_time': 0}
            
        # Simple frequency count of exact queries
        queries = [q['query'] for q in self.query_log if q.get('query')]
        query_counts = Counter(queries).most_common(top_n)
        
        latencies = [q['latency'] for q in self.query_log if 'latency' in q]
        avg_response_time = statistics.mean(latencies) if latencies else 0.0
        
        return {
            'most_frequent_queries': query_counts,
            'avg_response_time': avg_response_time
        }

    def get_guardrail_report(self) -> dict:
        """Get report on guardrail triggers."""
        if not self.guardrail_events:
            return {'total_triggers': 0, 'breakdown': {}, 'most_common_type': None}
            
        types = [e['type'] for e in self.guardrail_events]
        counts = Counter(types)
        
        return {
            'total_triggers': len(self.guardrail_events),
            'breakdown': dict(counts),
            'most_common_type': counts.most_common(1)[0][0] if counts else None
        }

    def get_user_activity(self, username=None) -> dict:
        """Get activity report for users."""
        if username:
            user_queries = [q for q in self.query_log if q.get('user') == username]
            return {
                'username': username,
                'query_count': len(user_queries),
                'total_tokens': sum(q.get('tokens_used', {}).get('prompt', 0) + 
                                   q.get('tokens_used', {}).get('completion', 0) 
                                   for q in user_queries)
            }
        else:
            users = [q['user'] for q in self.query_log if q.get('user')]
            return {
                'total_active_users': len(set(users)),
                'queries_per_user': dict(Counter(users))
            }

    def get_token_usage_report(self) -> dict:
        """Get report on token usage and estimated cost."""
        total_prompt = sum(t.get('prompt_tokens', 0) for t in self.token_usage)
        total_completion = sum(t.get('completion_tokens', 0) for t in self.token_usage)
        
        # Example cost estimation (e.g., $0.01 per 1k prompt tokens, $0.03 per 1k completion tokens)
        cost_estimate = (total_prompt / 1000.0 * 0.01) + (total_completion / 1000.0 * 0.03)
        
        return {
            'total_prompt_tokens': total_prompt,
            'total_completion_tokens': total_completion,
            'total_tokens': total_prompt + total_completion,
            'estimated_cost_usd': cost_estimate
        }
