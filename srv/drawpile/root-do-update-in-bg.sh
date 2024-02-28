#!/bin/bash

# usage: ./root-do-update-in-bg.sh --stats --records etc

drawpile_root_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )/"
source "${drawpile_root_dir}common-variables.sh"

sudo -u "${drawpile_service_user_name}" nohup "${drawpile_root_dir}update.sh" "$@" &
