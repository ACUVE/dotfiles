"""Tests for Docker credential helper."""

import json
import sys
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from cli.docker_credential import (
    _cmd_erase_noop,
    _cmd_get_docker_hub,
    _cmd_list_docker_hub,
    _cmd_store_noop,
    docker_credential_bw_docker,
)
from cli.docker_credential.bitwarden import (
    BitwardenError,
    check_bw_status,
    output_error,
    search_items,
)
from cli.docker_credential.types import DockerCredential


class TestCmdGet:
    """Tests for the get command."""

    @patch("cli.docker_credential.check_bw_status")
    @patch("cli.docker_credential.search_items")
    @patch("builtins.print")
    def test_get_success(
        self, mock_print: MagicMock, mock_search: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test successful credential retrieval."""
        mock_search.return_value = [
            {
                "login": {
                    "username": "testuser",
                    "password": "testpass",
                }
            }
        ]

        _cmd_get_docker_hub("https://index.docker.io/v1/", "DockerHub")

        # Verify output
        mock_print.assert_called_once()
        output = json.loads(mock_print.call_args[0][0])
        assert output["ServerURL"] == "https://index.docker.io/v1/"
        assert output["Username"] == "testuser"
        assert output["Secret"] == "testpass"

    @patch("cli.docker_credential.output_error")
    def test_get_wrong_server(self, mock_error: MagicMock) -> None:
        """Test get with non-Docker Hub server."""
        _cmd_get_docker_hub("https://ghcr.io", "DockerHub")
        mock_error.assert_called_once()
        assert "credentials not found for" in mock_error.call_args[0][0]

    @patch("cli.docker_credential.check_bw_status")
    @patch("cli.docker_credential.search_items")
    @patch("cli.docker_credential.output_error")
    def test_get_no_items(
        self,
        mock_error: MagicMock,
        mock_search: MagicMock,
        mock_check: MagicMock,
    ) -> None:
        """Test get when no items found."""
        mock_search.return_value = []
        _cmd_get_docker_hub("https://index.docker.io/v1/", "DockerHub")
        mock_error.assert_called_once_with("credentials not found")

    @patch("cli.docker_credential.check_bw_status")
    @patch("cli.docker_credential.search_items")
    @patch("cli.docker_credential.output_error")
    def test_get_invalid_credentials(
        self,
        mock_error: MagicMock,
        mock_search: MagicMock,
        mock_check: MagicMock,
    ) -> None:
        """Test get with invalid credential format."""
        mock_search.return_value = [
            {
                "login": {
                    "username": "testuser",
                    # Missing password
                }
            }
        ]
        _cmd_get_docker_hub("https://index.docker.io/v1/", "DockerHub")
        mock_error.assert_called_once_with("invalid credentials format")

    @patch("cli.docker_credential.check_bw_status")
    @patch("cli.docker_credential.output_error")
    def test_get_bitwarden_error(
        self, mock_error: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test get when Bitwarden raises an error."""
        mock_check.side_effect = BitwardenError("Bitwarden is locked")
        _cmd_get_docker_hub("https://index.docker.io/v1/", "DockerHub")
        mock_error.assert_called_once_with("Bitwarden is locked")

    @patch("cli.docker_credential.check_bw_status")
    @patch("cli.docker_credential.search_items")
    @patch("cli.docker_credential.output_error")
    def test_get_validation_error(
        self,
        mock_error: MagicMock,
        mock_search: MagicMock,
        mock_check: MagicMock,
    ) -> None:
        """Test get when pydantic validation fails."""
        mock_search.return_value = [
            {
                "login": {
                    "username": "testuser",
                    "password": "testpass",
                }
            }
        ]

        # Patch DockerCredential to raise ValidationError
        with patch("cli.docker_credential.DockerCredential") as mock_cred:
            # Create a ValidationError by trying to create invalid model
            try:
                from cli.docker_credential.types import DockerCredential as DC

                DC(ServerURL="", Username="u", Secret="s")
            except ValidationError as ve:
                mock_cred.side_effect = ve

            _cmd_get_docker_hub("https://index.docker.io/v1/", "DockerHub")

            mock_error.assert_called_once()
            assert "validation error" in mock_error.call_args[0][0]


class TestCmdStore:
    """Tests for the store command."""

    @patch("sys.exit")
    def test_store_valid_input(self, mock_exit: MagicMock) -> None:
        """Test store with valid input."""
        input_data = {
            "ServerURL": "https://index.docker.io/v1/",
            "Username": "testuser",
            "Secret": "testpass",
        }
        _cmd_store_noop(input_data)
        mock_exit.assert_called_once_with(0)

    @patch("cli.docker_credential.output_error")
    def test_store_invalid_input(self, mock_error: MagicMock) -> None:
        """Test store with invalid input."""
        input_data = {
            "ServerURL": "https://index.docker.io/v1/",
            # Missing Username and Secret
        }
        _cmd_store_noop(input_data)
        mock_error.assert_called_once()
        assert "invalid input" in mock_error.call_args[0][0]


class TestCmdErase:
    """Tests for the erase command."""

    @patch("sys.exit")
    def test_erase(self, mock_exit: MagicMock) -> None:
        """Test erase command (no-op)."""
        _cmd_erase_noop("https://index.docker.io/v1/")
        mock_exit.assert_called_once_with(0)


class TestCmdList:
    """Tests for the list command."""

    @patch("cli.docker_credential.check_bw_status")
    @patch("cli.docker_credential.search_items")
    @patch("builtins.print")
    def test_list_success(
        self, mock_print: MagicMock, mock_search: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test successful list command."""
        mock_search.return_value = [
            {
                "login": {
                    "username": "testuser",
                    "password": "testpass",
                }
            }
        ]

        _cmd_list_docker_hub("DockerHub")

        # Verify output
        mock_print.assert_called_once()
        output = json.loads(mock_print.call_args[0][0])
        assert output["https://index.docker.io/v1/"] == "testuser"

    @patch("cli.docker_credential.check_bw_status")
    @patch("cli.docker_credential.search_items")
    @patch("builtins.print")
    @patch("sys.exit")
    def test_list_no_items(
        self,
        mock_exit: MagicMock,
        mock_print: MagicMock,
        mock_search: MagicMock,
        mock_check: MagicMock,
    ) -> None:
        """Test list when no items found."""
        mock_search.return_value = []
        _cmd_list_docker_hub("DockerHub")
        mock_print.assert_called_once_with("{}")
        mock_exit.assert_called_once_with(0)

    @patch("cli.docker_credential.check_bw_status")
    @patch("cli.docker_credential.search_items")
    @patch("builtins.print")
    def test_list_no_username(
        self, mock_print: MagicMock, mock_search: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test list when item has no username."""
        mock_search.return_value = [
            {
                "login": {
                    # Missing username
                    "password": "testpass",
                }
            }
        ]
        _cmd_list_docker_hub("DockerHub")
        mock_print.assert_called_once_with("{}")

    @patch("cli.docker_credential.check_bw_status")
    @patch("cli.docker_credential.output_error")
    def test_list_bitwarden_error(
        self, mock_error: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test list when Bitwarden raises an error."""
        mock_check.side_effect = BitwardenError("Bitwarden is locked")
        _cmd_list_docker_hub("DockerHub")
        mock_error.assert_called_once_with("Bitwarden is locked")


class TestBitwardenFunctions:
    """Tests for Bitwarden helper functions."""

    @patch("subprocess.run")
    def test_check_bw_status_not_installed(self, mock_run: MagicMock) -> None:
        """Test check_bw_status when bw is not installed."""
        mock_run.return_value = MagicMock(returncode=1)

        with pytest.raises(
            BitwardenError, match="Bitwarden CLI \\(bw\\) is not installed"
        ):
            check_bw_status()

    @patch("subprocess.run")
    def test_check_bw_status_command_failed(self, mock_run: MagicMock) -> None:
        """Test check_bw_status when bw status command fails."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # which bw succeeds
            MagicMock(returncode=1, stderr="Error"),  # bw status fails
        ]

        with pytest.raises(BitwardenError, match="Failed to get Bitwarden status"):
            check_bw_status()

    @patch("subprocess.run")
    def test_check_bw_status_locked(self, mock_run: MagicMock) -> None:
        """Test check_bw_status when vault is locked."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # which bw succeeds
            MagicMock(returncode=0, stdout='{"status":"locked"}'),  # vault is locked
        ]

        with pytest.raises(BitwardenError, match="Bitwarden is locked"):
            check_bw_status()

    @patch("subprocess.run")
    def test_check_bw_status_invalid_json(self, mock_run: MagicMock) -> None:
        """Test check_bw_status with invalid JSON response."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # which bw succeeds
            MagicMock(returncode=0, stdout="invalid json"),  # invalid JSON
        ]

        with pytest.raises(BitwardenError, match="Failed to parse Bitwarden status"):
            check_bw_status()

    @patch("subprocess.run")
    def test_check_bw_status_unlocked(self, mock_run: MagicMock) -> None:
        """Test check_bw_status when vault is unlocked."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # which bw succeeds
            MagicMock(
                returncode=0, stdout='{"status":"unlocked"}'
            ),  # vault is unlocked
        ]

        # Should not raise
        check_bw_status()

    @patch("subprocess.run")
    def test_search_items_success(self, mock_run: MagicMock) -> None:
        """Test search_items with successful response."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout='[{"id":"1","name":"test"}]'
        )

        result = search_items("test")
        assert result == [{"id": "1", "name": "test"}]

    @patch("subprocess.run")
    def test_search_items_command_failed(self, mock_run: MagicMock) -> None:
        """Test search_items when command fails."""
        mock_run.return_value = MagicMock(returncode=1, stderr="Error")

        with pytest.raises(BitwardenError, match="Failed to search Bitwarden items"):
            search_items("test")

    @patch("subprocess.run")
    def test_search_items_invalid_json(self, mock_run: MagicMock) -> None:
        """Test search_items with invalid JSON response."""
        mock_run.return_value = MagicMock(returncode=0, stdout="invalid json")

        with pytest.raises(BitwardenError, match="Failed to parse Bitwarden response"):
            search_items("test")

    @patch("subprocess.run")
    def test_search_items_not_a_list(self, mock_run: MagicMock) -> None:
        """Test search_items when response is not a list."""
        mock_run.return_value = MagicMock(returncode=0, stdout='{"error":"not a list"}')

        with pytest.raises(
            BitwardenError, match="Invalid response from Bitwarden: expected a list"
        ):
            search_items("test")

    @patch("sys.exit")
    @patch("builtins.print")
    def test_output_error(self, mock_print: MagicMock, mock_exit: MagicMock) -> None:
        """Test output_error function."""
        output_error("Test error", 2)

        # Check that error was printed to stderr
        mock_print.assert_called_once()
        args, kwargs = mock_print.call_args
        assert kwargs.get("file") == sys.stderr
        assert "Test error" in args[0]

        # Check exit code
        mock_exit.assert_called_once_with(2)


