# drawpile_webpage_automation

Included `/etc/nginx/nginx.conf` is just an incomplete example.
Everything else should probably run as is, although not advised and not tested in a bare install.

## Features:

* Launch script for Drawpile server and its message processing chain.
* Webpage templates and static files.
* Autoupdating stats page with currently open session list after each user join/leave.
* Autoupdating session archive folder with stats (user names, stroke counts) and screenshots after each closed session.

## Required:

* **drawpile-srv** (tested with versions 2.0.10 and 2.1.17)
* **drawpile-cmd**
* **dprectool**
* **bash**
* **awk** (tested with mawk version 1.3.3)
* **python** (2 or 3, tested with versions 2.7.18, 3.6.9 and 3.8.1) with modules:
	* **dateutil** (python-dateutil)
	* **PIL** (Pillow)
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

It is possible to configure all paths to write changes directly to a public web folder.
By default symlinks from web pages to drawpile are used.
To create service user accounts and the symlinks, use this command:
```
sudo /srv/drawpile/root-do-initial-setup.sh
```

To start the Drawpile server, use this command:
```
sudo -u drawpile /srv/drawpile/start-drawpile-srv.sh
```

To add it as an autostarting service, put the service config into `/lib/systemd/system/drawpile-srv.service` and then use these commands to enable and start it:
```
systemctl daemon-reload
systemctl enable drawpile-srv
service drawpile-srv start
```

Service stop is recommended for maintenance safety before editing any scripts in `/srv/drawpile/`. Example command:
```
service drawpile-srv stop
```

Service restart is required for `common-variables.sh`, `start-drawpile-srv.sh` and `event-listener.awk` script changes to take effect. Example command:
```
service drawpile-srv restart
```

To start Drawpile with its default SSL certificate, in `/srv/drawpile/common-variables.sh` set `cert_dir` path to empty or leave it commented. This is default and recommended.

For custom SSL certificates, the filenames used are `privkey.pem` and `fullchain.pem`.
Also the Drawpile service user account must be allowed to read those certificate files.
Loose command example to allow this:
```
chmod -r 0755 /etc/letsencrypt/live/ /etc/letsencrypt/archive/
```

To manually run updates in terminal as the Drawpile service user account, use this command example:
```
sudo -u drawpile /srv/drawpile/update.sh --records --stats
```

To manually run updates in background, use this command:
```
sudo /srv/drawpile/root-do-update-in-bg.sh --records --stats
```

Public session archive may be deleted and regenerated as follows:
1. Preemptively delete the whole public archive folder, or any files in it, which contain relevant session ID in their filename.
	* This is optional, as the script will try to remove relevant leftovers from previous runs if possible, such as session recording copies and screenshots, matching to each processed session ID, in public archive and unprocessed archived folder.
	* But if the public archive folder is somehow a parent to the working folder (not recommended), automatic preemptive cleanup will not work. Do it manually in such case.
2. Put all relevant files from the closed sessions, which you want to process, back into active session folder without renaming or subfolders.
3. Run manual update command, mentioned above.
4. After update is finished, all processed source files will be moved to closed session storage. Do not delete them.
