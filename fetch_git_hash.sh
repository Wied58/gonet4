#!/bin/bash
cd /home/pi/Tools/git_repo
VER=`git log --pretty=oneline | head -1 | awk '{print substr($1,1,5)}'`
rm -f /home/pi/Tools/Version/*
touch /home/pi/Tools/Version/$VER

