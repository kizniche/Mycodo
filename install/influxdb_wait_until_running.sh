#!/bin/bash
until nc -z localhost 8086; do sleep 1; done
