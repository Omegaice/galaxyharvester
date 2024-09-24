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
import sys
from http import cookies
import dbSession
import dbShared
import cgi
from xml.dom import minidom
import ghShared

#
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

# Get form info
resourceType = form.getfirst("resourceType", "")
galaxy = form.getfirst("galaxy", "")
creatureName = form.getfirst("creatureName", "")
harvestYield = form.getfirst("harvestYield", "")
missionLevel = form.getfirst("missionLevel", "")
forceOp = form.getfirst("forceOp", "")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
resourceType = dbShared.dbInsertSafe(resourceType)
galaxy = dbShared.dbInsertSafe(galaxy)
creatureName = dbShared.dbInsertSafe(creatureName)

result = ""
# Get a session
logged_state = 0

sess = dbSession.getSession(sid)
if sess != "":
    logged_state = 1
    currentUser = sess


def addCreature(conn, resourceType, creatureName, harvestYield, missionLevel, galaxy):
    # Add new creature data
    returnStr = "Creature data not added."
    result = 0
    cursor = conn.cursor()
    if missionLevel == "":
        missionLevel = None
    tempSQL = "INSERT INTO tResourceTypeCreature (resourceType, speciesName, maxAmount, missionLevel, galaxy, enteredBy) VALUES (%s, %s, %s, %s, %s, %s);"
    try:
        cursor.execute(
            tempSQL,
            (
                resourceType,
                creatureName,
                harvestYield,
                missionLevel,
                galaxy,
                currentUser,
            ),
        )
        result = cursor.rowcount
    except Exception as e:
        returnStr = "Error: Add Failed. {0}".format(e)

    if result > 0:
        returnStr = "Creature data added."
    cursor.close()
    return returnStr


def updateCreature(
    conn, resourceType, creatureName, harvestYield, missionLevel, galaxy
):
    # Update creature information
    returnStr = ""
    cursor = conn.cursor()
    if missionLevel == "":
        missionLevel = None
    tempSQL = "UPDATE tResourceTypeCreature SET maxAmount=%s, missionLevel=%s WHERE resourceType=%s and speciesName=%s and galaxy=%s;"
    cursor.execute(
        tempSQL, (harvestYield, missionLevel, resourceType, creatureName, galaxy)
    )
    result = cursor.rowcount
    if result < 1:
        returnStr = "Error: creature data not updated."
    else:
        returnStr = " creature data updated."

    cursor.close()
    return returnStr


#  Check for errors
errstr = ""

if len(resourceType) < 1:
    errstr = errstr + "Error: no resource type provided. \r\n"
if galaxy == "":
    errstr = errstr + "Error: no galaxy selected. \r\n"
if creatureName == "":
    errstr = errstr + "Error: You must the creature name. \r\n"

if len(harvestYield) > 0 and harvestYield.isdigit() != True:
    errstr = errstr + "Error: Harvest yield was not a valid number."
if len(missionLevel) > 0 and missionLevel.isdigit() != True:
    errstr = errstr + "Error: Harvest yield was not a valid number."

# Only process if no errors or just verifying
if errstr == "":
    result = ""
    if logged_state > 0:
        try:
            conn = dbShared.ghConn()
        except Exception:
            result = "Error: could not connect to database"

        # Get user reputation for later checking
        stats = dbShared.getUserStats(currentUser, galaxy).split(",")
        userReputation = int(stats[2])
        # data already entered?
        if forceOp == "edit":
            # check owner
            cursor = conn.cursor()

            if cursor:
                cursor.execute(
                    "SELECT enteredBy FROM tResourceTypeCreature WHERE resourceType=%s AND speciesName=%s AND galaxy=%s;",
                    (resourceType, creatureName, galaxy),
                )
                row = cursor.fetchone()

                if row != None:
                    owner = row[0]
                else:
                    owner = ""

                cursor.close()

                # edit it
                if (
                    owner == currentUser
                    or userReputation >= ghShared.MIN_REP_VALS["EDIT_OTHER_CREATURE"]
                    or dbShared.getUserAdmin(conn, currentUser, galaxy)
                ):
                    result = "edit: "
                    result = result + updateCreature(
                        conn,
                        resourceType,
                        creatureName,
                        harvestYield,
                        missionLevel,
                        galaxy,
                    )
                else:
                    result = "Error: You do not yet have permission to edit others' creature data."
            else:
                result = "Error: No database connection"

        else:
            if userReputation >= ghShared.MIN_REP_VALS[
                "ADD_CREATURE"
            ] or dbShared.getUserAdmin(conn, currentUser, galaxy):
                result = addCreature(
                    conn, resourceType, creatureName, harvestYield, missionLevel, galaxy
                )
            else:
                result = "Error: You don't have permission to add creature data yet."

        conn.close()
    else:
        result = "Error: must be logged in to add creature data"
else:
    result = errstr

print("Content-type: text/xml\n")
doc = minidom.Document()
eRoot = doc.createElement("result")
doc.appendChild(eRoot)

eText = doc.createElement("resultText")
tText = doc.createTextNode(result)
eText.appendChild(tText)
eRoot.appendChild(eText)
print(doc.toxml())

if result.find("Error:") > -1:
    sys.exit(500)
else:
    sys.exit(200)
