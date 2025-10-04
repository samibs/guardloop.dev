"""CLI commands for Guardrail"""

import asyncio
import json
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

from guardrail.core.daemon import AIRequest, GuardrailDaemon
from guardrail.core.workers import WorkerManager
from guardrail.utils.config import Config, ConfigManager, get_config
from guardrail.utils.db import DatabaseManager

console = Console()


@click.group()
@click.version_option(version="2.0.0")
def cli():
    """🛡️  Guardrail v2 - Self-Learning AI Governance System

    \b
    Commands:
      run         Execute single AI request with guardrails
      interactive Start interactive session (for conversations)
      init        Initialize guardrail configuration
      status      Show system status
      config      View configuration
      analyze     Analyze violations and failures
      export      Export failures to markdown
      daemon      Start background daemon

    \b
    Examples:
      guardrail run claude "implement auth"      # One-shot request
      guardrail interactive                      # Start conversation
      guardrail status                           # Check system
    """
    pass


@cli.command()
@click.argument("tool", type=click.Choice(["claude", "gemini", "codex"]))
@click.argument("prompt")
@click.option("--agent", "-a", help="Specify agent (architect/coder/tester/etc)")
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["standard", "strict"]),
    default="standard",
    help="Enforcement mode",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def run(tool: str, prompt: str, agent: Optional[str], mode: str, verbose: bool):
    """Execute AI tool with guardrails"""

    async def execute():
        try:
            # Load configuration
            config = get_config()

            # Create daemon
            daemon = GuardrailDaemon(config)

            # Create request
            request = AIRequest(
                tool=tool, prompt=prompt, agent=agent or "auto", mode=mode
            )

            # Show spinner
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Running {tool} with guardrails...", total=None
                )

                # Execute request
                result = await daemon.process_request(request)

            # Display results
            if result.approved:
                console.print("\n✅ [green bold]Request Approved[/green bold]\n")
            else:
                console.print("\n❌ [red bold]Request Blocked[/red bold]\n")

            # Show output
            console.print(Panel(result.raw_output, title="AI Output", border_style="blue"))

            # Show violations if any
            if result.violations and verbose:
                violations_table = Table(title="Violations Detected")
                violations_table.add_column("Type", style="cyan")
                violations_table.add_column("Rule", style="yellow")
                violations_table.add_column("Severity", style="red")
                violations_table.add_column("Description")

                for violation in result.violations:
                    violations_table.add_row(
                        violation.guardrail_type,
                        violation.rule,
                        violation.severity,
                        violation.description,
                    )

                console.print("\n")
                console.print(violations_table)

            # Show failures if any
            if result.failures and verbose:
                failures_table = Table(title="Failures Detected")
                failures_table.add_column("Category", style="cyan")
                failures_table.add_column("Pattern", style="yellow")
                failures_table.add_column("Severity", style="red")
                failures_table.add_column("Context")

                for failure in result.failures:
                    failures_table.add_row(
                        failure.category,
                        failure.pattern,
                        failure.severity,
                        failure.context[:50] + "..." if len(failure.context) > 50 else failure.context,
                    )

                console.print("\n")
                console.print(failures_table)

            # Show execution time
            console.print(
                f"\n⏱️  Execution time: [cyan]{result.execution_time_ms}ms[/cyan]"
            )
            console.print(f"🆔 Session ID: [dim]{result.session_id}[/dim]")

        except Exception as e:
            console.print(f"\n[red bold]Error:[/red bold] {str(e)}", style="red")
            sys.exit(1)

    asyncio.run(execute())


