#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import errno, io, json, os, re, shutil, ssl, string, subprocess, sys, time, traceback, urllib2

from datetime import datetime
from dateutil.parser import parse as datetime_text_to_object
from dateutil.tz import tzlocal
from PIL import Image, ImageChops

# - Common config: ------------------------------------------------------------

# self_path = os.path.realpath(__file__)

# Order of preference: cmd arg > ini? > default:
cfg_default = {
	'root': u'./'
,	'rec_src': 'sessions/'	# <- source, scanned not recursively
,	'rec_del': 'sessions/removed/'
,	'rec_end': 'sessions/closed/'
,	'rec_pub': 'sessions/public_archive/'

,	'sub_del': ''
,	'sub_end': 'Y-M/Y-M-D_H-N-S_I'
,	'sub_pub': 'Y-M'

# ,	'ini': 'updater.ini'
,	'txt':  'users.txt'
,	'html': 'stats.htm'
,	'lock': None
,	'log':  None

,	'new_dir_rights': {'min': 0, 'default': 0755, 'max': 0777}	# <- bit-mask
,	'rec_del_max':    {'min': 0, 'default': 9000}			# <- bytes
,	'path_len_max':   {'min': 1, 'default': 250}			# <- symbols
,	'thumb_w':        {'min': 1, 'default': 200}			# <- pixels
,	'thumb_h':        {'min': 1, 'default': 200}			# <- pixels
,	'sleep':          {'min': 0, 'default': 1}			# <- seconds, wait_after_pipe_task
,	'wait':           {'min': 0, 'default': 0}			# <- seconds, wait_before_single_task

,	'cmd_rec_stats':    'dprectool --acl --format text'		# not needed: -o /dev/stdout, -o CON, etc.
,	'cmd_rec_render':   'drawpile-cmd --acl --verbose --every-seq 1000 -platform offscreen'
,	'cmd_optimize_jpg': 'jpegoptim --all-progressive'		# 'jpegtran -progressive -optimize -outfile %s.out %s'
,	'cmd_optimize_png': 'optipng -i 0 -fix' 			# 'oxipng -i 0 --fix -t 1 %s'

,	'api_url_prefix': 'http://127.0.0.1:1234/'
# ,	'run_after_stats': 'http://127.0.0.1/drawpile/add_time.php'

,	'add_pwd_session_users': '[a], [anyway]'
}

def print_help():
	line_sep = '''
-------------------------------------------------------------------------------
'''
	print line_sep
	print ' - Usage:'
	print
	print '"%s" [<task>] [<option>] ["<option = value>"] [<option>] [...]' % __file__
	print line_sep
	print ' - <Task> is always first, required, may be any of:'
	print
	print 'r, records: Once, move archived sessions and their records into subdir by date.'
	print 's, stats: Once, rewrite stats in file(s), using actual data from server API.'
# TODO:	print 'c, cycle: Repeatedly check server API, run update on changes.'
	print 'p, pipe: Continuosly wait for input, line by line, looking for:'
	print '	Joined / Left session / Changed [session settings] => update stats'
	print '	Closing (...) session                              => update records'
	print 'h, help: Show this text.'
	print
	print '- Function as task, called once per every optional argument/file path:'
	print
	for i in tasks_as_function_name: print i
	print line_sep
	print ' - <Option> in any order, optional:'
	print
	print 'ro, readonly: Don\'t save or change anything, only show output, for testing.'
	print
	print '</path/to/file>.log:  Log file to print messages.  ', get_cfg_for_help('log')
	print '</path/to/file>.lock: Lock file to queue self runs.', get_cfg_for_help('lock')
	print '</path/to/file>.txt:  Save only CSV of usernames.  ', get_cfg_for_help('txt')
	print '</path/to/file>.html: Save HTML part for SSI.      ', get_cfg_for_help('html')
	print line_sep
	print ' - <Option = value> in any order, optional:'
	print
	print ', '.join(cfg_by_ext), '= </path/to/file>: Same as above options.'
	print
	print 'task = <task>: Override first task argument.'
	print 'run_after_<task> = <URL or command line>: Call after specified task finishes.'
	print
	print 'wait  = <number of seconds>: Pause before task in single mode.', get_cfg_for_help('wait')
	print 'sleep = <number of seconds>: Pause after task in pipe mode.   ', get_cfg_for_help('sleep')
	print
	print 'thumb_w = <number of pixels>: Thumbnail maximum width.        ', get_cfg_for_help('thumb_w')
	print 'thumb_h = <number of pixels>: Thumbnail maximum height.       ', get_cfg_for_help('thumb_h')
	print
	print 'path_len_max = <number of symbols>: Maximum dest. path length.', get_cfg_for_help('path_len_max')
	print
	print 'api_url_prefix = <http://server:port/path/>.', get_cfg_for_help('api_url_prefix')
	print
	print 'add_pwd_session_users = <CSV of substrings used in session names>:'
	print '	usernames from passworded sessions will not be saved into the txt file,'
	print '	unless its name contains one of these marks.'
	print '	Txt file is intended to be used by a chat bot to announce new users.'
	print '	', get_cfg_for_help('add_pwd_session_users')
	print
	print ' - Commands for processing (%s for subject filename, or it will be appended):'
	print
	print 'cmd_rec_stats      = <command line>.', get_cfg_for_help('cmd_rec_stats')
	print 'cmd_rec_render     = <command line>.', get_cfg_for_help('cmd_rec_render')
	print 'cmd_optimize_jpg   = <command line>.', get_cfg_for_help('cmd_optimize_jpg')
	print 'cmd_optimize_png   = <command line>.', get_cfg_for_help('cmd_optimize_png')
	print 'cmd_optimize_<ext> = <command line>.'
	print
	print ' - Source to process:'
	print
	print 'root    = </path/to/root/dir/>.          ', get_cfg_for_help('root')
	print 'rec_src = </path/to/active/sessions/>.   ', get_cfg_for_help('rec_src')
	print
	print ' - Destination to keep:'
	print
	print 'rec_end = </path/to/closed/sessions/>.   ', get_cfg_for_help('rec_end')
	print 'rec_pub = </path/to/public/web/archive/>.', get_cfg_for_help('rec_pub')
	print
	print ' - Destination to remove (no path = delete at once):'
	print
	print 'rec_del = </path/to/removed/sessions/>.  ', get_cfg_for_help('rec_del')
	print 'rec_del_max = <number of bytes>: Max record size to remove.', get_cfg_for_help('rec_del_max')
	print
	print ' - Destination subdirs (YMD/HNS/I = date/ID from filenames):'
	print
	print 'sub_del = <Y-M-D/HNS_I>.', get_cfg_for_help('sub_del')
	print 'sub_end = <Y-M-D/HNS_I>.', get_cfg_for_help('sub_end')
	print 'sub_pub = <Y/Y-M/Y-M-D>.', get_cfg_for_help('sub_pub')
	print
	print ' - Text encoding:'
	print
	print 'print_enc = <encoding name>. Default:', default_enc
	print 'path_enc  = <encoding name>. Default:', default_enc
	print 'file_enc  = <encoding name>. Default:', default_enc
	print 'log_enc   = <encoding name>. Default:', default_enc
	print 'web_enc   = <encoding name>. Default:', default_enc
	print line_sep
	print ' - Result (error) codes:'
	print
	print '0: All done, or cycle was interrupted by user.'
	print '1: Help shown.'
	print '2: Wrong arguments.'
	print '3: Cannot log.'
	print '4: Cannot lock.'
	print line_sep

