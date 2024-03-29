#!/bin/bash

# Check command line arguments: ---------------------------------------------

# https://superuser.com/a/186279
# Idiomatic parameter and option handling in sh:

log_date=$(date '+%F')

while test $# -gt 0
do
	case "$1" in
		-w|--wait)		cmd_wait="wait = 3";;
		-q|--quiet|--silent)	cmd_silent="silent";;
		-ro|--readonly)		cmd_readonly="readonly";;
		-r|--records)		cmd_records="records";;
		-s|--stats)		cmd_stats="stats";;
		--reason=*)		cmd_reason="$1";;
		[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*)	log_date=$1;;
	esac
	shift
done

# Check paths: --------------------------------------------------------------

# https://stackoverflow.com/a/246128
# Getting the source directory of a Bash script from within:
# It will work as long as the last component of the path used to find the script is not a symlink (directory links are OK).

drawpile_root_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )/"
source "${drawpile_root_dir}common-variables.sh"

# Version-specific: ---------------------------------------------------------

if [ -f "${version_file_path}" ]
then

# https://stackoverflow.com/a/10771857

	running_version=$(<"${version_file_path}")
	target_version=2.1.14

# https://stackoverflow.com/a/16939706

	if [ "${target_version}" == "$(echo -ne "${target_version}\n${running_version}" |sort -V |head -n1)" ]
	then
		api_url_subdir=api/
	fi
fi

# Prepare command: ----------------------------------------------------------

# https://superuser.com/a/360986
# Use array for storing arguments:

run_update_cmd () {
	local cmd_task=$1
	local cmd_array=(
		"${cmd_name_python}"
		"${drawpile_root_dir}update.py"
		"$@"
		"${cmd_wait}"
		"${cmd_readonly}"
		"${cmd_reason}"
		"${update_lock_dir}update_${cmd_task}.lock"
		"${update_log_dir}update_${cmd_task}_${log_date}.log"
		"root = ${drawpile_root_dir}"
		"rec_src = ${active_sessions_dir}"
		"api_url_prefix = http://127.0.0.1:${admin_port}/${api_url_subdir}"
		"add_pwd_session_users = ${tags_to_add_passworded_session_users_to_txt}"
	)
	"${cmd_array[@]}"
}

# Run update: ---------------------------------------------------------------

if   [ -z "$cmd_reason"  ]; then cmd_reason="reason = manual_update"; fi
if   [ -z "$cmd_silent"  ]; then echo "Update started: ${start_date}"; fi
if ! [ -z "$cmd_stats"   ]; then echo "Update stats:";   run_update_cmd stats;   fi
if ! [ -z "$cmd_records" ]; then echo "Update records:"; run_update_cmd records; fi
if   [ -z "$cmd_silent"  ]; then echo "Update ended:   $(date '+%F_%H-%M-%S.%N')"; fi
