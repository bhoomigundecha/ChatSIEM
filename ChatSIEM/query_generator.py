"""
Query Generator - Converts intents into Elasticsearch DSL queries
"""
from typing import Dict, List, Any, Optional
from intent_parser import Intent
import logging

logger = logging.getLogger(__name__)


class QueryGenerator:
    """Generates Elasticsearch DSL queries from intents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.schema = config.get('schema', {})
        self.indices = config['siem'].get('indices', {})
        self.limits = config.get('limits', {})
    
    def generate(self, intent: Intent) -> Dict[str, Any]:
        """
        Generate Elasticsearch query from intent
        
        Args:
            intent: Parsed intent
            
        Returns:
            Dictionary with 'index' and 'query' for Elasticsearch
        """
        # Determine which index to query
        index = self._determine_index(intent)
        
        # Build the query based on action
        if intent.action == 'count':
            query = self._build_count_query(intent)
        elif intent.action == 'aggregate':
            query = self._build_aggregation_query(intent)
        elif intent.action == 'report':
            query = self._build_report_query(intent)
        else:  # search
            query = self._build_search_query(intent)
        
        return {
            'index': index,
            'query': query,
            'size': self._determine_size(intent)
        }
    
    def _determine_index(self, intent: Intent) -> str:
        """Determine which index pattern to query"""
        event_types = intent.entities.get('event_types', [])
        
        # Map event types to indices
        if 'malware' in event_types or 'threat' in event_types:
            return self.indices.get('endpoint_security', 'logs-*')
        elif 'network_connection' in event_types:
            return self.indices.get('network_traffic', 'packetbeat-*')
        elif 'alerts' in event_types:
            return self.indices.get('alerts', '.alerts-*')
        else:
            return self.indices.get('security_events', 'logs-*')
    
    def _determine_size(self, intent: Intent) -> int:
        """Determine result size limit"""
        if 'limit' in intent.filters:
            return min(intent.filters['limit'], self.limits.get('max_results', 10000))
        
        if intent.action == 'aggregate':
            return 0  # Don't return documents for aggregations
        
        return self.limits.get('default_size', 100)
    
    def _build_search_query(self, intent: Intent) -> Dict[str, Any]:
        """Build a search query"""
        must_clauses = []
        filter_clauses = []
        
        # Add event type conditions
        must_clauses.extend(self._build_event_conditions(intent))
        
        # Add filters
        filter_clauses.extend(self._build_filter_conditions(intent))
        
        # Add time range
        if 'time_range' in intent.filters:
            filter_clauses.append({
                'range': {
                    '@timestamp': intent.filters['time_range']
                }
            })
        
        query = {
            'query': {
                'bool': {
                    'must': must_clauses if must_clauses else [{'match_all': {}}],
                    'filter': filter_clauses
                }
            },
            'sort': [
                {'@timestamp': {'order': 'desc'}}
            ]
        }
        
        return query
    
    def _build_count_query(self, intent: Intent) -> Dict[str, Any]:
        """Build a count query"""
        # Similar to search but we only need the bool query
        must_clauses = []
        filter_clauses = []
        
        must_clauses.extend(self._build_event_conditions(intent))
        filter_clauses.extend(self._build_filter_conditions(intent))
        
        if 'time_range' in intent.filters:
            filter_clauses.append({
                'range': {
                    '@timestamp': intent.filters['time_range']
                }
            })
        
        return {
            'query': {
                'bool': {
                    'must': must_clauses if must_clauses else [{'match_all': {}}],
                    'filter': filter_clauses
                }
            }
        }
    
    def _build_aggregation_query(self, intent: Intent) -> Dict[str, Any]:
        """Build an aggregation query"""
        base_query = self._build_count_query(intent)
        
        # Determine aggregation fields
        agg_field = self._determine_aggregation_field(intent)
        
        # Add aggregation
        base_query['aggs'] = {
            'grouped_results': {
                'terms': {
                    'field': agg_field,
                    'size': self.limits.get('aggregation_size', 50)
                }
            },
            'over_time': {
                'date_histogram': {
                    'field': '@timestamp',
                    'calendar_interval': self._determine_time_interval(intent),
                    'min_doc_count': 0
                }
            }
        }
        
        return base_query
    
    def _build_report_query(self, intent: Intent) -> Dict[str, Any]:
        """Build a comprehensive query for report generation"""
        base_query = self._build_aggregation_query(intent)
        
        # Add multiple aggregations for comprehensive reporting
        event_types = intent.entities.get('event_types', [])
        
        base_query['aggs']['severity_breakdown'] = {
            'terms': {
                'field': 'event.severity',
                'size': 10
            }
        }
        
        base_query['aggs']['top_users'] = {
            'terms': {
                'field': 'user.name.keyword',
                'size': 10
            }
        }
        
        base_query['aggs']['top_hosts'] = {
            'terms': {
                'field': 'host.name.keyword',
                'size': 10
            }
        }
        
        if 'network_connection' in event_types:
            base_query['aggs']['top_destinations'] = {
                'terms': {
                    'field': 'destination.ip',
                    'size': 10
                }
            }
        
        return base_query
    
    def _build_event_conditions(self, intent: Intent) -> List[Dict[str, Any]]:
        """Build conditions for event types"""
        conditions = []
        event_types = intent.entities.get('event_types', [])
        
        for event_type in event_types:
            if event_type in self.schema:
                schema = self.schema[event_type]
                event_conditions = schema.get('conditions', {})
                
                for field, values in event_conditions.items():
                    if isinstance(values, list):
                        conditions.append({
                            'terms': {
                                field: values
                            }
                        })
                    else:
                        conditions.append({
                            'term': {
                                field: values
                            }
                        })
        
        return conditions
    
    def _build_filter_conditions(self, intent: Intent) -> List[Dict[str, Any]]:
        """Build filter conditions"""
        conditions = []
        filters = intent.filters
        
        # User filter
        if 'user' in filters:
            conditions.append({
                'term': {
                    'user.name.keyword': filters['user']
                }
            })
        
        # IP filters
        if 'ip' in filters:
            conditions.append({
                'bool': {
                    'should': [
                        {'term': {'source.ip': filters['ip']}},
                        {'term': {'destination.ip': filters['ip']}}
                    ]
                }
            })
        
        if 'source_ip' in filters:
            conditions.append({
                'term': {
                    'source.ip': filters['source_ip']
                }
            })
        
        if 'destination_ip' in filters:
            conditions.append({
                'term': {
                    'destination.ip': filters['destination_ip']
                }
            })
        
        # Hostname filter
        if 'hostname' in filters:
            conditions.append({
                'term': {
                    'host.name.keyword': filters['hostname']
                }
            })
        
        # Port filter
        if 'port' in filters:
            conditions.append({
                'term': {
                    'destination.port': int(filters['port'])
                }
            })
        
        # Severity filter
        if 'severity' in filters:
            conditions.append({
                'term': {
                    'event.severity': filters['severity'].lower()
                }
            })
        
        # Status filter
        if 'status' in filters:
            conditions.append({
                'term': {
                    'event.outcome': filters['status'].lower()
                }
            })
        
        return conditions
    
    def _determine_aggregation_field(self, intent: Intent) -> str:
        """Determine the best field for aggregation"""
        event_types = intent.entities.get('event_types', [])
        
        # Check for specific aggregation requests in the query
        if 'user' in str(intent.entities).lower():
            return 'user.name.keyword'
        elif 'host' in str(intent.entities).lower():
            return 'host.name.keyword'
        elif 'ip' in str(intent.entities).lower():
            return 'source.ip'
        
        # Default aggregations based on event type
        if 'malware' in event_types:
            return 'file.name.keyword'
        elif 'network_connection' in event_types:
            return 'destination.ip'
        elif 'failed_login' in event_types or 'successful_login' in event_types:
            return 'user.name.keyword'
        
        # Default
        return 'event.action.keyword'
    
    def _determine_time_interval(self, intent: Intent) -> str:
        """Determine appropriate time interval for date histograms"""
        time_range = intent.filters.get('time_range', {})
        gte = time_range.get('gte', 'now-24h')
        
        # Parse the time range to determine interval
        if 'now-1h' in gte or 'last_hour' in gte:
            return '1m'  # 1 minute intervals
        elif 'now-24h' in gte or 'now-1d' in gte:
            return '1h'  # 1 hour intervals
        elif 'now-7d' in gte:
            return '1d'  # 1 day intervals
        elif 'now-30d' in gte or 'now-1M' in gte:
            return '1d'  # 1 day intervals
        else:
            return '1d'  # Default to daily
    
    def generate_kql(self, intent: Intent) -> str:
        """
        Generate KQL (Kibana Query Language) as alternative to DSL
        
        Args:
            intent: Parsed intent
            
        Returns:
            KQL query string
        """
        kql_parts = []
        
        # Add event type conditions
        event_types = intent.entities.get('event_types', [])
        for event_type in event_types:
            if event_type in self.schema:
                schema = self.schema[event_type]
                conditions = schema.get('conditions', {})
                
                for field, values in conditions.items():
                    if isinstance(values, list):
                        value_str = ' or '.join([f'"{v}"' for v in values])
                        kql_parts.append(f'{field}: ({value_str})')
                    else:
                        kql_parts.append(f'{field}: "{values}"')
        
        # Add filters
        filters = intent.filters
        
        if 'user' in filters:
            kql_parts.append(f'user.name: "{filters["user"]}"')
        
        if 'source_ip' in filters:
            kql_parts.append(f'source.ip: {filters["source_ip"]}')
        
        if 'destination_ip' in filters:
            kql_parts.append(f'destination.ip: {filters["destination_ip"]}')
        
        if 'hostname' in filters:
            kql_parts.append(f'host.name: "{filters["hostname"]}"')
        
        if 'port' in filters:
            kql_parts.append(f'destination.port: {filters["port"]}')
        
        # Combine with AND
        kql = ' and '.join(kql_parts) if kql_parts else '*'
        
        return kql
    
    def optimize_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize query for performance
        
        Args:
            query: Elasticsearch query
            
        Returns:
            Optimized query
        """
        # Add _source filtering to reduce payload
        if '_source' not in query:
            query['_source'] = [
                '@timestamp',
                'event.*',
                'user.name',
                'host.name',
                'source.ip',
                'destination.ip',
                'destination.port',
                'file.name',
                'process.name',
                'message'
            ]
        
        # Add track_total_hits limit for better performance
        if 'track_total_hits' not in query:
            query['track_total_hits'] = 10000
        
        return query


