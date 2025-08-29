#!/usr/bin/env python3
"""
Session CLI - Command-line interface for agent swarm session management

Usage:
    python session_cli.py [command] [options]

Commands:
    list        List all sessions
    view        View session details
    replay      Replay a session
    analyze     Analyze a session
    metrics     View aggregated metrics
    report      Generate session report
    debug       Debug a failed session
    monitor     Start performance monitoring
    archive     Archive old sessions
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import signal

# Add lib directory to path
sys.path.append(str(Path(__file__).parent / "lib"))

from lib.session_manager import SessionManager, SessionStatus, ReplayMode, Checkpoint
from lib.metrics_aggregator import MetricsAggregator, AggregationPeriod, MetricType
from lib.performance_tracker import PerformanceTracker, PerformanceAlert, AlertSeverity
from lib.session_analyzer import SessionAnalyzer, AnalysisType

# Rich console for better output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.live import Live
    console = Console()
except ImportError:
    console = None
    print("Warning: Rich not installed. Install with: pip install rich")

class SessionCLI:
    """Command-line interface for session management"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.metrics_aggregator = MetricsAggregator(self.session_manager)
        self.session_analyzer = SessionAnalyzer(self.session_manager)
        self.performance_tracker = None
        
    def list_sessions(self, args):
        """List all sessions"""
        # Parse filters
        status = SessionStatus[args.status.upper()] if args.status else None
        
        date_from = None
        date_to = None
        if args.date_from:
            date_from = datetime.fromisoformat(args.date_from)
        if args.date_to:
            date_to = datetime.fromisoformat(args.date_to)
        
        # Get sessions
        sessions = self.session_manager.list_sessions(
            status=status,
            project_type=args.project_type,
            date_from=date_from,
            date_to=date_to
        )
        
        if not sessions:
            print("No sessions found")
            return
        
        # Display results
        if console and not args.json:
            table = Table(title=f"Sessions ({len(sessions)} found)")
            table.add_column("Session ID", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Project Type", style="yellow")
            table.add_column("Created At", style="magenta")
            
            for session in sessions[:args.limit]:
                status_style = "green" if session["status"] == "completed" else "red"
                table.add_row(
                    session["session_id"][:8] + "...",
                    f"[{status_style}]{session['status']}[/{status_style}]",
                    session["project_type"],
                    session["created_at"][:19]
                )
            
            console.print(table)
        else:
            # JSON output
            print(json.dumps(sessions[:args.limit], indent=2))
    
    def view_session(self, args):
        """View session details"""
        session = self.session_manager.load_session(args.session_id)
        
        if not session:
            print(f"Session {args.session_id} not found")
            return
        
        if args.format == "summary":
            summary = self.session_manager.get_session_summary(args.session_id)
            
            if console:
                # Rich formatted output
                console.print(Panel(f"[bold]Session: {args.session_id}[/bold]"))
                
                # Status panel
                status_color = "green" if summary["status"] == "completed" else "red"
                console.print(f"Status: [{status_color}]{summary['status']}[/{status_color}]")
                console.print(f"Project Type: {summary['project_type']}")
                console.print(f"Duration: {summary.get('duration_ms', 0):.1f}ms")
                
                # Metrics table
                if summary["agent_summary"]:
                    table = Table(title="Agent Metrics")
                    table.add_column("Agent", style="cyan")
                    table.add_column("Calls", style="green")
                    table.add_column("Success Rate", style="yellow")
                    table.add_column("Avg Duration", style="magenta")
                    
                    for agent, metrics in summary["agent_summary"].items():
                        table.add_row(
                            agent,
                            str(metrics["calls"]),
                            f"{metrics['success_rate']:.1f}%",
                            f"{metrics['avg_duration_ms']:.1f}ms"
                        )
                    
                    console.print(table)
            else:
                print(json.dumps(summary, indent=2))
        
        elif args.format == "full":
            # Full session data
            print(json.dumps(session.to_dict(), indent=2))
        
        else:  # entries
            # Show log entries
            if console:
                console.print(f"[bold]Session Entries ({len(session.entries)} total)[/bold]")
                
                for i, entry in enumerate(session.entries[:args.limit]):
                    if isinstance(entry, dict):
                        timestamp = entry.get("timestamp", "")[:19]
                        agent = entry.get("agent_name", "unknown")
                        event = entry.get("event_type", "")
                        message = entry.get("message", "")[:100]
                        
                        console.print(f"[{i:3}] [{timestamp}] [{agent:15}] {event:15} {message}")
            else:
                for entry in session.entries[:args.limit]:
                    if isinstance(entry, dict):
                        print(f"{entry.get('timestamp', '')} - {entry.get('agent_name', '')} - {entry.get('message', '')}")
    
    def replay_session(self, args):
        """Replay a session"""
        mode = ReplayMode[args.mode.upper()]
        
        if console:
            console.print(Panel(f"[bold]Replaying Session: {args.session_id}[/bold]"))
            console.print(f"Mode: {mode.value}")
            if args.start_from:
                console.print(f"Starting from: {args.start_from}")
            if args.skip:
                console.print(f"Skipping agents: {', '.join(args.skip)}")
        
        success = self.session_manager.replay_session(
            session_id=args.session_id,
            mode=mode,
            start_from=args.start_from,
            agents_to_skip=args.skip
        )
        
        if success:
            print("\nReplay completed successfully")
        else:
            print("\nReplay failed")
    
    def analyze_session(self, args):
        """Analyze a session"""
        # Parse analysis types
        analysis_types = []
        if args.types:
            for type_str in args.types:
                try:
                    analysis_types.append(AnalysisType[type_str.upper()])
                except KeyError:
                    print(f"Unknown analysis type: {type_str}")
                    return
        else:
            analysis_types = list(AnalysisType)
        
        if console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing session...", total=1)
                
                analysis = self.session_analyzer.analyze_session(
                    args.session_id,
                    analysis_types
                )
                
                progress.update(task, completed=1)
        else:
            analysis = self.session_analyzer.analyze_session(
                args.session_id,
                analysis_types
            )
        
        # Display results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            print(f"Analysis saved to {args.output}")
        else:
            if console:
                self._display_analysis_results(analysis)
            else:
                print(json.dumps(analysis, indent=2, default=str))
    
    def show_metrics(self, args):
        """Show aggregated metrics"""
        period = AggregationPeriod[args.period.upper()]
        
        # Parse dates
        date_from = datetime.fromisoformat(args.from_date) if args.from_date else None
        date_to = datetime.fromisoformat(args.to_date) if args.to_date else None
        
        # Get metrics
        metrics = self.metrics_aggregator.aggregate_metrics(
            period=period,
            date_from=date_from,
            date_to=date_to,
            project_type=args.project_type
        )
        
        if console:
            # Display summary
            console.print(Panel(f"[bold]Metrics Summary ({period.value})[/bold]"))
            console.print(f"Period: {metrics.start_date[:10]} to {metrics.end_date[:10]}")
            console.print(f"Total Sessions: {metrics.total_sessions}")
            console.print(f"Success Rate: {(metrics.successful_sessions/max(1, metrics.total_sessions)*100):.1f}%")
            console.print(f"Total API Calls: {metrics.total_api_calls}")
            console.print(f"Estimated Cost: ${metrics.total_estimated_cost:.2f}")
            console.print(f"Average Duration: {metrics.average_session_duration_ms:.1f}ms")
            
            # Agent rankings
            if args.rankings:
                metric_type = MetricType[args.rankings.upper()]
                rankings = self.metrics_aggregator.get_agent_rankings(metric_type, top_n=10)
                
                table = Table(title=f"Top Agents by {metric_type.value}")
                table.add_column("Rank", style="cyan")
                table.add_column("Agent", style="green")
                table.add_column("Value", style="yellow")
                
                for i, (agent, value) in enumerate(rankings, 1):
                    table.add_row(str(i), agent, f"{value:.1f}")
                
                console.print(table)
        else:
            # Export metrics
            if args.export:
                self.metrics_aggregator.export_metrics("json", args.export)
                print(f"Metrics exported to {args.export}")
            else:
                print(json.dumps({
                    "period": period.value,
                    "sessions": metrics.total_sessions,
                    "success_rate": metrics.successful_sessions/max(1, metrics.total_sessions)*100,
                    "api_calls": metrics.total_api_calls,
                    "cost": metrics.total_estimated_cost
                }, indent=2))
    
    def generate_report(self, args):
        """Generate session report"""
        if console:
            console.print(f"Generating report for session {args.session_id}...")
        
        output_file = args.output or f"report_{args.session_id[:8]}.md"
        
        result = self.session_analyzer.generate_analysis_report(
            args.session_id,
            output_file
        )
        
        print(result)
        
        # Also generate HTML if requested
        if args.format == "html":
            # Convert markdown to HTML (simplified)
            import markdown
            with open(output_file, 'r') as f:
                md_content = f.read()
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Session Report - {args.session_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #eee; padding-bottom: 5px; }}
        h3 {{ color: #888; }}
        pre {{ background: #f5f5f5; padding: 10px; border-radius: 5px; }}
        ul {{ line-height: 1.6; }}
    </style>
</head>
<body>
    {markdown.markdown(md_content) if 'markdown' in sys.modules else md_content}
</body>
</html>
"""
            html_file = output_file.replace('.md', '.html')
            with open(html_file, 'w') as f:
                f.write(html_content)
            print(f"HTML report saved to {html_file}")
    
    def debug_session(self, args):
        """Debug a failed session"""
        debug_info = self.session_manager.debug_session(
            args.session_id,
            breakpoint_agent=args.breakpoint
        )
        
        if "error" in debug_info:
            print(debug_info["error"])
            return
        
        if console:
            console.print(Panel(f"[bold red]Debug Information for {args.session_id}[/bold red]"))
            
            console.print(f"[yellow]Status:[/yellow] {debug_info['status']}")
            console.print(f"[yellow]Last Successful Agent:[/yellow] {debug_info.get('last_successful_agent', 'None')}")
            
            if debug_info.get("failure_point"):
                fp = debug_info["failure_point"]
                console.print("\n[red]Failure Point:[/red]")
                console.print(f"  Agent: {fp.get('agent', 'unknown')}")
                console.print(f"  Message: {fp.get('message', '')}")
                if fp.get('reasoning'):
                    console.print(f"  Reasoning: {fp['reasoning']}")
            
            if debug_info.get("reasoning_before_failure"):
                console.print("\n[yellow]Reasoning Before Failure:[/yellow]")
                for reasoning in debug_info["reasoning_before_failure"]:
                    console.print(f"  - {reasoning[:100]}...")
            
            if debug_info.get("errors"):
                console.print(f"\n[red]Total Errors:[/red] {len(debug_info['errors'])}")
                for error in debug_info["errors"][:5]:
                    console.print(f"  - {error}")
            
            console.print(f"\n[cyan]Checkpoints Available:[/cyan] {debug_info['checkpoints_available']}")
        else:
            print(json.dumps(debug_info, indent=2))
    
    def monitor_performance(self, args):
        """Start performance monitoring"""
        def alert_handler(alert: PerformanceAlert):
            if console:
                color = "yellow" if alert.severity == AlertSeverity.WARNING else "red"
                console.print(f"[{color}][{alert.severity.value.upper()}] {alert.message}[/{color}]")
            else:
                print(f"[{alert.severity.value.upper()}] {alert.message}")
        
        self.performance_tracker = PerformanceTracker(
            alert_callback=alert_handler,
            snapshot_interval_seconds=args.interval
        )
        
        # Start monitoring
        self.performance_tracker.start_monitoring()
        
        if console:
            console.print(Panel("[bold green]Performance Monitoring Started[/bold green]"))
            console.print("Press Ctrl+C to stop monitoring")
        else:
            print("Performance monitoring started. Press Ctrl+C to stop.")
        
        # Set up signal handler
        def signal_handler(sig, frame):
            self.performance_tracker.stop_monitoring()
            
            # Export data if requested
            if args.export:
                self.performance_tracker.export_performance_data(args.export)
                print(f"\nPerformance data exported to {args.export}")
            
            # Show summary
            summary = self.performance_tracker.get_performance_summary()
            print(f"\nPerformance Summary:")
            print(f"  Total Executions: {summary['totals']['executions']}")
            print(f"  Success Rate: {summary['success_rate']:.1f}%")
            print(f"  Peak Memory: {summary['peaks']['memory_mb']:.1f}MB")
            print(f"  Peak CPU: {summary['peaks']['cpu_percent']:.1f}%")
            
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Keep running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    
    def archive_sessions(self, args):
        """Archive old sessions"""
        if console:
            console.print(f"Archiving sessions older than {args.days} days...")
        
        count = self.session_manager.archive_old_sessions(days_old=args.days)
        
        print(f"Archived {count} sessions")
    
    def _display_analysis_results(self, analysis):
        """Display analysis results in rich format"""
        console.print(Panel(f"[bold]Analysis Results for {analysis['session_id']}[/bold]"))
        
        for analysis_type, results in analysis["analyses"].items():
            console.print(f"\n[bold cyan]{analysis_type.upper()}[/bold cyan]")
            
            if analysis_type == "error_patterns" and results:
                for pattern in results[:5]:
                    console.print(f"  • {pattern.pattern_type}: {pattern.frequency} occurrences")
                    console.print(f"    Affected: {', '.join(pattern.affected_agents)}")
                    console.print(f"    Fix: {pattern.suggested_fix}")
            
            elif analysis_type == "reasoning_quality" and results:
                for quality in results[:5]:
                    color = "green" if quality.overall_score > 70 else "yellow" if quality.overall_score > 50 else "red"
                    console.print(f"  • {quality.agent_name}: [{color}]{quality.overall_score:.1f}/100[/{color}]")
                    if quality.issues:
                        console.print(f"    Issues: {', '.join(quality.issues)}")
            
            elif analysis_type == "optimizations" and results:
                for opt in results[:5]:
                    console.print(f"  • [Priority {opt.priority}] {opt.description}")
                    console.print(f"    Expected: {opt.expected_improvement}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Session Management CLI for Agent Swarm")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List sessions")
    list_parser.add_argument("--status", choices=["running", "completed", "failed", "partial"])
    list_parser.add_argument("--project-type", help="Filter by project type")
    list_parser.add_argument("--date-from", help="Start date (ISO format)")
    list_parser.add_argument("--date-to", help="End date (ISO format)")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum results")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # View command
    view_parser = subparsers.add_parser("view", help="View session details")
    view_parser.add_argument("session_id", help="Session ID to view")
    view_parser.add_argument("--format", choices=["summary", "full", "entries"], default="summary")
    view_parser.add_argument("--limit", type=int, default=100, help="Limit entries shown")
    
    # Replay command
    replay_parser = subparsers.add_parser("replay", help="Replay a session")
    replay_parser.add_argument("session_id", help="Session ID to replay")
    replay_parser.add_argument("--mode", choices=["mock", "real", "step"], default="mock")
    replay_parser.add_argument("--start-from", help="Agent to start from")
    replay_parser.add_argument("--skip", nargs="*", help="Agents to skip")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a session")
    analyze_parser.add_argument("session_id", help="Session ID to analyze")
    analyze_parser.add_argument("--types", nargs="*", help="Analysis types")
    analyze_parser.add_argument("--output", help="Output file for results")
    
    # Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="View aggregated metrics")
    metrics_parser.add_argument("--period", choices=["hourly", "daily", "weekly", "monthly", "all_time"], default="daily")
    metrics_parser.add_argument("--from-date", help="Start date")
    metrics_parser.add_argument("--to-date", help="End date")
    metrics_parser.add_argument("--project-type", help="Filter by project type")
    metrics_parser.add_argument("--rankings", choices=["success_rate", "execution_time", "error_rate"])
    metrics_parser.add_argument("--export", help="Export to file")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate session report")
    report_parser.add_argument("session_id", help="Session ID")
    report_parser.add_argument("--output", help="Output file")
    report_parser.add_argument("--format", choices=["markdown", "html"], default="markdown")
    
    # Debug command
    debug_parser = subparsers.add_parser("debug", help="Debug a failed session")
    debug_parser.add_argument("session_id", help="Session ID to debug")
    debug_parser.add_argument("--breakpoint", help="Agent to set breakpoint at")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Start performance monitoring")
    monitor_parser.add_argument("--interval", type=int, default=10, help="Snapshot interval (seconds)")
    monitor_parser.add_argument("--export", help="Export data on exit")
    
    # Archive command
    archive_parser = subparsers.add_parser("archive", help="Archive old sessions")
    archive_parser.add_argument("--days", type=int, default=30, help="Archive sessions older than N days")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create CLI instance
    cli = SessionCLI()
    
    # Execute command
    command_map = {
        "list": cli.list_sessions,
        "view": cli.view_session,
        "replay": cli.replay_session,
        "analyze": cli.analyze_session,
        "metrics": cli.show_metrics,
        "report": cli.generate_report,
        "debug": cli.debug_session,
        "monitor": cli.monitor_performance,
        "archive": cli.archive_sessions
    }
    
    if args.command in command_map:
        try:
            command_map[args.command](args)
        except Exception as e:
            print(f"Error: {e}")
            if console:
                console.print_exception()

if __name__ == "__main__":
    main()