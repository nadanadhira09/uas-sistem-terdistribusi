#!/bin/bash
# Start Broker B - Auto cleanup jika port terpakai

# Kill process lama yang menggunakan port 1884
if lsof -ti:1884 > /dev/null 2>&1; then
    echo "🔄 Stopping old process on port 1884..."
    kill -9 $(lsof -ti:1884)
    sleep 1
fi

# Start Broker B
echo "🚀 Starting Broker B on port 1884..."
cd "$(dirname "$0")"
mosquitto -c brokers/brokerB.conf