@cli.command()
def init():
    """Initialize guardrail configuration"""
    console.print("\n🛡️  [bold]Initializing Guardrail...[/bold]\n")

    # Create config manager
    config_manager = ConfigManager()

    # Initialize directories
    console.print("📁 Creating directory structure...")
    config_manager.init_directories()

    # Create default config if not exists
    if not config_manager.config_path.exists():
        console.print("⚙️  Creating default configuration...")
        config_manager.load()
        console.print(f"   Config saved to: [cyan]{config_manager.config_path}[/cyan]")
    else:
        console.print(f"   Config already exists at: [cyan]{config_manager.config_path}[/cyan]")

    # Initialize database
    console.print("🗄️  Initializing database...")
    config = config_manager.load()
    db = DatabaseManager(str(config.database.path))
    db.init_db()
    console.print(f"   Database initialized at: [cyan]{config.database.path}[/cyan]")

    # Copy guardrail files from package to user directory
    guardrails_path = Path(config.guardrails.base_path)
    console.print(f"📋 Guardrails directory: [cyan]{guardrails_path}[/cyan]")

    # Find package guardrails directory
    import guardrail
    package_dir = Path(guardrail.__file__).parent.parent
    source_guardrails = package_dir / "guardrails"

    if source_guardrails.exists():
        import shutil

        # Copy guardrail files if they don't exist
        if not guardrails_path.exists() or not list(guardrails_path.glob("*.md")):
            guardrails_path.mkdir(parents=True, exist_ok=True)

            # Copy all .md files
            for md_file in source_guardrails.glob("*.md"):
                dest_file = guardrails_path / md_file.name
                if not dest_file.exists():
                    shutil.copy2(md_file, dest_file)
                    console.print(f"   ✅ Copied: {md_file.name}")

            # Copy agents directory
            source_agents = source_guardrails / "agents"
            if source_agents.exists():
                dest_agents = guardrails_path / "agents"
                dest_agents.mkdir(parents=True, exist_ok=True)

                for agent_file in source_agents.glob("*.md"):
                    dest_file = dest_agents / agent_file.name
                    if not dest_file.exists():
                        shutil.copy2(agent_file, dest_file)
                        console.print(f"   ✅ Copied agent: {agent_file.name}")
        else:
            console.print("   ℹ️  Guardrail files already exist")
    else:
        guardrails_path.mkdir(parents=True, exist_ok=True)
        console.print("   ⚠️  No template guardrails found in package")
        console.print("   Note: Place your guardrail files in this directory")

    console.print("\n✅ [green bold]Initialization complete![/green bold]\n")
    console.print("Next steps:")
    console.print("  1. Review guardrails: [cyan]~/.guardrail/guardrails/[/cyan]")
    console.print("  2. Configure: [cyan]guardrail config[/cyan]")
    console.print("  3. Test: [cyan]guardrail run claude 'Hello, world!'[/cyan]")


@cli.command()
@click.option("--tool", help="Filter by tool")
@click.option("--days", default=7, help="Number of days to analyze")
def analyze(tool: Optional[str], days: int):
    """Analyze failures and violations"""
    console.print(f"\n📊 [bold]Analyzing last {days} days...[/bold]\n")

    config = get_config()
    db = DatabaseManager(str(config.database.path))

    # Get statistics
    stats = db.get_stats()

    # Display overall stats
    stats_table = Table(title="Overall Statistics")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")

    stats_table.add_row("Total Sessions", str(stats["total_sessions"]))
    stats_table.add_row("Total Failures", str(stats["total_failures"]))
    stats_table.add_row("Total Violations", str(stats["total_violations"]))
    stats_table.add_row("Agent Activities", str(stats["total_agents_activity"]))
    stats_table.add_row("Database Size", f"{stats['db_size_mb']:.2f} MB")

    console.print(stats_table)

    # TODO: Add trend analysis, top violations, top failures
    # This would query the database for specific metrics

    console.print("\n✅ Analysis complete")