# - Do not change: ------------------------------------------------------------

default_enc = print_enc = path_enc = file_enc = log_enc = web_enc = 'utf-8'

cfg_by_ext = ['lock', 'log', 'htm', 'html', 'txt']

# url2name = string.maketrans(r'":/|\?*<>', "';,,,&___")

safe_chars_as_ord = [
	[ord('0'), ord('9')]
,	[ord('A'), ord('Z')]
,	[ord('a'), ord('z')]
# ,	[ord(u'А'), ord(u'Я')]
# ,	[ord(u'а'), ord(u'я')]
] + map(ord, list('\';,.-_=+~` !@#$%^&()[]{}'))

unsafe_chars_as_ord = [
	[0, 31]
# ,	[127]
] + map(ord, list(r'\/:*?"<>|'))

lock_file = None
log_file = None
current_sessions = None

time_before_task = None
time_epoch_start = datetime_text_to_object('1970-01-01T00:00:00Z')

time_format_iso   = '%Y-%m-%dT%H:%M:%S%z'
time_format_print = '%Y-%m-%d %H:%M:%S%z'
time_format_print_log = '[' + time_format_print + '.%f]'
time_format_bak  = '.%Y-%m-%d_%H-%M-%S.%f.bak'
time_format_rec   = '%Y-%m-%dT%H-%M-%S%z'

pat_session_ID_part = r'(?P<SessionID>[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})'
pat_session_ID = re.compile(r'''^
	(?P<Before>.*?[^0-9a-f])?
	''' + pat_session_ID_part + '''
	(?P<After>[^0-9a-f].*)?
$''', re.I | re.X | re.DOTALL)

# Log[sample]: 2018-04-17T12:13:19Z Info/Join 2;::ffff:1.2.3.4;?????@{8315280b-6293-4d6f-83dd-00a484ee59c5}: Joined session
pat_time_from_log = re.compile(r'''^
	(?P<Before>[^\]]*\]:\s*)?
	(?P<DateTime>\d{4}(?:\D\d\d){5}\S*)
	\s+
	(?:
		(?:
			(?P<MessageLevel>\S+)
		/	(?P<MessageType>\S+)
		\s+
		)?

		(?:
			(?P<UserID>\d+)
		;	(?P<UserIP>[^;]+)
		;	(?P<UserName>.*?)
		@
		)?

		\{
			''' + pat_session_ID_part + '''
		\}:\s+
	)?
	(?P<After>.*?)
$''', re.I | re.X | re.DOTALL)

pat_time_from_text = re.compile(r'''^
	(?P<Before>.*?\D)?
	(?P<Date>
		(?P<Year>\d{4})
	\D	(?P<Month>\d\d)
	\D	(?P<Day>\d\d)
	)
	(?P<Between>
		\D+
	)
	(?P<Time>
		(?P<Hours>\d\d)
	\D	(?P<Minutes>\d\d)
	\D	(?P<Seconds>\d\d)
	)
	(?P<After>
		(
			\D.*?
			(?P<Epoch>\d{9,})
		)?
		\D.*
	)?
$''', re.X | re.DOTALL)

pat_time_to_text = r'\g<Year>-\g<Month>-\g<Day> \g<Hours>:\g<Minutes>:\g<Seconds>'
pat_time_to_html = (
	r'<time data-t="\g<Epoch>">'
+		r'\g<Date> '
+		r'<small>'
+			r'\g<Time>'
+		r'</small>'
+	r'</time>'
)
# pat_time_to_html = r'\g<Date> <small>\g<Time></small>'

pat_conseq_slashes   = re.compile(r'[\\/]+')
pat_conseq_spaces    = re.compile(r'\s+')
pat_conseq_spaces_un = re.compile(r'[_\s]+')
pat_cmd_line_arg     = re.compile(r'(?P<Arg>"([^"]|\")*"|\S+)(?P<After>\s+|$)')

session_closed_ext = '.archived'
session_cfg_ext    = '.session'
session_rec_ext    = '.dprec'
session_log_ext    = '.log'
session_meta_ext   = '.js'

session_meta_var_name = 'dprecMetaByID'

tasks_as_function_name = [
	'get_recording_stats_for_each_user'
,	'get_recording_screenshots_saved'
,	'get_recording_screenshots_with_thumbs'
]

# - Utility functions: --------------------------------------------------------

int_type = type(0)
arr_type = type([])
dic_type = type({})
fun_type = type(print_help)
reg_type = type(pat_conseq_spaces)
reg_match_type = type(re.search(pat_conseq_spaces, ' '))
str_type = type('')
uni_type = type(u'')

def is_type_int(v): return isinstance(v, int_type)
def is_type_arr(v): return isinstance(v, arr_type)
def is_type_dic(v): return isinstance(v, dic_type)
def is_type_fun(v): return isinstance(v, fun_type)
def is_type_reg(v): return isinstance(v, reg_type)
def is_type_reg_match(v): return isinstance(v, reg_match_type)
def is_type_str(v): return isinstance(v, str_type) or isinstance(v, uni_type)

def dump(obj, check_list=[]):
	r = ''
	for i in (check_list or dir(obj)):
		found = hasattr(obj, i) if check_list else True
		if found:
			v = getattr(obj, i)
			if v and (check_list or not callable(v)):
				r += 'obj.%s = %s\n' % (i, v)
	return r

def print_whats_wrong(err, title='Error:'):
	print get_time_stamp(), title or 'Error:'

	traceback.print_exc()

	try:
		print dump(err)
	except:
		try_print(err)

# https://stackoverflow.com/a/919684
def try_print(*list_args, **keyword_args):
	arr = []

	def try_append(v):
		try:
			arr.append(unicode(v))
		except:
			try:
				arr.append(str(v))
			except:
				arr.append(v)

	if list_args:
		for v in list_args:
			try_append(v)
	if keyword_args:
		for k, v in keyword_args.items():
			try_append(v)

	if not arr:
		print
	else:
		try:
			t = '\n'.join(arr)
		except:
			try:
				t = '\n'.join(map(lambda x: x.encode(print_enc), arr))
			except:
				t = '\n'.join(map(lambda x: x.decode(print_enc), arr))

		try:
			print get_time_stamp(), t
		except:
			try:
				print get_time_stamp(), t.encode(print_enc)
			except:
				try:
					print get_time_stamp(), t.decode(print_enc)
				except Exception, e:
					print get_time_stamp(), 'Error: unprintable text.'

					traceback.print_exc()

# https://stackoverflow.com/a/3314411
def get_obj_pretty_print(obj):
	try:
		d = obj.__dict__ if '__dict__' in obj else obj
		return json.dumps(d, sort_keys=True, indent=4, default=repr)

	except Exception, e:
		print_whats_wrong(e)

		return str(obj)

# https://stackoverflow.com/a/18126680
def get_file_mod_time(file_path):
	return datetime.fromtimestamp(os.path.getctime(file_path), tzlocal())

def get_time_stamp(format=time_format_print_log, before_task=False):
	global time_before_task

	t = datetime.now().replace(tzinfo=tzlocal())

	if before_task:
		time_before_task = t

	return t.strftime(format)

