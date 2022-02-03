#!/bin/bash

echo "# Starting SSHD"
/usr/sbin/sshd -D &

echo "# Starting CORE daemon"
core-daemon > /var/log/core-daemon.log 2>&1 &
sleep 1

# Start CORE gui if $DISPLAY is set
if [ ! -z "$DISPLAY" ]; then
    echo "# Starting CORE gui (DISPLAY=$DISPLAY)"
    core-gui $CORE_PARAMS > /var/log/core-gui.log 2>&1 &
    CORE_GUI_PID=$!

    echo "# Dropping into bash (exit with ^D or \`exit\`)"
    bash

    echo "# Waiting until core-gui is closed..."
    wait $CORE_GUI_PID

elif [ ! -z "$BACKEND" ]; then
    echo "# Starting MACI worker (BACKEND=$BACKEND)"
    wget $BACKEND:63658/workers/script.py -O /worker/worker.py &&
        python3 -u /worker/worker.py --backend $BACKEND:63658 --capabilities core --maxidletime $IDLE --no-clear-tmp-dir &&

        exit

    echo "# Couldn't connect to MACI backend." && 
        exit 1
else
    echo "# Dropping into bash (exit with ^D or \`exit\`)"
    bash
fi
