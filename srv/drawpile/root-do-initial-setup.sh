#!/bin/bash

drawpile_root_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )/"
source "${drawpile_root_dir}common-variables.sh"

add_group_and_user_if_not_yet()
{
	local group_name="${1?need a string}"
	local user_name="${2?need a string}"

	# https://superuser.com/a/336708
	if [ ! -z "$(getent group "${group_name}")" ]
	then
		echo "Group exists: ${group_name}"
	else
		echo "Group does not exist, adding now: ${group_name}"

		addgroup "${group_name}"
	fi

	if [ ! -z "$(getent passwd "${user_name}")" ]
	then
		echo "User exists: ${user_name}"
	else
		echo "User does not exist, adding now: ${user_name}"

		adduser --system --no-create-home --disabled-login --ingroup "${group_name}" "${user_name}"
	fi
}

drawpile_www_dir=${www_root_dir}${www_drawpile_subdir}

add_group_and_user_if_not_yet "${www_service_group_name}" "${www_service_user_name}"
add_group_and_user_if_not_yet "${drawpile_service_group_name}" "${drawpile_service_user_name}"

chown -R "${www_service_user_name}:${www_service_group_name}" "${drawpile_www_dir}"
chown -R "${drawpile_service_user_name}:${drawpile_service_group_name}" "${drawpile_root_dir}" "${update_log_dir}"

www_files_for_ssi=(
	"${www_filename_canonical}"
	"${www_filename_hostname}"
	"${www_filename_port}"
	"${www_filename_records}"
	"${www_filename_version}"
	"stats.en.htm"
	"stats.ru.htm"
	"users.txt"
)

if [ -d "${drawpile_www_dir}" ]
then
	if [ ! -d "${www_drawpile_records_subdir}" ]
	then
		sudo -u "${www_service_user_name}" ln -s "${public_archive_dir}" "${www_drawpile_records_subdir}"
	fi

	for filename in "${www_files_for_ssi[@]}"
	do
		if [ ! -f "${drawpile_www_dir}${filename}" ]
		then
			sudo -u "${www_service_user_name}" ln -s "${drawpile_root_dir}${filename}" "${drawpile_www_dir}${filename}"
		fi
	done
fi
