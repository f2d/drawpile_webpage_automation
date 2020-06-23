{
	print
}
match($0, /\{........-....-....-....-............\}|(\s|\/|\@)\w{26}(\s|\.|\:)/) {
	print >> sessions_logs_dir substr($0, RSTART+1, RLENGTH-2) ".log"
}
/(\{........-....-....-....-............\}|\b\w{26}):.+?(Closing.+?session|Last.+?user.+?left)/ {
	system(cmd_before "records" cmd_after)
}
/(\{........-....-....-....-............\}|\b\w{26}):.+?(Changed|Made|Tagged|preserve|(Left|Joined).+?session)|Starting.+?microhttpd.+?on.+?port/ {
	system(cmd_before "stats" cmd_after)
}