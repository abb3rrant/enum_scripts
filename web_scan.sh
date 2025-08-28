#!/bin/bash

read -p "Enter the network range to scan (e.g., 192.168.1.0/24): " NETWORK


if [ -z "$NETWORK" ]; then
  echo "No network range entered. Exiting."
  exit 1
fi

read -p "Enter the port to scan: " PORT


if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
  echo "Invalid port entered. Please enter a number between 1 and 65535."
  exit 1
fi

echo "Scanning for hosts with port $PORT open on $NETWORK..."
open_hosts=$(nmap -p "$PORT" --open --min-rate 1000 "$NETWORK" | grep 'Nmap scan report for' | awk '{print $5}')

if [ -z "$open_hosts" ]; then
  echo "No hosts with port $PORT open found."
  exit 1
else
  echo "$open_hosts:$PORT" >> web_hosts.txt
  echo "Hosts saved to web_hosts.txt."

  read -p "Do you want to open the found hosts in Firefox? (y/n): " OPEN_BROWSER

  if [[ "$OPEN_BROWSER" =~ ^[Yy]$ ]]; then
   
    PROTOCOL="http"
    if [ "$PORT" -eq 443 ]; then
      PROTOCOL="https"
    fi

    for host in $open_hosts; do
      echo "Opening $PROTOCOL://$host:$PORT in Firefox..."
      firefox "$PROTOCOL://$host:$PORT" &
    done

    echo "Done opening hosts with port $PORT open."
  else
    echo "Skipping opening hosts in Firefox."
  fi
fi
