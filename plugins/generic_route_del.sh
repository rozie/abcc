#!/bin/bash

ROUTE=$1
GW=$2

/sbin/ip route del $ROUTE via $2