def get_time_html(format=time_format_print, content_type='html', lang='en'):
	if content_type == 'html':
		return fix_html_time_stamp(get_time_stamp(format))

	if content_type == 'txt':
		return get_time_stamp(format)

def datetime_to_utc_epoch(dt):
	return (dt - time_epoch_start).total_seconds()

def datetime_text_to_utc_epoch(t):
	p = datetime_text_to_object(t)
	i = datetime_to_utc_epoch(p)

	return i

def fix_html_time_stamp(t):
	u = datetime_text_to_utc_epoch(t)
	t += ' ' + str(u)

	return re.sub(pat_time_from_text, pat_time_to_html, t)

def fix_slashes(path):
	return re.sub(pat_conseq_slashes, '/', unicode(path))

def prepend_root_if_none(path):
	p = fix_slashes(path)
	o = p[ : 1]
	if o != '/' and o != '.' and p[1 : 3] != ':/':
		p = dir_root + '/' + p

	return fix_slashes(p)

def get_filename(path):
	i = path.rfind('/')
	if i >= 0: return path[i + 1 : ]

	return path

def get_file_ext(path, include_dot=False):
	i = path.rfind('/')
	if i >= 0: path = path[i + 1 : ]

	i = path.rfind('.')
	if i >= 0: path = path[(i if include_dot else i + 1) : ]

	return path.lower()

def get_lang(name):
	i = name.find('.')
	if i >= 0: name = name[ : i]

	return name.lower()

# https://gist.github.com/mattjmorrison/932345
def get_trimmed_image(im, border=None):

	def get_trimmed_image_bbox(border):
		bg = Image.new(im.mode, im.size, border)
		diff = ImageChops.difference(im, bg)
		return diff.getbbox()

	bbox = None

	if border:
		bbox = get_trimmed_image_bbox(border)
	else:
		sz = im.size
		x = sz[0] - 1
		y = sz[1] - 1

		bboxes = filter(None, map(lambda x: get_trimmed_image_bbox(im.getpixel(x)), [
			(0, 0)
		,	(x, 0)
		,	(0, y)
		,	(x, y)
		]))

		for i in bboxes:
			if bbox:
				if bbox[0] < i[0]: bbox[0] = i[0]
				if bbox[1] < i[1]: bbox[1] = i[1]
				if bbox[2] > i[2]: bbox[2] = i[2]
				if bbox[3] > i[3]: bbox[3] = i[3]
			else:
				bbox = list(i)

# http://pillow.readthedocs.io/en/3.1.x/reference/Image.html#PIL.Image.Image.getbbox
# The bounding box is returned as a 4-tuple defining the left, upper, right, and lower pixel coordinate.

	if bbox:
		return im.crop(bbox)

	return im

def replace_by_arr(text, arr):
	for r in arr:
		text = (
			r(text) if is_type_fun(r) else
			re.sub(r[0], r[1], text) if is_type_arr(r) else
			re.sub(r, '', text)
		)
	return text

# https://gist.github.com/carlsmith/b2e6ba538ca6f58689b4c18f46fef11c
def replace_key_to_value(text, substitutions):
	substrings = sorted(substitutions, key=len, reverse=True)
	regex = re.compile('|'.join(map(re.escape, substrings)))
	return regex.sub(lambda match: substitutions[match.group(0)], text)

def sanitize_filename(input_text, safe_only=False):
	result_text = ''

	for i in range(len(input_text)):
		c_i = input_text[i]

		try:
			o_i = ord(c_i)

			if safe_only:
				safe = False

				for j in safe_chars_as_ord:
					if (
						(o_i >= j[0] and o_i <= j[1])
						if is_type_arr(j) else
						o_i == j
					):
						safe = True
						break
			else:
				safe = True

				for j in unsafe_chars_as_ord:
					if (
						(o_i >= j[0] and o_i <= j[1])
						if is_type_arr(j) else
						o_i == j
					):
						safe = False
						break
		except:
			pass # - 2018-04-30 10:42 - I just want to sleep already.

		result_text += c_i if safe else '_'

	return result_text

def expand_task(task):
	if task in tasks_as_function_name:
		return task

	t = task[0] if task and is_type_str(task) else ''

	if (not t) or (t in '-/?h'):
		return 'help'

	if t == 'p': return 'pipe'
	if t == 'r': return 'records'
	if t == 's': return 'stats'

	return ''

def get_cfg_default(k):
	if k in cfg_default:
		v = cfg_default[k]

		if is_type_dic(v):
			v = int(v.get('default', 0))
	else:
		v = None

	return v

def get_cfg_for_help(k):
	v = get_cfg_default(k)

	return 'Default: %s' % (
		('"%s"' % v)
		if is_type_str(v) else
		str(v)
	)

def get_cfg_path_with_root(i, ext=None):
	v = cfg.get(i, '')
	if not v:
		if v == None:
			return v

		v = cfg.cfg_default(i, '')
		if not v:
			if v == None:
				return v

			v = (
				(cfg.get('root', '') or '.') + (
					(
						'/update.' + (
							ext if is_type_str(ext) else i
						).strip('.')
					) if ext else ''
				)
			)
	return prepend_root_if_none(v or '.')

def save_current_sessions(sessions_on_server=None):
	global current_sessions

	current_sessions = sessions_on_server

def is_user_included_in_txt(user_session_id=None):
	if (
		not current_sessions
	or	not user_session_id
	):
		return False

	marks = cfg.get('add_pwd_session_users') or []

	for s in current_sessions:
		session_id = s.get('id')
		if (
			not session_id
		or	session_id != user_session_id
		):
			continue

		passworded = s.get('hasPassword')
		if (
			passworded.lower() == 'false'
			if is_type_str(passworded) else
			not passworded
		):
			return True

		title = s.get('title', '').lower()
		if (
			not marks
		or	not title
		or	len(marks) == 0
		or	len(title) == 0
		):
			return False

		for mark in marks:
			if mark in title:
				return True

	return False

# - Check arguments: ----------------------------------------------------------

argc = len(sys.argv)

task = sys.argv[1] if argc > 1 else 'help'
options = sys.argv[2 : ] if argc > 2 else []

# - Check options: ------------------------------------------------------------

READ_ONLY = set(('readonly', 'ro')).intersection(options)
TEST      = set(('TEST'    , 'T' )).intersection(options)

cfg = {}

for k in cfg_default:
	cfg[k] = get_cfg_default(k)

for v in options:
	if v.find('=') > 0:
		k, v = v.split('=', 1)
		k = k.strip()
		v = v.strip()
	else:
		k = ''

	k_known = k and k in cfg_default

	if k_known:
		d = cfg_default[k]

		if is_type_dic(d):
			v = int(v)

			v_max = d.get('max')
			v_min = d.get('min')

			if is_type_int(v_max) and v > v_max: v = v_max
			if is_type_int(v_min) and v < v_min: v = v_min

		elif k == 'add_pwd_session_users':
			v = map(lambda x: x.strip().lower(), v.split(','))

		elif k != 'api_url_prefix':
			v = fix_slashes(v)

	elif not k:
		k_ext = get_file_ext(fix_slashes(v))

		if k_ext in cfg_by_ext:
			k = 'html' if k_ext == 'htm' else k_ext
	if k:
		cfg[k] = v

dir_root       = cfg['root']
new_dir_rights = cfg['new_dir_rights']

