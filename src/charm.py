"""Charmed Data-OAuth Integrator Operator."""

import logging

from ops.charm import (
    CharmBase,
    CollectStatusEvent,
    ConfigChangedEvent,
    StartEvent,
    UpdateStatusEvent,
)
from ops.main import main
from ops.model import BlockedStatus, MaintenanceStatus

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

    def _on_start(self, event: StartEvent) -> None:
        """Handle `start` event."""
        if not self.workload.ready:
            event.defer()
            return

        if self.workload.health_check():
            return

        self.workload.configure()
        self.workload.start()

    def _update_status(self, event: UpdateStatusEvent) -> None:
        """Handle `update-status` event."""
        if not self.workload.health_check():
            self.on.start.emit()

        self.unit.set_ports(REST_PORT)

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Handle `config-changed` event."""
        if not self.workload.ready:
            event.defer()
            return

        self.workload.configure()

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


if __name__ == "__main__":
    main(IntegratorCharm)
