#!/bin/sh

NUMPROCESSES=`ps -ef | grep python | grep -v 'grep' | wc -l`

if [ $NUMPROCESSES -lt 2 ]
then
  # less than two processes running. restart!
  ps -ef | grep python | awk {'print $2'} | xargs kill
  echo "killed"
  sleep 10
  nohup python consume.py --settings=settings_db_server &
  nohup python process.py --settings=settings_db_server &
  echo "restarted"
else
  echo "still runnning ok"
  # two or more are running. we're A-OK!
fi
ps -ef | grep python | grep -v 'grep'