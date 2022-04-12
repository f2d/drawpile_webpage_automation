{
	print
}
match($0, /\{........-....-....-....-............\}|[^0-9a-z-][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][^0-9a-z-]/) {
	print >> sessions_logs_dir substr($0, RSTART+1, RLENGTH-2) ".log"
}
/(\{........-....-....-....-............\}|[^0-9a-z-][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z]):.+?(Closing.+?session|Last.+?user.+?left)/ {
	system(cmd_before "records '--reason=" $0 "'" cmd_after)
}
/(\{........-....-....-....-............\}|[^0-9a-z-][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z]):.+?(Changed|Made|Tagged|preserve|(Left|Joined).+?session)|Starting.+?microhttpd.+?on.+?port/ {
	system(cmd_before "stats '--reason=" $0 "'" cmd_after)
}