print_enc = cfg.get('print_enc', '') or default_enc
path_enc  = cfg.get('path_enc',  '') or default_enc
file_enc  = cfg.get('file_enc',  '') or default_enc
log_enc   = cfg.get('log_enc',   '') or default_enc
web_enc   = cfg.get('web_enc',   '') or default_enc

thumb_size = cfg['thumb_w'], cfg['thumb_h']

# - Open log: -----------------------------------------------------------------

log_path = cfg['log']

if log_path:
	log_path = prepend_root_if_none(log_path)
	log_file = open(log_path, 'a')

	if log_file:
		sys.stdout = sys.stderr = log_file
		print_enc = log_enc
	else:
		print get_time_stamp(), 'Error: cannot open log file:', log_path

		sys.exit(3)

# - Check task: ---------------------------------------------------------------

task = expand_task(cfg.get('task', task))

if task == 'help':
	print_help()

	sys.exit(1)

if not task:
	print get_time_stamp(), 'Error: wrong arguments:', sys.argv

	sys.exit(2)

# - Config for records: -------------------------------------------------------

if task == 'records' or task == 'pipe':

	# - to check if dirs exist:

	dirs_required = {
		'made': ['rec_src']
	,	'make': ['rec_end', 'rec_pub', 'rec_del']
	}

	for k, v in dirs_required.items():
		for i in v:
			cfg[i] = get_cfg_path_with_root(i)

	dir_active = cfg['rec_src']
	dir_closed = cfg['rec_end']
	dir_public = cfg['rec_pub']
	dir_removed = cfg['rec_del']

	# - to get from record filenames:

	pat_get_date = re.compile(r'''
		(?:^|\D)
			(?P<Year>\d{4})
		[._-]	(?P<Month>\d\d)
		[._-]	(?P<Day>\d\d)
		[,T\s._-]	(?P<Hours>\d\d)
		[,;'._-]	(?P<Minutes>\d\d)
		[,;'._-]	(?P<Seconds>\d\d)
		(?:\b|Z)
	''', re.X)

	pat_subdir_replace = {
		'I': 'ID'
	,	'Y': 'Year'
	,	'M': 'Month'
	,	'D': 'Day'
	,	'H': 'Hours'
	,	'N': 'Minutes'
	,	'S': 'Seconds'
	}

# - Config for stats: ---------------------------------------------------------

if task == 'stats' or task == 'pipe':

	stats_output = ['txt', 'html']
	stats_output_path = {}

	for i in stats_output:
		stats_output_path[i] = get_cfg_path_with_root(i, ext=True)

	data_sources = ['users', 'sessions']
	html_langs = ['en', 'ru']

	headers = {}
	timeout = 30
	ssl_context = None

	block_start = '<i class="blue">'
	block_end = '</i>'
	indent_block = '\n\t\t\t'
	indent_inline = indent_block + '\t'
	indent_newline = indent_inline + '<br><br>'
	indent_param = indent_inline + '- '

	unformatted_var_separator = ' - '

	replace_before_html = [
		['<', '&lt;']
	,	['>', '&gt;']
	]
	replace_whitespace = [
		[re.compile(r'\s+'), ' ']
	]

	output_format = [
		{
			'input': [
				{
					'from_api': 'sessions'
				,	'run_with_data': save_current_sessions
				,	'get_vars': [
						{
							'id': 'startTime'
						,	'replace': [
							#	[re.compile(r'[^\d:-]+'), ' ']
								fix_html_time_stamp
							]
						}
					,	{
							'get_by_id': 'nsfm'
						,	'put_by_id': 'nsfm'
						,	'replace': [
								[re.compile('^.*false.*$', re.I), '(0+)']
							,	[re.compile('^.*true.*$', re.I), '(18+)']
							]
						}
					,	'title', 'founder', 'userCount', 'maxUserCount'
					]
				}
			]
		,	'output': ['html']
		,	'output_title': {
				'en': u'Active sessions'
			,	'ru': u'Активные сессии'
			}
		,	'output_entry_format': {
				'en': indent_param.join([
					(
						indent_inline + u'<span title="title">"$title"</span>'
					+	indent_inline + u'<span title="minimal user age requirement">$nsfm</span>'
					)
				,	u'<span title="started by">$founder</span>'
				,	u'<span title="users">$userCount/$maxUserCount</span>'
				,	u'<span title="start time">$startTime</span>'
				])
			,	'ru': indent_param.join([
					(
						indent_inline + u'<span title="название">"$title"</span>'
					+	indent_inline + u'<span title="минимальный возраст для участия">$nsfm</span>'
					)
				,	u'<span title="кто начал">$founder</span>'
				,	u'<span title="участники">$userCount/$maxUserCount</span>'
				,	u'<span title="время начала">$startTime</span>'
				])
			}
		,	'output_entry_separator': indent_newline
		}
	,	{
			'input': [
				{
					'from_api': 'users'
				,	'skip_if_empty': ['session']
				,	'get_vars': [
						{
							'id': 'name'
						,	'replace_before_html': replace_before_html
						,	'replace': replace_whitespace
						}
					]
				}
			]
		,	'output': ['html']
		,	'output_title': {
				'en': u'Users'
			,	'ru': u'Участники'
			}
		,	'output_entry_separator': ', '
		}
	,	{
			'input': [
				{
					'from_api': 'users'
				,	'skip_if_empty': [
						'session'
					,	{
							'function': is_user_included_in_txt
						,	'data_id': 'session'
						}
					]
				,	'get_vars': [
						{
							'id': 'name'
						,	'replace': replace_whitespace
						}
					]
				}
			]
		,	'output': ['txt']
		,	'output_entry_separator': '\n'
		}
	,	{
			'input': get_time_html
		,	'output': ['html']
		,	'output_title': {
				'en': u'Last updated'
			,	'ru': u'Обновлено'
			}
		}
	]

# - Common functions: ---------------------------------------------------------

# - Lock file to prevent concurrent task run and log writes:
def lock_on():
	global lock_file

	lock_path = cfg['lock']

	if not lock_path:
		return

	lock_path = prepend_root_if_none(lock_path)
	lock_file = open(lock_path, 'a')

	if lock_file:
		sleep_time = 0

		# http://tilde.town/~cristo/file-locking-in-python.html
		import fcntl

		while True:
			try:
				fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
				break

			except IOError as e:
				# - raise on unrelated IOErrors:
				if e.errno != errno.EAGAIN:
					raise
				else:
					if   sleep_time <  1: sleep_time += 0.1
					elif sleep_time < 10: sleep_time += 1
					time.sleep(sleep_time)
	else:
		print get_time_stamp(), 'Error: cannot open lock file:', lock_path
		sys.exit(4)

def lock_off():
	global lock_file

	if lock_file:
		lock_file.close()

def get_dict_from_matches(key_to_name, *list_args):
	key_to_value = {}

	for target_key, arg_key in key_to_name.items():
		match = None

		for arg in list_args:
			if is_type_reg_match(arg):
				try:
					match = arg.group(arg_key)
				except IndexError:
					pass

			elif is_type_dic(arg):
				if arg_key in arg:
					match = arg[arg_key]

			if match:
				break

		if match:
			key_to_value[target_key] = match

	return key_to_value

def get_subdir_from_matches(cfg_key, key_to_value):
	path = cfg.get(cfg_key, '')

	if path:
		path = replace_key_to_value(path, key_to_value)

	return fix_slashes(path)

