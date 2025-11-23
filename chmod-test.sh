#!/bin/bash

# Ensure the file exists before trying to change its permissions
echo "Creating ./test.txt (if it doesn't exist)..."
touch ./test.txt

# Run the chmod command once
echo "Setting permissions for ./test.txt to 600..."
chmod 600 ./test.txt

echo "Permissions set. Starting infinite loop... (Press Ctrl+C to stop)"

# Start the infinite loop
while true; do
    echo "Looping... script is alive at $(date)"
    sleep 5
done