class QueryValidator:
    """Validates generated queries before execution"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_results = config.get('limits', {}).get('max_results', 10000)
    
    def validate(self, query_config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a query configuration
        
        Args:
            query_config: Query configuration with index and query
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if index is specified
        if 'index' not in query_config:
            return False, "No index specified"
        
        # Check if query is present
        if 'query' not in query_config:
            return False, "No query specified"
        
        # Validate size
        size = query_config.get('size', 0)
        if size > self.max_results:
            return False, f"Size {size} exceeds maximum {self.max_results}"
        
        # Validate query structure
        query = query_config['query']
        if not isinstance(query, dict):
            return False, "Query must be a dictionary"
        
        if 'query' not in query:
            return False, "Query must contain 'query' field"
        
        return True, None
    
    def estimate_cost(self, query_config: Dict[str, Any]) -> str:
        """
        Estimate the performance cost of a query
        
        Args:
            query_config: Query configuration
            
        Returns:
            Cost estimate: 'low', 'medium', 'high'
        """
        query = query_config.get('query', {})
        size = query_config.get('size', 100)
        
        # Check for expensive operations
        has_aggregations = 'aggs' in query
        has_wildcards = self._has_wildcards(query)
        has_regex = self._has_regex(query)
        
        if has_regex or (has_aggregations and size > 1000):
            return 'high'
        elif has_wildcards or has_aggregations:
            return 'medium'
        else:
            return 'low'
    
    def _has_wildcards(self, obj: Any) -> bool:
        """Check if query contains wildcard queries"""
        if isinstance(obj, dict):
            if 'wildcard' in obj:
                return True
            return any(self._has_wildcards(v) for v in obj.values())
        elif isinstance(obj, list):
            return any(self._has_wildcards(item) for item in obj)
        return False
    
    def _has_regex(self, obj: Any) -> bool:
        """Check if query contains regex queries"""
        if isinstance(obj, dict):
            if 'regexp' in obj:
                return True
            return any(self._has_regex(v) for v in obj.values())
        elif isinstance(obj, list):
            return any(self._has_regex(item) for item in obj)
        return False