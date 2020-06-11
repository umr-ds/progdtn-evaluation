import json
import time

from core.emulator.coreemu import Session


class DTN7:
    def __init__(self, session: Session):
        assert isinstance(session, Session), type(session)
        self.session = session

        # We have a 54 Mbit/s (6.75 MB/s) network, means it takes about
        # 15 seconds to transmit 100 MB over one hop in the best case.
        # Smaller tests show, that DTN7 takes about 25 seconds to transmit
        # 100 MB over one hop, which means 27 minutes for 64 hops.
        # To be on the safe site, we give the experiments 30 minutes.
        self.timeout = time.time() + 60 * 30

    def _timeout_reached(self) -> bool:
        if time.time() >= self.timeout:
            return True

        return False

    def send_file(self, node_name: str, path: str, dst: str):
        node = self.session.nodes[node_name]
        node.cmd(
            'bash -c \'cat {path} | dtncat send "http://127.0.0.1:8080" "dtn://{dst}/"\''.format(
                **locals()
            )
        )

    def wait_for_arrival(self, node_name):
        node = self.session.nodes[node_name]

        with open("{node.nodedir}/dtnd_run.log".format(**locals())) as log_file:

            while True:

                if self._timeout_reached():
                    print("Timeout reached. Stopping experiment.")
                    break

                line = log_file.readline()

                if not line:
                    time.sleep(0.1)
                    continue

                try:
                    json_obj = json.loads(line)
                    if json_obj["msg"] == "Received bundle for local delivery":
                        break
                except Exception as e:
                    print(e)
                    continue
