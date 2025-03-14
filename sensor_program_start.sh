#!/bin/bash
PIPE_PATH="/tmp/temperature_flag_pipe"

if [ -p "$PIPE_PATH" ]; then
    echo "Removing existing pipe..."
    rm "$PIPE_PATH"
fi

mkfifo "$PIPE_PATH"
echo "Created new pipe at $PIPE_PATH"

echo "Checking for runaway libgpiod_pulsein processes..."
ps aux | grep libgpiod_pulsein | grep -v grep | awk '{print $2}' | xargs kill -9
echo "Killed any runaway libgpiod_pulsein processes."

#path to whichever env you activated with proper libraries
source /home/atz001/dht11/env/bin/activate

python3 publisher.py &
PYTHON_PID=$!

./subscriber3 &
C_PID=$!

echo "Both scripts are now running in the background."
echo "Press any key to stop them."

read -n 1 -s

echo "Stopping both scripts..."

if ps -p $PYTHON_PID > /dev/null; then
    kill $PYTHON_PID
    echo "Python script stopped."
else
    echo "Python script already stopped."
fi

if ps -p $C_PID > /dev/null; then
    kill $C_PID
    echo "C script stopped."
else
    echo "C script already stopped."
fi

sleep 1

if [ -p "$PIPE_PATH" ]; then
    rm "$PIPE_PATH"
    echo "Removed pipe at $PIPE_PATH"
else
    echo "No named pipe found to remove."
fi

echo "Both scripts have been terminated."
