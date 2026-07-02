"""
Driftwatch CLI — driftwatch command.
"""
import os
import sys

import click
import httpx


@click.group()
@click.version_option("0.1.0", prog_name="driftwatch")
def cli() -> None:
    """Driftwatch — Security monitoring for developer APIs."""
    pass


@cli.command()
@click.argument("target")
@click.option("--ports", "-p", help="Comma-separated list of ports to scan")
@click.option("--timeout", "-t", default=1.5, type=float, help="Per-port timeout in seconds")
@click.option("--api-key", "-k", help="Driftwatch API key (or set DRIFTWATCH_API_KEY)")
@click.option("--base-url", default="https://api.driftwatch.io", help="API base URL")
def scan(target: str, ports: str | None, timeout: float, api_key: str | None, base_url: str) -> None:
    """Scan a target host for open ports and security risks."""
    from driftwatch.scanner import scan as run_scan

    port_list = None
    if ports:
        try:
            port_list = [int(p.strip()) for p in ports.split(",")]
        except ValueError:
            click.echo("Error: --ports must be comma-separated integers", err=True)
            sys.exit(1)

    key = api_key or os.getenv("DRIFTWATCH_API_KEY")
    if not key:
        click.echo("Error: API key required. Set DRIFTWATCH_API_KEY or pass --api-key", err=True)
        sys.exit(1)

    click.echo(f"Scanning {target} ...")
    result = run_scan(target, ports=port_list, timeout=timeout, api_key=key, base_url=base_url)

    click.echo(f"\n✓ Scan complete: {result['summary']}")
    if result["open_ports"]:
        click.echo("\nOpen ports:")
        for p in result["open_ports"]:
            click.echo(f"  {p['port']:>5}  {p['status']:<6}  [{p.get('risk_level','LOW'):>5}]  {p.get('description','')}")
    if result["risks"]:
        click.echo("\n⚠ Risks identified:")
        for r in result["risks"]:
            click.echo(f"  {r['port']:>5}  [{r['risk_level']:<5}]  {r['issue']}")
    else:
        click.echo("\n✓ No high-risk ports found.")


@cli.command()
@click.argument("org_id")
@click.argument("report_type", type=click.Choice(["soc2", "gdpr", "iso27001"]), default="soc2")
@click.option("--api-key", "-k", help="Driftwatch API key (or set DRIFTWATCH_API_KEY)")
@click.option("--base-url", default="https://api.driftwatch.io", help="API base URL")
def report(org_id: str, report_type: str, api_key: str | None, base_url: str) -> None:
    """Generate or fetch a compliance report."""
    from driftwatch.reporter import report as fetch_report

    key = api_key or os.getenv("DRIFTWATCH_API_KEY")
    if not key:
        click.echo("Error: API key required. Set DRIFTWATCH_API_KEY or pass --api-key", err=True)
        sys.exit(1)

    click.echo(f"Fetching {report_type.upper()} report for org {org_id} ...")
    try:
        content = fetch_report(org_id, api_key=key, report_type=report_type, base_url=base_url)
        if content:
            click.echo(f"\n{content}")
        else:
            click.echo("Report generated but returned empty content.")
    except TimeoutError:
        click.echo("Error: Report generation timed out after 30s", err=True)
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        click.echo(f"Error: API returned {e.response.status_code}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("api_key", required=False)
@click.option("--base-url", default="https://api.driftwatch.io", help="API base URL")
def init(api_key: str | None, base_url: str) -> None:
    """Check your Driftwatch credentials."""
    key = api_key or os.getenv("DRIFTWATCH_API_KEY")
    if not key:
        click.echo("Error: API key required. Set DRIFTWATCH_API_KEY or pass api_key argument", err=True)
        sys.exit(1)

    import asyncio

    async def _check():
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{base_url}/api/v2/status",
                headers={"x-driftwatch-api-key": key},
                timeout=5.0,
            )
            resp.raise_for_status()
            return resp.json()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data = loop.run_until_complete(_check())
        loop.close()
        click.echo(f"✓ Connected to Driftwatch ({data.get('org_name', 'OK')})")
    except httpx.HTTPStatusError:
        click.echo("✗ Invalid API key or network error", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Connection failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