def read_file(path, mode='rb'):
	binary = 'b' in mode

	f = open(path, mode) if binary else io.open(path, mode, encoding=file_enc)
	content = f.read()
	f.close()

	return content

def write_file(path, conts, mode='a+b'):
	if READ_ONLY:
		return READ_ONLY

	for f in ['lower', 'real']:
		if hasattr(conts, f):
			conts = [conts]
			break

	path = fix_slashes(path)
	binary = 'b' in mode

	written = False
	retry = True
	f = None

	while retry:
		try:
			f = open(path, mode) if binary else io.open(path, mode, encoding=file_enc)
			retry = False
		except Exception, e:
			print_whats_wrong(e, 'Error: cannot open file for writing.')

			try:
				print get_time_stamp(), 'Let\'s try to move it away.'

				os.rename(path, path + get_time_stamp(time_format_bak))

				print get_time_stamp(), 'Done.'
			except Exception, e:
				print_whats_wrong(e, 'Error: cannot rename pre-existing file.')

				retry = False
	if f:
		for content in conts:
			try:
				written = f.write(content if binary else unicode(content))
			except:
				try:
					k = dump(content, ['__class__', '__doc__', 'args', 'message'])
					written = f.write(k or dump(content))
				except:
					print_whats_wrong(e, 'Error: cannot write content to file.')
		f.close()

	return written

def rewrite_file(path, conts, mode='w+b'):
	return write_file(path, conts, mode)

def save_files(path, content, suffix_before_ext=True):
	if is_type_arr(content) or is_type_dic(content):
		if suffix_before_ext:
			ext = get_file_ext(path, include_dot=True)
			path = path[0 : -len(ext)] + '.'
		else:
			ext = ''
			path = path + '.'

		for k, v in (
			enumerate(content) if is_type_arr(content) else
			content.items()
		):
			save_files(path + k + ext, v)

	else:
		if READ_ONLY:
			print get_time_stamp()
			print 'File path to save:', path
			print 'File content to save =', len(content), 'bytes:'

			try_print(content or 'None')
		else:
			print get_time_stamp(), 'Saving file:', path, '=', len(content), 'bytes'
			rewrite_file(path, content, 'w')

def fetch_url(url):
	print get_time_stamp(), 'Request URL:', url

	if url.find('https://') == 0:
		if not ssl_context:
			# - skip some insignificant SSL checks:
			# http://stackoverflow.com/questions/19268548/python-ignore-certicate-validation-urllib2
			ssl_context = ssl.create_default_context()
			ssl_context.check_hostname = False
			ssl_context.verify_mode = ssl.CERT_NONE
		context = ssl_context
	else:
		context = None

	request = urllib2.Request(url, headers=headers) if headers else url
	response = urllib2.urlopen(request, timeout=timeout, context=context)

	print get_time_stamp(), 'Request finished.'
	info = response.info()
	print get_time_stamp(), 'Response info:', info
	content = response.read()
	print get_time_stamp(), 'Response content:', content

	response.close()

	return {
		'info': info
	,	'content': content
	}

def check_and_move(src_path, dest_path):
	src_path = fix_slashes(src_path)
	dest_path = fix_slashes(dest_path)

	print

	if os.path.isdir(dest_path.encode(path_enc)):
		try_print('Error: destination path is an existing folder:', dest_path)
	elif os.path.isfile(dest_path.encode(path_enc)):
		try_print('Error: destination path is an existing file:', dest_path)
	elif os.path.isfile(src_path.encode(path_enc)):
		try_print('Move from:', src_path, 'To:', dest_path)

		if dest_path.find('/') < 0:
			dest_dir = '.'
		else:
			dest_dir = dest_path.rsplit('/', 1)[0]

			if not os.path.exists(dest_dir.encode(path_enc)):
				try_print('Make folders with rights %#03o:' % new_dir_rights, dest_dir)

				if not READ_ONLY:
					os.makedirs(dest_dir.encode(path_enc), new_dir_rights)

		if not READ_ONLY:
			if os.path.isdir(dest_dir.encode(path_enc)):
				os.rename(src_path.encode(path_enc), dest_path.encode(path_enc))
			else:
				try_print('Error: destination path was not created:', dest_dir)

	# os.rename(src, dst):
	# Rename the file or directory src to dst. If dst is a directory, OSError will be raised. On Unix, if dst exists and is a file, it will be replaced silently if the user has permission. The operation may fail on some Unix flavors if src and dst are on different filesystems. If successful, the renaming will be an atomic operation (this is a POSIX requirement). On Windows, if dst already exists, OSError will be raised even if it is a file; there may be no way to implement an atomic rename when dst names an existing file.

def get_cmd_with_path(cmd_line, subject=''):
	arr = []
	placeholder = '%s'
	found_subject = False

	for match in re.finditer(pat_cmd_line_arg, cmd_line):
		arg = match.group('Arg')

		if arg[0] == '"':
			arg = arg[1 : -1]

		if arg.find(placeholder) >= 0:
			arg = arg.replace(placeholder, subject)

			found_subject = True

		arr.append(arg)

	if not found_subject:
		arr.append(subject)

	exe_full_path = prepend_root_if_none(arr[0])

	if os.path.isfile(exe_full_path):
		arr[0] = exe_full_path

	return map(fix_slashes, arr)

def get_and_print_cmd_result(
	cmd_line
,	filename=''
,	title=''
,	pipe_line_handler_function=None
,	print_cmd_output=True
,	return_cmd_output=True
):
	print get_time_stamp(), 'Run command%s%s:' % (
		(' as PIPE' if pipe_line_handler_function else '')
	,	((' - ' + title) if title else '')
	)

	cmd = get_cmd_with_path(cmd_line, filename)
	print cmd

	cmd_result = ''

	try:
		if '|' in cmd:

			# - Not needed, not tested, not sure if works:

			cmd = ' '.join([
				(
					x
					if x.find(' ') < 0 or x == '|' or x[0] == '>' or x[1] == '>' else
					('"%s"' % x)
				) for x in cmd
			])

			if return_cmd_output:
				cmd_result += subprocess.check_output(cmd, shell=True)
			else:
				subprocess.check_call(cmd, shell=True)

			# - TODO, maybe (still not needed):

			# p1 = subprocess.Popen(['command_1', 'args'], stdout=subprocess.PIPE)
			# p2 = subprocess.Popen(['command_2', 'args'], stdout=subprocess.PIPE, stdin=p1.stdout)
			# p1.stdout.close()
			# p3 = subprocess.Popen(['command_3', 'args'], stdout=subprocess.PIPE, stdin=p2.stdout)
			# p2.stdout.close()
			# output = p3.communicate()[0]

		elif pipe_line_handler_function:

			running_process = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

			while True:
				line = running_process.stdout.readline()

				if line == b'':
					break

				if print_cmd_output:
					print line.rstrip()

				if return_cmd_output:
					cmd_result += line

				pipe_line_handler_function(line)

		elif return_cmd_output:
			cmd_result += subprocess.check_output(cmd, stderr=subprocess.STDOUT)
		else:
			subprocess.check_call(cmd, stderr=subprocess.STDOUT)

	except subprocess.CalledProcessError, e:

		print get_time_stamp(), 'Command returned code:', e.returncode

		if print_cmd_output or return_cmd_output:
			cmd_result += e.output

	if print_cmd_output and not pipe_line_handler_function:
		print get_time_stamp(), 'Command result:'
		print cmd_result

	return cmd_result if return_cmd_output else None

