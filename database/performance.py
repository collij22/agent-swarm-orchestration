"""
Database performance monitoring and optimization utilities
Provides query analysis, indexing recommendations, and performance metrics
"""

import time
import sqlite3
import json
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime, timedelta
from dataclasses import dataclass
from database.models import DATABASE_URL


@dataclass
class QueryStats:
    """Statistics for a database query"""
    query: str
    execution_time_ms: float
    rows_examined: int
    rows_returned: int
    timestamp: datetime
    explain_plan: str


class PerformanceMonitor:
    """Monitor and analyze database performance"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url.replace('sqlite:///', '')
        self.query_log: List[QueryStats] = []
        self.slow_query_threshold_ms = 50  # Log queries slower than 50ms
    
    @contextmanager
    def get_connection(self):
        """Get database connection with performance monitoring"""
        conn = sqlite3.connect(self.database_url)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()
    
    def analyze_query(self, query: str, params: Optional[Tuple] = None) -> QueryStats:
        """Analyze a query's performance and execution plan"""
        with self.get_connection() as conn:
            # Get execution plan
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            cursor = conn.execute(explain_query, params or ())
            explain_plan = '\n'.join([str(row) for row in cursor.fetchall()])
            
            # Execute query with timing
            start_time = time.perf_counter()
            cursor = conn.execute(query, params or ())
            results = cursor.fetchall()
            end_time = time.perf_counter()
            
            execution_time_ms = (end_time - start_time) * 1000
            
            stats = QueryStats(
                query=query,
                execution_time_ms=execution_time_ms,
                rows_examined=0,  # SQLite doesn't provide this directly
                rows_returned=len(results),
                timestamp=datetime.utcnow(),
                explain_plan=explain_plan
            )
            
            # Log slow queries
            if execution_time_ms > self.slow_query_threshold_ms:
                self.query_log.append(stats)
            
            return stats
    
    def get_table_stats(self) -> Dict[str, Any]:
        """Get statistics for all tables"""
        with self.get_connection() as conn:
            stats = {}
            
            # Get all table names
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                # Get row count
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                # Get table info
                cursor = conn.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                # Get index info
                cursor = conn.execute(f"PRAGMA index_list({table})")
                indexes = cursor.fetchall()
                
                stats[table] = {
                    'row_count': row_count,
                    'column_count': len(columns),
                    'index_count': len(indexes),
                    'columns': [col[1] for col in columns],  # Column names
                    'indexes': [idx[1] for idx in indexes]   # Index names
                }
            
            return stats
    
    def analyze_index_usage(self) -> Dict[str, Any]:
        """Analyze index usage and provide recommendations"""
        with self.get_connection() as conn:
            analysis = {
                'existing_indexes': {},
                'recommendations': [],
                'unused_indexes': []
            }
            
            # Get all indexes
            cursor = conn.execute("""
                SELECT name, tbl_name, sql 
                FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """)
            indexes = cursor.fetchall()
            
            for idx_name, table_name, sql in indexes:
                # Get index info
                cursor = conn.execute(f"PRAGMA index_info({idx_name})")
                columns = [col[2] for col in cursor.fetchall()]
                
                analysis['existing_indexes'][idx_name] = {
                    'table': table_name,
                    'columns': columns,
                    'sql': sql
                }
            
            # Analyze common query patterns for index recommendations
            recommendations = self._generate_index_recommendations()
            analysis['recommendations'] = recommendations
            
            return analysis
    
    def _generate_index_recommendations(self) -> List[Dict[str, Any]]:
        """Generate index recommendations based on query patterns"""
        recommendations = []
        
        # Common query patterns that benefit from indexes
        patterns = [
            {
                'table': 'tasks',
                'columns': ['user_id', 'status'],
                'reason': 'Frequently filtered by user and status together',
                'priority': 'high'
            },
            {
                'table': 'tasks',
                'columns': ['user_id', 'priority'],
                'reason': 'Common for priority-based task queries',
                'priority': 'medium'
            },
            {
                'table': 'tasks',
                'columns': ['category_id'],
                'reason': 'Filtering tasks by category',
                'priority': 'medium'
            },
            {
                'table': 'ai_processing_log',
                'columns': ['task_id', 'operation_type'],
                'reason': 'AI operation lookups and analytics',
                'priority': 'low'
            }
        ]
        
        # Check which indexes already exist
        with self.get_connection() as conn:
            for pattern in patterns:
                index_name = f"idx_{pattern['table']}_{'_'.join(pattern['columns'])}"
                
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name = ?
                """, (index_name,))
                
                if not cursor.fetchone():
                    recommendations.append({
                        'table': pattern['table'],
                        'columns': pattern['columns'],
                        'index_name': index_name,
                        'reason': pattern['reason'],
                        'priority': pattern['priority'],
                        'sql': f"CREATE INDEX {index_name} ON {pattern['table']}({', '.join(pattern['columns'])})"
                    })
        
        return recommendations
    
    def get_slow_queries(self, limit: int = 10) -> List[QueryStats]:
        """Get slowest queries from the log"""
        sorted_queries = sorted(
            self.query_log, 
            key=lambda q: q.execution_time_ms, 
            reverse=True
        )
        return sorted_queries[:limit]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        if not self.query_log:
            return {'message': 'No performance data available'}
        
        execution_times = [q.execution_time_ms for q in self.query_log]
        
        return {
            'total_queries_logged': len(self.query_log),
            'avg_execution_time_ms': sum(execution_times) / len(execution_times),
            'max_execution_time_ms': max(execution_times),
            'min_execution_time_ms': min(execution_times),
            'slow_query_threshold_ms': self.slow_query_threshold_ms,
            'queries_over_threshold': len(execution_times)
        }
    
    def optimize_database(self) -> Dict[str, Any]:
        """Perform database optimization operations"""
        with self.get_connection() as conn:
            results = {}
            
            # Analyze database
            conn.execute("ANALYZE")
            results['analyze'] = 'completed'
            
            # Vacuum database (reclaim space)
            conn.execute("VACUUM")
            results['vacuum'] = 'completed'
            
            # Update statistics
            conn.execute("PRAGMA optimize")
            results['optimize'] = 'completed'
            
            # Get database size info
            cursor = conn.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            
            cursor = conn.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            database_size_mb = (page_count * page_size) / (1024 * 1024)
            
            results['database_size_mb'] = round(database_size_mb, 2)
            results['optimization_timestamp'] = datetime.utcnow().isoformat()
            
            return results
    
    def benchmark_queries(self) -> Dict[str, Any]:
        """Run benchmark queries to test database performance"""
        benchmarks = {}
        
        # Common query patterns
        test_queries = [
            {
                'name': 'user_tasks_by_status',
                'query': """
                    SELECT COUNT(*) FROM tasks 
                    WHERE user_id = ? AND status = ? AND deleted_at IS NULL
                """,
                'params': ('test-user-id', 'todo')
            },
            {
                'name': 'high_priority_tasks',
                'query': """
                    SELECT id, title, priority FROM tasks 
                    WHERE priority >= 4 AND deleted_at IS NULL 
                    ORDER BY priority DESC, created_at ASC 
                    LIMIT 10
                """,
                'params': None
            },
            {
                'name': 'category_task_count',
                'query': """
                    SELECT c.name, COUNT(t.id) as task_count
                    FROM categories c
                    LEFT JOIN tasks t ON c.id = t.category_id AND t.deleted_at IS NULL
                    GROUP BY c.id, c.name
                """,
                'params': None
            },
            {
                'name': 'recent_ai_operations',
                'query': """
                    SELECT operation_type, COUNT(*) as count, AVG(processing_time_ms) as avg_time
                    FROM ai_processing_log
                    WHERE created_at >= datetime('now', '-7 days')
                    GROUP BY operation_type
                """,
                'params': None
            }
        ]
        
        for test in test_queries:
            try:
                stats = self.analyze_query(test['query'], test['params'])
                benchmarks[test['name']] = {
                    'execution_time_ms': stats.execution_time_ms,
                    'rows_returned': stats.rows_returned,
                    'explain_plan': stats.explain_plan
                }
            except Exception as e:
                benchmarks[test['name']] = {
                    'error': str(e)
                }
        
        return benchmarks
    
    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report"""
        report = []
        report.append("TaskManagerAPI Database Performance Report")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append("")
        
        # Table statistics
        table_stats = self.get_table_stats()
        report.append("Table Statistics:")
        report.append("-" * 20)
        for table, stats in table_stats.items():
            report.append(f"{table}:")
            report.append(f"  Rows: {stats['row_count']:,}")
            report.append(f"  Columns: {stats['column_count']}")
            report.append(f"  Indexes: {stats['index_count']}")
            report.append("")
        
        # Index analysis
        index_analysis = self.analyze_index_usage()
        if index_analysis['recommendations']:
            report.append("Index Recommendations:")
            report.append("-" * 25)
            for rec in index_analysis['recommendations']:
                report.append(f"• {rec['table']}.{', '.join(rec['columns'])} ({rec['priority']} priority)")
                report.append(f"  Reason: {rec['reason']}")
                report.append(f"  SQL: {rec['sql']}")
                report.append("")
        
        # Performance summary
        perf_summary = self.get_performance_summary()
        if 'total_queries_logged' in perf_summary:
            report.append("Query Performance Summary:")
            report.append("-" * 30)
            report.append(f"Queries logged: {perf_summary['total_queries_logged']}")
            report.append(f"Average execution time: {perf_summary['avg_execution_time_ms']:.2f}ms")
            report.append(f"Slowest query: {perf_summary['max_execution_time_ms']:.2f}ms")
            report.append("")
        
        # Slow queries
        slow_queries = self.get_slow_queries(5)
        if slow_queries:
            report.append("Slowest Queries:")
            report.append("-" * 20)
            for i, query in enumerate(slow_queries, 1):
                report.append(f"{i}. {query.execution_time_ms:.2f}ms")
                report.append(f"   Query: {query.query[:100]}...")
                report.append("")
        
        return "\n".join(report)


