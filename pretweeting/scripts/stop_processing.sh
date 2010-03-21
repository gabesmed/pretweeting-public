#!/bin/sh

ps -ef | grep python | awk {'print $2'} | xargs kill
ps -ef | grep python | grep -v 'grep'