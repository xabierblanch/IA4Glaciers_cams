#!/bin/bash

# Esperar 45 minutos antes de ejecutar el resto del script
sleep 1

gpio -g mode 4 out
gpio -g write 4 0
