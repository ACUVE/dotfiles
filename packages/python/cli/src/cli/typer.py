import sys
from typing import Annotated
from logging import DEBUG, INFO, WARNING, basicConfig, getLogger

import typer
from typer import Typer

from .sbx import sbx as sbx_command

_LOGGER = getLogger(__name__)

app = Typer()


@app.callback()
def main_callback(
    *,
    verbose: Annotated[
        int,
        typer.Option(
            "-v",
            "--verbose",
            count=True,
            help="Increase verbosity level. Can be specified multiple times.",
        ),
    ] = 0,
) -> None:
    """CLI tool for various utilities."""

    level = WARNING
    if verbose >= 2:
        level = DEBUG
    elif verbose == 1:
        level = INFO

    basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def sbx(
    ctx: typer.Context,
    enable_git: Annotated[
        bool,
        typer.Option(
            "--git",
            help="Enable git-related sandboxing features.",
        ),
    ] = False,
    enable_cwd: Annotated[
        bool,
        typer.Option(
            "--cwd",
            help="Enable current working directory access in the sandbox.",
        ),
    ] = False,
    write: Annotated[
        list[str],
        typer.Option(
            "-w",
            "--write",
            help="Directories to allow write access. Can be specified multiple times.",
        ),
    ] = [],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Print the sandbox-exec command without executing it.",
        ),
    ] = False,
) -> None:
    """Execute a command in a sandboxed environment using sandbox-exec."""
    sbx_command(
        enable_git=enable_git,
        enable_cwd=enable_cwd,
        write=write,
        dry_run=dry_run,
        command=ctx.args,
    )


@app.command()
def version() -> None:
    """Show the version of the CLI tool."""

    from . import __version__

    print(f"cli version {__version__}")


@app.command()
def show_python_executable() -> None:
    """Show the current Python path."""
    print(sys.executable)


def main() -> None:
    app()
