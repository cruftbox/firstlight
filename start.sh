#!/bin/bash
# Start CUPS daemon in background
mkdir -p /run/cups
cupsd

# Wait for CUPS socket to be ready
for i in $(seq 1 10); do
    [ -S /run/cups/cups.sock ] && break
    sleep 1
done

# Allow localhost printing without authentication
cupsctl --no-remote-admin --no-remote-any --no-share-printers 2>/dev/null || true

# Start Flask as the main process
exec python -m flask --app app run --host=0.0.0.0
