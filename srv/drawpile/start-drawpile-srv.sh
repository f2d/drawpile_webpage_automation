#!/bin/bash

# Check paths: --------------------------------------------------------------

# https://stackoverflow.com/a/246128
# Getting the source directory of a Bash script from within:
# It will work as long as the last component of the path used to find the script is not a symlink (directory links are OK).

drawpile_root_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )/"
source "${drawpile_root_dir}common-variables.sh"

required_dirs_arr=(
	"${active_sessions_dir}"
	"${session_templates_dir}"
	"${update_lock_dir}"
	"${update_log_dir}"
)

for i in "${required_dirs_arr[@]}"
do
	if [ ! -d "$i" ]
	then
		mkdir -p "$i"

		if [ ! -d "$i" ]
		then
			echo "Directory not found and could not be created:"
			echo "$i"
			echo "Aborted."

			exit 1
		fi
	fi
done

drawpile_server_version=$(${cmd_name_drawpile_srv} --version | ${cmd_name_awk} '/^drawpile/ {print $2}')

if [ -z "$drawpile_server_version" ]
then
	echo "Could not get Drawpile server version."
	echo "Aborted."

	exit 2
fi

# Use configured text parts: ------------------------------------------------

drawpile_www_dir="${www_root_dir}${www_drawpile_subdir}"
drawpile_page_link="${www_protocol}${hostname}${www_drawpile_subdir}"
drawpile_records_link="${www_protocol}${hostname}${www_drawpile_records_subdir}"

canonical_page_link_html="<link rel=\"canonical\" href=\"${drawpile_page_link}\">"
replace_welcome_message="s!(^|[\r\n])\b(welcomeMessage\b.*?recordings?)[: -]+[^ \r\n]*/!\1\2 - ${drawpile_records_link}!"

# Save configured text parts for web page includes: -------------------------

# https://stackoverflow.com/a/49418406
# Save variable to file without trailing newline:

printf "%s" "${canonical_page_link_html}"    > "${drawpile_root_dir}${www_filename_canonical}"
printf "%s" "${hostname}"                    > "${drawpile_root_dir}${www_filename_hostname}"
printf "%s" "${client_port}"                 > "${drawpile_root_dir}${www_filename_port}"
printf "%s" "${www_drawpile_records_subdir}" > "${drawpile_root_dir}${www_filename_records}"
printf "%s" "${drawpile_server_version}"     > "${drawpile_root_dir}${www_filename_version}"

# https://stackoverflow.com/a/2237103
# Version file path for scripts may be configured separately:

if [ "${version_file_path}" != "${drawpile_root_dir}${www_filename_version}" ]
then
	printf "%s" "${drawpile_server_version}" > "${version_file_path}"
fi

# Replace variable text parts in config: ------------------------------------

sed --in-place=.bak --regexp-extended "${replace_welcome_message}" "${config_file_path}"

# Prepare command: ----------------------------------------------------------

# https://superuser.com/a/360986
# Use array for storing arguments:

cmd_drawpile=(
	${cmd_name_drawpile_srv}
	--port           "${client_port}"
	--web-admin-port "${admin_port}"
	--local-host     "${hostname}"
	--record    "${active_sessions_dir}"
	--sessions  "${active_sessions_dir}"
	--templates "${session_templates_dir}"
	--config    "${config_file_path}"
)

if [ -z "$cert_dir" ]
then
	cmd_ssl_cert=()
else
	cmd_ssl_cert=(
		--ssl-key  "${cert_dir}privkey.pem"
		--ssl-cert "${cert_dir}fullchain.pem"
	)
fi

cmd_awk=(
	${cmd_name_awk}
	-Winteractive
	-f "${drawpile_root_dir}event-listener.awk"
	-v "sessions_logs_dir=${active_sessions_dir}"
	-v "cmd_before=\"${drawpile_root_dir}update.sh\" --silent --wait --"
	-v "cmd_after= &"
)

# Run server: ---------------------------------------------------------------

"${cmd_drawpile[@]}" "${cmd_ssl_cert[@]}" 2>&1 | "${cmd_awk[@]}"
