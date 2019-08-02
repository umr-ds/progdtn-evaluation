import json
import time

from base import Software


class DTN7(Software):

    def send_file(self, node_name, path, dst):
        node = self.session.get_object_by_name(node_name)
        node.cmd(
            "bash -c 'cat {path} | dtn7cat send \"http://127.0.0.1:8080\" \"dtn://{dst}/\"'".format(**locals()))

    def wait_for_arrival(self, node_name):
        node = self.session.get_object_by_name(node_name)

        with open("{node.nodedir}/dtn7d_run.log".format(**locals())) as log_file:

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
