#!/bin/bash

APP_DIR="app"
SERVICE_FILE="ctp_service.py"
export PYTHONPATH=$PYTHONPATH:./


start_service() {
  echo "Starting service..."
  python3 app/$SERVICE_FILE &
  echo "Service started. PID(s): $(pgrep -f $SERVICE_FILE)"
}

stop_service() {
  if ! pgrep -f $SERVICE_FILE > /dev/null; then
    echo "Service is not running."
    exit 1
  fi
  echo "Stopping service..."
  pkill -f $SERVICE_FILE
  echo "Service stopped."
}

restart_service() {
  stop_service
  start_service
}

if [ $# -eq 0 ]; then
  echo "Usage: $0 {start|stop|restart}"
  exit 1
fi

case "$1" in
  start)
    start_service
    ;;
  stop)
    stop_service
    ;;
  restart)
    restart_service
    ;;
  *)
    echo "Usage: $0 {start|stop|restart}"
    exit 1
esac
