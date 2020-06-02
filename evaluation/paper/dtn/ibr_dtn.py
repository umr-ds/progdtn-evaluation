import datetime
import re

from .base import DtnSoftware


class IBRDTN(DtnSoftware):
    def _find_log_entry(self, node_no, msg_pattern):
        node_logfile = self.experiment_dir / f"n{node_no}.conf_ibrdtn_run.log"

        with open(node_logfile) as f:
            for log_line in f.readlines():
                if re.search(msg_pattern, log_line):
                    return log_line

    @staticmethod
    def _log_entry_time(log_entry):
        timestamp = re.match("^\d+\.\d+", log_entry).group(0)
        return datetime.datetime.utcfromtimestamp(float(timestamp))

    @property
    def duration(self):
        send_no, recv_no = 1, int(self.node_num)

        send_log = self._find_log_entry(send_no,
                "BundleCore: Bundle received .* \(local\)")
        recv_log = self._find_log_entry(recv_no,
                f"BundleCore: Bundle received .* dtn://n{send_no}")
        
        return IBRDTN._log_entry_time(recv_log) - IBRDTN._log_entry_time(send_log)