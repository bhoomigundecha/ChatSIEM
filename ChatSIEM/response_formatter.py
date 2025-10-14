"""
Response Formatter - Formats SIEM query results for user consumption
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import json
import logging

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Formats raw SIEM results into user-friendly output"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def format_response(self, results: Dict[str, Any], 
                       intent_action: str) -> Dict[str, Any]:
        """
        Format response based on intent action
        
        Args:
            results: Raw Elasticsearch results
            intent_action: Type of action (search, count, aggregate, report)
            
        Returns:
            Formatted response with text, data, and visualizations
        """
        if intent_action == 'count':
            return self._format_count_response(results)
        elif intent_action == 'aggregate':
            return self._format_aggregation_response(results)
        elif intent_action == 'report':
            return self._format_report_response(results)
        else:  # search
            return self._format_search_response(results)
    
    def _format_search_response(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format search results"""
        hits = results.get('hits', {}).get('hits', [])
        total = results.get('hits', {}).get('total', {}).get('value', 0)
        
        # Extract relevant fields
        formatted_hits = []
        for hit in hits:
            source = hit['_source']
            formatted_hit = {
                'timestamp': source.get('@timestamp', 'N/A'),
                'event_type': source.get('event', {}).get('action', 'N/A'),
                'user': source.get('user', {}).get('name', 'N/A'),
                'host': source.get('host', {}).get('name', 'N/A'),
                'source_ip': source.get('source', {}).get('ip', 'N/A'),
                'destination_ip': source.get('destination', {}).get('ip', 'N/A'),
                'outcome': source.get('event', {}).get('outcome', 'N/A'),
                'message': source.get('message', 'N/A')
            }
            formatted_hits.append(formatted_hit)
        
        # Generate text summary
        text_summary = self._generate_search_summary(formatted_hits, total)
        
        # Create table data
        table_data = self._create_table(formatted_hits)
        
        return {
            'type': 'search',
            'text': text_summary,
            'total_count': total,
            'result_count': len(hits),
            'data': formatted_hits,
            'table': table_data
        }
    
    def _format_count_response(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format count results"""
        count = results.get('hits', {}).get('total', {}).get('value', 0)
        
        text_summary = f"Found {count} matching events."
        
        return {
            'type': 'count',
            'text': text_summary,
            'count': count
        }
    
    def _format_aggregation_response(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format aggregation results"""
        aggregations = results.get('aggregations', {})
        
        # Extract grouped results
        grouped = aggregations.get('grouped_results', {}).get('buckets', [])
        over_time = aggregations.get('over_time', {}).get('buckets', [])
        
        # Format grouped data
        grouped_data = [
            {
                'key': bucket['key'],
                'count': bucket['doc_count']
            }
            for bucket in grouped[:10]  # Top 10
        ]
        
        # Format time series data
        time_series = [
            {
                'timestamp': bucket['key_as_string'],
                'count': bucket['doc_count']
            }
            for bucket in over_time
        ]
        
        # Generate text summary
        total_events = sum(item['count'] for item in grouped_data)
        text_summary = self._generate_aggregation_summary(grouped_data, total_events)
        
        # Create chart data
        chart_data = self._create_chart_data(grouped_data, time_series)
        
        return {
            'type': 'aggregation',
            'text': text_summary,
            'total_count': total_events,
            'grouped_data': grouped_data,
            'time_series': time_series,
            'charts': chart_data
        }
    
    def _format_report_response(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format comprehensive report"""
        aggregations = results.get('aggregations', {})
        
        # Extract all aggregations
        grouped = aggregations.get('grouped_results', {}).get('buckets', [])
        over_time = aggregations.get('over_time', {}).get('buckets', [])
        severity = aggregations.get('severity_breakdown', {}).get('buckets', [])
        top_users = aggregations.get('top_users', {}).get('buckets', [])
        top_hosts = aggregations.get('top_hosts', {}).get('buckets', [])
        
        # Format data
        report_data = {
            'overview': {
                'total_events': sum(b['doc_count'] for b in grouped),
                'time_range': self._extract_time_range(over_time),
                'generated_at': datetime.now().isoformat()
            },
            'event_breakdown': [
                {'type': b['key'], 'count': b['doc_count']}
                for b in grouped
            ],
            'severity_breakdown': [
                {'severity': b['key'], 'count': b['doc_count']}
                for b in severity
            ],
            'top_users': [
                {'user': b['key'], 'events': b['doc_count']}
                for b in top_users
            ],
            'top_hosts': [
                {'host': b['key'], 'events': b['doc_count']}
                for b in top_hosts
            ],
            'timeline': [
                {'timestamp': b['key_as_string'], 'count': b['doc_count']}
                for b in over_time
            ]
        }
        
        # Generate narrative text
        narrative = self._generate_report_narrative(report_data)
        
        # Create visualizations
        charts = self._create_report_charts(report_data)
        
        return {
            'type': 'report',
            'text': narrative,
            'data': report_data,
            'charts': charts,
            'metadata': {
                'generated_at': report_data['overview']['generated_at'],
                'total_events': report_data['overview']['total_events']
            }
        }
    
    def _generate_search_summary(self, hits: List[Dict], total: int) -> str:
        """Generate natural language summary of search results"""
        if total == 0:
            return "No matching events found."
        
        summary_parts = [f"Found {total} events."]
        
        if hits:
            # Extract key statistics
            users = set(h['user'] for h in hits if h['user'] != 'N/A')
            hosts = set(h['host'] for h in hits if h['host'] != 'N/A')
            
            if users:
                summary_parts.append(f"Involving {len(users)} unique user(s).")
            if hosts:
                summary_parts.append(f"Across {len(hosts)} host(s).")
            
            # Add time information
            if hits[0]['timestamp'] != 'N/A':
                summary_parts.append(f"Latest event at {hits[0]['timestamp']}.")
        
        return " ".join(summary_parts)
    
    def _generate_aggregation_summary(self, grouped_data: List[Dict], 
                                     total: int) -> str:
        """Generate summary for aggregation results"""
        if not grouped_data:
            return "No data available for aggregation."
        
        top_item = grouped_data[0]
        summary = f"Total of {total} events across {len(grouped_data)} categories. "
        summary += f"Top category: '{top_item['key']}' with {top_item['count']} events "
        summary += f"({(top_item['count']/total*100):.1f}% of total)."
        
        return summary
    
    def _generate_report_narrative(self, report_data: Dict[str, Any]) -> str:
        """Generate narrative text for report"""
        overview = report_data['overview']
        
        narrative = f"""
# Security Event Report

**Generated:** {overview['generated_at']}
**Time Range:** {overview['time_range']}
**Total Events:** {overview['total_events']:,}

## Executive Summary

This report provides a comprehensive analysis of security events during the specified time period. 
A total of {overview['total_events']:,} events were analyzed.

## Event Breakdown

"""
        
        # Add event breakdown
        for event in report_data['event_breakdown'][:5]:
            percentage = (event['count'] / overview['total_events'] * 100)
            narrative += f"- **{event['type']}**: {event['count']:,} events ({percentage:.1f}%)\n"
        
        # Add severity analysis
        if report_data['severity_breakdown']:
            narrative += "\n## Severity Analysis\n\n"
            for sev in report_data['severity_breakdown']:
                narrative += f"- {sev['severity'].upper()}: {sev['count']:,} events\n"
        
        # Add top users
        if report_data['top_users']:
            narrative += "\n## Most Active Users\n\n"
            for user in report_data['top_users'][:5]:
                narrative += f"- {user['user']}: {user['events']:,} events\n"
        
        # Add top hosts
        if report_data['top_hosts']:
            narrative += "\n## Most Active Hosts\n\n"
            for host in report_data['top_hosts'][:5]:
                narrative += f"- {host['host']}: {host['events']:,} events\n"
        
        return narrative
    
    def _create_table(self, data: List[Dict]) -> str:
        """Create ASCII table from data"""
        if not data:
            return "No data to display"
        
        # Use pandas for nice table formatting
        df = pd.DataFrame(data)
        return df.to_string(index=False, max_rows=20)
    
    def _create_chart_data(self, grouped: List[Dict], 
                          time_series: List[Dict]) -> Dict[str, Any]:
        """Create chart specifications for visualization"""
        charts = {}
        
        # Bar chart for grouped data
        if grouped:
            charts['bar_chart'] = {
                'type': 'bar',
                'title': 'Event Distribution',
                'data': {
                    'labels': [item['key'] for item in grouped],
                    'values': [item['count'] for item in grouped]
                }
            }
        
        # Time series chart
        if time_series:
            charts['timeline'] = {
                'type': 'line',
                'title': 'Events Over Time',
                'data': {
                    'timestamps': [item['timestamp'] for item in time_series],
                    'values': [item['count'] for item in time_series]
                }
            }
        
        return charts
    
    def _create_report_charts(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive charts for report"""
        charts = {}
        
        # Event breakdown pie chart
        if report_data['event_breakdown']:
            charts['event_pie'] = {
                'type': 'pie',
                'title': 'Event Type Distribution',
                'data': {
                    'labels': [e['type'] for e in report_data['event_breakdown']],
                    'values': [e['count'] for e in report_data['event_breakdown']]
                }
            }
        
        # Severity bar chart
        if report_data['severity_breakdown']:
            charts['severity_bar'] = {
                'type': 'bar',
                'title': 'Events by Severity',
                'data': {
                    'labels': [s['severity'] for s in report_data['severity_breakdown']],
                    'values': [s['count'] for s in report_data['severity_breakdown']]
                }
            }
        
        # Timeline
        if report_data['timeline']:
            charts['timeline'] = {
                'type': 'line',
                'title': 'Event Timeline',
                'data': {
                    'timestamps': [t['timestamp'] for t in report_data['timeline']],
                    'values': [t['count'] for t in report_data['timeline']]
                }
            }
        
        # Top users horizontal bar
        if report_data['top_users']:
            charts['users_bar'] = {
                'type': 'horizontal_bar',
                'title': 'Top 10 Active Users',
                'data': {
                    'labels': [u['user'] for u in report_data['top_users'][:10]],
                    'values': [u['events'] for u in report_data['top_users'][:10]]
                }
            }
        
        return charts
    
    def _extract_time_range(self, time_buckets: List[Dict]) -> str:
        """Extract human-readable time range from buckets"""
        if not time_buckets:
            return "N/A"
        
        start = time_buckets[0].get('key_as_string', 'N/A')
        end = time_buckets[-1].get('key_as_string', 'N/A')
        
        return f"{start} to {end}"
    
    def export_to_json(self, formatted_response: Dict[str, Any]) -> str:
        """Export response as JSON"""
        return json.dumps(formatted_response, indent=2, default=str)
    
    def export_to_csv(self, formatted_response: Dict[str, Any]) -> str:
        """Export response data as CSV"""
        data = formatted_response.get('data', [])
        
        if isinstance(data, list) and data:
            df = pd.DataFrame(data)
            return df.to_csv(index=False)
        
        return ""
    
    def export_to_html(self, formatted_response: Dict[str, Any]) -> str:
        """Export response as HTML report"""
        text = formatted_response.get('text', '')
        data = formatted_response.get('data', [])
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SIEM Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                .summary {{ background-color: #f9f9f9; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>SIEM Investigation Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <pre>{text}</pre>
            </div>
        """
        
        if isinstance(data, list) and data:
            df = pd.DataFrame(data)
            html += "<h2>Details</h2>"
            html += df.to_html(index=False)
        
        html += """
        </body>
        </html>
        """
        
        return html