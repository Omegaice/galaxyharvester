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

import os
import cgi
from http import cookies
import dbSession
import dbShared

# Get current url
try:
    url = os.environ["SCRIPT_NAME"]
except KeyError:
    url = ""

form = cgi.FieldStorage()
# Get Cookies
errorstr = ""
C = cookies.SimpleCookie()
try:
    C.load(os.environ["HTTP_COOKIE"])
except KeyError:
    errorstr = "no cookies\n"

if errorstr == "":
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
else:
    currentUser = ""
    loginResult = "success"
    sid = form.getfirst("gh_sid", "")

alert = form.getfirst("alert", "")
status = form.getfirst("status")
alertType = form.getfirst("alertType", "")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
# Get a session
logged_state = 0
linkappend = ""

sess = dbSession.getSession(sid)
if sess != "":
    logged_state = 1
    currentUser = sess
    linkappend = "gh_sid=" + sid

alertCriteria = " WHERE 0 = 1"

#  Check for errors
errstr = ""
if not alert.isdigit() and not alertType.isdigit():
    errstr = errstr + "You must provide a valid alert id or alert type. \r\n"
if not status.isdigit():
    errstr = errstr + "That is not a valid status id. \r\n"
if logged_state == 0:
    errstr = errstr + "You must be logged in to update alert status. \r\n"

if alertType.isdigit():
    alertCriteria = " WHERE userID='{0}'".format(currentUser)

if alert.isdigit():
    cconn = dbShared.ghConn()
    ccursor = cconn.cursor()

    ccursor.execute("SELECT userID FROM tAlerts WHERE alertID=" + str(alert) + ";")
    row = ccursor.fetchone()
    if row != None:
        alertUser = row[0]
    if alertUser != currentUser:
        errstr = errstr + "That alert does not belong to you."

    ccursor.close()
    cconn.close()
    alertCriteria = " WHERE alertID={0}".format(alert)

if errstr != "":
    result = (
        "Error: Alert could not be updated because of the following errors:\r\n"
        + errstr
    )
else:
    conn = dbShared.ghConn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tAlerts SET alertStatus="
        + str(status)
        + ", statusChanged=NOW()"
        + alertCriteria
        + ";"
    )
    if alert.isdigit():
        result = alert
    else:
        result = "{0} alerts updated".format(cursor.rowcount)
    cursor.close()
    conn.close()


print("Content-Type: text/html\n")
print(result)
