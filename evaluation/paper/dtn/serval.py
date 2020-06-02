import datetime
import os
import re

from .base import DtnSoftware


class Serval(DtnSoftware):
    def _find_log_entry(self, node_no, msg_pattern):
        node_logfiles = sorted([self.experiment_dir / f
                for f in os.listdir(self.experiment_dir)
                if re.match(f"^n{node_no}\.conf_log_serval-\d+\.log$", f)])

        if not node_logfiles:
            raise Exception(f"No Serval logfile for n{node_no} was found")

        for log_file in node_logfiles:
            with open(log_file) as f:
                for log_line in f.readlines():
                    if re.search(msg_pattern, log_line):
                        return log_line

    @staticmethod
    def _log_entry_time(log_entry):
        timestamp = re.search("\d{2}:\d{2}:\d{2}\.\d{3}", log_entry).group(0)
        return datetime.datetime.strptime(timestamp, "%H:%M:%S.%f")

    @property
    def duration(self):
        send_no, recv_no = 1, int(self.node_num)

        send_log = self._find_log_entry(send_no, "RHIZOME ADD MANIFEST")
        recv_log = self._find_log_entry(recv_no, "RHIZOME ADD MANIFEST")
    
        send_time = Serval._log_entry_time(send_log)
        recv_time = Serval._log_entry_time(recv_log)

        # Serval's logs do not contain the complete date, only the time.
        # We have to check if the time leaps one day and correct it.
        if recv_time < send_time:
            recv_time = recv_time + datetime.timedelta(days=1)

        return recv_time - send_time