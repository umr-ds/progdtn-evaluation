from core.service import CoreService
from core.service import ServiceMode

class TcpdumpService(CoreService):
    name = "tcpdump"
    group = "Logging"
    executables = ('tcpdump', )
    startup = ('bash -c " \
for ifpath in /sys/class/net/eth*; do \
    export iface=`basename $ifpath`; \
    nohup tcpdump -n -e -s 200 -i $iface -w $iface.pcap &> $iface.log & \
    echo $! >> tcpdump.pids; \
done \
"''', )
    shutdown = ('bash -c " \
for pid in `cat tcpdump.pids`; do \
    kill $pid; \
done; \
rm tcpdump.pids \
"', )
    validation_mode = ServiceMode.BLOCKING