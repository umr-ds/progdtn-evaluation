from core.service import CoreService
from core.service import ServiceMode

class MMDRService(CoreService):
    name = "mmdr"
    group = "Utility"
    executables = ('/serval_routing/mmdr.py', )
    startup = ('bash -c " \
nohup /serval_routing/mmdr.py > mmdr_run.log 2>&1 & \
echo $! > mmdr.pid; \
sleep 1; \
"', )
    shutdown = ('bash -c " \
kill `cat mmdr.pid`; \
rm mmdr.pid; \
"', )
    validation_mode = ServiceMode.BLOCKING
