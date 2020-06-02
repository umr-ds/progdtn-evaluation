import datetime
import json
import re
import os

from .base import DtnSoftware


class Forban(DtnSoftware):
    def _get_sender_time(self):
        node_logfile = self.experiment_dir / f"n1.conf_forban_insert.log"
        
        with open(node_logfile) as f:
            line = f.readlines()[0]
            timestamp = line.split(',')[1]
            
            return datetime.datetime.fromtimestamp(float(timestamp))
        
    def _find_log_event(self, node_no, msg_pattern):
        node_logfiles = sorted([self.experiment_dir / f
                for f in os.listdir(self.experiment_dir)
                if re.match(f"^n{node_no}\.conf_forban_var_log_forban_opportunistic\.log.*$", f)], reverse=True)

        if not node_logfiles:
            return None
            raise Exception(f"No Forban logfile for n{node_no} was found")

        for log_file in node_logfiles:
            with open(log_file) as f:
                for log_line in f.readlines():
                    if re.search(msg_pattern, log_line):
                        return log_line

    @staticmethod
    def _log_entry_time(log_entry):
        return datetime.datetime.strptime(
                log_entry[:23], "%Y-%m-%d %H:%M:%S,%f")

    @property
    def duration(self):
        send_no, recv_no = 1, int(self.node_num)

        recv_log = self._find_log_event(
                recv_no, "INFO - saved local file")
        
        # Forban has sometimes issues with logfiles. We ignore these cases.
        if not recv_log:
            return None

        return Forban._log_entry_time(recv_log) - self._get_sender_time()