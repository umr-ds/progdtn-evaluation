### ENV string algo "write description here..."
import time

from general import *

if __name__ == '__main__':
    logger.info("STAGE 0: start MACI experiment and CORE session")
    framework.start()
    session = make_session('/serval_routing/scenarios/slaw.xml', {{simInstanceId}}, '{{algo}}')
    time.sleep(10)

    logger.info("STAGE 1: start position information thread")
    log_positions(session)

    time.sleep(100)

    logger.info("STAGE 2 shutdown: stop services")
    stop_services(session)

    logger.info("STAGE 1 shutdown: collect all logs and files")
    collect_logs(session.session_dir)

    logger.info("STAGE 0 shutdown: stop CORE session and MACI experiment")
    session.shutdown()
    framework.stop()
