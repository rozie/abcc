#!/bin/bash

ROUTE=$1
GW=$2

/sbin/ip route add $ROUTE via $2 2>/dev/null