# - Task-specific functions: --------------------------------------------------

def get_recording_stats_for_each_user(
	source_rec_file_path
,	users_by_ID=None
):
	global rec_stats_multiline

	pat_username = re.compile(r'^(?P<ID>\d+)\s+(?:\S+\s+)*name=(?P<Name>[^\r\n]*)', re.I | re.DOTALL)
	pat_stroke = re.compile(r'^(?P<ID>\d+)\s+penup', re.I | re.DOTALL)

	if users_by_ID:
		for i, v in users_by_ID.items():
			if not 'name' in v:
				v['name'] = '#' + i
			if not 'strokes' in v:
				v['strokes'] = 0
	else:
		users_by_ID = {}

	rec_stats_multiline = ''

	# - Find usernames by ID and their stroke counts:

	def run_for_each_line(line):
		global rec_stats_multiline

		try:
			line = unicode(line.decode(file_enc))
		except:
			pass

		line = line.strip()

		if rec_stats_multiline or line[-1 : ] == '{':

			if line == '}':
				line = rec_stats_multiline + line
				rec_stats_multiline = ''
			else:
				rec_stats_multiline += line + '\n'

				return

		r_u = re.search(pat_username, line)
		r_s = re.search(pat_stroke, line) if not r_u else None
		res = r_u or r_s

		if res:
			i = res.group('ID')
			known = (i in users_by_ID)
			v = users_by_ID[i] if known else {
				'name': '#' + i
			,	'strokes': 0
			}

			if r_u:
				name = res.group('Name').strip()

				if len(name) > 0:
					v['name'] = name

			elif r_s:
				v['strokes'] += 1

			if not known:
				users_by_ID[i] = v

	get_and_print_cmd_result(
		cfg['cmd_rec_stats']
	,	source_rec_file_path
	,	'get recording stats'
	,	run_for_each_line
	,	print_cmd_output=False	# <- to keep output/logs cleaner
	,	return_cmd_output=False	# <- to use less memory uselessly
	)

	if rec_stats_multiline:
		run_for_each_line('}')

	return users_by_ID

def get_recording_stats_for_each_username(users_by_ID):
	users_by_name = {}

	for k, v in users_by_ID.items():
		try:
			user_name = v['name']
			strokes_count = v['strokes']

			if strokes_count > 0:
				user_name = re.sub(pat_conseq_spaces_un, '_', user_name.strip())

				if user_name in users_by_name:
					users_by_name[user_name] += strokes_count
				else:
					users_by_name[user_name] = strokes_count

		except Exception, e:
			print_whats_wrong(e)

	print get_time_stamp(), 'User strokes count by name:', get_obj_pretty_print(users_by_name)

	return users_by_name

def get_recording_usernames_with_stats(users_by_name):
	users_by_name_with_stats = {}

	for k, v in users_by_name.items():
		users_by_name_with_stats['%s %d' % (k, v)] = v

	return users_by_name_with_stats

def get_recording_screenshots_saved(source_rec_file_path):
	img_paths = []

	if READ_ONLY:
		return img_paths

	# - Get path markers to look for:

	res = re.search(pat_session_ID, source_rec_file_path)
	if res:
		source_prefix = res.group('Before') + res.group('SessionID')
	else:
		s = source_rec_file_path

		while len(s):
			source_prefix = s

			slash_pos = s.rfind('/')
			dash_pos = s.rfind('-')
			dot_pos = s.rfind('.')

			if slash_pos >= dot_pos or dash_pos >= dot_pos:
				break

			elif dot_pos > 0:
				s = s[ : dot_pos]

	s = ' Writing '

	path_prefix = [
		[s, len(s)]
	,	source_prefix
	]

	# - Save image files:

	def run_for_each_line(line):
		for i in path_prefix:
			prefix, offset = i if is_type_arr(i) else (i, 0)

			pos = line.find(prefix)
			if pos >= 0:
				img_path = line[pos + offset : ].rstrip().rstrip('.')
				img_paths.append(img_path)

				return

	get_and_print_cmd_result(
		cfg['cmd_rec_render']
	,	source_rec_file_path
	,	'save screenshots + thumbs'
	,	run_for_each_line
	,	return_cmd_output=False
	)

	return get_recording_screenshots_with_thumbs(img_paths)

def get_recording_screenshots_with_thumbs(img_paths):
	to_move = []

	if not is_type_arr(img_paths):
		img_paths = [img_paths]

	for img_path in img_paths:
		print 'Resizing image:', img_path

		try:
			img_filename = get_filename(img_path)
			img_folder = img_path[ : -len(img_filename)]
			img_ext = get_file_ext(img_filename, include_dot=True)
			img_basename = img_filename[ : -len(img_ext)]
			res_filename = img_basename + '_resized' + img_ext

			img = Image.open(img_path)
			size = 'x'.join(map(str, img.size))

			print 'Full size:', size

			to_move.append([
				img_filename
			,	img_basename + '_full_' + size + img_ext
			])

			thumb = get_trimmed_image(img)

			try: img.close()
			except: pass

			thumb.thumbnail(thumb_size, Image.ANTIALIAS) # <- best for downscaling
			size = 'x'.join(map(str, thumb.size))

			print 'Thumb size:', size

			to_move.append([
				res_filename
			,	img_basename + '_thumb_' + size + img_ext
			])

			thumb.save(img_folder + res_filename, quality=95)

			try: thumb.close()
			except: pass

			ext = img_ext.strip('.').replace('jpeg', 'jpg')
			cmd = cfg.get('cmd_optimize_' + ext, '')

			if cmd:
				for filename in [img_filename, res_filename]:
					get_and_print_cmd_result(
						cmd
					,	img_folder + filename
					,	'optimize image'
					)

		except Exception, e:
			print_whats_wrong(e)

	return to_move

