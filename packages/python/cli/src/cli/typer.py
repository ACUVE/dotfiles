import sys
from typing import Annotated, Literal
from logging import DEBUG, INFO, WARNING, basicConfig, getLogger

import typer
from typer import Typer

from .sbx import sbx as sbx_command
from .docker_credential import (
    docker_credential_bw as docker_credential_bw_command,
    docker_credential_bw_docker as docker_credential_bw_docker_command,
)

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
            envvar="CLI_VERBOSE",
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

    _LOGGER.debug(f"Set logging level to {level}")


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


@app.command(
    name="docker-credential-bw",
)
def docker_credential_bw(
    command: Annotated[
        Literal["get", "store", "erase", "list"],
        typer.Argument(help="The command to execute"),
    ],
) -> None:
    """Docker credential helper with Bitwarden storage.

    This command implements the Docker credential helper specification,
    storing all Docker credentials in a single Bitwarden secure note item.

    Supported subcommands: get, store, erase, list

    Usage:
        py_cli docker-credential-bw get < server_url.txt
        py_cli docker-credential-bw list
        py_cli docker-credential-bw store < credentials.json
        py_cli docker-credential-bw erase < server_url.txt

    Environment variables:
        BW_SESSION: Bitwarden session token (required for unlocked vault)
    """
    docker_credential_bw_command(command)


@app.command(
    name="docker-credential-bw-docker",
)
def docker_credential_bw_docker(
    command: Annotated[
        Literal["get", "store", "erase", "list"],
        typer.Argument(help="The command to execute"),
    ],
    search_term: Annotated[
        str,
        typer.Option(
            "--search-term",
            "-s",
            envvar="BW_DOCKER_SEARCH_TERM",
            help="Search term for Bitwarden item lookup (default: DockerHub)",
        ),
    ] = "DockerHub",
) -> None:
    """Docker credential helper using Bitwarden CLI.

    This command implements the Docker credential helper specification,
    providing read-only access to Docker Hub credentials stored in Bitwarden.

    Supported subcommands: get, store, erase, list

    Usage:
        py_cli docker-credential-bw-docker get < server_url.txt
        py_cli docker-credential-bw-docker list
        py_cli docker-credential-bw-docker store < credentials.json
        py_cli docker-credential-bw-docker erase < server_url.txt

    Environment variables:
        BW_DOCKER_SEARCH_TERM: Override the default search term (default: "DockerHub")
        BW_SESSION: Bitwarden session token (required for unlocked vault)
    """
    docker_credential_bw_docker_command(command, search_term)


def main() -> None:
    app()


@app.command()
def version() -> None:
    """Show the version of the CLI tool."""

    from . import __version__

    print(f"cli version {__version__}")


@app.command()
def show_python_executable() -> None:
    """Show the current Python path."""
    print(sys.executable)
