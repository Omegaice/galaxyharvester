#!/usr/bin/env python3
"""

Copyright 2019 Paul Willworth <ioscode@gmail.com>

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
import dbShared
import time
from datetime import datetime

C = cookies.SimpleCookie()
useCookies = 1
errorstr = ""
try:
    C.load(os.environ["HTTP_COOKIE"])
except KeyError:
    useCookies = 0

form = cgi.FieldStorage()

verifycode = form.getfirst("vc")
verifytype = form.getfirst("vt")
# escape input to prevent sql injection
verifycode = dbShared.dbInsertSafe(verifycode)

result = "verifysuccess"
if verifycode == None:
    errorstr = "Missing verification code"

if errorstr != "":
    result = "verifyfail"
else:
    conn = dbShared.ghConn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT userID, created FROM tUsers WHERE verificationCode=%s;", [verifycode]
    )
    row = cursor.fetchone()
    if row != None:
        timeSinceCreated = datetime.fromtimestamp(time.time()) - row[1]
        if timeSinceCreated.days > 0 and verifytype != "mail":
            result = "verifyfail"
            errorstr = "That verification code is expired.  Please try joining again to get a new code."
        else:
            if verifytype == "mail":
                result = "verifymailsuccess"
                updatestr = "UPDATE tUsers SET emailAddress=emailChange WHERE userID='{0}';".format(
                    row[0]
                )
            else:
                remoteIP = os.environ["REMOTE_ADDR"]
                updatestr = "UPDATE tUsers SET userState=1, emailVerifyDate=NOW(), emailVerifyIP='{0}' WHERE userID='{1}';".format(
                    remoteIP, row[0]
                )
            cursor.execute(updatestr)
            updatedCount = cursor.rowcount
            if not updatedCount > 0:
                result = "verifyfail"
                errorstr = "Could not find user to verify."
    else:
        result = "verifyfail"
        errorstr = "That is not a valid verification code."

    cursor.close()
    conn.close()

print("Content-Type: text/html\n")
print(
    '<html><head><script type=text/javascript>document.location.href="message.py?action='
    + result
    + "&actionreason="
    + errorstr
    + '"</script></head><body></body></html>'
)
