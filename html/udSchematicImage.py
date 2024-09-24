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
import ghShared

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

if "schemImage" not in form:
    errstr = "No image sent."
img_data = form["schemImage"]
if not img_data.file:
    errstr = "image sent is not a file."
src_url = form.getfirst("src_url", "/schematics.py")
schematicID = form.getfirst("schematicID", "")
copyFromSchem = form.getfirst("copyFromSchem", "")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
schematicID = dbShared.dbInsertSafe(schematicID)
copyFromSchem = dbShared.dbInsertSafe(copyFromSchem)

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
errstr = ""
imgName = img_data.filename
if logged_state == 0:
    errstr = errstr + "You must be logged in to add schematic images. \r\n"
else:
    # Only allow update if user has enough reputation
    stats = dbShared.getUserStats(currentUser, 0).split(",")
    if int(stats[2]) < ghShared.MIN_REP_VALS["UPDATE_SCHEMATIC_IMAGE"]:
        errstr = "Error: You must earn a little reputation on the site before you can update schematic images.  Try adding or verifying some resources first. \r\n"

if schematicID == "":
    errstr = errstr + "You must specify a schematic upload an image for. \r\n"
else:
    src_url = src_url + "/" + schematicID

if copyFromSchem == "":
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
    result = "Errors:\r\n" + errstr
else:
    result = ""
    imageType = 0
    conn = dbShared.ghConn()
    if copyFromSchem == "":
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
            im.thumbnail((int(newwidth), int(newheight)))
        except IOError:
            result = (
                "I can't handle that type of image file, please try a different one."
            )

        if result == "":
            # write image file
            imageName = schematicID + str(time.time()) + ".jpg"
            im.save("images/schematics/" + imageName, "JPEG")
    else:
        # use already existing image name
        cursor = conn.cursor()
        # get copy from file name
        cursor.execute(
            "SELECT imageName FROM tSchematicImages WHERE imageType=1 AND schematicID='"
            + copyFromSchem
            + "';"
        )
        row = cursor.fetchone()
        if row != None:
            imageName = row[0]
        else:
            result = "That schematic does not have any image to copy from."
        cursor.close()

    if result == "":
        # update user record to point to file
        cursor = conn.cursor()
        # get old image file name
        cursor.execute(
            "SELECT imageName FROM tSchematicImages WHERE imageType=1 AND schematicID='"
            + schematicID
            + "';"
        )
        row = cursor.fetchone()
        if row != None:
            result = row[0]
            result = cursor.execute(
                "UPDATE tSchematicImages SET imageType=imageType+1 WHERE schematicID='"
                + schematicID
                + "';"
            )
            if not (result > 0):
                result = "There was an error replacing the old image."
            else:
                imageType = 1
        else:
            imageType = 1
        # update to new file name
        cursor.execute(
            "INSERT INTO tSchematicImages (schematicID, imageType, imageName, addedBy) VALUES ('"
            + schematicID
            + "',"
            + str(imageType)
            + ",'"
            + imageName
            + "','"
            + currentUser
            + "');"
        )

        cursor.close()

        if imageType == 1:
            result = "Image Added"
            if copyFromSchem == "":
                updateType = "New upload"
            else:
                updateType = "Copy from {0}".format(copyFromSchem)
            dbShared.logSchematicEvent(
                0,
                0,
                schematicID,
                currentUser,
                "i",
                "Updated schematic image to {0} by {1}.".format(imageName, updateType),
                "history",
            )
        else:
            result = "Image has been added and will become active as the new image for this schematic after it has been reviewed."
    conn.close()


if useCookies:
    C["schemImageAttempt"] = result
    C["schemImageAttempt"]["max-age"] = 60
    print(C)
else:
    linkappend = linkappend + "&schemImageAttempt=" + urllib.parse.quote(result)

print("Content-Type: text/html\n")
if src_url != None:
    print(
        '<html><head><script type=text/javascript>document.location.href="'
        + src_url
        + "?"
        + linkappend
        + '"</script></head><body></body></html>'
    )
else:
    print(result)
