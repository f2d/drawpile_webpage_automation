#!/bin/bash

if [ -z ${start_date+x} ]
then
	start_date=$(date '+%F_%H-%M-%S.%N')
fi

if [ -z "${drawpile_root_dir}" ]
then
	drawpile_root_dir=/srv/drawpile/
fi

hostname=www.example.com

www_service_user_name=www-data
www_service_group_name=www-data

drawpile_service_user_name=drawpile
drawpile_service_group_name=drawpile

www_protocol=https://
www_root_dir=/srv/www/
www_drawpile_subdir=/drawpile/
www_drawpile_records_subdir=/drawpile/record/

www_filename_canonical=canonical.htm
www_filename_hostname=hostname.txt
www_filename_port=port.txt
www_filename_records=records.txt
www_filename_version=version.txt

client_port=9002
admin_port=9292

# cert_dir=/etc/letsencrypt/live/${hostname}/

public_archive_dir=${drawpile_root_dir}sessions/public_archive/
active_sessions_dir=${drawpile_root_dir}sessions/
session_templates_dir=${drawpile_root_dir}session_templates/

version_file_path=${drawpile_root_dir}version.txt
config_file_path=${drawpile_root_dir}config.ini
update_lock_dir=${drawpile_root_dir}
update_log_dir=${drawpile_root_dir}logs/

# update_log_dir=/var/log/drawpile/

cmd_name_drawpile_srv=drawpile-srv
cmd_name_awk=mawk
cmd_name_python=python3

tags_to_add_passworded_session_users_to_txt='[a], [anyway]'
