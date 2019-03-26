{
	print
}
match($0, /\{........-....-....-....-............\}/) {
	print >> sessions_logs_dir substr($0, RSTART+1, RLENGTH-2) ".log"
}
/\{........-....-....-....-............\}:.+?(Closing.+?session|Last.+?user.+?left)/ {
	system(cmd_before "records" cmd_after)
}
/\{........-....-....-....-............\}:.+?(Changed|Made|Tagged|preserve|(Left|Joined).+?session)|Starting.+?microhttpd.+?on.+?port/ {
	system(cmd_before "stats" cmd_after)
}