def process_archived_session(session_ID, src_files):
	all_files_to_move     = []
	cfg_files_to_read     = []
	log_files_to_read     = []
	rec_files_to_copy_one = []

	time_started = time_closed = date_match = None
	to_keep = False

	# - Find files to move away:

	for filename in src_files:
		if filename.find(session_ID) >= 0:
			# ext = get_file_ext(filename, include_dot=True)

			if not date_match:
				date_match = re.search(pat_get_date, filename)

			if   filename.find(session_rec_ext) > 0: rec_files_to_copy_one.append(filename)
			elif filename.find(session_cfg_ext) > 0: cfg_files_to_read.append(filename)
			elif filename.find(session_log_ext) > 0: log_files_to_read.append(filename)

			all_files_to_move.append(filename)

	# - Find best session recording to copy:

	max_size_found = 0
	selected_rec_file_path = source_rec_file_path = None

	for filename in rec_files_to_copy_one:
		rec_file_path = fix_slashes(dir_active + '/' + filename)

		if os.path.isfile(rec_file_path):
			sz = os.path.getsize(rec_file_path)

			print get_time_stamp(), 'Found rec file,', sz, 'bytes:', rec_file_path

			if max_size_found < sz:
				max_size_found = sz
				selected_rec_file_path = rec_file_path

	# - Find session flags from cfg:

	session_flags = []

	for filename in cfg_files_to_read:
		file_path = fix_slashes(dir_active + '/' + filename)

		if os.path.isfile(file_path):
			sz = os.path.getsize(file_path)

			print get_time_stamp(), 'Reading config file:,', sz, 'bytes:', file_path

			with open(file_path, 'rU') as f:
				for line in f:
					words = line.strip().split(' ')

					if words[0] == 'FLAGS':
						session_flags = words[1 : ]	# <- overwrite previously found set

	if len(session_flags) > 0:
			print get_time_stamp(), 'Found session flags:', session_flags

	# - Find session start/end time + usernames from log:

	users_by_ID_from_log = {}

	for filename in log_files_to_read:
		file_path = fix_slashes(dir_active + '/' + filename)

		if os.path.isfile(file_path):
			sz = os.path.getsize(file_path)

			print get_time_stamp(), 'Reading log file:,', sz, 'bytes:', file_path

			with open(file_path, 'rU') as f:
				for line in f:
					# if READ_ONLY: try_print(line.rstrip())

					res = re.search(pat_time_from_log, line)
					if res:
						t = res.group('DateTime')
						t = datetime_text_to_object(t).strftime(time_format_rec).replace('+0000', 'Z')

						if not time_started:
							time_started = t

							if not date_match:
								date_match = re.search(pat_get_date, t)

						if not time_closed or time_closed < t:
							time_closed = t

						i = res.group('UserID')
						n = res.group('UserName')

						if (
							i != None
						and	n != None
						and	not i in users_by_ID_from_log
						):
							users_by_ID_from_log[i] = {'name': n}

						if len(session_flags) == 0:
							s = res.group('After')

							if s.find(' NSF') >= 0:
								session_flags.append('nsfm')

			print get_time_stamp(), 'Users found in log:', get_obj_pretty_print(users_by_ID_from_log)

	# - Set destination path subfolders:

	d = get_dict_from_matches(pat_subdir_replace, date_match, {'ID': session_ID})

	subdir_del = get_subdir_from_matches('sub_del', d)
	subdir_end = get_subdir_from_matches('sub_end', d)
	subdir_pub = get_subdir_from_matches('sub_pub', d)

	# - Check if session is good to keep:

	if selected_rec_file_path:
		sz = os.path.getsize(selected_rec_file_path)

		if sz > cfg['rec_del_max']:
			to_keep = True

		source_rec_filename = session_ID + session_rec_ext + '.temp_copy'
		source_rec_file_path = fix_slashes(dir_active + '/' + source_rec_filename)

		if READ_ONLY:
			source_rec_file_path = selected_rec_file_path
		elif to_keep:
			shutil.copy2(selected_rec_file_path, source_rec_file_path)

	# - Process session to put into archive:

	if to_keep and source_rec_file_path and os.path.isfile(source_rec_file_path):

		public_files_to_move = []

	# - Find usernames in recording, sort by stroke count, most to least:

		user_stats_by_ID = get_recording_stats_for_each_user(source_rec_file_path, users_by_ID_from_log)
		user_stats_by_name = get_recording_stats_for_each_username(user_stats_by_ID)
		user_stats_by_name_with_stats = get_recording_usernames_with_stats(user_stats_by_name)
		usernames_list = sorted(
			user_stats_by_name_with_stats
		,	key=user_stats_by_name_with_stats.get
		,	reverse=True
		)
		usernames_count = len(usernames_list)
		strokes_count = sum(user_stats_by_name.itervalues())

		if not usernames_list:
			usernames_list = 'none'

	# - Save screenshots + thumbs:

		public_files_to_move += get_recording_screenshots_saved(source_rec_file_path)

	# - Move session recording to public folder:

		max_len = cfg['path_len_max']
		dir_len = len(dir_active)
		shortened = False

		parts = filter(None, [
			time_started
		,	time_closed
		,	'r18' if 'nsfm' in session_flags else None
		,	(str(  strokes_count) + 's') if   strokes_count else None
		,	(str(usernames_count) + 'u') if usernames_count else None
		])

		stats = ' - '.join(parts)

		while usernames_count > 0 and len(usernames_list) > 0:
			parts = filter(None, [
				stats
			,	', '.join(sorted(set(usernames_list), key=string.lower)) # <- https://stackoverflow.com/a/10269708
			,	session_ID + session_rec_ext
			])

			if READ_ONLY:
				print 'File name parts:', get_obj_pretty_print(parts)

			j = ' - '.join(parts)

			try:
				public_rec_filename = sanitize_filename(j)
			except:
				public_rec_filename = sanitize_filename(j, safe_only=True)

			path_len = dir_len + len(public_rec_filename)

			if path_len > max_len:
				print 'Path too long:', path_len, '>', max_len

				usernames_list.pop()

				shortened = True
			else:
				break

		if shortened:
			public_meta_filename = session_ID + session_meta_ext
			content = (
				session_meta_var_name + '["'
			+		session_ID
			+	'"] = '
			+		json.dumps(user_stats_by_name, sort_keys=True, indent=0, separators=(',', ': '), default=repr)
			+	';'
			)

			if READ_ONLY:
				print 'Public metadata file content:', content
			else:
				save_files(dir_active + '/' + public_meta_filename, content)

			public_files_to_move.append(public_meta_filename)

		if READ_ONLY:
			print 'File name joined:', get_obj_pretty_print(public_rec_filename)

		public_files_to_move.append([
			source_rec_filename
		,	public_rec_filename
		])

	# - Move saved files to public folder:

		for filename in public_files_to_move:
			if is_type_arr(filename):
				src, dest = filename
			else:
				src = dest = filename

			check_and_move(
				dir_active + '/' + src
			,	dir_public + '/' + subdir_pub + '/' + dest.replace('.jpeg', '.jpg')
			)

	# - Move away all found files:

	a = dir_active + '/'
	b = None

	if to_keep:
		b = dir_closed + '/' + subdir_end + '/'
	else:
		if len(dir_removed):
			b = dir_removed + '/' + subdir_del + '/'

	for filename in all_files_to_move:
		f = a + filename

		if b == None:
			try_print('Small session, remove file:', f)

			if not READ_ONLY:
				os.remove(f)
		else:
			check_and_move(f, b + filename)

	# - END process_archived_session

def do_task_records():

	# - Check if all dirs exist or can be created first:

	for k, dirs_array in dirs_required.items():
		for d in dirs_array:
			d = get_cfg_path_with_root(d)

			if not os.path.isdir(d):
				if k == 'make':
					if not READ_ONLY:
						os.makedirs(d, new_dir_rights)

						if not os.path.isdir(d):
							try_print('Error: cannot create folder:', d)

							return 3
					else:
						try_print('Warning: folder does not exist:', d)
				else:
					try_print('Error: required folder does not exist:', d)

					return 2

	# - Move away all files of closed sessions, make files for public archive:

	IDs_done = []
	src_files = os.listdir(dir_active)

	for filename in src_files:
		try:
			ext = get_file_ext(filename, include_dot=True)
			if ext == session_closed_ext:
				res = re.search(pat_session_ID, filename)
				if res:
					session_ID = res.group('SessionID')
					if session_ID in IDs_done:
						continue

					IDs_done.append(session_ID)

					process_archived_session(session_ID, src_files)

		except Exception, e:
			print_whats_wrong(e)

	# - END do_task_records

