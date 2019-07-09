from core.service import CoreService
from core.service import ServiceMode

class PidstatService(CoreService):
    name = "pidstat"
    group = "Logging"
    executables = ('pidstat', )
    startup = ('bash -c " \
nohup pidstat -drush -p ALL 1 > pidstat 2> pidstat.log & \
echo $! > pidstat.pid \
"', ) 
    shutdown = ('bash -c " \
kill `cat pidstat.pid`; \
rm pidstat.pid \
"', )
    validation_mode = ServiceMode.BLOCKING