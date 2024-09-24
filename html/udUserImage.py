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
import ghShared
import dbSession
import dbShared

try:
    from PIL import Image
except ImportError:
    import Image
import urllib.parse
import time

# Get current url
try:
    url = os.environ["SCRIPT_NAME"]
except KeyError:
    url = ""

form = cgi.FieldStorage()
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
else:
    currentUser = ""
    loginResult = "success"
    sid = form.getfirst("gh_sid", "")

errstr = ""
if "avatar" not in form:
    errstr = "No avatar sent."
else:
    img_data = form["avatar"]
    if not img_data.file:
        errstr = "avatar is not a file."

src_url = form.getfirst("src_url", ghShared.BASE_SCRIPT_URL + "user.py/" + currentUser)
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)

# Get a session
logged_state = 0
linkappend = ""

sess = dbSession.getSession(sid)
if sess != "":
    logged_state = 1
    currentUser = sess
    if useCookies == 0:
        linkappend = "gh_sid=" + sid

#  Check for errors
if errstr == "":
    imgName = img_data.filename
if logged_state == 0:
    errstr = errstr + "You must be logged in to update your avatar. \r\n"
try:
    im = Image.open(img_data.file)
except:
    errstr = (
        errstr
        + "I don't recognize the file you uploaded as an image ("
        + imgName
        + ").  Please make sure it is a jpg, gif, or png.  \r\n"
    )

if errstr != "":
    result = (
        "Your Avatar could not be updated because of the following errors:\r\n" + errstr
    )
else:
    result = ""

    # resize if too big
    xsize, ysize = im.size
    newwidth = xsize
    newheight = ysize
    if xsize > 320 or ysize > 320:
        if xsize >= ysize:
            newheight = ysize * (320.0 / xsize)
            newwidth = 320
        elif ysize > xsize:
            newwidth = xsize * (320.0 / ysize)
            newheight = 320
    try:
        im.thumbnail((newwidth, newheight))
    except IOError:
        result = "I can't handle that type of image file, please try a different one."

    if result == "":
        # write image file
        imageName = currentUser + str(time.time()) + ".jpg"
        # remove alpha channel incase its there so we are jpg compatible
        im = im.convert("RGB")
        im.save("images/users/" + imageName, "JPEG")

        # update user record to point to file
        conn = dbShared.ghConn()
        cursor = conn.cursor()
        # get old image file name
        cursor.execute(
            "SELECT pictureName FROM tUsers WHERE userID='" + currentUser + "';"
        )
        row = cursor.fetchone()
        if row != None:
            result = row[0]
        # update to new file name
        cursor.execute(
            "UPDATE tUsers SET pictureName='"
            + imageName
            + "' WHERE userID='"
            + currentUser
            + "';"
        )

        cursor.close()
        conn.close()
        # remove old file
        if result != None and result != "default.jpg":
            os.remove("images/users/" + result)

        result = "Avatar Updated"


if useCookies:
    C["avatarAttempt"] = result
    C["avatarAttempt"]["max-age"] = 60
    print(C)
else:
    linkappend = linkappend + "&avatarAttempt=" + urllib.parse.quote(result)

if currentUser != None:
    # redirect back to user page
    print("Status: 303 See Other")
    print(
        "Location: {0}user.py/{1}?{2}".format(
            ghShared.BASE_SCRIPT_URL, currentUser, linkappend
        )
    )
    print("")
else:
    print(result)
