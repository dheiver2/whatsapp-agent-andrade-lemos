#!/bin/bash
# Reminder worker - 30 min antes da consulta
LOG=/var/log/whatsapp-reminder.log
docker exec whatsapp-agent-api-1 python -m app.scripts.reminder_tick >> $LOG 2>&1
