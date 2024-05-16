#!/bin/bash

# Writing to /proc/sys/kernel/sysrq file
echo "1" > /proc/sys/kernel/sysrq

# Writing to /proc/sysrq-trigger file
echo "s" > /proc/sysrq-trigger
echo "u" > /proc/sysrq-trigger
echo "b" > /proc/sysrq-trigger
