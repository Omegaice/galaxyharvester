#!/usr/bin/env python3
"""

Copyright 2020 Paul Willworth <ioscode@gmail.com>

This file is part of Galaxy Harvester.

Galaxy Harvester is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Galaxy Harvester is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Galaxy Harvester.  If not, see <http://www.gnu.org/licenses/>.

"""

import cgi
import os
from http import cookies

import dbSession
import dbShared
import ghLists
import ghShared
from jinja2 import Environment, FileSystemLoader

# Get current url
try:
    url = os.environ["SCRIPT_NAME"]
except KeyError:
    url = ""

form = cgi.FieldStorage()
uiTheme = ""
# Get Cookies
useCookies = 1
C = cookies.SimpleCookie()
try:
    C.load(os.environ["HTTP_COOKIE"])
except KeyError:
    useCookies = 0

if useCookies:
    try:
        currentUser = C["userID"].value
    except KeyError:
        currentUser = ""
    try:
        loginResult = C["loginAttempt"].value
    except KeyError:
        loginResult = "success"
    try:
        sid = C["gh_sid"].value
    except KeyError:
        sid = form.getfirst("gh_sid", "")
    try:
        uiTheme = C["uiTheme"].value
    except KeyError:
        uiTheme = ""
    try:
        galaxy = C["galaxy"].value
    except KeyError:
        galaxy = form.getfirst("galaxy", ghShared.DEFAULT_GALAXY)
else:
    currentUser = ""
    loginResult = form.getfirst("loginAttempt", "")
    sid = form.getfirst("gh_sid", "")
    galaxy = form.getfirst("galaxy", ghShared.DEFAULT_GALAXY)

# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)

# Get a session
logged_state = 0
linkappend = ""
disableStr = ""
if loginResult == None:
    loginResult = "success"

sess = dbSession.getSession(sid)
if sess != "":
    logged_state = 1
    currentUser = sess
    if uiTheme == "":
        uiTheme = dbShared.getUserAttr(currentUser, "themeName")
    if useCookies == 0:
        linkappend = "gh_sid=" + sid
else:
    disableStr = ' disabled="disabled"'
    if uiTheme == "":
        uiTheme = "crafter"

# Allow for specifying galaxy in URL
path = []
if "PATH_INFO" in os.environ:
    path = os.environ["PATH_INFO"].split("/")[1:]
    path = [p for p in path if p != ""]

if len(path) > 0 and path[0].isdigit():
    galaxy = dbShared.dbInsertSafe(path[0])
    C["galaxy"] = path[0]
    C["galaxy"]["path"] = "/"
    print(C)

conn = dbShared.ghConn()

adminList = dbShared.getGalaxyAdminList(conn, currentUser).split("/option")[0]
if len(adminList) > 0:
    galaxyAdmin = int(adminList[15 : adminList.rfind('"')])
else:
    galaxyAdmin = 0
conn.close()

pictureName = dbShared.getUserAttr(currentUser, "pictureName")
print("Content-type: text/html\n")
env = Environment(loader=FileSystemLoader("templates"))
env.globals["BASE_SCRIPT_URL"] = ghShared.BASE_SCRIPT_URL

userAgent = "unknown"
if "HTTP_USER_AGENT" in os.environ:
    userAgent = os.environ["HTTP_USER_AGENT"]
env.globals["MOBILE_PLATFORM"] = ghShared.getMobilePlatform(
    os.environ["HTTP_USER_AGENT"]
)

template = env.get_template("home.html")
print(
    template.render(
        uiTheme=uiTheme,
        galaxy=galaxy,
        loggedin=logged_state,
        currentUser=currentUser,
        loginResult=loginResult,
        linkappend=linkappend,
        url=url,
        pictureName=pictureName,
        imgNum=ghShared.imgNum,
        resourceGroupListShort=ghLists.getResourceGroupListShort(),
        professionList=ghLists.getProfessionList(galaxy),
        planetList=ghLists.getPlanetList(galaxy),
        resourceGroupList=ghLists.getResourceGroupList(),
        resourceTypeList=ghLists.getResourceTypeList(galaxy),
        galaxyList=ghLists.getGalaxyList(),
        galaxyAdmin=galaxyAdmin,
        
        
    )
)
