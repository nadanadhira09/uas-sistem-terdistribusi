#!/bin/bash
# Start Node B with Failover Support

cd "$(dirname "$0")"
python3 nodes/node_b_failover.py
