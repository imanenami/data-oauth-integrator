"""Charmed Data-OAuth Integrator Operator."""

import logging
import secrets

from charms.hydra.v0.hydra_token_hook import AuthIn, HydraHookProvider, ProviderData
from ops.charm import (
    CharmBase,
    CollectStatusEvent,
    ConfigChangedEvent,
    StartEvent,
    UpdateStatusEvent,
)
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus

from constants import CHARM_KEY, REST_PORT, SUBSTRATE
from models import Context
from workload import VmWorkload

logger = logging.getLogger(__name__)


class IntegratorCharm(CharmBase):
    """Generic Integrator Charm."""

    def __init__(self, *args):
        super().__init__(*args)

        self.name = CHARM_KEY
        self.context = Context(self, substrate=SUBSTRATE)

        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.update_status, self._update_status)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.collect_unit_status, self._on_collect_status)
        self.framework.observe(self.on.collect_app_status, self._on_collect_status)

        container = self.unit.get_container("fastapi") if SUBSTRATE == "k8s" else None
        self.workload = VmWorkload(
            container=container,
            charm_dir=self.charm_dir,
            base_address=self.context.unit.internal_address,
            port=REST_PORT,
        )

        self.hook_provider_data = ProviderData(
            url=f"http://{self.context.unit.internal_address}:{self.workload.port}/api/v1/oauth2/hook",
            auth_config_value=self.context.app.api_key,
            auth_config_name="Bearer",
            auth_config_in=AuthIn.header,
        )
        self.hook_provider = HydraHookProvider(self, "hydra-token-hook")

    @property
    def healthy(self) -> bool:
        """Return the overall health status of the charm."""
        return all([self.context.ready, self.workload.ready])

    def reconcile(self) -> None:
        """Reconcile the workload and service."""
        if self.context.app.relation and not self.context.app.api_key:
            self.context.app.api_key = secrets.token_urlsafe(64)

        if not self.healthy:
            return

        if self.workload.health_check():
            return

        self.workload.configure(api_key=self.context.app.api_key)
        self.workload.start()

    def _on_start(self, event: StartEvent) -> None:
        """Handle `start` event."""
        self.reconcile()

    def _update_status(self, event: UpdateStatusEvent) -> None:
        """Handle `update-status` event."""
        self.reconcile()

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Handle `config-changed` event."""
        self.reconcile()

    def _on_collect_status(self, event: CollectStatusEvent):
        """Handle `collect-status` event."""
        if not self.workload.health_check():
            event.add_status(MaintenanceStatus("Setting up the integrator..."))
            return

        if not self.workload.ready:
            event.add_status(
                BlockedStatus(
                    "Integrator not ready to start, check if all relations are setup successfully."
                )
            )
            return

        event.add_status(
            ActiveStatus(
                f"Webhook served at {self.context.unit.internal_address}:{self.workload.port}"
            )
        )
        self.unit.set_ports(REST_PORT)


if __name__ == "__main__":
    main(IntegratorCharm)
