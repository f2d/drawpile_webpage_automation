# drawpile_webpage_automation

Included `/etc/nginx/nginx.conf` is just an incomplete example.
Everything else should probably run as is, although not advised and not tested in a bare install.

## Features:

* Drawpile server launch script.
* Webpage templates and static files.
* Autoupdating stats page with currently open session list after each user join/leave.
* Autoupdating session archive folder with stats (user names, stroke counts) and screenshots after each closed session.

## Required:

* **drawpile-srv**
* **bash**
* **awk** (mawk is OK)
* **python2** (for now)
* **nginx** with modules:
	* **ngx_http_ssi_module**
	* **ngx_http_xslt_module**

## Optional:

* Nginx modules:
	* **ngx_http_auth_basic_module** (for access to API from outside)
	* **nginx_accept_language_module** (for automatic HTML file selection)
* Image file optimizers (for generated screenshots and thumbnails):
	* **jpegoptim**
	* **optipng**

## Using:

Set all *.sh files to be executable:
```
chmod +x /srv/drawpile/*.sh
```

To start the Drawpile server, use this command:
```
/srv/drawpile/start-drawpile-srv.sh
```

Or put it into drawpile-srv service config and use:
```
service drawpile-srv start
```

For maintenance safety, `stop` the service before editing any scripts in `/srv/drawpile/`, do not edit them while it's running.
Service `restart` is required for script changes to take effect.

It is possible to configure all paths to write changes directly to a public web folder.
Otherwise, create links as following, written as link -> real target (defaults, adjust as needed):
```
/srv/www/drawpile/record/      -> /srv/drawpile/sessions/public_archive/
/srv/www/drawpile/stats.en.htm -> /srv/drawpile/stats.en.htm
/srv/www/drawpile/stats.ru.htm -> /srv/drawpile/stats.ru.htm
/srv/www/drawpile/users.txt    -> /srv/drawpile/users.txt
```

To start drawpile-srv with its default SSL certificate, in `/srv/drawpile/common-variables.sh` set `cert_dir` path to empty or leave it commented (by default).

Certificate filenames used are `privkey.pem` and `fullchain.pem`.

If you want to use custom SSL certificates, then the user in system, under whose name the Drawpile service will run, must be allowed to read those certificate files.
Loose command example:
```
chmod -r 0755 /etc/letsencrypt/live/ /etc/letsencrypt/archive/
```

To manually run updates in terminal as your Drawpile service user, use this command example:
```
sudo -u drawpile-user-name /srv/drawpile/update.sh --records --stats
```