def main():
    """Command-line interface for performance monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TaskManagerAPI Database Performance Tool')
    parser.add_argument('command', choices=['analyze', 'optimize', 'benchmark', 'report'], 
                       help='Performance command to execute')
    parser.add_argument('--query', help='Specific query to analyze')
    parser.add_argument('--output', help='Output file for report')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor()
    
    if args.command == 'analyze' and args.query:
        stats = monitor.analyze_query(args.query)
        print(f"Execution time: {stats.execution_time_ms:.2f}ms")
        print(f"Rows returned: {stats.rows_returned}")
        print(f"Explain plan:\n{stats.explain_plan}")
    
    elif args.command == 'optimize':
        results = monitor.optimize_database()
        print("Database optimization completed:")
        for operation, status in results.items():
            print(f"  {operation}: {status}")
    
    elif args.command == 'benchmark':
        benchmarks = monitor.benchmark_queries()
        print("Benchmark Results:")
        print("-" * 20)
        for name, result in benchmarks.items():
            if 'error' in result:
                print(f"{name}: ERROR - {result['error']}")
            else:
                print(f"{name}: {result['execution_time_ms']:.2f}ms ({result['rows_returned']} rows)")
    
    elif args.command == 'report':
        report = monitor.generate_performance_report()
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)


if __name__ == '__main__':
    main()