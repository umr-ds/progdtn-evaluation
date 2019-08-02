import time

from helpers import *


class Software:

    def __init__(self, session):
        self.session = session

        # We have a 54 Mbit/s (6.75 MB/s) network, means it takes about
        # 15 seconds to transmit 100 MB over one hop in the best case.
        # Smaller tests show, that DTN7 takes about 25 seconds to transmit
        # 100 MB over one hop, which means 27 minutes for 64 hops.
        # To be on the safe site, we give the experiments 30 minutes.
        self.timeout = time.time() + 60 * 30

    def _timeout_reached(self):
        if time.time() >= self.timeout:
            return True

        return False

    def send_file(self, node_name, path, dst):
        pass

    def wait_for_arrival(self, node_name):
        pass
