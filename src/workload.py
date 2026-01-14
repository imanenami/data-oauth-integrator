#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Plugin Server Workload."""

import inspect
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Mapping

import requests
from charmlibs.systemd import (
    daemon_reload,
    service_restart,
    service_running,
    service_stop,
)
from ops import Container
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_fixed,
)
from typing_extensions import override

from constants import REST_PORT, SERVICE_NAME, SERVICE_PATH

logger = logging.getLogger(__name__)


class BaseWorkload(ABC):
    """Abstract Base Interface for Integrator Workload."""

    charm_dir: Path
    user: str
    group: str

    def __init__(
        self,
        container: Container | None = None,
        charm_dir: Path = Path("/path/to/charm/"),
        base_address: str = "localhost",
        port: int = REST_PORT,
    ) -> None:
        self.container = container
        self.charm_dir = charm_dir
        self.base_address = base_address
        self.port = port

    @abstractmethod
    def read(self, path: str) -> list[str]:
        """Reads a file from the workload.

        Args:
            path: the full filepath to read from

        Returns:
            List of string lines from the specified path
        """
        ...

    @abstractmethod
    def write(self, content: str | BinaryIO, path: str, mode: str = "w") -> None:
        """Writes content to a workload file.

        Args:
            content: string of content to write
            path: the full filepath to write to
            mode: the write mode. Usually "w" for write, or "a" for append. Default "w"
        """
        ...

    @abstractmethod
    def exec(
        self,
        command: list[str] | str,
        env: Mapping[str, str] | None = None,
        working_dir: str | None = None,
    ) -> str:
        """Executes a command on the workload substrate.

        Returns None if the command failed to be executed.
        """
        ...

    @property
    @abstractmethod
    def ready(self) -> bool:
        """Returns True if the workload service is ready to interact, and False otherwise."""
        ...

    @abstractmethod
    def start(self) -> None:
        """Starts the FastAPI service."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stops the  FastAPIservice."""
        ...

    @abstractmethod
    def configure(self) -> None:
        """Makes all necessary configurations to start the server service."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Checks that the FastAPI service is active and healthy."""
        ...


class VmWorkload(BaseWorkload):
    """An Implementation of Workload Interface for VM."""

    user: str = "root"
    group: str = "root"
    service: str = SERVICE_NAME
    service_path: str = SERVICE_PATH

    @override
    def read(self, path: str) -> list[str]:
        if not os.path.exists(path):
            return []
        else:
            with open(path) as f:
                content = f.read().split("\n")

        return content

    @override
    def write(self, content: str, path: str, mode: str = "w") -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, mode) as f:
            f.write(content)

        self.exec(["chown", "-R", f"{self.user}:{self.group}", f"{path}"])

    @override
    def exec(
        self,
        command: list[str] | str,
        env: Mapping[str, str] | None = None,
        working_dir: str | None = None,
    ) -> str:
        try:
            output = subprocess.check_output(
                command,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                shell=isinstance(command, str),
                env=env,
                cwd=working_dir,
            )
            logger.debug(f"{output=}")
            return output
        except subprocess.CalledProcessError as e:
            logger.error(f"cmd failed - cmd={e.cmd}, stdout={e.stdout}, stderr={e.stderr}")
            raise e

    @property
    @override
    def ready(self) -> bool:
        return True

    @override
    def start(self) -> None:
        service_restart(self.service)

    @override
    def stop(self) -> None:
        service_stop(self.service)

    @override
    def configure(self) -> None:
        self.write(content=self.systemd_config + "\n", path=self.service_path)
        daemon_reload()

    @override
    @retry(
        wait=wait_fixed(1),
        stop=stop_after_attempt(5),
        retry=retry_if_exception(lambda _: True),
        retry_error_callback=lambda _: False,
    )
    def health_check(self) -> bool:
        if not service_running(self.service):
            return False

        try:
            response = requests.get(self.health_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.info(f"Something went wrong during health check: {e}")
            raise e

    @property
    def systemd_config(self) -> str:
        """Returns the Systemd configuration for FastAPI service."""
        return inspect.cleandoc(
            f"""
            [Unit]
            Description=OAuth Webhook
            Wants=network.target
            Requires=network.target

            [Service]
            WorkingDirectory={self.charm_dir}/src/rest
            EnvironmentFile=-/etc/environment
            Environment=PORT={self.port}
            ExecStart={self.charm_dir}/venv/bin/python {self.charm_dir}/src/rest/entrypoint.py
            Restart=always
            Type=simple
        """
        )

    @property
    def health_url(self) -> str:
        """Returns the health check URL."""
        return f"http://{self.base_address}:{self.port}/api/v1/healthcheck/liveness"