class TestMainFunction:
    """Tests for the main entry point."""

    @patch("sys.stdin")
    @patch("cli.docker_credential._cmd_get_docker_hub")
    def test_main_get_command(self, mock_cmd: MagicMock, mock_stdin: MagicMock) -> None:
        """Test main function with get command."""
        mock_stdin.read.return_value = "https://index.docker.io/v1/\n"

        docker_credential_bw_docker("get", "DockerHub")

        mock_cmd.assert_called_once_with("https://index.docker.io/v1/", "DockerHub")

    @patch("sys.stdin")
    @patch("cli.docker_credential._cmd_store_noop")
    def test_main_store_command(
        self, mock_cmd: MagicMock, mock_stdin: MagicMock
    ) -> None:
        """Test main function with store command."""
        mock_stdin.read.return_value = '{"ServerURL":"https://index.docker.io/v1/","Username":"user","Secret":"pass"}'

        docker_credential_bw_docker("store", "DockerHub")

        mock_cmd.assert_called_once()

    @patch("sys.stdin")
    @patch("cli.docker_credential.output_error")
    def test_main_store_invalid_json(
        self, mock_error: MagicMock, mock_stdin: MagicMock
    ) -> None:
        """Test main function with invalid JSON for store command."""
        mock_stdin.read.return_value = "invalid json"

        docker_credential_bw_docker("store", "DockerHub")

        mock_error.assert_called_once()
        assert "invalid JSON input" in mock_error.call_args[0][0]

    @patch("sys.stdin")
    @patch("cli.docker_credential._cmd_erase_noop")
    def test_main_erase_command(
        self, mock_cmd: MagicMock, mock_stdin: MagicMock
    ) -> None:
        """Test main function with erase command."""
        mock_stdin.read.return_value = "https://index.docker.io/v1/\n"

        docker_credential_bw_docker("erase", "DockerHub")

        mock_cmd.assert_called_once_with("https://index.docker.io/v1/")

    @patch("cli.docker_credential._cmd_list_docker_hub")
    def test_main_list_command(self, mock_cmd: MagicMock) -> None:
        """Test main function with list command."""
        docker_credential_bw_docker("list", "DockerHub")

        mock_cmd.assert_called_once_with("DockerHub")

    @patch("cli.docker_credential.output_error")
    def test_main_unknown_command(self, mock_error: MagicMock) -> None:
        """Test main function with unknown command."""
        docker_credential_bw_docker("unknown", "DockerHub")  # type: ignore

        mock_error.assert_called_once()
        assert "Unknown command" in mock_error.call_args[0][0]


class TestTypes:
    """Tests for pydantic models."""

    def test_docker_credential_valid(self) -> None:
        """Test DockerCredential with valid data."""
        cred = DockerCredential(
            ServerURL="https://index.docker.io/v1/",
            Username="testuser",
            Secret="testpass",
        )
        assert cred.ServerURL == "https://index.docker.io/v1/"
        assert cred.Username == "testuser"
        assert cred.Secret == "testpass"

    def test_docker_credential_empty_server_url(self) -> None:
        """Test DockerCredential with empty ServerURL."""
        with pytest.raises(ValidationError):
            DockerCredential(ServerURL="", Username="testuser", Secret="testpass")

    def test_docker_credential_empty_username(self) -> None:
        """Test DockerCredential with empty Username."""
        with pytest.raises(ValidationError):
            DockerCredential(
                ServerURL="https://index.docker.io/v1/", Username="", Secret="testpass"
            )

    def test_docker_credential_empty_secret(self) -> None:
        """Test DockerCredential with empty Secret."""
        with pytest.raises(ValidationError):
            DockerCredential(
                ServerURL="https://index.docker.io/v1/", Username="testuser", Secret=""
            )
