#!/bin/sh

nohup python consume.py --settings=settings_db_server &
nohup python process.py --settings=settings_db_server &

ps -ef | grep python | grep -v 'grep'