def do_task_stats():

	# - Query server JSON API to collect data:

	data = {}

	for i in data_sources:
		try:
			url = cfg['api_url_prefix'] + i

			response = fetch_url(url)
			content = response['content']

			obj = json.loads(content, encoding=web_enc)

			print get_time_stamp(), 'Data object:', get_obj_pretty_print(obj)

			data[i] = obj

		except Exception, e:
			print_whats_wrong(e)

			continue

	# - Compile content to save:

	output = {}

	for o in output_format:
		format = o.get('output_entry_format')

		o_i = o.get('input', [])
		o_o = o.get('output', [])

		output_entries = {}

		if is_type_fun(o_i):
			for lang in html_langs:
				for ext in o_o:
					k = (lang + '.' + ext) if ext == 'html' else ext
					output_entries[k] = o_i(content_type=ext, lang=lang)

		elif is_type_arr(o_i):
			for lang in html_langs:
				for ext in o_o:
					k = (lang + '.' + ext) if ext == 'html' else ext
					output_entries[k] = []

			for j in o_i:
				from_api = j.get('from_api')
				if (
					not from_api
				or	not from_api in data
				):
					continue

				data_from_api = data[from_api]
				if not data_from_api:
					continue

				f = j.get('run_with_data')
				if f:
					f(data_from_api)

				get_vars = j.get('get_vars')
				if not get_vars:
					continue

				skip_list = j.get('skip_if_empty', [])

				for d in data_from_api:
					skip = False

					for k in skip_list:
						if is_type_dic(k):
							f = k.get('function')
							g = k.get('data_id')
							if f and g:
								v = d.get(g)
								if v and not f(v):
									skip = True
						elif not d.get(k):
							skip = True
						if skip:
							break
					if skip:
						continue

					output_vars = {}

					for g in get_vars:
						r = {}

						k_i = k_o = None

						if is_type_str(g):
							k_i = k_o = g

						elif is_type_dic(g):
							k_i = (
								g.get('get_by_id')
							or	g.get('id')
							or	g.get('put_by_id')
							)

							k_o = (
								g.get('put_by_id')
							or	g.get('id')
							or	g.get('get_by_id')
							)

							for k in o_o:
								r[k] = (
									g.get('replace_before_' + k, [])
								+	g.get('replace', [])
								)

						if k_o and k_i and k_i in d:
							v = unicode(d[k_i])

							for k in o_o:
								if k in r:
									v = replace_by_arr(v, r[k])

								if not k in output_vars:
									output_vars[k] = {}

								output_vars[k][k_o] = v or '?'

					for lang in html_langs:
						for ext, d in output_vars.items():
							entry = format or ''

							if entry:
								if is_type_dic(entry):
									entry = entry.get(lang, '')

								for k_o, v in d.items():
									entry = entry.replace('$' + k_o, v)
							else:
								for k_o, v in d.items():
									if entry:
										entry += unformatted_var_separator
									entry += v

							k = (lang + '.' + ext) if ext == 'html' else ext

							if not k in output_entries:
								output_entries[k] = []

							output_entries[k].append(entry)

		o_title = o.get('output_title', 'unknown')
		o_sep = o.get('output_entry_separator', ', ')

		for k, a in output_entries.items():
			ext = get_file_ext(k)
			lang = html_langs[0] if ext == k else get_lang(k)

			title = o_title.get(lang, '') if is_type_dic(o_title) else o_title
			sep = o_sep.get(lang, '') if is_type_dic(o_sep) else o_sep

			if is_type_arr(a):
				count = len(a)
				text = sep.join(sorted(set(a)))	# <- uniq, sort, join: https://stackoverflow.com/a/2931683
			else:
				count = None
				text = a

			if ext == 'html':
				if is_type_arr(a):
					if text:
						text = indent_newline + text + indent_block

					text = str(count) + text

				text = (
					indent_block
				+	block_start
				+		title + ': ' + text
				+	block_end
				)
			else:
				text = ('\n' if k in output else '') + text

			if not k in output:
				output[k] = ''

			output[k] += text

	for k, content in output.items():
		ext = get_file_ext(k)

		if ext in stats_output_path:
			path = fix_slashes(stats_output_path[ext])

			if not ext == k:
				lang = get_lang(k)
				ext = get_file_ext(path, include_dot=True)
				path = path[ : -len(ext)] + '.' + lang + ext

			save_files(path, content)

	# - END do_task_stats

def do_task(task):

	if task in tasks_as_function_name:

		# https://stackoverflow.com/a/7936588
		possibles = globals().copy()
		possibles.update(locals())
		method = possibles.get(task)

		if not method:
			print 'Error: method "%s" not implemented' % method_name

			return 1

		for i in options:
			file_path = prepend_root_if_none(i)

			if os.path.isfile(file_path):
				try:
					print get_time_stamp(), 'Processing file:', file_path

					results = method(file_path)

					print get_time_stamp(), 'Task result:', results

				except Exception, e:
					print_whats_wrong(e, 'Task error:')

			# elif READ_ONLY or TEST:
				# print get_time_stamp(), 'Not a file:', file_path

	elif task == 'records':

		do_task_records()

	elif task == 'stats':

		try_files = []

		if time_before_task:
			for k, v in stats_output_path.items():
				try_files.append(v)

				for lang in html_langs:
					ext = get_file_ext(v, include_dot=True)
					try_files.append(v[ : -len(ext)] + '.' + lang + ext)

		t_last = None

		for v in try_files:
			try:
				if os.path.isfile(v):
					t = get_file_mod_time(v)

					if not t_last or t_last > t:
						t_last = t

			except Exception, e:
				print_whats_wrong(e, 'Old file check error:')

		if t_last and t_last > time_before_task:
			print get_time_stamp(), 'Task was already done while waiting for lock.'
		else:
			do_task_stats()

	else:
		try_print('Error: unknown task:', task)

		return 1

	if not READ_ONLY:
		x = cfg.get('run_after_' + task)
		if x and is_type_str(x):
			try:
				if x.find('://') > 0:
					response = fetch_url(x)
				else:
					os.system(x)

			except Exception, e:
				print_whats_wrong(e, 'Run after task error:')

	return 0

	# - END do_task

# - Run: ----------------------------------------------------------------------

if READ_ONLY: print 'READ ONLY mode ON'
if TEST:      print 'TEST mode ON'

lock_on()

print get_time_stamp(before_task=True), 'Start task:', (task or 'none')
print 'Command line:', sys.argv

if task == 'pipe':

	pat_ID_part = r'\{' + pat_session_ID_part + '}:.+?'
	pat_tasks = {
		'records' : re.compile(pat_ID_part + r'(Closing.+?session|Last.+?user.+?left)', re.I | re.DOTALL)
	,	'stats' : re.compile(pat_ID_part + r'(Changed|Made|Tagged|preserve|(Left|Joined).+?session)', re.I | re.DOTALL)
	}
	lock_off()

	for line in sys.stdin:
		lock_on()

		try:
			for task, pat in pat_tasks.items():
				match = re.search(pat, line)
				if match:
					print line
					print get_time_stamp(before_task=True), 'Next task:', task

					do_task(task)

					time.sleep(cfg['sleep'])

					break

		except KeyboardInterrupt:
			print get_time_stamp(), 'Stopped by KeyboardInterrupt'
			sys.exit(0)

		except Exception, e:
			print_whats_wrong(e)

		lock_off()
else:
	time.sleep(cfg['wait'])

	do_task(task)

# - End: ----------------------------------------------------------------------

lock_off()
