#!/usr/bin/bash
for VARIABLE in aurora_config.txt  custom.txt  dark_config.txt  meteor_config.txt  urban_config.txt
do
       for i in {1..50}
       do
          python3 gonet4.py $VARIABLE
       done
done


