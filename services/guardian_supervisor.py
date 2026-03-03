import logging
import time


class GuardianSupervisor:

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger("GuardianSupervisor")

    # =========================================================
    # Observer Core Layer
    # =========================================================

    def observe(self, state_snapshot: dict):

        """
        Guardian Supervisor Observer.

        Apenas monitora e registra estados.
        Nunca executa mutações storage.
        """

        try:

            if not state_snapshot:
                self.logger.warning("Guardian received empty snapshot")
                return

            # Log state observation
            self.logger.info(f"Guardian Observation → {state_snapshot}")

            # Early anomaly detection
            self._anomaly_detection(state_snapshot)

        except Exception as e:
            self.logger.error(f"Guardian internal error: {str(e)}")

    # =========================================================
    # Early Anomaly Detection (Observer Only)
    # =========================================================

    def _anomaly_detection(self, snapshot):

        """
        Apenas detecção passiva.

        Não executa nenhuma ação corretiva.
        """

        if snapshot.get("Success") is False:
            self.logger.error(
                f"Guardian Alert: Operation Failure Detected → {snapshot.get('ErrorMessage')}"
            )

        filesystem = snapshot.get("FileSystem")

        if filesystem:
            self.logger.info(f"Guardian verified filesystem state → {filesystem}")

        partition_style = snapshot.get("PartitionStyle")

        if partition_style:
            self.logger.info(f"Guardian observed partition style → {partition_style}")

    # =========================================================
    # Notification Hook (Future Extension Point)
    # =========================================================

    def notify(self, event_type: str, payload: dict):

        """
        Future integration point.

        Examples:
        - GUI notification
        - Logging aggregator
        - Telemetry
        - External observer system
        """

        self.logger.info(
            f"Guardian Event → {event_type} | Payload → {payload}"
        )

    # =========================================================
    # Execution Guard Check (Lightweight)
    # =========================================================

    def guard_execution(self):

        """
        Lightweight heartbeat-style guard.

        Apenas observa engine alive state.
        """

        return {
            "GuardianStatus": "ONLINE",
            "Timestamp": time.time()
        }