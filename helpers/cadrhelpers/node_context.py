import multiprocessing
import logging

from cadrhelpers.dtnclient import send_context
from cadrhelpers.movement_context import Nodes
from cadrhelpers.util import compute_euclidean_distance


class SensorContext:
    def __init__(self, rest_url: str, node_name: str, wifi_range: float, nodes: Nodes):
        self.rest_url: str = rest_url
        self.node_name: str = node_name
        self.wifi_range: float = wifi_range
        self.nodes: Nodes = nodes
        self.logger: logging.Logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Starting SensorContext generator")
        # process = multiprocessing.Process(target=self._run)
        # process.start()
        # self.logger.info("SensorContext running")
        self._run()

    def _run(self):
        connectedness = self.compute_connectedness()
        send_context(
            rest_url=self.rest_url,
            context_name="connectedness",
            node_context={"value": str(connectedness)},
        )

    def compute_connectedness(self) -> int:
        """Finds (static) nodes within wifi range"""
        logging.info("Computing connectedness")
        connectedness: int = 0

        ourself = self.nodes.get_node_for_name(node_name=self.node_name)

        static_nodes = self.nodes.sensors + self.nodes.backbone

        for node in static_nodes:
            distance = compute_euclidean_distance(node_a=ourself, node_b=node)
            if distance <= self.wifi_range:
                connectedness += 1

        self.logger.info(f"Connectedness: {connectedness}")
        return connectedness
