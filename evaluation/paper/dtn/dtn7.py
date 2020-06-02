import datetime
import json

from .base import DtnSoftware


class DTN7(DtnSoftware):
    def _find_log_event(self, node_no, trigger_func):
        node_logfile = self.experiment_dir / f"n{node_no}.conf_dtn7d_run.log"

        with open(node_logfile) as f:
            for log_line in f.readlines():
                try:
                    log_entry = json.loads(log_line)
                    if trigger_func(log_entry):
                        return log_entry
                except:
                    pass

    def _find_log_msg(self, node_no, msg):
        search_func = lambda log_entry: log_entry["msg"] == msg
        return self._find_log_event(node_no, search_func)

    @staticmethod
    def _log_entry_time(log_entry):
        return datetime.datetime.strptime(
                log_entry["time"][:-4], "%Y-%m-%dT%H:%M:%S.%f")

    @property
    def duration(self):
        send_no, recv_no = 1, int(self.node_num)

        send_log = self._find_log_msg(
                send_no, "Transmission of bundle requested")
        recv_log = self._find_log_msg(
                recv_no, "Received bundle for local delivery")

        return DTN7._log_entry_time(recv_log) - DTN7._log_entry_time(send_log)