"""
SIEM Assistant - Main conversational interface
"""
import yaml
import os
from typing import Dict, List, Any, Optional
import logging
from dotenv import load_dotenv

from siem_connector import create_siem_connector
from intent_parser import IntentParser, ContextManager, Intent
from query_generator import QueryGenerator, QueryValidator
from response_formatter import ResponseFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SIEMAssistant:
    """
    Conversational SIEM Assistant for Investigation and Automated Threat Reporting
    """
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize the SIEM Assistant
        
        Args:
            config_path: Path to configuration file
        """
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        logger.info("Initializing SIEM Assistant components...")
        
        try:
            self.siem_connector = create_siem_connector(self.config)
            self.intent_parser = IntentParser(self.config)
            self.context_manager = ContextManager()
            self.query_generator = QueryGenerator(self.config)
            self.query_validator = QueryValidator(self.config)
            self.response_formatter = ResponseFormatter(self.config)
            
            logger.info("SIEM Assistant initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SIEM Assistant: {e}")
            raise
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Substitute environment variables
            config = self._substitute_env_vars(config)
            
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """Recursively substitute environment variables in config"""
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
            var_name = config[2:-1]
            return os.getenv(var_name, config)
        return config
    
    def ask(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query
        
        Args:
            query: Natural language query from user
            
        Returns:
            Formatted response with results
        """
        try:
            logger.info(f"Processing query: {query}")
            
            # Step 1: Parse intent from natural language
            context = self.context_manager.get_context()
            intent = self.intent_parser.parse(query, context)
            logger.info(f"Parsed intent: {intent}")
            
            # Step 2: Generate Elasticsearch query
            query_config = self.query_generator.generate(intent)
            logger.info(f"Generated query for index: {query_config['index']}")
            
            # Step 3: Validate query
            is_valid, error_msg = self.query_validator.validate(query_config)
            if not is_valid:
                logger.error(f"Query validation failed: {error_msg}")
                return {
                    'success': False,
                    'error': f"Query validation failed: {error_msg}",
                    'suggestions': self._get_query_suggestions(intent)
                }
            
            # Step 4: Estimate query cost
            cost = self.query_validator.estimate_cost(query_config)
            logger.info(f"Query cost estimate: {cost}")
            
            # Step 5: Execute query
            results = self._execute_query(query_config, intent)
            
            # Step 6: Format response
            formatted_response = self.response_formatter.format_response(
                results, 
                intent.action
            )
            
            # Step 7: Update context
            self.context_manager.add_intent(intent)
            
            # Add metadata
            formatted_response['success'] = True
            formatted_response['query_cost'] = cost
            formatted_response['intent'] = {
                'action': intent.action,
                'entities': intent.entities,
                'filters': intent.filters
            }
            
            logger.info("Query processed successfully")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'suggestions': ['Try rephrasing your question', 
                              'Check if the time range is valid',
                              'Verify field names and values']
            }
    
    def _execute_query(self, query_config: Dict[str, Any], 
                       intent: Intent) -> Dict[str, Any]:
        """Execute the query based on intent action"""
        index = query_config['index']
        query = query_config['query']
        size = query_config['size']
        
        if intent.action == 'count':
            count = self.siem_connector.count_documents(index, query)
            return {
                'hits': {
                    'total': {'value': count}
                }
            }
        elif intent.action in ['aggregate', 'report']:
            return self.siem_connector.execute_aggregation(index, query)
        else:
            return self.siem_connector.execute_query(index, query, size)
    
    def _get_query_suggestions(self, intent: Intent) -> List[str]:
        """Generate helpful suggestions based on intent"""
        suggestions = []
        
        if not intent.entities.get('event_types'):
            suggestions.append("Try specifying an event type (e.g., 'failed logins', 'malware', 'network connections')")
        
        if not intent.filters.get('time_range'):
            suggestions.append("Consider adding a time range (e.g., 'yesterday', 'last week', 'last 24 hours')")
        
        suggestions.append("Use more specific terms like user names, IP addresses, or hostnames")
        
        return suggestions
    
    def generate_report(self, query: str, output_format: str = 'text') -> str:
        """
        Generate a comprehensive report
        
        Args:
            query: Natural language query describing the report
            output_format: Output format (text, json, html, csv)
            
        Returns:
            Report in specified format
        """
        # Process query with report action
        response = self.ask(query)
        
        if not response.get('success'):
            return f"Error generating report: {response.get('error')}"
        
        # Export based on format
        if output_format == 'json':
            return self.response_formatter.export_to_json(response)
        elif output_format == 'csv':
            return self.response_formatter.export_to_csv(response)
        elif output_format == 'html':
            return self.response_formatter.export_to_html(response)
        else:
            return response.get('text', 'No report generated')
    
    def get_available_indices(self) -> List[str]:
        """Get list of available indices in SIEM"""
        try:
            indices = self.config['siem']['indices']
            return list(indices.values())
        except Exception as e:
            logger.error(f"Error getting indices: {e}")
            return []
    
    def get_field_suggestions(self, index: str, field_pattern: str) -> List[str]:
        """
        Get field name suggestions
        
        Args:
            index: Index pattern to search
            field_pattern: Partial field name
            
        Returns:
            List of matching field names
        """
        return self.siem_connector.search_fields(index, field_pattern)
    
    def explain_query(self, query: str) -> Dict[str, Any]:
        """
        Explain how a natural language query will be processed
        
        Args:
            query: Natural language query
            
        Returns:
            Explanation of query processing
        """
        try:
            # Parse intent
            context = self.context_manager.get_context()
            intent = self.intent_parser.parse(query, context)
            
            # Generate query
            query_config = self.query_generator.generate(intent)
            
            # Generate KQL alternative
            kql = self.query_generator.generate_kql(intent)
            
            return {
                'original_query': query,
                'detected_intent': {
                    'action': intent.action,
                    'event_types': intent.entities.get('event_types', []),
                    'filters': intent.filters
                },
                'target_index': query_config['index'],
                'elasticsearch_dsl': query_config['query'],
                'kql_equivalent': kql,
                'estimated_cost': self.query_validator.estimate_cost(query_config)
            }
        except Exception as e:
            return {
                'error': str(e),
                'original_query': query
            }
    
    def clear_context(self):
        """Clear conversation context"""
        self.context_manager.clear()
        logger.info("Conversation context cleared")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        history = []
        for intent in self.context_manager.history:
            history.append({
                'timestamp': intent.timestamp.isoformat(),
                'action': intent.action,
                'entities': intent.entities,
                'filters': intent.filters
            })
        return history
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of all components
        
        Returns:
            Health status of components
        """
        health = {
            'overall': 'healthy',
            'components': {}
        }
        
        # Check SIEM connection
        try:
            self.siem_connector.client.info()
            health['components']['siem_connection'] = 'healthy'
        except Exception as e:
            health['components']['siem_connection'] = f'unhealthy: {str(e)}'
            health['overall'] = 'degraded'
        
        # Check configuration
        try:
            assert self.config is not None
            health['components']['configuration'] = 'healthy'
        except Exception as e:
            health['components']['configuration'] = f'unhealthy: {str(e)}'
            health['overall'] = 'degraded'
        
        return health
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'siem_connector'):
            self.siem_connector.close()
        logger.info("SIEM Assistant closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class InteractiveSession:
    """Interactive command-line session with the SIEM Assistant"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """Initialize interactive session"""
        self.assistant = SIEMAssistant(config_path)
        self.running = False
    
    def start(self):
        """Start interactive session"""
        self.running = True
        
        print("=" * 70)
        print("SIEM Conversational Assistant")
        print("=" * 70)
        print("\nWelcome! Ask me questions about your security events.")
        print("\nCommands:")
        print("  - Type your question naturally")
        print("  - 'explain <query>' - Explain how a query will be processed")
        print("  - 'report <query>' - Generate a comprehensive report")
        print("  - 'clear' - Clear conversation context")
        print("  - 'history' - Show conversation history")
        print("  - 'health' - Check system health")
        print("  - 'help' - Show this help message")
        print("  - 'exit' or 'quit' - Exit the assistant")
        print("\n" + "=" * 70 + "\n")
        
        while self.running:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    self.running = False
                    print("\nGoodbye!")
                    break
                
                elif user_input.lower() == 'help':
                    self._show_help()
                
                elif user_input.lower() == 'clear':
                    self.assistant.clear_context()
                    print("✓ Context cleared")
                
                elif user_input.lower() == 'history':
                    self._show_history()
                
                elif user_input.lower() == 'health':
                    self._show_health()
                
                elif user_input.lower().startswith('explain '):
                    query = user_input[8:].strip()
                    self._explain_query(query)
                
                elif user_input.lower().startswith('report '):
                    query = user_input[7:].strip()
                    self._generate_report(query)
                
                else:
                    # Process as normal query
                    self._process_query(user_input)
                
                print()  # Add blank line for readability
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.")
            except Exception as e:
                print(f"\n✗ Error: {e}")
                logger.error(f"Session error: {e}", exc_info=True)
    
    def _process_query(self, query: str):
        """Process a user query"""
        print("\nProcessing...", end='', flush=True)
        
        response = self.assistant.ask(query)
        
        print("\r" + " " * 20 + "\r", end='')  # Clear "Processing..."
        
        if response.get('success'):
            print(f"Assistant: {response.get('text')}")
            
            # Show table if available
            if 'table' in response:
                print("\n" + response['table'])
            
            # Show count if available
            if 'count' in response:
                print(f"\nTotal Count: {response['count']}")
            
            # Show cost estimate
            if 'query_cost' in response:
                print(f"\nQuery Cost: {response['query_cost']}")
        else:
            print(f"✗ Error: {response.get('error')}")
            if 'suggestions' in response:
                print("\nSuggestions:")
                for suggestion in response['suggestions']:
                    print(f"  • {suggestion}")
    
    def _explain_query(self, query: str):
        """Explain a query"""
        explanation = self.assistant.explain_query(query)
        
        if 'error' in explanation:
            print(f"✗ Error: {explanation['error']}")
            return
        
        print(f"\nQuery Explanation:")
        print(f"  Action: {explanation['detected_intent']['action']}")
        print(f"  Event Types: {', '.join(explanation['detected_intent']['event_types']) or 'None detected'}")
        print(f"  Filters: {explanation['detected_intent']['filters']}")
        print(f"  Target Index: {explanation['target_index']}")
        print(f"  Estimated Cost: {explanation['estimated_cost']}")
        print(f"\n  KQL Equivalent: {explanation['kql_equivalent']}")
    
    def _generate_report(self, query: str):
        """Generate a report"""
        print("\nGenerating report...", end='', flush=True)
        
        report = self.assistant.generate_report(query, output_format='text')
        
        print("\r" + " " * 30 + "\r", end='')  # Clear status
        print(report)
    
    def _show_history(self):
        """Show conversation history"""
        history = self.assistant.get_conversation_history()
        
        if not history:
            print("No conversation history")
            return
        
        print("\nConversation History:")
        for i, entry in enumerate(history, 1):
            print(f"\n{i}. {entry['timestamp']}")
            print(f"   Action: {entry['action']}")
            print(f"   Event Types: {entry['entities'].get('event_types', [])}")
    
    def _show_health(self):
        """Show system health"""
        health = self.assistant.health_check()
        
        print(f"\nSystem Health: {health['overall'].upper()}")
        print("\nComponents:")
        for component, status in health['components'].items():
            icon = "✓" if status == 'healthy' else "✗"
            print(f"  {icon} {component}: {status}")
    
    def _show_help(self):
        """Show help message"""
        print("\nAvailable Commands:")
        print("  Natural language queries:")
        print("    - 'Show me failed login attempts from yesterday'")
        print("    - 'How many malware detections last week?'")
        print("    - 'List VPN connections from user john.doe'")
        print("\n  Special commands:")
        print("    - explain <query>  - Explain query processing")
        print("    - report <query>   - Generate comprehensive report")
        print("    - clear           - Clear conversation context")
        print("    - history         - Show conversation history")
        print("    - health          - Check system health")
        print("    - exit/quit       - Exit the assistant")
    
    def stop(self):
        """Stop the session"""
        self.running = False
        self.assistant.close()


# Example usage and main entry point
if __name__ == "__main__":
    import sys
    
    # Check if running in interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        session = InteractiveSession()
        try:
            session.start()
        finally:
            session.stop()
    else:
        # Example programmatic usage
        with SIEMAssistant() as assistant:
            # Check health
            health = assistant.health_check()
            print(f"System Health: {health['overall']}")
            
            # Example queries
            queries = [
                "Show me failed login attempts from yesterday",
                "How many malware detections in the last week?",
                "Generate a report of security alerts from last month"
            ]
            
            for query in queries:
                print(f"\nQuery: {query}")
                response = assistant.ask(query)
                print(f"Response: {response.get('text')}")