import multiprocessing

from dataclasses import dataclass

from cadrhelpers.dtnclient import send_context
from cadrhelpers.movement_context import Nodes
from cadrhelpers.traffic_generator import compute_euclidean_distance


@dataclass()
class SensorContext:

    rest_url: str
    node_name: str
    wifi_range: float
    nodes: Nodes

    def run(self):
        process = multiprocessing.Process(target=self._run)
        process.start()

    def _run(self):
        connectedness = self._compute_connectedness()
        send_context(
            rest_url=self.rest_url,
            context_name="connectedness",
            node_context={"value": connectedness},
        )

    def _compute_connectedness(self) -> int:
        """Finds (static) nodes within wifi range"""
        connectedness: int = 0

        ourself = self.nodes.get_node_for_name(node_name=self.node_name)

        static_nodes = self.nodes.sensors + self.nodes.backbone

        for node in static_nodes:
            distance = compute_euclidean_distance(node_a=ourself, node_b=node)
            if distance <= self.wifi_range:
                connectedness += 1

        return connectedness
