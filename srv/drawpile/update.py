#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

# - Dependencies: -------------------------------------------------------------

import errno, io, json, os, re, shutil, ssl, string, subprocess, sys, time, traceback

from datetime import datetime
from dateutil.parser import parse as datetime_text_to_object
from dateutil.tz import tzlocal, tzutc
from PIL import Image, ImageChops

# https://stackoverflow.com/a/17510727
try:
	# Python 3.0 and later:
	from urllib.request import urlopen, Request

except ImportError:
	# Python 2.x fallback:
	from urllib2 import urlopen, Request

# https://stackoverflow.com/a/47625614
if sys.version_info[0] >= 3:
	unicode = str

# - Common config: ------------------------------------------------------------

default_enc = 'utf-8'
read_encodings = 'utf_8|utf_16_le|utf_16_be|cp1251'.split('|')

cmd_optimize_prefix = 'cmd_optimize_'

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

,	'new_dir_rights': {'min': 0, 'default': 0o755, 'max': 0o777}	# <- bit-mask
,	'rec_del_max':    {'min': 0, 'default': 9000}			# <- bytes
,	'path_len_max':   {'min': 1, 'default': 250}			# <- symbols
,	'thumb_w':        {'min': 1, 'default': 200}			# <- pixels
,	'thumb_h':        {'min': 1, 'default': 200}			# <- pixels
,	'sleep':          {'min': 0, 'default': 1}			# <- seconds, wait_after_pipe_task
,	'wait':           {'min': 0, 'default': 0}			# <- seconds, wait_before_single_task

,	'cmd_rec_versions': '-2.0/-2.1'
,	'cmd_rec_stats':    'dprectool --acl --format text'		# not needed: -o /dev/stdout, -o CON, etc.
,	'cmd_rec_render':   'drawpile-cmd --acl --verbose --every-seq 1000 -platform offscreen'
,	cmd_optimize_prefix + 'jpg': 'jpegoptim --all-progressive'	# 'jpegtran -progressive -optimize -outfile %s.out %s'
,	cmd_optimize_prefix + 'png': 'optipng -i 0 -fix' 		# 'oxipng -i 0 --fix -t 1 %s'

,	'api_url_prefix': 'http://127.0.0.1:80/'

,	'add_pwd_session_users': ''					# '[a], [anyway]'
}

def print_help():
	self_name = os.path.basename(__file__)

	line_sep = '''
-------------------------------------------------------------------------------
'''

	cmd_optimize_lines = []

	prefix_len = len(cmd_optimize_prefix)
	pad_to_len = prefix_len + len('<ext>')

	for arg in cfg_default:
		if arg[:prefix_len] == cmd_optimize_prefix:
			pad_width = pad_to_len - len(arg)
			pad_text = (' ' * pad_width) if pad_width > 0 else ''

			cmd_optimize_lines.append(arg + pad_text + ' = <command line>. ' + get_cfg_for_help(arg))

	help_text_lines = [
		line_sep

	,	' * Usage:'
	,	''
	,	'"%s" [<task>] [<option>] ["<option = value>"] [<option>] [...]' % self_name

	,	line_sep

	,	' * <Task> is always the first and required argument. May be any of:'
	,	''
	,	'h, help: Show this text.'
	,	'r, records: Once, process and move all files of closed/archived sessions.'
	,	's, stats: Once, rewrite stats in file(s), using actual data from server API.'
# TODO:	,	'c, cycle: Repeatedly check server API, run update on changes.'
	,	'p, pipe: Continuosly wait for input, line by line, looking for:'
	,	'	Joined / Left session / Changed [session settings] => update stats'
	,	'	Closing (...) session / Last user left             => update records'
	,	''
	,	'Notes:'
	,	'	Pipe mode does not require interlayer (e.g. awk),'
	,	'	but will require restarting the whole setup,'
	,	'	including drawpile-srv itself, to apply changes to updater script.'
	,	'	Also it is likely less robust to errors and exceptions.'
	,	''
	,	' * <Function name as task>, call for each optional file path argument:'
	,	''
	,	'\n'.join(tasks_as_function_name)

	,	line_sep

	,	' * <Option> in any order, optional:'
	,	''
	,	'ro, readonly: Don\'t save or change anything, only show output, for testing.'
	,	'copyrec: Copy session recording files to public archive instead of symlink.'
	,	''
	,	'</path/to/file>.log:  Log file to print messages.      ' + get_cfg_for_help('log')
	,	'</path/to/file>.lock: Lock file to queue self runs.    ' + get_cfg_for_help('lock')
	,	'</path/to/file>.txt:  Save usernames, one per line.    ' + get_cfg_for_help('txt')
	,	'</path/to/file>.html: Save partial HTML files for SSI. ' + get_cfg_for_help('html')

	,	line_sep

	,	' * <Option = value> in any order, optional:'
	,	''
	,	', '.join(cfg_var_name_by_exts) + ' = </path/to/file>: Same as above options.'
	,	''
	,	'task = <task>: Override first task argument.'
	,	'run_after_<task> = <URL or command line>: Call after specified task finishes.'
	,	''
	,	'wait  = <number of seconds>: Pause before task in single mode. ' + get_cfg_for_help('wait')
	,	'sleep = <number of seconds>: Pause after task in pipe mode.    ' + get_cfg_for_help('sleep')
	,	''
	,	'thumb_w = <number of pixels>: Thumbnail maximum width.         ' + get_cfg_for_help('thumb_w')
	,	'thumb_h = <number of pixels>: Thumbnail maximum height.        ' + get_cfg_for_help('thumb_h')
	,	''
	,	'path_len_max = <number of symbols>: Maximum dest. path length. ' + get_cfg_for_help('path_len_max')
	,	''
	,	'api_url_prefix = <http://server:port/path/>. ' + get_cfg_for_help('api_url_prefix')
	,	''
	,	'add_pwd_session_users = <comma-separated substrings>, used in session titles:'
	,	'	Txt file is intended to be used by a chat bot to announce new users.'
	,	'	It will skip usernames from passworded sessions,'
	,	'	unless session title contains one of these substrings.'
	,	'		' + get_cfg_for_help('add_pwd_session_users')
	,	''
	,	'cmd_rec_versions = <version.number.1/v.2/v.3>:'
	,	'	Try to append each part as literal suffix'
	,	'	to filename or last folder of external record processing tool,'
	,	'	starting with configured path as is without any suffix.'
	,	'	Stop on the first variant that returns viable result.'
	,	'		' + get_cfg_for_help('cmd_rec_versions')
	,	''
	,	' * Commands for processing (%s for subject filename, or it will be appended):'
	,	''
	,	'cmd_rec_stats      = <command line>. ' + get_cfg_for_help('cmd_rec_stats')
	,	'cmd_rec_render     = <command line>. ' + get_cfg_for_help('cmd_rec_render')
	,	''
	,	cmd_optimize_prefix + '<ext> = <command line>. Custom formats may be added here.'
	,	'\n'.join(cmd_optimize_lines)
	,	''
	,	' * Source to process:'
	,	''
	,	'root    = </path/to/root/folder/>.        ' + get_cfg_for_help('root')
	,	'rec_src = </path/to/active/sessions/>.    ' + get_cfg_for_help('rec_src')
	,	''
	,	' * Destination to keep:'
	,	''
	,	'rec_end = </path/to/closed/sessions/>.    ' + get_cfg_for_help('rec_end')
	,	'rec_pub = </path/to/public/web/archive/>. ' + get_cfg_for_help('rec_pub')
	,	''
	,	' * Destination to remove (no path = delete at once):'
	,	''
	,	'rec_del = </path/to/removed/sessions/>.   ' + get_cfg_for_help('rec_del')
	,	'rec_del_max = <number of bytes>: Max record size to remove. ' + get_cfg_for_help('rec_del_max')
	,	''
	,	' * Destination subfolders (YMD/HNS/I = date/ID from filenames):'
	,	''
	,	'sub_del = <Y-M-D/HNS_I>. ' + get_cfg_for_help('sub_del')
	,	'sub_end = <Y-M-D/HNS_I>. ' + get_cfg_for_help('sub_end')
	,	'sub_pub = <Y/Y-M/Y-M-D>. ' + get_cfg_for_help('sub_pub')
	,	''
	,	' * Text encoding:'
	,	''
	,	'print_enc = <encoding name>. Default: ' + default_enc
	,	'path_enc  = <encoding name>. Default: ' + default_enc
	,	'file_enc  = <encoding name>. Default: ' + default_enc
	,	'log_enc   = <encoding name>. Default: ' + default_enc
	,	'web_enc   = <encoding name>. Default: ' + default_enc

	,	line_sep

	,	' * Result status codes:'
	,	''
	,	'0: All done, or cycle was interrupted by user.'
	,	'1: Nothing done, help shown.'
	,	'2: Error: wrong arguments.'
	,	'3: Error: cannot log.'
	,	'4: Error: cannot lock.'

	,	line_sep
	]

	print('\n'.join(help_text_lines))

# - Do not change: ------------------------------------------------------------

print_enc = path_enc = file_enc = log_enc = web_enc = default_enc

cfg_var_name_by_exts = ['lock', 'log', 'htm', 'html', 'txt']

# url2name = string.maketrans(r'":/|\?*<>', "';,,,&___")
must_quote_chars = ' ,;>='