@cli.command()
def status():
    """Show guardrail system status"""
    console.print("\n🛡️  [bold]Guardrail System Status[/bold]\n")

    try:
        config = get_config()

        # Configuration status
        config_tree = Tree("⚙️  Configuration")
        config_tree.add(f"Mode: [cyan]{config.mode}[/cyan]")
        config_tree.add(f"Default Agent: [cyan]{config.default_agent}[/cyan]")

        tools_branch = config_tree.add("🔧 Tools")
        for tool_name, tool_config in config.tools.items():
            status = "✅" if tool_config.enabled else "❌"
            tools_branch.add(f"{status} {tool_name} ({tool_config.cli_path})")

        features_branch = config_tree.add("🎯 Features")
        features_branch.add(
            f"{'✅' if config.features.background_analysis else '❌'} Background Analysis"
        )
        features_branch.add(
            f"{'✅' if config.features.analysis_worker else '❌'} Analysis Worker"
        )
        features_branch.add(
            f"{'✅' if config.features.metrics_worker else '❌'} Metrics Worker"
        )
        features_branch.add(
            f"{'✅' if config.features.markdown_export else '❌'} Markdown Export"
        )
        features_branch.add(
            f"{'✅' if config.features.cleanup_worker else '❌'} Cleanup Worker"
        )

        console.print(config_tree)

        # Database status
        db = DatabaseManager(str(config.database.path))
        stats = db.get_stats()

        db_table = Table(title="\n🗄️  Database Status")
        db_table.add_column("Metric", style="cyan")
        db_table.add_column("Value", style="green")

        db_table.add_row("Path", str(config.database.path))
        db_table.add_row("Total Sessions", str(stats["total_sessions"]))
        db_table.add_row("Size", f"{stats['db_size_mb']:.2f} MB")

        console.print("\n")
        console.print(db_table)

        console.print("\n✅ System operational")

    except Exception as e:
        console.print(f"\n[red bold]Error:[/red bold] {str(e)}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--output", "-o", default="AI_Failure_Modes.md", help="Output file path")
@click.option("--limit", "-l", default=100, help="Number of failures to export")
def export(output: str, limit: int):
    """Export failures to markdown"""
    console.print(f"\n📤 [bold]Exporting failures to {output}...[/bold]\n")

    try:
        config = get_config()
        db = DatabaseManager(str(config.database.path))

        # Get recent failures
        # This would query the failure_modes table
        # For now, just create a placeholder

        md_content = f"""# AI Failure Modes Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Total Failures Exported**: {limit}
- **Report Period**: Last 30 days

## Failures

_(Failures would be listed here in table format)_
"""

        output_path = Path(output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md_content)

        console.print(f"✅ Exported to: [cyan]{output_path}[/cyan]")

    except Exception as e:
        console.print(f"\n[red bold]Error:[/red bold] {str(e)}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--background", "-b", is_flag=True, help="Run in background")
def daemon(background: bool):
    """Start guardrail daemon with background workers"""

    async def run_daemon():
        config = get_config()
        db = DatabaseManager(str(config.database.path))

        # Initialize daemon and workers
        daemon_instance = GuardrailDaemon(config)
        worker_manager = WorkerManager(config, db)

        # Handle shutdown signals
        def signal_handler(signum, frame):
            console.print("\n\n🛑 Shutting down gracefully...")
            asyncio.create_task(worker_manager.stop_all())
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        console.print("\n🛡️  [bold]Guardrail Daemon Started[/bold]\n")
        console.print(f"Mode: [cyan]{config.mode}[/cyan]")
        console.print(f"Workers: [cyan]{len(worker_manager.workers)}[/cyan]")
        console.print("\nPress Ctrl+C to stop\n")

        # Start workers
        await worker_manager.start_all()

    if background:
        # TODO: Implement proper daemonization
        console.print("[yellow]Background mode not yet implemented. Running in foreground...[/yellow]")

    asyncio.run(run_daemon())


