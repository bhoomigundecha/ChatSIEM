"""
SIEM Connector - Handles communication with Elasticsearch/Wazuh
"""
import os
from typing import Dict, List, Any, Optional
from elasticsearch import Elasticsearch, exceptions
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SIEMConnector:
    """Base connector for ELK-based SIEMs"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize SIEM connection"""
        self.config = config
        self.client = self._create_client()
        self._verify_connection()
    
    def _create_client(self) -> Elasticsearch:
        """Create Elasticsearch client"""
        siem_config = self.config['siem']
        
        client = Elasticsearch(
            hosts=[{
                'host': siem_config['host'],
                'port': siem_config['port'],
                'scheme': siem_config['scheme']
            }],
            basic_auth=(siem_config['username'], siem_config['password']),
            verify_certs=siem_config.get('verify_certs', False),
            request_timeout=30
        )
        
        return client
    
    def _verify_connection(self):
        """Verify SIEM connection is working"""
        try:
            info = self.client.info()
            logger.info(f"Connected to Elasticsearch cluster: {info['cluster_name']}")
            logger.info(f"Version: {info['version']['number']}")
        except Exception as e:
            logger.error(f"Failed to connect to SIEM: {e}")
            raise ConnectionError(f"Cannot connect to SIEM: {e}")
    
    def execute_query(self, index: str, query: Dict[str, Any], 
                     size: int = 100) -> Dict[str, Any]:
        """
        Execute an Elasticsearch DSL query
        
        Args:
            index: Index pattern to search
            query: Elasticsearch DSL query
            size: Number of results to return
            
        Returns:
            Query results
        """
        try:
            response = self.client.search(
                index=index,
                body=query,
                size=size
            )
            
            logger.info(f"Query executed successfully. Found {response['hits']['total']['value']} hits")
            return response
            
        except exceptions.RequestError as e:
            logger.error(f"Query error: {e.info}")
            raise ValueError(f"Invalid query: {e.info['error']['reason']}")
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise
    
    def execute_aggregation(self, index: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an aggregation query
        
        Args:
            index: Index pattern to search
            query: Query with aggregations
            
        Returns:
            Aggregation results
        """
        try:
            response = self.client.search(
                index=index,
                body=query,
                size=0  # We only want aggregations
            )
            
            return response.get('aggregations', {})
            
        except Exception as e:
            logger.error(f"Aggregation error: {e}")
            raise
    
    def get_index_mappings(self, index: str) -> Dict[str, Any]:
        """
        Get field mappings for an index
        
        Args:
            index: Index pattern
            
        Returns:
            Field mappings
        """
        try:
            mappings = self.client.indices.get_mapping(index=index)
            return mappings
        except Exception as e:
            logger.error(f"Error getting mappings: {e}")
            return {}
    
    def search_fields(self, index: str, field_name: str) -> List[str]:
        """
        Search for fields matching a pattern
        
        Args:
            index: Index pattern
            field_name: Field name pattern to search
            
        Returns:
            List of matching field names
        """
        try:
            mappings = self.get_index_mappings(index)
            fields = []
            
            for idx, mapping in mappings.items():
                properties = mapping['mappings'].get('properties', {})
                fields.extend(self._extract_fields(properties, field_name))
            
            return list(set(fields))
        except Exception as e:
            logger.error(f"Error searching fields: {e}")
            return []
    
    def _extract_fields(self, properties: Dict, pattern: str, prefix: str = "") -> List[str]:
        """Recursively extract field names matching pattern"""
        fields = []
        
        for field, details in properties.items():
            full_field = f"{prefix}.{field}" if prefix else field
            
            if pattern.lower() in field.lower():
                fields.append(full_field)
            
            if 'properties' in details:
                fields.extend(
                    self._extract_fields(details['properties'], pattern, full_field)
                )
        
        return fields
    
    def count_documents(self, index: str, query: Dict[str, Any]) -> int:
        """
        Count documents matching a query
        
        Args:
            index: Index pattern
            query: Query to count
            
        Returns:
            Document count
        """
        try:
            response = self.client.count(index=index, body=query)
            return response['count']
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
    
    def get_field_values(self, index: str, field: str, 
                        query: Optional[Dict] = None, size: int = 100) -> List[Any]:
        """
        Get unique values for a field
        
        Args:
            index: Index pattern
            field: Field name
            query: Optional filter query
            size: Max number of unique values
            
        Returns:
            List of unique field values
        """
        agg_query = {
            "size": 0,
            "aggs": {
                "unique_values": {
                    "terms": {
                        "field": field,
                        "size": size
                    }
                }
            }
        }
        
        if query:
            agg_query["query"] = query
        
        try:
            result = self.execute_aggregation(index, agg_query)
            buckets = result.get('unique_values', {}).get('buckets', [])
            return [bucket['key'] for bucket in buckets]
        except Exception as e:
            logger.error(f"Error getting field values: {e}")
            return []
    
    def close(self):
        """Close the connection"""
        if self.client:
            self.client.close()
            logger.info("SIEM connection closed")


class WazuhConnector(SIEMConnector):
    """Specialized connector for Wazuh SIEM"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Wazuh connection"""
        super().__init__(config)
        # Add Wazuh-specific initialization if needed
        self.wazuh_api_url = config['siem'].get('wazuh_api_url')
    
    def get_agents(self) -> List[Dict[str, Any]]:
        """Get list of Wazuh agents"""
        # Implement Wazuh-specific API calls if needed
        pass
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Get Wazuh rules"""
        # Implement Wazuh-specific API calls if needed
        pass


def create_siem_connector(config: Dict[str, Any]) -> SIEMConnector:
    """
    Factory function to create appropriate SIEM connector
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Appropriate SIEM connector instance
    """
    siem_type = config['siem'].get('type', 'elastic').lower()
    
    if siem_type == 'wazuh':
        return WazuhConnector(config)
    else:
        return SIEMConnector(config)