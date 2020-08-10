#!/bin/bash

# usage: ./update-as-user.sh --stats etc

sudo -u drawpile nohup /srv/drawpile/update.sh "$@" &