@cli.command()
def config():
    """Show current configuration"""
    console.print("\n⚙️  [bold]Guardrail Configuration[/bold]\n")

    try:
        config_manager = ConfigManager()
        cfg = config_manager.load()

        # Convert to dict and display as YAML
        config_dict = cfg.model_dump()

        console.print(Panel(
            yaml.dump(config_dict, default_flow_style=False, sort_keys=False),
            title=f"Config: {config_manager.config_path}",
            border_style="cyan"
        ))

    except Exception as e:
        console.print(f"\n[red bold]Error:[/red bold] {str(e)}", style="red")
        sys.exit(1)


@cli.command()
def interactive():
    """Interactive guardrail session"""
    console.print("\n🛡️  [bold]Interactive Guardrail Session[/bold]\n")
    console.print("Type 'exit' or 'quit' to end session\n")

    # Load config
    config = get_config()

    # Get tool selection
    console.print("Select AI tool:")
    console.print("  1. Claude")
    console.print("  2. Gemini")
    console.print("  3. Codex")

    tool_map = {"1": "claude", "2": "gemini", "3": "codex"}
    tool_choice = console.input("\nTool [cyan](1-3)[/cyan]: ").strip()
    tool = tool_map.get(tool_choice, "claude")

    # Get mode selection
    console.print("\nSelect mode:")
    console.print("  1. Standard (warn only)")
    console.print("  2. Strict (block violations)")

    mode_map = {"1": "standard", "2": "strict"}
    mode_choice = console.input("\nMode [cyan](1-2)[/cyan]: ").strip()
    mode = mode_map.get(mode_choice, "standard")

    # Get agent
    agent = console.input("\nAgent [cyan](or 'auto')[/cyan]: ").strip() or "auto"

    console.print(f"\n✨ Session started: [cyan]{tool}[/cyan] in [cyan]{mode}[/cyan] mode\n")

    # REPL loop with conversation history (v2)
    async def repl():
        import uuid
        import os

        daemon = GuardrailDaemon(config)
        conversation_id = str(uuid.uuid4())  # v2: conversation tracking
        project_root = os.getcwd()  # v2: for file execution

        # Start conversation in daemon
        daemon.conversation_manager.start_conversation(conversation_id)

        while True:
            try:
                prompt = console.input("[bold cyan]>>> [/bold cyan]")

                if prompt.lower() in ["exit", "quit"]:
                    console.print("\n👋 Goodbye!\n")
                    break

                if not prompt.strip():
                    continue

                # v2: Execute request with conversation history
                request = AIRequest(
                    tool=tool,
                    prompt=prompt,
                    agent=agent,
                    mode=mode,
                    conversation_id=conversation_id,
                    project_root=project_root,
                )

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    progress.add_task("[cyan]Processing...", total=None)
                    result = await daemon.process_request(request)

                # Display result
                status = "✅" if result.approved else "❌"
                console.print(f"\n{status} {result.raw_output}\n")

                # v2: Show task classification if available
                if result.task_classification and result.task_classification.task_type != "code":
                    console.print(
                        f"[dim]📋 Task: {result.task_classification.task_type} "
                        f"({result.task_classification.confidence:.0%} confidence)[/dim]"
                    )

                # v2: Show file operations if any
                if result.file_operations:
                    console.print(
                        f"[green]💾 Created {len(result.file_operations)} file(s)[/green]"
                    )
                    for file_path in result.file_operations:
                        console.print(f"   ✅ {file_path}")

                # Show violations only if guardrails were applied
                if result.guardrails_applied and result.violations:
                    console.print(
                        f"[yellow]⚠️  {len(result.violations)} violation(s) detected[/yellow]"
                    )

                if result.failures:
                    console.print(
                        f"[red]🚨 {len(result.failures)} failure(s) detected[/red]"
                    )

                console.print()

            except KeyboardInterrupt:
                console.print("\n\n👋 Goodbye!\n")
                break
            except EOFError:
                console.print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                console.print(f"\n[red]Error: {str(e)}[/red]\n")

    asyncio.run(repl())


if __name__ == "__main__":
    cli()
