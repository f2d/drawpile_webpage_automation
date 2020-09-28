#!/bin/bash

# Check paths: --------------------------------------------------------------

# https://stackoverflow.com/a/246128
# Getting the source directory of a Bash script from within:
# It will work as long as the last component of the path used to find the script is not a symlink (directory links are OK).

root_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )/"

source "${root_dir}common-variables.sh"

required_dirs_arr=(
	"${active_sessions_dir}"
	"${session_templates_dir}"
	"${update_lock_dir}"
	"${update_log_dir}"
)

for i in "${required_dirs_arr[@]}"
do
	if [ ! -d "$i" ]; then
		mkdir -p "$i"

		if [ ! -d "$i" ]; then
			echo "Directory not found and could not be created:"
			echo "$i"
			echo "Aborted."

			exit
		fi
	fi
done

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
	--config    "${root_dir}config.ini"
)

if [ -z "$cert_dir" ]; then
	cmd_ssl_cert=()
else
	cmd_ssl_cert=(
		--ssl-key  "${cert_dir}privkey.pem"
		--ssl-cert "${cert_dir}fullchain.pem"
	)
fi

# Save version info to file: ------------------------------------------------

${cmd_name_drawpile_srv} --version | ${cmd_name_awk} '/^drawpile/ {print $2}' > "${version_file_path}"

# Run server: ---------------------------------------------------------------

"${cmd_drawpile[@]}" \
"${cmd_ssl_cert[@]}" \
2>&1 \
| ${cmd_name_awk} \
-Winteractive \
-f "${root_dir}event-listener.awk" \
-v "sessions_logs_dir=${active_sessions_dir}" \
-v "cmd_before=\"${root_dir}update.sh\" --silent --wait --"
-v "cmd_after= &"
