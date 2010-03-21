#!/bin/sh

ps -ef | grep python | awk {'print $2'} | xargs kill
echo "killed"
sleep 10
nohup python consume.py --settings=settings_db_server &
nohup python process.py --settings=settings_db_server &
echo "restarted"
ps -ef | grep python | grep -v 'grep'