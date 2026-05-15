#!/bin/bash
cd /root/whatsapp-agent
docker exec whatsapp-agent-api-1 python -m app.scripts.post_meeting_tick >> /var/log/post_meeting.log 2>&1
