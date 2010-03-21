#!/bin/sh
# Use to remove all pyc files from repository
find . -name "*.pyc" -exec rm '{}' ';'

# If somehow a pyc file was committed to the repository, then clean that up
# svn update
# find . -name "*.pyc" -exec svn rm '{}' ';'