safe_chars_as_ord = [
	[ord('0'), ord('9')]
,	[ord('A'), ord('Z')]
,	[ord('a'), ord('z')]
# ,	[ord(u'А'), ord(u'Я')]
# ,	[ord(u'а'), ord(u'я')]
] + list(map(ord, list('\';,.-_=+~` !@#$%^&()[]{}')))

unsafe_chars_as_ord = [
	[0, 31]
# ,	[127]
] + list(map(ord, list(r'\/:*?"<>|')))

lock_file = None
log_file = None
current_sessions = None

time_before_task = None
time_epoch_start_text = '1970-01-01T00:00:00Z'
time_epoch_start = datetime_text_to_object(time_epoch_start_text)

time_format_iso   = '%Y-%m-%dT%H:%M:%S%z'
time_format_print = '%Y-%m-%d %H:%M:%S%z'
time_format_print_log = '[' + time_format_print + '.%f]'
time_format_bak   = '.%Y-%m-%d_%H-%M-%S.%f.bak'
time_format_rec   = '%Y-%m-%dT%H-%M-%S%z'

pat_session_ID_part = (
	r'(?P<SessionID>'
+		r'[0-9a-f]{8}-'
+		r'(?:[0-9a-f]{4}-){3}'
+		r'[0-9a-f]{12}'
+	r'|'
+		r'(?<![0-9a-z-])'
+		r'[0-9a-z]{26}'
+		r'(?![0-9a-z-])'
+	r')'
)

