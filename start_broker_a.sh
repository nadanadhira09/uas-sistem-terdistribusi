#!/bin/bash
# Start Broker A - Auto cleanup jika port terpakai

# Kill process lama yang menggunakan port 1883
if lsof -ti:1883 > /dev/null 2>&1; then
    echo "🔄 Stopping old process on port 1883..."
    kill -9 $(lsof -ti:1883)
    sleep 1
fi

# Start Broker A
echo "🚀 Starting Broker A on port 1883..."
cd "$(dirname "$0")"
mosquitto -c brokers/brokerA.conf
