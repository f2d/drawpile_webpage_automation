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

update_lock_dir=${root_dir}
update_log_dir=/var/log/drawpile/
