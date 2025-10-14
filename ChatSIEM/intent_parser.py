"""
Intent Parser - Extracts intent and entities from natural language queries
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
from dateutil import parser as date_parser
import logging

logger = logging.getLogger(__name__)


class Intent:
    """Represents a parsed user intent"""
    
    def __init__(self, action: str, entities: Dict[str, Any], 
                 filters: Dict[str, Any], context: Optional[Dict] = None):
        self.action = action  # search, count, aggregate, report
        self.entities = entities  # event types, users, IPs, etc.
        self.filters = filters  # time range, status, etc.
        self.context = context or {}
        self.timestamp = datetime.now()
    
    def __repr__(self):
        return f"Intent(action={self.action}, entities={self.entities}, filters={self.filters})"


class IntentParser:
    """Parses natural language into structured intents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.schema = config.get('schema', {})
        self.time_ranges = config.get('time_ranges', {})
        
        # Intent patterns
        self.action_patterns = {
            'search': [
                r'show|find|get|list|display|what|which',
                r'search for|look for|give me'
            ],
            'count': [
                r'how many|count|number of|total',
                r'how much'
            ],
            'aggregate': [
                r'summarize|summary|group by|breakdown',
                r'aggregate|top|most|least'
            ],
            'report': [
                r'report|generate report|create report',
                r'export|document'
            ]
        }
        
        # Entity patterns for security events
        self.entity_patterns = {
            'failed_login': [
                r'failed login|login failure|authentication fail|unsuccessful login',
                r'failed auth|auth fail|bad password|invalid credentials'
            ],
            'successful_login': [
                r'successful login|login success|authenticated|logged in successfully'
            ],
            'malware': [
                r'malware|virus|trojan|ransomware|suspicious file',
                r'threat detected|malicious|infected'
            ],
            'network_connection': [
                r'network connection|outbound connection|inbound connection',
                r'network traffic|connection attempt'
            ],
            'vpn': [
                r'vpn|virtual private network|vpn connection|vpn login',
                r'remote access'
            ],
            'firewall': [
                r'firewall|blocked|denied|dropped',
                r'firewall rule|firewall block'
            ],
            'user_activity': [
                r'user activity|user action|user behavior',
                r'what did user|user events'
            ],
            'alerts': [
                r'alert|security alert|triggered alert|alerted',
                r'detection|detected'
            ],
            'process': [
                r'process|execution|program|command|executed'
            ],
            'file_operation': [
                r'file created|file modified|file deleted|file access',
                r'file operation|file activity'
            ]
        }
        
        # Filter patterns
        self.filter_patterns = {
            'user': r'(?:user|username|account|user name)[\s:]+([a-zA-Z0-9._-]+)',
            'ip': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'hostname': r'(?:host|hostname|computer)[\s:]+([a-zA-Z0-9._-]+)',
            'source_ip': r'(?:source|from|src)[\s:]+(?:ip[\s:]+)?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
            'destination_ip': r'(?:destination|dest|dst|to)[\s:]+(?:ip[\s:]+)?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
            'port': r'(?:port|:)(\d{1,5})',
            'severity': r'(?:severity|priority)[\s:]+(\w+)',
            'status': r'(?:status)[\s:]+(\w+)'
        }
    
    def parse(self, query: str, context: Optional[Dict] = None) -> Intent:
        """
        Parse a natural language query into an Intent
        
        Args:
            query: Natural language query
            context: Previous conversation context
            
        Returns:
            Parsed Intent object
        """
        query_lower = query.lower()
        
        # Detect action
        action = self._detect_action(query_lower)
        
        # Extract entities
        entities = self._extract_entities(query_lower)
        
        # Extract filters
        filters = self._extract_filters(query, query_lower)
        
        # Apply context from previous queries
        if context:
            entities = self._apply_context(entities, context.get('entities', {}))
            filters = self._apply_context(filters, context.get('filters', {}))
        
        return Intent(action, entities, filters, context)
    
    def _detect_action(self, query: str) -> str:
        """Detect the primary action from query"""
        for action, patterns in self.action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return action
        
        # Default to search
        return 'search'
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract security event entities from query"""
        entities = {'event_types': []}
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    entities['event_types'].append(entity_type)
                    
                    # Add schema information if available
                    if entity_type in self.schema:
                        entities[f'{entity_type}_schema'] = self.schema[entity_type]
        
        return entities
    
    def _extract_filters(self, original_query: str, query: str) -> Dict[str, Any]:
        """Extract filters from query"""
        filters = {}
        
        # Extract specific filters using patterns
        for filter_name, pattern in self.filter_patterns.items():
            match = re.search(pattern, original_query, re.IGNORECASE)
            if match:
                filters[filter_name] = match.group(1)
        
        # Extract time range
        time_filter = self._extract_time_range(query)
        if time_filter:
            filters['time_range'] = time_filter
        
        # Extract limit/size
        limit_match = re.search(r'(?:top|first|last|limit)\s+(\d+)', query, re.IGNORECASE)
        if limit_match:
            filters['limit'] = int(limit_match.group(1))
        
        return filters
    
    def _extract_time_range(self, query: str) -> Optional[Dict[str, str]]:
        """Extract time range from query"""
        # Check predefined time ranges
        for time_key, time_value in self.time_ranges.items():
            if time_key.replace('_', ' ') in query:
                return {
                    'gte': time_value,
                    'lte': 'now'
                }
        
        # Try to parse specific dates
        date_patterns = [
            r'(?:from|since|after)\s+([0-9]{4}-[0-9]{2}-[0-9]{2})',
            r'(?:until|before|to)\s+([0-9]{4}-[0-9]{2}-[0-9]{2})',
            r'on\s+([0-9]{4}-[0-9]{2}-[0-9]{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, query)
            if match:
                try:
                    date_str = match.group(1)
                    parsed_date = date_parser.parse(date_str)
                    
                    if 'from' in pattern or 'since' in pattern or 'after' in pattern:
                        return {'gte': parsed_date.isoformat(), 'lte': 'now'}
                    elif 'until' in pattern or 'before' in pattern or 'to' in pattern:
                        return {'gte': 'now-30d', 'lte': parsed_date.isoformat()}
                    elif 'on' in pattern:
                        end_date = parsed_date + timedelta(days=1)
                        return {
                            'gte': parsed_date.isoformat(),
                            'lte': end_date.isoformat()
                        }
                except Exception as e:
                    logger.warning(f"Failed to parse date: {e}")
        
        # Default time range for queries without explicit time
        return {'gte': 'now-24h', 'lte': 'now'}
    
    def _apply_context(self, current: Dict[str, Any], 
                       previous: Dict[str, Any]) -> Dict[str, Any]:
        """Apply context from previous queries"""
        # Merge context intelligently
        result = previous.copy()
        result.update(current)
        
        # Combine event types if present in both
        if 'event_types' in current and 'event_types' in previous:
            current_types = set(current['event_types'])
            previous_types = set(previous['event_types'])
            
            # If current is more specific, use it; otherwise combine
            if current_types:
                result['event_types'] = list(current_types)
            else:
                result['event_types'] = list(previous_types)
        
        return result
    
    def extract_filter_refinements(self, query: str) -> Dict[str, Any]:
        """
        Extract filter refinements for follow-up queries
        Examples: "only VPN", "exclude user admin", "from last hour"
        """
        refinements = {}
        
        # Include/only patterns
        include_match = re.search(r'(?:only|just|include)\s+(.+)', query, re.IGNORECASE)
        if include_match:
            refinements['include'] = include_match.group(1).strip()
        
        # Exclude patterns
        exclude_match = re.search(r'(?:exclude|without|not)\s+(.+)', query, re.IGNORECASE)
        if exclude_match:
            refinements['exclude'] = exclude_match.group(1).strip()
        
        # Time refinements
        if 'last hour' in query.lower():
            refinements['time_range'] = {'gte': 'now-1h', 'lte': 'now'}
        
        return refinements


class ContextManager:
    """Manages conversation context across multiple queries"""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[Intent] = []
        self.current_context: Dict[str, Any] = {}
    
    def add_intent(self, intent: Intent):
        """Add an intent to history"""
        self.history.append(intent)
        
        # Update current context
        self.current_context = {
            'entities': intent.entities,
            'filters': intent.filters,
            'action': intent.action
        }
        
        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_context(self) -> Dict[str, Any]:
        """Get current context"""
        return self.current_context
    
    def clear(self):
        """Clear conversation history"""
        self.history.clear()
        self.current_context.clear()
    
    def get_last_intent(self) -> Optional[Intent]:
        """Get the last intent"""
        return self.history[-1] if self.history else None
    
    def is_refinement_query(self, query: str) -> bool:
        """Check if query is refining previous query"""
        refinement_keywords = [
            'filter', 'only', 'exclude', 'also', 'and', 
            'show more', 'narrow', 'focus on', 'just'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in refinement_keywords)