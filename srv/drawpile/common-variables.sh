#!/bin/bash

if [ -z ${start_date+x} ]; then
	start_date=$(date '+%F_%H-%M-%S.%N')
fi

if [ -z "${root_dir}" ]; then
	root_dir=/srv/drawpile/
fi

hostname=www.example.org
client_port=9002
admin_port=9292

# cert_dir=/etc/letsencrypt/live/${hostname}/

active_sessions_dir=${root_dir}sessions/
session_templates_dir=${root_dir}session_templates/

version_file_path=${root_dir}version.txt
update_lock_dir=${root_dir}
update_log_dir=/var/log/drawpile/

cmd_name_drawpile_srv=drawpile-srv
cmd_name_awk=mawk
cmd_name_python=python3

tags_to_add_passworded_session_users_to_txt='[a], [anyway]'