pat_session_ID = re.compile(r'''^
	(?P<Before>.*?[^0-9a-z-])?
	''' + pat_session_ID_part + '''
	(?P<After>[^0-9a-z-].*)?
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

		\{?
			''' + pat_session_ID_part + '''
		\}?:\s+
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

pat_false = re.compile('^.*false.*$', re.I)
pat_true  = re.compile('^.*true.*$', re.I)

pat_non_digit        = re.compile(r'\D+')
pat_conseq_slashes   = re.compile(r'[\\/]+')
pat_conseq_spaces    = re.compile(r'\s+')
pat_conseq_spaces_un = re.compile(r'[_\s]+')
pat_cmd_line_arg     = re.compile(r'(?P<Arg>"([^"]|\")*"|\S+)(?P<After>\s+|$)')

session_temp_copy_ext = '.temp_copy'
session_closed_ext    = '.archived'
session_cfg_ext       = '.session'
session_rec_ext       = '.dprec'
session_log_ext       = '.log'
session_meta_ext      = '.js'

session_meta_var_name = 'dprecMetaByID'

removable_temp_file_exts = [
	session_temp_copy_ext
,	session_meta_ext
,	'.jpeg'
,	'.jpg'
,	'.png'
]

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
date_type = type(time_epoch_start)
str_type = type('')
uni_type = type(u'')

def is_type_int(v): return isinstance(v, int_type)
def is_type_arr(v): return isinstance(v, arr_type)
def is_type_dic(v): return isinstance(v, dic_type)
def is_type_fun(v): return isinstance(v, fun_type)
def is_type_reg(v): return isinstance(v, reg_type)
def is_type_reg_match(v): return isinstance(v, reg_match_type)
def is_type_date(v): return isinstance(v, date_type)
def is_type_str(v): return isinstance(v, str_type) or isinstance(v, uni_type)

def is_any_char_of_a_in_b(chars, text):
	for char in chars:
		if text.find(char) >= 0:
			return True

	return False

def is_quoted(text):
	if len(text) > 1:
		for char in '\'"':
			if (
				char == text[0]
			and	char == text[-1 : ][0]
			):
				return True

	return False

def quoted_if_must(text):
	text = '%s' % text

	return (
		('"%s"' % text)
		if not is_quoted(text) and is_any_char_of_a_in_b(must_quote_chars, text)
		else text
	)

def quoted_list(args):
	return list(map(quoted_if_must, args))

def cmd_args_to_text(args):
	return ' '.join(quoted_list(args))

def cmd_args_to_text_with_pipe(args):
	return ' '.join([
		(
			arg
			if arg.find(' ') < 0
			or arg == '|'
			or arg[0] == '>'
			or arg[1] == '>'
			else
			quoted_if_must(arg)
		) for arg in args
	])

def dump(obj, check_list=[]):
	result_text = ''

	for attr_name in (check_list or dir(obj)):
		found = hasattr(obj, attr_name) if check_list else True

		if found:
			attr_value = getattr(obj, attr_name)

			if attr_value and (check_list or not callable(attr_value)):
				result_text += 'obj.%s = %s\n' % (attr_name, attr_value)

	return result_text

def print_whats_wrong(exception, title='Error:'):
	print_with_time_stamp(title or 'Error:')
	traceback.print_exc()

	if TEST:
		try:
			print_with_time_stamp(dump(exception))
		except:
			print_with_time_stamp(exception)

	print('')

def print_action_path(prefix, path):
	print_with_time_stamp('%s: "%s"' % (prefix, path), tell_if_readonly=True)

def print_action_paths(prefix, from_path, to_path):
	print_with_time_stamp('%s from: "%s"' % (prefix, from_path), tell_if_readonly=True)
	print_with_time_stamp('%s to:   "%s"' % (prefix, to_path), tell_if_readonly=True)

# https://stackoverflow.com/a/919684
def print_with_time_stamp(*list_args, **keyword_args):
	lines = []
	count_args = count_keyword_args = 0
	before_task = tell_if_readonly = False

	def try_append(arg):
		try:
			lines.append(unicode(arg))
		except:
			try:
				lines.append(str(arg))
			except:
				try:
					lines.append('%s' % arg)
				except:
					lines.append(arg)

	if list_args:
		for arg in list_args:
			try_append(arg)
			count_args += 1

	if keyword_args:
		for keyword, arg in keyword_args.items():
			if keyword == 'before_task':
				before_task = arg
			elif keyword == 'tell_if_readonly':
				tell_if_readonly = arg
			else:
				try_append(arg)
				count_keyword_args += 1

	if not (count_args or count_keyword_args):
		return

	time_stamp = get_time_now_text(before_task=before_task)

# encode/decode are bad kludges:

	if lines:
		if tell_if_readonly and READ_ONLY:
			time_stamp += ' (skipped)'

		try:
			text = '\n'.join(lines)
		except:
			try:
				text = '\n'.join(line.encode(print_enc) for line in lines)
			except:
				text = '\n'.join(line.decode(print_enc) for line in lines)

		try:
			print('%s %s' % (time_stamp, text))
		except:
			try:
				print('%s %s' % (time_stamp, text.encode(print_enc)))
			except:
				try:
					print('%s %s' % (time_stamp, text.decode(print_enc)))
				except:
					print('%s %s' % (time_stamp, 'Error: unprintable text.'))

					traceback.print_exc()

	else:
		print('%s Warning: nothing to print with %d args and %d keyword args.' % (time_stamp, count_args, count_keyword_args))

# https://stackoverflow.com/a/3314411
def get_obj_pretty_print(obj):
	try:
		dict = obj.__dict__ if '__dict__' in obj else obj

		return (
			json.dumps(
				dict
			,	sort_keys=True
			,	indent=4
			,	default=repr
			).replace(' '*4, '\t')
		)

	except Exception as exception:
		print_whats_wrong(exception)

		return '%r' % obj

# https://stackoverflow.com/a/18126680
def epoch_to_datetime(time_arg):
	return datetime.fromtimestamp(time_arg, tzutc())

def get_file_mod_time(file_path):
	return epoch_to_datetime(os.path.getmtime(file_path))

def get_time_now_text(format=time_format_print_log, before_task=False):
	global time_before_task

	time_obj = datetime.now().replace(tzinfo=tzlocal())

	if before_task:
		time_before_task = time_obj

	return time_obj.strftime(format)

def get_time_now_html(format=time_format_print, content_type='html', lang='en'):
	if content_type == 'html':
		return fix_html_time_stamp(get_time_now_text(format))

	if content_type == 'txt':
		return get_time_now_text(format)

def datetime_to_utc_epoch(time_arg):
	return (time_arg - time_epoch_start).total_seconds()

def datetime_text_to_utc_epoch(time_arg):
	time_obj = datetime_text_to_object(time_arg)
	time_int = datetime_to_utc_epoch(time_obj)

	return time_int

def fix_html_time_stamp(time_arg):
	if time_arg and is_type_str(time_arg):
		time_text = '%s %s' % (time_arg, datetime_text_to_utc_epoch(time_arg))
	else:
		time_text = '%s %s' % (time_epoch_start_text, time_epoch_start)

	return re.sub(pat_time_from_text, pat_time_to_html, time_text)

def get_rec_time_text(time_arg):
	if time_arg:
		if is_type_str(time_arg):
			time_arg = datetime_text_to_object(time_arg)

		elif not is_type_date(time_arg):
			time_arg = epoch_to_datetime(time_arg)
	else:
		return ''

	time_text = (
		time_arg
		.strftime(time_format_rec)
		.replace('+0000', 'Z')
	)

	return time_text

def bytes_to_text(content, encoding=file_enc, trim=False):
	try:	content = content.decode(encoding or default_enc)
	except:	pass

	try:	content = unicode(content)
	except:	pass

	if trim:
		try:	content = content.strip(' \t\r\n')
		except:	pass

	return content

def fix_slashes(path):
	return re.sub(pat_conseq_slashes, '/', unicode(path))

def prepend_root_if_none(path):
	path = fix_slashes(path)

	if (
		path[0] != '.'
	and	path[0] != '/'
	and	path[1 : 3] != ':/'
	):
		path = dir_root + '/' + path

	return fix_slashes(path)

def get_file_name(path):
	path = fix_slashes(path)
	index = path.rfind('/')

	if index >= 0:
		return path[index + 1 : ]

	return path

def get_file_ext(path, include_dot=False):
	path = get_file_name(path)
	index = path.rfind('.')

	if index >= 0:
		path = path[(index if include_dot else index + 1) : ]

	return path.lower()

def get_lang(name):
	index = name.find('.')
	if index >= 0: name = name[ : index]

	return name.lower()

def get_text_as_is_or_by_lang(lang, text):
	return '%s' % (
		text.get(lang, '')
		if is_type_dic(text)
		else text
	)

# https://gist.github.com/mattjmorrison/932345
def get_trimmed_image(image, border=None):

	def get_trimmed_image_bounding_box(border):
		bg = Image.new(image.mode, image.size, border)
		diff = ImageChops.difference(image, bg)
		return diff.getbbox()

# http://pillow.readthedocs.io/en/3.1.x/reference/Image.html#PIL.Image.Image.getbbox
# The bounding box is returned as a 4-tuple defining the left, upper, right, and lower pixel coordinate.

	bounding_box = None

	if border:
		bounding_box = get_trimmed_image_bounding_box(border)
	else:
		image_dimensions = image.size
		x = image_dimensions[0] - 1
		y = image_dimensions[1] - 1

		corner_pixels = [
			(0, 0)
		,	(x, 0)
		,	(0, y)
		,	(x, y)
		]

		corner_bounding_boxes = filter(None, [
			get_trimmed_image_bounding_box(image.getpixel(pixel_coordinates))
			for pixel_coordinates in corner_pixels
		])

		for corner_bounding_box in corner_bounding_boxes:
			if bounding_box:
				if bounding_box[0] < corner_bounding_box[0]: bounding_box[0] = corner_bounding_box[0]
				if bounding_box[1] < corner_bounding_box[1]: bounding_box[1] = corner_bounding_box[1]
				if bounding_box[2] > corner_bounding_box[2]: bounding_box[2] = corner_bounding_box[2]
				if bounding_box[3] > corner_bounding_box[3]: bounding_box[3] = corner_bounding_box[3]
			else:
				bounding_box = list(corner_bounding_box)

	if bounding_box:
		return image.crop(bounding_box)

	return image

def replace_by_arr(text, replacements):

	if not is_type_arr(replacements):
		replacements = [replacements]

# 1 or 2 strings - set to 1st if "true", 2nd if "false":

	replacement_count = len(replacements)

	if (
		replacement_count >= 1
	and	replacement_count <= 2
	and	replacement_count == len(list(filter(is_type_str, replacements)))
	):
		replacement_index = 1 if (re.match(pat_true, text) == None) else 0

		text = (
			replacements[replacement_index]
			if replacement_count > replacement_index
			else ''
		)

# batch of replacements:

	else:
		for replacement in replacements:
			if   is_type_fun(replacement): text = replacement(text)
			elif is_type_arr(replacement): text = re.sub(replacement[0], replacement[1], text)
			elif is_type_str(replacement): text = re.sub(replacement, '', text)

	return text

# https://gist.github.com/carlsmith/b2e6ba538ca6f58689b4c18f46fef11c
def replace_key_to_value(text, substitutions):
	substrings = sorted(substitutions, key=len, reverse=True)
	regex = re.compile('|'.join(map(re.escape, substrings)))
	return regex.sub(lambda match: substitutions[match.group(0)], text)

def sanitize_filename(input_text, safe_only=False):
	result_text = ''

	for index in range(len(input_text)):
		input_char = input_text[index]

		try:
			input_char_code = ord(input_char)

			if safe_only:
				safe = False

				for safe_char_code in safe_chars_as_ord:
					if (
						(
							input_char_code >= safe_char_code[0]
						and	input_char_code <= safe_char_code[1]
						)
						if is_type_arr(safe_char_code) else
						input_char_code == safe_char_code
					):
						safe = True
						break
			else:
				safe = True

				for unsafe_char_code in unsafe_chars_as_ord:
					if (
						(
							input_char_code >= unsafe_char_code[0]
						and	input_char_code <= unsafe_char_code[1]
						)
						if is_type_arr(unsafe_char_code) else
						input_char_code == unsafe_char_code
					):
						safe = False
						break
		except:
			pass # - 2018-04-30 10:42 - I just want to sleep already.

		result_text += input_char if safe else '_'

	return result_text

def get_filename_from_array(input_array):
	parts = list(filter(None, input_array))

	if len(parts) > 0:
		if READ_ONLY:
			print_with_time_stamp('File name parts:\n%s' % get_obj_pretty_print(parts))

		return ' - '.join(parts)

	return ''

def get_sanitized_filename_from_text(text):
	if len(text) > 0:
		try:
			return sanitize_filename(text)
		except:
			return sanitize_filename(text, safe_only=True)

	return ''

def expand_task(task):
	if task in tasks_as_function_name:
		return task

	first_char = task[0] if task and is_type_str(task) else ''

	if (not first_char) or (first_char in '-/?h'):
		return 'help'

	if first_char == 'p': return 'pipe'
	if first_char == 'r': return 'records'
	if first_char == 's': return 'stats'

	return ''

def get_cfg_default(var_name):
	if var_name in cfg_default:
		result = cfg_default[var_name]

		if is_type_dic(result):
			result = int(result.get('default', 0))
	else:
		result = None

	return result

def get_cfg_for_help(var_name):
	result = get_cfg_default(var_name)

	return 'Default: %s' % (
		('"%s"' % result) if is_type_str(result) else
		('%d' % result) if is_type_int(result) else
		('%r' % result)
	)

def get_cfg_path_with_root(var_name, ext=None):
	result = cfg.get(var_name, '')

	if not result:
		if result == None:
			return result

		result = cfg.cfg_default(var_name, '')

		if not result:
			if result == None:
				return result

			result = (
				(cfg.get('root', '') or '.') + (
					(
						'/update.' + (
							ext if is_type_str(ext) else var_name
						).strip('.')
					) if ext else ''
				)
			)

	return prepend_root_if_none(result or '.')

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

	for session in current_sessions:
		session_id = session.get('id')

		if (
			not session_id
		or	session_id != user_session_id
		):
			continue

		passworded = session.get('hasPassword')

		if (
			passworded.lower() == 'false'
			if is_type_str(passworded) else
			not passworded
		):
			return True

		title = session.get('title', '').lower()

		if marks and title:
			for mark in marks:
				if mark in title:
					return True

	return False

def is_any_option_set(*list_args):
	return bool(set(list_args).intersection(options))

# - Check arguments: ----------------------------------------------------------

argc = len(sys.argv)

task = sys.argv[1] if argc > 1 else 'help'
options = sys.argv[2 : ] if argc > 2 else []

# - Check options: ------------------------------------------------------------

COPY_REC_FILES = is_any_option_set('copyrec')
READ_ONLY = is_any_option_set('readonly', 'ro')
TEST = is_any_option_set('TEST', 'T' )

cfg = {}

for var_name in cfg_default:
	cfg[var_name] = get_cfg_default(var_name)

for arg in options:
	var_name = ''
	var_value = ''

	if arg.find('=') > 0:
		var_name, var_value = [
			x.strip()
			for x in
			arg.split('=', 1)
		]

	known_var_name = var_name and var_name in cfg_default

	if known_var_name:
		var_default = cfg_default[var_name]

		if is_type_dic(var_default):
			var_value = int(var_value)

			var_value_max = var_default.get('max')
			var_value_min = var_default.get('min')

			if is_type_int(var_value_max) and var_value > var_value_max: var_value = var_value_max
			if is_type_int(var_value_min) and var_value < var_value_min: var_value = var_value_min

		elif var_name == 'add_pwd_session_users':
			var_value = sorted(set(
				x.strip(' \t\r\n\'",.').lower()
				for x in
				var_value.split(',')
			))

		elif var_name != 'api_url_prefix':
			var_value = fix_slashes(var_value)

	elif not var_name:
		var_value = fix_slashes(arg)
		ext = get_file_ext(var_value)

		if ext and ext in cfg_var_name_by_exts:
			var_name = 'html' if ext == 'htm' else ext

	if var_name:
		cfg[var_name] = var_value

dir_root       = cfg['root']
new_dir_rights = cfg['new_dir_rights']

print_enc = cfg.get('print_enc', '') or default_enc
path_enc  = cfg.get('path_enc',  '') or default_enc
file_enc  = cfg.get('file_enc',  '') or default_enc
log_enc   = cfg.get('log_enc',   '') or default_enc
web_enc   = cfg.get('web_enc',   '') or default_enc

thumb_size = cfg['thumb_w'], cfg['thumb_h']

rec_versions = sorted(set(
	x.strip()
	for x in
	cfg.get('cmd_rec_versions', '').split('/')
))

# - Open log: -----------------------------------------------------------------

log_path = cfg['log']

if log_path:
	log_path = prepend_root_if_none(log_path)
	log_file = open(log_path, 'a')

	if log_file:
		sys.stdout = sys.stderr = log_file
		print_enc = log_enc
	else:
		print_with_time_stamp('Error: cannot open log file: "%s"' % log_path)

		sys.exit(3)

# - Check task: ---------------------------------------------------------------

task = expand_task(cfg.get('task', task))

if task == 'help':
	print_help()

	sys.exit(1)

if not task:
	print_with_time_stamp('Error: wrong arguments: %r' % sys.argv)

	sys.exit(2)

# - Config for records: -------------------------------------------------------

if task == 'records' or task == 'pipe':

	# - to check if dirs exist:

	dirs_required = {
		'made': ['rec_src']				# <- need first to read/write/remove files
	,	'make': ['rec_end', 'rec_pub', 'rec_del']	# <- need later to move results
	}

	for condition, dir_paths in dirs_required.items():
		for var_name in dir_paths:
			cfg[var_name] = get_cfg_path_with_root(var_name)

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

	for var_name in stats_output:
		stats_output_path[var_name] = get_cfg_path_with_root(var_name, ext=True)

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

	output_formats = [
		{
			'input': [
				{
					'api_endpoint': 'sessions'
				,	'run_with_data': save_current_sessions
				,	'get_vars': [
						{
							'id': 'startTime'
						,	'replace': [fix_html_time_stamp]
						}
					,	{
							'id': 'persistent'
						,	'replace': ['&#x231b;', ' ']
						}
					,	{
							'id': 'hasPassword'
						,	'replace': ['&#x1F512;', ' ']
						}
					,	{
							'get_by_id': 'nsfm'
						,	'put_by_id': 'nsfm'
						,	'replace': ['18+', '0+']
						}
					,	'protocol', 'title', 'founder', 'userCount', 'maxUserCount'
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
					indent_inline.join([
						''
					,	u'<span title="title">"$title"</span>'
					,	u'<span title="minimal user age requirement">($nsfm</span>'
					,	u'<span title="persistent session, will not end without users">$persistent</span>'
					,	u'<span title="need password to join">$hasPassword</span>'
					,	u'<span title="protocol version">$protocol)</span>'
					])
				,	u'<span title="started by">$founder</span>'
				,	u'<span title="users">$userCount/$maxUserCount</span>'
				,	u'<span title="start time">$startTime</span>'
				])
			,	'ru': indent_param.join([
					indent_inline.join([
						''
					,	u'<span title="название">"$title"</span>'
					,	u'<span title="минимальный возраст для участия">($nsfm</span>'
					,	u'<span title="постоянная сессия, не закроется пользователей">$persistent</span>'
					,	u'<span title="нужен пароль, чтобы зайти">$hasPassword</span>'
					,	u'<span title="версия протокола">$protocol)</span>'
					])
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
					'api_endpoint': 'users'
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
					'api_endpoint': 'users'
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
			'input': get_time_now_html
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

			except IOError as exception:
				# - raise on unrelated IOErrors:
				if exception.errno != errno.EAGAIN:
					raise
				else:
					if   sleep_time <  1: sleep_time += 0.1
					elif sleep_time < 10: sleep_time += 1
					time.sleep(sleep_time)
	else:
		print_with_time_stamp('Error: cannot open lock file: "%s"' % lock_path)

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

def get_normalized_dir_path(path):
	return fix_slashes(os.path.abspath(path)).rstrip('/') + '/'

def is_parent_path(parent_path, child_path):
	parent_path = get_normalized_dir_path(parent_path)
	child_path  = get_normalized_dir_path(child_path)

	return child_path.find(parent_path) == 0

def get_rec_file_sort_value(filename):
	path = fix_slashes(dir_active + '/' + filename)
	match = re.search(pat_session_ID, filename)
	index = 0

	if match:
		suffix = match.group('After')
		index = int(re.sub(pat_non_digit, '', suffix) or 0)

	file_size = os.path.getsize(path)
	file_mtime = os.path.getmtime(path)
	file_ctime = os.path.getctime(path)

	return (
		file_mtime
	,	file_ctime
	,	index
	,	file_size
	,	filename
	,	path
	)

	# Sample session parts set, sorted by modtime:
	# 01e0vaxg66g7xpj77v5ptmcn7f.dprec.archived	15 732 354 bytes, modtime = 2020-02-12 05:06
	# 01e0vaxg66g7xpj77v5ptmcn7f_r2.dprec.archived	17 218 604 bytes, modtime = 2020-02-12 07:24
	# 01e0vaxg66g7xpj77v5ptmcn7f_r3.dprec.archived	 4 512 169 bytes, modtime = 2020-02-12 14:36
	# 2020-02-12 02.56.27 session 01e0vaxg66g7xpj77v5ptmcn7f.dprec		15 732 087 bytes, modtime = 2020-02-12 05:06
	# 2020-02-12 02.56.27 session 01e0vaxg66g7xpj77v5ptmcn7f (1).dprec	17 218 341 bytes, modtime = 2020-02-12 07:24
	# 2020-02-12 02.56.27 session 01e0vaxg66g7xpj77v5ptmcn7f (2).dprec	 4 511 906 bytes, modtime = 2020-02-12 14:36

def get_rec_files_in_session_sequence_order(filenames):
	files = map(get_rec_file_sort_value, filenames)
	sorted_files = sorted(files)
	sorted_files_as_dicts = [
		{
			'path' : file[5]
		,	'name' : file[4]
		,	'size' : file[3]
		,	'index': file[2]
		,	'ctime': file[1]
		,	'mtime': file[0]
		} for file in sorted_files
	]

	return sorted_files_as_dicts

def get_file_paths_in_tree_by_session_id(session_ID, path, skip_paths=None, nested_call=False):
	if skip_paths:
		if not nested_call:
			skip_paths = filter(
				lambda skip_path: not is_parent_path(skip_path, path)
			,	skip_paths
			)

		for skip_path in skip_paths:
			if is_parent_path(skip_path, path):
				return []

	result_paths = []

	if os.path.isdir(path):
		for name in os.listdir(path):
			path_name = fix_slashes(path + '/' + name)

			if os.path.isdir(path_name):
				result_paths += get_file_paths_in_tree_by_session_id(
					session_ID
				,	path_name
				,	skip_paths=skip_paths
				,	nested_call=True
				)

			elif name.find(session_ID) >= 0:
				result_paths.append(path_name)

	return result_paths

def get_open_file(path, mode='rU'):

	# - python3 DeprecationWarning: 'U' mode is deprecated
	mode = mode.replace('U', '')

	if 'b' in mode:
		return open(path, mode)

	for read_enc in read_encodings:
		try:
			return io.open(path, mode, encoding=read_enc)

		except UnicodeDecodeError:
			continue

	return None

def read_file(path, mode='rb'):
	if not os.path.isfile(path):
		return ''

	try:
		if 'b' in mode:
			file = open(path, mode)
			file_content = file.read()
		else:
			file = None
			file_content = ''

			for read_enc in read_encodings:
				if file:
					file.close()

				try:
					file = io.open(path, mode, encoding=read_enc)
					file_content = file.read()

					break

				except UnicodeDecodeError:
					continue

	# except PermissionError:
	# There was no PermissionError in Python 2.7, it was introduced in the Python 3.3 stream with PEP 3151.
	# https://stackoverflow.com/a/18199529

	except (IOError, OSError) as exception:
		print_whats_wrong(exception, title='Error reading contents of file: "%s"' % path.encode(print_enc))

	if file:
		file.close()

	return file_content

def write_file(path, conts, mode='a+b'):
	if READ_ONLY:
		return READ_ONLY

	for attr in ['lower', 'real']:
		if hasattr(conts, attr):
			conts = [conts]
			break

	path = fix_slashes(path)
	binary = 'b' in mode

	written = False
	retry = True
	file = None

	while retry:
		try:
			file = open(path, mode) if binary else io.open(path, mode, encoding=file_enc)
			retry = False

		except Exception as exception:
			print_whats_wrong(exception, 'Error: cannot open file for writing: "%s"' % path.encode(print_enc))

			try:
				print_with_time_stamp('Let\'s try to move it away.')

				os.rename(path, path + get_time_now_text(time_format_bak))

				print_with_time_stamp('Done.')

			except Exception as exception:
				print_whats_wrong(exception, 'Error: cannot rename pre-existing file: "%s"' % path.encode(print_enc))

				retry = False
	if file:
		for content in conts:
			try:
				written = file.write(content if binary else unicode(content))
			except:
				try:
					written = file.write(
						dump(content, ['__class__', '__doc__', 'args', 'message'])
					or	dump(content)
					)
				except:
					print_whats_wrong(exception, 'Error: cannot write content to file: "%s"' % path.encode(print_enc))
		file.close()

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

		for file_name, file_content in (
			enumerate(content) if is_type_arr(content) else
			content.items()
		):
			save_files(path + file_name + ext, file_content)

	else:
		if READ_ONLY:
			print_with_time_stamp('%d bytes to save to file: "%s"' % (len(content), path))

			if content:
				print_with_time_stamp('File content to save:\n%s' % content)
		else:
			print_with_time_stamp('Saving %d bytes to file: "%s"' % (len(content), path))
			rewrite_file(path, content, 'w')

def fetch_url(url):
	print_with_time_stamp('Request URL: %s' % url)

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

	request = Request(url, headers=headers) if headers else url
	response = urlopen(request, timeout=timeout, context=context)

	print_with_time_stamp('Request finished.')

	info = response.info()
	print_with_time_stamp('Response info:\n%s' % info)

	content = response.read()
	print_with_time_stamp('Response content:\n%r' % content)

	response.close()

	return {
		'info': info
	,	'content': content
	}

def get_path_type(path):
	text_parts = []

	if os.path.isdir(path):  text_parts.append('folder')
	if os.path.isfile(path): text_parts.append('file')
	if os.path.islink(path): text_parts.append('symlink')

	return ' '.join(text_parts)

def check_and_remove(path, title=None, skip_done_message=False):
	title = ' '.join(filter(None, [
		'Remove'
	,	title
	,	get_path_type(path)
	]))

	print_action_path(title, path)

	if not READ_ONLY:
		os.remove(path)

		if not skip_done_message:
			print_with_time_stamp('Done.')

		return 1

	return 0

def check_and_move(src_path, dest_path, make_symlink=False):
	src_path = fix_slashes(src_path)
	dest_path = fix_slashes(dest_path)

	src_path_encoded = src_path.encode(path_enc)
	dest_path_encoded = dest_path.encode(path_enc)

	if os.path.exists(dest_path_encoded):
		print_with_time_stamp('Error: destination path is an existing %s: "%s"' % (get_path_type(dest_path), dest_path))

	elif os.path.isfile(src_path_encoded):
		is_nested_path = (dest_path.find('/') >= 0)

		if is_nested_path:
			dest_dir = dest_path.rsplit('/', 1)[0]
		else:
			dest_dir = '.'

		dest_dir_encoded = dest_dir.encode(path_enc)

		if is_nested_path and not os.path.exists(dest_dir_encoded):
			print_action_path('Make dirs with rights %#03o' % new_dir_rights, dest_dir)

			if not READ_ONLY:
				os.makedirs(dest_dir_encoded, new_dir_rights)

				print_with_time_stamp('Done.')

		print_action_paths('Make symlink' if make_symlink else 'Move file', src_path, dest_path)

		if not READ_ONLY:
			if os.path.isdir(dest_dir_encoded):
				if make_symlink:
					os.symlink(src_path_encoded, dest_path_encoded)
				else:
					os.rename(src_path_encoded, dest_path_encoded)

				print_with_time_stamp('Done.')

				return 1
			else:
				print_with_time_stamp('Error: destination path was not created: "%s"' % dest_dir)

	else:
		print_with_time_stamp('Error: source file does not exist: "%s"' % src_path)

	return 0

	# os.rename(src, dst):
	# Rename the file or directory src to dst. If dst is a directory, OSError will be raised. On Unix, if dst exists and is a file, it will be replaced silently if the user has permission. The operation may fail on some Unix flavors if src and dst are on different filesystems. If successful, the renaming will be an atomic operation (this is a POSIX requirement). On Windows, if dst already exists, OSError will be raised even if it is a file; there may be no way to implement an atomic rename when dst names an existing file.

def get_cmd_with_path(cmd_line, subject='', exe_suffix=''):

	def get_path_variants_with_suffix(path, suffix):
		path = fix_slashes(path)
		filename = get_file_name(path)
		file_ext = get_file_ext(path, include_dot=True)
		file_dir = path[ : -len(filename)]
		basename = filename[ : -len(file_ext)]

		return [
			path + str(suffix)
		,	file_dir + basename + str(suffix) + file_ext
		,	(file_dir.rstrip('/') + str(suffix) + '/' + filename) if file_dir else None
		]

	arr = []
	placeholder = '%s'
	found_subject = False

	for match in re.finditer(pat_cmd_line_arg, cmd_line):
		arg = match.group('Arg')

		if is_quoted(arg):
			arg = arg[1 : -1]

		if arg.find(placeholder) >= 0:
			arg = arg.replace(placeholder, subject)

			found_subject = True

		arr.append(arg)

	if not found_subject:
		arr.append(subject)

	exe_path_arg = arr[0]
	exe_path_full = prepend_root_if_none(exe_path_arg)

	if exe_suffix:
		arr[0] += exe_suffix

		exe_path_variants = (
			get_path_variants_with_suffix(exe_path_full, exe_suffix)
		+	get_path_variants_with_suffix(exe_path_arg, exe_suffix)
		)
	else:
		exe_path_variants = [
			exe_path_full
		,	exe_path_arg
		]

	if TEST:
		print('Exe paths to check:')
		print('\n'.join(exe_path_variants))

	for exe_path in exe_path_variants:
		if exe_path and os.path.isfile(exe_path):
			arr[0] = exe_path
			break

	return list(map(fix_slashes, arr))

def get_print_and_check_cmd_result(
	cmd_line
,	filename=''
,	title=''
,	callback_for_each_line=None
,	callback_for_final_check=None
,	retry_exe_suffixes=None
,	print_cmd_output=True
,	return_cmd_output=True
):
	if not retry_exe_suffixes:
		retry_exe_suffixes = []

	retry_exe_suffixes.append('')
	retry_exe_suffixes = sorted(set(map(str, retry_exe_suffixes)))

	if TEST:
		print('Exe suffixes to try:')
		print('\n'.join(retry_exe_suffixes))

	for exe_suffix in retry_exe_suffixes:

		if TEST:
			print('Trying exe suffix: ' + (exe_suffix or 'none'))

		cmd_result = get_and_print_cmd_result(
			get_cmd_with_path(cmd_line, filename, exe_suffix)
		,	title=title
		,	callback_for_each_line=callback_for_each_line
		,	print_cmd_output=print_cmd_output
		,	return_cmd_output=return_cmd_output
		)

		if callback_for_final_check:
			if callback_for_final_check():
				break
		elif cmd_result:
			break

	return cmd_result

def get_and_print_cmd_result(
	cmd_line
,	filename=''
,	title=''
,	callback_for_each_line=None
,	print_cmd_output=True
,	return_cmd_output=True
):
	if is_type_str(cmd_line):
		cmd_args = get_cmd_with_path(cmd_line, filename)
	else:
		cmd_args = cmd_line

	if not cmd_args:
		return None

	if TEST:
		print_cmd_output = True

	print_with_time_stamp('Run command%s%s%s:\n%s' % (
		(' with PIPE' if '|' in cmd_args else '')
	,	(' via pipe handler' if callback_for_each_line else '')
	,	((' - ' + title) if title else '')
	,	cmd_args_to_text(cmd_args)
	))

	lines_count = 0
	cmd_output_parts = []
	cmd_output = ''
	end_time = None
	start_time = time.time()

	try:
		if '|' in cmd_args:

			# - Not needed, not tested, not sure if works:

			cmd_line = cmd_args_to_text_with_pipe(cmd_args)

			if return_cmd_output:
				cmd_output = subprocess.check_output(cmd_line, shell=True)
				cmd_output_parts.append(cmd_output)
			else:
				subprocess.check_call(cmd_line, shell=True)

			# - Not needed, not finished code part:

			# p1 = subprocess.Popen(['command_1', 'args'], stdout=subprocess.PIPE)
			# p2 = subprocess.Popen(['command_2', 'args'], stdout=subprocess.PIPE, stdin=p1.stdout)
			# p1.stdout.close()
			# p3 = subprocess.Popen(['command_3', 'args'], stdout=subprocess.PIPE, stdin=p2.stdout)
			# p2.stdout.close()
			# output = p3.communicate()[0]

		elif callback_for_each_line:

			running_process = subprocess.Popen(cmd_args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

			while True:
				line = running_process.stdout.readline()

				if line == b'':
					break

				lines_count += 1
				line_text = bytes_to_text(line, trim=True)

				if print_cmd_output:
					print('line %d: %s' % (lines_count, line_text))

				if return_cmd_output:
					cmd_output_parts.append(line)

				callback_for_each_line(line_text)

		elif return_cmd_output:
			cmd_output = subprocess.check_output(cmd_args, stderr=subprocess.STDOUT)
			cmd_output_parts.append(cmd_output)
		else:
			subprocess.check_call(cmd_args, stderr=subprocess.STDOUT)

		end_time = time.time()

	except subprocess.CalledProcessError as exception:
		end_time = time.time()

		if callback_for_each_line:
			print_with_time_stamp('Command returned code: %d at line %d.' % (lines_count, exception.returncode))
		else:
			print_with_time_stamp('Command returned code: %d' % exception.returncode)

		if print_cmd_output or return_cmd_output:
			cmd_output_parts.append(exception.output)

	except FileNotFoundError as exception:
		print_with_time_stamp('Command error: %r' % exception)

	if return_cmd_output or (print_cmd_output and not callback_for_each_line):
		cmd_output = (
			'\n'
			.join(map(bytes_to_text, cmd_output_parts))
			.rstrip(' \t\r\n')
		)

	if callback_for_each_line:
		print_with_time_stamp('Command finished processing %d lines.' % lines_count)
	elif print_cmd_output:
		print_with_time_stamp('Command result:\n%s' % cmd_output)

	if end_time:
		# https://stackoverflow.com/questions/1557571/how-do-i-get-time-of-a-python-programs-execution#comment45925018_1557584
		print_with_time_stamp('Command finished in %.3f seconds.' % (end_time - start_time))

	return cmd_output if return_cmd_output else None

# - Task-specific functions: --------------------------------------------------

def get_recording_stats_for_each_user(
	source_rec_file_path
,	users_by_ID=None
):
	global rec_stats_multiline, rec_stats_users_by_ID, rec_stats_total_strokes

	rec_stats_multiline = []
	rec_stats_users_by_ID = {}
	rec_stats_total_strokes = 0

	pat_username = re.compile(r'^(?P<ID>\d+)\s+(?:\S+\s+)*name=(?P<Name>[^\r\n]*)', re.I | re.U | re.DOTALL)
	pat_stroke = re.compile(r'^(?P<ID>\d+)\s+penup', re.I | re.U | re.DOTALL)

	if users_by_ID:
		for user_ID, user in users_by_ID.items():
			rec_stats_users_by_ID[user_ID] = {
				'name': user.get('name', '#' + user_ID)
			,	'strokes': user.get('strokes', 0)
			}

	# - Find usernames by ID and their stroke counts:

	def callback_for_each_line(line):
		global rec_stats_multiline, rec_stats_users_by_ID, rec_stats_total_strokes

		if rec_stats_multiline or line[-1 : ] == '{':
			rec_stats_multiline.append(line)

			if line == '}':
				line = '\n'.join(rec_stats_multiline)
				rec_stats_multiline = []
			else:
				return

		match_username = re.search(pat_username, line)
		match_stroke = re.search(pat_stroke, line)
		match = match_username or match_stroke

		if match:
			user_ID = match.group('ID')
			user = rec_stats_users_by_ID.get(user_ID)

			if not user:
				user = rec_stats_users_by_ID[user_ID] = {
					'name': '#' + user_ID
				,	'strokes': 0
				}

			if match_username:
				name = match_username.group('Name').strip()

				if len(name) > 0:
					user['name'] = name

			if match_stroke:
				user['strokes'] += 1
				rec_stats_total_strokes += 1

	def callback_for_final_check():
		if rec_stats_multiline:
			callback_for_each_line('}')

		return bool(rec_stats_users_by_ID) and rec_stats_total_strokes > 0

	get_print_and_check_cmd_result(
		cfg['cmd_rec_stats']
	,	filename=source_rec_file_path
	,	title='get recording stats'
	,	callback_for_each_line=callback_for_each_line
	,	callback_for_final_check=callback_for_final_check
	,	retry_exe_suffixes=rec_versions
	,	print_cmd_output=False	# <- to keep output/logs cleaner
	,	return_cmd_output=False	# <- to use less memory uselessly
	)

	return rec_stats_users_by_ID

def get_recording_stats_for_each_username(users_by_ID):
	users_by_name = {}

	for user_ID, user in users_by_ID.items():
		try:
			strokes_count = user.get('strokes', 0)

			if strokes_count > 0:
				user_name = user.get('name', '#' + user_ID)
				user_name = re.sub(pat_conseq_spaces_un, '_', user_name.strip())

				if user_name in users_by_name:
					users_by_name[user_name] += strokes_count
				else:
					users_by_name[user_name] = strokes_count

		except Exception as exception:
			print_whats_wrong(exception)

	print_with_time_stamp('User strokes count by name:\n%s' % get_obj_pretty_print(users_by_name))

	return users_by_name

def get_recording_usernames_with_stats(users_by_name):
	users_by_name_with_stats = {}

	for user_name, strokes_count in users_by_name.items():
		users_by_name_with_stats['%s %d' % (user_name, strokes_count)] = strokes_count

	return users_by_name_with_stats

def get_recording_screenshots_saved(source_rec_file_path):
	global rec_img_paths

	rec_img_paths = []

	if READ_ONLY:
		return rec_img_paths

	# - Get path markers to look for:

	match = re.search(pat_session_ID, source_rec_file_path)
	if match:
		source_prefix = match.group('Before') + match.group('SessionID')
	else:
		path = source_rec_file_path

		while len(path):
			source_prefix = path

			slash_pos = path.rfind('/')
			dash_pos = path.rfind('-')
			dot_pos = path.rfind('.')

			if slash_pos >= dot_pos or dash_pos >= dot_pos:
				break

			elif dot_pos > 0:
				path = path[ : dot_pos]

	marker_text = ' Writing '
	markers = [
		[marker_text, len(marker_text)]
	,	[source_prefix, 0]
	]

	# - Save image files and grab their paths:

	def callback_for_each_line(line):
		global rec_img_paths

		for marker in markers:
			prefix, offset = marker

			pos = line.find(prefix)
			if pos >= 0:
				img_path = line[pos + offset : ].rstrip('.')
				rec_img_paths.append(img_path)

				return

	def callback_for_final_check():
		return bool(rec_img_paths)

	get_print_and_check_cmd_result(
		cfg['cmd_rec_render']
	,	filename=source_rec_file_path
	,	title='save screenshots + thumbs'
	,	callback_for_each_line=callback_for_each_line
	,	callback_for_final_check=callback_for_final_check
	,	retry_exe_suffixes=rec_versions
	,	return_cmd_output=False
	)

	return get_recording_screenshots_with_thumbs(rec_img_paths)

def get_recording_screenshots_with_thumbs(img_paths):
	to_move = []

	if not is_type_arr(img_paths):
		img_paths = [img_paths]

	for img_path in img_paths:
		print_with_time_stamp('Resizing image: "%s"' % img_path)

		try:
			img_filename = get_file_name(img_path)
			img_dir = img_path[ : -len(img_filename)]
			img_ext = get_file_ext(img_filename, include_dot=True)
			img_basename = img_filename[ : -len(img_ext)]
			res_filename = img_basename + '_resized' + img_ext

			img = Image.open(img_path)
			img_size_text = 'x'.join(map(str, img.size))

			print_with_time_stamp('Full size: %s' % img_size_text)

			to_move.append([
				img_filename
			,	img_basename + '_full_' + img_size_text + img_ext
			])

			thumb = get_trimmed_image(img)

			if img and thumb != img:
				try: img.close()
				except: pass

			thumb.thumbnail(thumb_size, Image.ANTIALIAS) # <- best for downscaling
			img_size_text = 'x'.join(map(str, thumb.size))

			print_with_time_stamp('Thumb size: %s' % img_size_text)

			to_move.append([
				res_filename
			,	img_basename + '_thumb_' + img_size_text + img_ext
			])

			thumb.save(img_dir + res_filename, quality=95)

			if thumb:
				try: thumb.close()
				except: pass

			ext = img_ext.strip('.').replace('jpeg', 'jpg')
			cmd_line = cfg.get(cmd_optimize_prefix + ext, '')

			if cmd_line:
				for filename in [img_filename, res_filename]:
					get_and_print_cmd_result(
						cmd_line
					,	img_dir + filename
					,	'optimize image'
					)

		except Exception as exception:
			print_whats_wrong(exception)

	return to_move

def process_archived_session(session_ID, src_files):
	all_filenames_to_move = []
	cfg_filenames_to_read = []
	log_filenames_to_read = []
	rec_filenames_to_publish = []
	bak_filenames_to_publish = []
	temp_filenames_to_remove = []

	time_started = time_closed = date_match = None
	is_session_good_to_keep = False

	# - Find files to move away:

	for filename in src_files:
		if filename.find(session_ID) >= 0:
			if not date_match:
				date_match = re.search(pat_get_date, filename)

			ext = get_file_ext(filename, include_dot=True)

			if ext in removable_temp_file_exts:
				temp_filenames_to_remove.append(filename)
			else:
				if filename.find(session_rec_ext) > 0:
					if ext == session_closed_ext:
						rec_filenames_to_publish.append(filename)
					else:
						bak_filenames_to_publish.append(filename)

				elif filename.find(session_cfg_ext) > 0: cfg_filenames_to_read.append(filename)
				elif filename.find(session_log_ext) > 0: log_filenames_to_read.append(filename)

				all_filenames_to_move.append(filename)

	old_public_file_paths_to_remove = get_file_paths_in_tree_by_session_id(
		session_ID
	,	dir_public
	,	skip_paths=[
			dir_active
		,	dir_closed
		,	dir_removed
		]
	)


	# - Remove leftovers of previous runs:

	if temp_filenames_to_remove:
		done_files = 0

		print_with_time_stamp(
			'Old temp files to remove:' if READ_ONLY else
			'Old temp files, removing:'
		)

		for filename in temp_filenames_to_remove:
			file_path = fix_slashes(dir_active + '/' + filename)
			done_files += check_and_remove(file_path, 'old temp', skip_done_message=True)

		if done_files:
			print_with_time_stamp('Removed %d files.' % done_files)

	if old_public_file_paths_to_remove:
		done_files = 0

		print_with_time_stamp(
			'Old public files to remove:' if READ_ONLY else
			'Old public files, removing:'
		)

		for file_path in old_public_file_paths_to_remove:
			done_files += check_and_remove(file_path, 'old public', skip_done_message=True)

		if done_files:
			print_with_time_stamp('Removed %d files.' % done_files)

	# - Find best session recording parts to copy:

	rec_files_to_publish = get_rec_files_in_session_sequence_order(rec_filenames_to_publish)
	bak_files_to_publish = get_rec_files_in_session_sequence_order(bak_filenames_to_publish)

	rec_parts_count = len(rec_files_to_publish)
	bak_parts_count = len(bak_files_to_publish)

	if rec_parts_count or bak_parts_count:

		print_with_time_stamp('Found %d session recording parts:\n%s' % (
			rec_parts_count
		,	get_obj_pretty_print(rec_files_to_publish)
		))

		print_with_time_stamp('Found %d fallback recording parts:\n%s' % (
			bak_parts_count
		,	get_obj_pretty_print(bak_files_to_publish)
		))

		if rec_parts_count < bak_parts_count:
			rec_files_to_publish += bak_files_to_publish[rec_parts_count : ]
			rec_parts_count = len(rec_files_to_publish)

			print_with_time_stamp('Got %d total recording parts combined:\n%s' % (
				rec_parts_count
			,	get_obj_pretty_print(rec_files_to_publish)
			))
		else:
			print_with_time_stamp('Got %d total recording parts.' % rec_parts_count)

		rec_file_sizes = [file['size'] for file in rec_files_to_publish]

		max_rec_file_size = max(rec_file_sizes)
		total_rec_file_size = sum(rec_file_sizes)

		print_with_time_stamp('Max rec part file size = %d bytes.' % max_rec_file_size)
		print_with_time_stamp('Total sum of parts = %d bytes.' % total_rec_file_size)

		if total_rec_file_size > cfg['rec_del_max']:
			is_session_good_to_keep = True

	# - Find session flags from cfg:

	session_flags = []

	for filename in cfg_filenames_to_read:
		file_path = fix_slashes(dir_active + '/' + filename)

		if os.path.isfile(file_path):
			file_size = os.path.getsize(file_path)

			print_with_time_stamp('Reading config file, %d bytes: "%s"' % (file_size, file_path))

			with get_open_file(file_path) as lines:
				for line in lines:
					words = line.strip().split(' ')

					if words[0] == 'FLAGS':
						session_flags = words[1 : ]	# <- overwrite previously found set

	if len(session_flags) > 0:
		print_with_time_stamp('Found session flags: %r' % session_flags)

	# - Find session start/end time + usernames from log:

	users_by_ID_from_log = {}

	for filename in log_filenames_to_read:
		file_path = fix_slashes(dir_active + '/' + filename)

		if os.path.isfile(file_path):
			file_size = os.path.getsize(file_path)

			print_with_time_stamp('Reading log file, %d bytes: "%s"' % (file_size, file_path))

			with get_open_file(file_path) as lines:
				for line in lines:
					if TEST and READ_ONLY:
						print_with_time_stamp(line.rstrip())

					match = re.search(pat_time_from_log, line)
					if match:
						time_text = get_rec_time_text(match.group('DateTime'))

						if not time_started:
							time_started = time_text

							if not date_match:
								date_match = re.search(pat_get_date, time_text)

						if not time_closed or time_closed < time_text:
							time_closed = time_text

						user_ID = match.group('UserID')
						user_name = match.group('UserName')

						if (
							user_ID != None
						and	user_name != None
						and	not user_ID in users_by_ID_from_log
						):
							users_by_ID_from_log[user_ID] = {'name': user_name}

						if len(session_flags) == 0:
							rest = match.group('After')

							if rest.find(' NSF') >= 0:
								session_flags.append('nsfm')

			print_with_time_stamp('Users found in log:\n%s' % get_obj_pretty_print(users_by_ID_from_log))

	# - Set destination path subfolders:

	dict = get_dict_from_matches(pat_subdir_replace, date_match, {'ID': session_ID})

	subdir_del = get_subdir_from_matches('sub_del', dict)
	subdir_end = get_subdir_from_matches('sub_end', dict)
	subdir_pub = get_subdir_from_matches('sub_pub', dict)

	# - Process session to put into archive:

	if not COPY_REC_FILES:
		public_filenames_to_link = {}

	if is_session_good_to_keep:
		session_part_index = 0
		session_part_label = ''
		public_meta_content_parts = []
		public_filenames_to_move = []

		for file in rec_files_to_publish:

	# - Prepare session recording copy for public archive:

			selected_rec_file_path = file['path']

			if rec_parts_count > 1:
				session_part_index += 1
				session_part_label = '_r%d' % session_part_index

			source_rec_filename = session_ID + session_part_label + session_rec_ext + session_temp_copy_ext
			source_rec_file_path = fix_slashes(dir_active + '/' + source_rec_filename)

			print_action_paths(
				'Copy file' if COPY_REC_FILES else 'Make symlink'
			,	selected_rec_file_path
			,	source_rec_file_path
			)

			if READ_ONLY:
				source_rec_file_path = selected_rec_file_path
			else:
				if COPY_REC_FILES:
					shutil.copy2(selected_rec_file_path, source_rec_file_path)
				else:
					os.symlink(selected_rec_file_path, source_rec_file_path)

				print_with_time_stamp('Done.')

			if os.path.isfile(source_rec_file_path):

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
				strokes_count = sum(user_stats_by_name.values())

				print_with_time_stamp('usernames_count: %d' % usernames_count)
				print_with_time_stamp('strokes_count: %d' % strokes_count)

	# - Construct public session recording filename:

				max_len = cfg['path_len_max']
				dir_len = len(dir_active)
				shortened = False

				public_rec_filename = ''
				public_rec_ctime = get_rec_time_text(file['ctime'])
				public_rec_mtime = get_rec_time_text(file['mtime'])
				public_rec_ext = session_ID + session_part_label + session_rec_ext

				rec_stats_parts = filter(None, [
					min(public_rec_mtime, public_rec_ctime, time_started)
				,	min(public_rec_mtime or public_rec_ctime, time_closed)
				,	'r18' if 'nsfm' in session_flags else None
				,	('part %d of %d' % (session_part_index, rec_parts_count)) if session_part_index else None
				,	('%ds' %   strokes_count) if   strokes_count else None
				,	('%du' % usernames_count) if usernames_count else None
				])

				rec_stats_text = ' - '.join(rec_stats_parts)

				while True:
					unsafe_filename = get_filename_from_array([
						rec_stats_text
					,	(
							', '.join(sorted(
								set(usernames_list)
							,	key=unicode.lower	# <- https://stackoverflow.com/a/57384669
							))
							if usernames_list
							else ''
						)
					,	public_rec_ext
					])

					public_rec_filename = get_sanitized_filename_from_text(unsafe_filename)
					path_len = dir_len + len(public_rec_filename)

					if len(usernames_list) > 0 and path_len > max_len:
						print_with_time_stamp('Path too long: %d > %d' % (path_len, max_len))

						usernames_list.pop()
						shortened = True
					else:
						break

				if (
					session_part_index
				or	shortened
				or	unsafe_filename != public_rec_filename
				):
					public_meta_content_parts.append(
						json.dumps(
							user_stats_by_name
						,	sort_keys=True
						,	indent=0
						,	separators=(',', ': ')
						,	default=repr
						)
					)


				if READ_ONLY:
					if unsafe_filename != public_rec_filename:
						print_with_time_stamp('Unsafe file name: "%s"' % unsafe_filename)

					print_with_time_stamp('Public session file name: "%s"' % public_rec_filename)

				elif COPY_REC_FILES:
					public_filenames_to_move.append([
						source_rec_filename
					,	public_rec_filename
					])
				else:
					public_filenames_to_link[selected_rec_file_path] = [
						source_rec_filename
					,	public_rec_filename
					]

	# - Save public screenshots + thumbs:

				public_filenames_to_move += get_recording_screenshots_saved(source_rec_file_path)

	# - Save some session stats into separate file instead of session filename:

		if public_meta_content_parts:
			filename = session_ID + session_meta_ext
			content = (
				session_meta_var_name
			+	'["'
			+		session_ID
			+	'"] = '
			+	(
					(
						'['
					+	','.join(public_meta_content_parts)
					+	']'
					)
					if len(public_meta_content_parts) > 1
					else public_meta_content_parts[0]
				)
			+	';'
			)

			if READ_ONLY:
				print_with_time_stamp('Public metadata file name: "%s"' % filename)
				print_with_time_stamp('Public metadata file content = %d bytes:\n%s' % (len(content), content))
			else:
				save_files(dir_active + '/' + filename, content)

				public_filenames_to_move.append(filename)

	# - Move saved files to public folder:

		for from_to_filenames in public_filenames_to_move:

			if is_type_arr(from_to_filenames):
				from_filename, to_filename = from_to_filenames
			else:
				from_filename = to_filename = from_to_filenames

			check_and_move(
				dir_active + '/' + from_filename
			,	dir_public + '/' + subdir_pub + '/' + to_filename.replace('.jpeg', '.jpg')
			)

	# - Move away all private source files:

	dir_target = None

	if is_session_good_to_keep:
		dir_target = dir_closed + '/' + subdir_end
	elif dir_removed:
		dir_target = dir_removed + '/' + subdir_del

	for filename in all_filenames_to_move:
		file_path = fix_slashes(dir_active + '/' + filename)
		target_path = fix_slashes(dir_target + '/' + filename)

		if dir_target == None:
			check_and_remove(file_path, 'small session')
		else:
			check_and_move(file_path, target_path)

		if not COPY_REC_FILES:
			filenames = public_filenames_to_link.get(file_path)

			if filenames:
				source_rec_filename, public_rec_filename = filenames

				if source_rec_filename:
					source_rec_file_path = fix_slashes(dir_active + '/' + source_rec_filename)

					check_and_remove(source_rec_file_path, 'temp source')

				if public_rec_filename:
					public_rec_file_path = fix_slashes(dir_public + '/' + subdir_pub + '/' + public_rec_filename)

					check_and_move(target_path, public_rec_file_path, make_symlink=True)

	# - END process_archived_session

def do_task_records():

	# - Check if all dirs exist or can be created first:

	for condition, dir_paths in dirs_required.items():
		for dir_path in dir_paths:
			dir_path = get_cfg_path_with_root(dir_path)

			if not os.path.isdir(dir_path):
				if condition == 'make':
					if not READ_ONLY:
						os.makedirs(dir_path, new_dir_rights)

						if not os.path.isdir(dir_path):
							print_with_time_stamp('Error: cannot create folder: "%s"' % dir_path)

							return 3
					else:
						print_with_time_stamp('Warning: folder does not exist: "%s"' % dir_path)
				else:
					print_with_time_stamp('Error: required folder does not exist: "%s"' % dir_path)

					return 2

	# - Move away all files of closed sessions, make files for public archive:

	IDs_done = []
	src_files = os.listdir(dir_active)

	session_closed_suffix = session_cfg_ext + session_closed_ext
	session_closed_suffix_len = len(session_closed_suffix)

	for filename in src_files:
		try:
			if filename[-session_closed_suffix_len : ] == session_closed_suffix:

				match = re.search(pat_session_ID, filename)
				if match:
					session_ID = match.group('SessionID')
					if session_ID in IDs_done:
						continue

					IDs_done.append(session_ID)

					process_archived_session(session_ID, src_files)

		except Exception as exception:
			print_whats_wrong(exception)

	# - END do_task_records

def do_task_stats():

	# - Query server JSON API to collect data:

	data = {}

	for api_endpoint in data_sources:
		try:
			url = cfg['api_url_prefix'] + api_endpoint

			response = fetch_url(url)
			content = response['content']

			try:
				obj = json.loads(content)

			except Exception as exception:
				print_whats_wrong(exception)

				# - python3 DeprecationWarning: 'encoding' is ignored and deprecated. It will be removed in Python 3.9
				obj = json.loads(content, encoding=web_enc)

			print_with_time_stamp('Data object:\n%s' % get_obj_pretty_print(obj))

			data[api_endpoint] = obj

		except Exception as exception:
			print_whats_wrong(exception)

			continue

	# - Compile content to save:

	output_files = {}

	for output_format in output_formats:
		format = output_format.get('output_entry_format')

		input_sources = output_format.get('input', [])
		output_target_rules = output_format.get('output', [])

		output_parts = {}

		if is_type_fun(input_sources):
			for lang in html_langs:
				for ext in output_target_rules:
					output_file_suffix = (lang + '.' + ext) if ext == 'html' else ext
					output_parts[output_file_suffix] = input_sources(content_type=ext, lang=lang)

		elif is_type_arr(input_sources):
			for lang in html_langs:
				for ext in output_target_rules:
					output_file_suffix = (lang + '.' + ext) if ext == 'html' else ext
					output_parts[output_file_suffix] = []

			for input_source in input_sources:
				api_endpoint = input_source.get('api_endpoint')

				if not api_endpoint:
					continue

				data_from_api = data.get(api_endpoint)

				if not data_from_api:
					continue

				data_function = input_source.get('run_with_data')

				if data_function:
					data_function(data_from_api)

				data_vars_to_get = input_source.get('get_vars')

				if not data_vars_to_get:
					continue

				skip_rules = input_source.get('skip_if_empty', [])

				for data_entry in data_from_api:
					skip = False

					for skip_rule in skip_rules:
						if is_type_dic(skip_rule):
							skip_rule_function = skip_rule.get('function')
							skip_rule_key = skip_rule.get('data_id')
							skip_rule_value = None

							if skip_rule_key:
								skip_rule_value = data_entry.get(skip_rule_key)

							if skip_rule_function:
								if not skip_rule_function(skip_rule_value):
									skip = True

							elif not skip_rule_value:
								skip = True

						elif not data_entry.get(skip_rule):
							skip = True

						if skip:
							break

					if skip:
						continue

					output_vars = {}

					for data_var in data_vars_to_get:
						replacements = {}

						data_var_name = output_var_name = None

						if is_type_str(data_var):
							data_var_name = output_var_name = data_var

						elif is_type_dic(data_var):
							data_var_name = (
								data_var.get('get_by_id')
							or	data_var.get('id')
							or	data_var.get('put_by_id')
							)

							output_var_name = (
								data_var.get('put_by_id')
							or	data_var.get('id')
							or	data_var.get('get_by_id')
							)

							for output_file_type in output_target_rules:
								replacements[output_file_type] = (
									data_var.get('replace_before_' + output_file_type, [])
								+	data_var.get('replace', [])
								)

						if (
							output_var_name
						and	data_var_name
						and	data_var_name in data_entry
						):
							var_value = unicode(data_entry[data_var_name])

							for output_file_type in output_target_rules:
								if output_file_type in replacements:
									var_value = replace_by_arr(var_value, replacements[output_file_type])

								if not output_file_type in output_vars:
									output_vars[output_file_type] = {}

								output_vars[output_file_type][output_var_name] = var_value or '?'

					for lang in html_langs:
						for ext, vars in output_vars.items():
							text = format or ''

							if text:
								if is_type_dic(text):
									text = text.get(lang, '')

								for output_var_name, var_value in vars.items():
									text = text.replace('$' + output_var_name, var_value)
							else:
								for output_var_name, var_value in vars.items():
									if text:
										text += unformatted_var_separator
									text += var_value

							output_file_suffix = (lang + '.' + ext) if ext == 'html' else ext

							if not output_file_suffix in output_parts:
								output_parts[output_file_suffix] = []

							output_parts[output_file_suffix].append(text)

		output_title = output_format.get('output_title', 'unknown')
		output_separator = output_format.get('output_entry_separator', ', ')

		for output_file_suffix, content in output_parts.items():
			ext = get_file_ext(output_file_suffix)
			lang = html_langs[0] if ext == output_file_suffix else get_lang(output_file_suffix)

			title     = get_text_as_is_or_by_lang(lang, output_title)
			separator = get_text_as_is_or_by_lang(lang, output_separator)

			if is_type_arr(content):
				count = len(content)
				text = separator.join(sorted(set(content)))	# <- uniq, sort, join: https://stackoverflow.com/a/2931683
			else:
				count = None
				text = '%s' % content

			if ext == 'html':
				if is_type_arr(content):
					if text:
						text = (
							indent_newline
						+	text
						+	indent_block
						)

					text = '%d%s' % (count, text)

				text = (
					indent_block
				+	block_start
				+		title + ': ' + text
				+	block_end
				)
			else:
				text = ('\n' if output_file_suffix in output_files else '') + text

			if not output_file_suffix in output_files:
				output_files[output_file_suffix] = ''

			output_files[output_file_suffix] += text

	for output_file_suffix, content in output_files.items():
		ext = get_file_ext(output_file_suffix)

		if ext in stats_output_path:
			path = fix_slashes(stats_output_path[ext])

			if not ext == output_file_suffix:
				lang = get_lang(output_file_suffix)
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
			print_with_time_stamp('Error: method "%s" not implemented.' % task)

			return 1

		for arg in options:
			file_path = prepend_root_if_none(arg)

			if os.path.isfile(file_path):
				try:
					print_with_time_stamp('Processing file: "%s"' % file_path)

					results = method(file_path)

					print_with_time_stamp('Task result:\n%s' % get_obj_pretty_print(results))

				except Exception as exception:
					print_whats_wrong(exception, 'Task error:')

			elif TEST:
				print_with_time_stamp('Not a file: "%s"' % file_path)

	elif task == 'records':

		do_task_records()

	elif task == 'stats':

		try_files = []

		if time_before_task:
			for k, file_path in stats_output_path.items():
				try_files.append(file_path)

				for lang in html_langs:
					ext = get_file_ext(file_path, include_dot=True)
					try_files.append(file_path[ : -len(ext)] + '.' + lang + ext)

		latest_time = None

		for file_path in try_files:
			try:
				if os.path.isfile(file_path):
					file_mod_time = get_file_mod_time(file_path)

					if not latest_time or latest_time > file_mod_time:
						latest_time = file_mod_time

			except Exception as exception:
				print_whats_wrong(exception, 'Old file check error:')

		if latest_time and latest_time > time_before_task:
			print_with_time_stamp('Task was already done while waiting for lock.')
		else:
			do_task_stats()

	else:
		print_with_time_stamp('Error: unknown task: "%s"' % task)

		return 1

	if not READ_ONLY:
		cmd_line = cfg.get('run_after_' + task)
		if cmd_line and is_type_str(cmd_line):
			try:
				if cmd_line.find('://') > 0:
					response = fetch_url(cmd_line)
				else:
					os.system(cmd_line)

			except Exception as exception:
				print_whats_wrong(exception, 'Run after task error:')

	return 0

	# - END do_task

# - Run: ----------------------------------------------------------------------

if READ_ONLY:	print_with_time_stamp('READ ONLY mode ON')
if TEST:	print_with_time_stamp('TEST mode ON')

lock_on()

print_with_time_stamp('Start task: %s' % (task or 'none'), before_task=True)
print_with_time_stamp('Command line: %s' % cmd_args_to_text(sys.argv))

if task == 'pipe':

	pat_ID_part = r'\{?' + pat_session_ID_part + '\}?:.+?'
	pat_tasks = {
		'records': re.compile(pat_ID_part + r'(Closing.+?session|Last.+?user.+?left)', re.I | re.DOTALL)
	,	'stats'  : re.compile(pat_ID_part + r'(Changed|Made|Tagged|preserve|(Left|Joined).+?session)', re.I | re.DOTALL)
	}
	lock_off()

	for line in sys.stdin:
		lock_on()

		try:
			for task, pat in pat_tasks.items():
				match = re.search(pat, line)
				if match:
					print_with_time_stamp(line)
					print_with_time_stamp('Next task: %s' % task, before_task=True)

					do_task(task)

					time.sleep(cfg['sleep'])

					break

		except KeyboardInterrupt:
			print_with_time_stamp('Stopped by KeyboardInterrupt.')

			sys.exit(0)

		except Exception as exception:
			print_whats_wrong(exception)

		lock_off()
else:
	time.sleep(cfg['wait'])

	do_task(task)

# - End: ----------------------------------------------------------------------

lock_off()
