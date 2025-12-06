import os
import sys
from typing import Annotated
from logging import DEBUG, INFO, WARNING, basicConfig

import typer
from typer import Typer

from .sbx import sbx as sbx_command

app = Typer()


@app.callback()
def main_callback(
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
    write: Annotated[
        list[str],
        typer.Option(
            "-w",
            "--write",
            help="Directories to allow write access. Can be specified multiple times.",
        ),
    ] = [],
) -> None:
    """Execute a command in a sandboxed environment using sandbox-exec."""
    sbx_command(write=write, command=ctx.args)


@app.command()
def version() -> None:
    """Show the version of the CLI tool."""

    from . import __version__

    print(f"cli version {__version__}")


_ALIAS = {
    "sbx": "sbx",
}


def main() -> None:
    invoked = os.path.basename(sys.argv[0])

    if invoked in _ALIAS:
        sys.argv = sys.argv[:1] + [_ALIAS[invoked]] + sys.argv[1:]

    app()
