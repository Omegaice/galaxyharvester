#!/usr/bin/env python3
"""

Copyright 2017 Paul Willworth <ioscode@gmail.com>

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
galaxy = form.getfirst("galaxy", "")
fltCount = form.getfirst("fltCount", "")
fltOrders = form.getfirst("fltOrders", "")
fltTypes = form.getfirst("fltTypes", "")
fltValues = form.getfirst("fltValues", "")
CRmins = form.getfirst("CRmins", "")
CDmins = form.getfirst("CDmins", "")
DRmins = form.getfirst("DRmins", "")
FLmins = form.getfirst("FLmins", "")
HRmins = form.getfirst("HRmins", "")
MAmins = form.getfirst("MAmins", "")
PEmins = form.getfirst("PEmins", "")
OQmins = form.getfirst("OQmins", "")
SRmins = form.getfirst("SRmins", "")
UTmins = form.getfirst("UTmins", "")
ERmins = form.getfirst("ERmins", "")
qualityMins = form.getfirst("qualityMins", "")
alertTypes = form.getfirst("alertTypes", "")
fltGroups = form.getfirst("fltGroups", "")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)
fltCount = dbShared.dbInsertSafe(fltCount)
fltOrders = dbShared.dbInsertSafe(fltOrders)
fltTypes = dbShared.dbInsertSafe(fltTypes)
fltValues = dbShared.dbInsertSafe(fltValues)
CRmins = dbShared.dbInsertSafe(CRmins)
CDmins = dbShared.dbInsertSafe(CDmins)
DRmins = dbShared.dbInsertSafe(DRmins)
FLmins = dbShared.dbInsertSafe(FLmins)
HRmins = dbShared.dbInsertSafe(HRmins)
MAmins = dbShared.dbInsertSafe(MAmins)
PEmins = dbShared.dbInsertSafe(PEmins)
OQmins = dbShared.dbInsertSafe(OQmins)
SRmins = dbShared.dbInsertSafe(SRmins)
UTmins = dbShared.dbInsertSafe(UTmins)
ERmins = dbShared.dbInsertSafe(ERmins)
qualityMins = dbShared.dbInsertSafe(qualityMins)
alertTypes = dbShared.dbInsertSafe(alertTypes)
fltGroups = dbShared.dbInsertSafe(fltGroups)

fltOrders = fltOrders.split(",")
fltUpdated = fltTypes.split(",")
fltTypes = fltTypes.split(",")
fltValues = fltValues.split(",")
CRmins = CRmins.split(",")
CDmins = CDmins.split(",")
DRmins = DRmins.split(",")
FLmins = FLmins.split(",")
HRmins = HRmins.split(",")
MAmins = MAmins.split(",")
PEmins = PEmins.split(",")
OQmins = OQmins.split(",")
SRmins = SRmins.split(",")
UTmins = UTmins.split(",")
ERmins = ERmins.split(",")
qualityMins = qualityMins.split(",")
alertTypes = alertTypes.split(",")
fltGroups = fltGroups.split(",")

result = ""
# Get a session
logged_state = 0

sess = dbSession.getSession(sid)
if sess != "":
    logged_state = 1
    currentUser = sess


def n2n(inVal):
    if inVal == "" or inVal == None or inVal == "undefined" or inVal == "None":
        return "NULL"
    else:
        return str(inVal)


#  Check for errors
errstr = ""
fc = len(fltValues)
if galaxy == "":
    errstr = errstr + "Error: no galaxy selected. \r\n"
if (
    fc == len(fltOrders)
    and fc == len(fltTypes)
    and fc == len(alertTypes)
    and fc == len(CRmins)
    and fc == len(CDmins)
    and fc == len(DRmins)
    and fc == len(FLmins)
    and fc == len(HRmins)
    and fc == len(MAmins)
    and fc == len(PEmins)
    and fc == len(OQmins)
    and fc == len(SRmins)
    and fc == len(UTmins)
    and fc == len(ERmins)
    and fc == len(fltGroups)
    and fc == len(qualityMins)
):
    for x in range(len(fltValues)):
        if fltValues[x] != "":
            if fltTypes[x].isdigit() != True:
                errstr = (
                    errstr + "Error: Type for " + fltValues[x] + " was not valid. \r\n"
                )
            if alertTypes[x].isdigit() != True:
                errstr = (
                    errstr
                    + "Error: Alert options for "
                    + fltValues[x]
                    + " was not valid. \r\n"
                )
            if CRmins[x].isdigit() != True:
                CRmins[x] = 0
            if CDmins[x].isdigit() != True:
                CDmins[x] = 0
            if DRmins[x].isdigit() != True:
                DRmins[x] = 0
            if FLmins[x].isdigit() != True:
                FLmins[x] = 0
            if HRmins[x].isdigit() != True:
                HRmins[x] = 0
            if MAmins[x].isdigit() != True:
                MAmins[x] = 0
            if PEmins[x].isdigit() != True:
                PEmins[x] = 0
            if OQmins[x].isdigit() != True:
                OQmins[x] = 0
            if SRmins[x].isdigit() != True:
                SRmins[x] = 0
            if UTmins[x].isdigit() != True:
                UTmins[x] = 0
            if ERmins[x].isdigit() != True:
                ERmins[x] = 0
            if qualityMins[x].isdigit() != True:
                qualityMins[x] = 0
            fltUpdated[x] = 0
else:
    errstr = (
        errstr
        + "Error: One of the filters sent is missing a type, alert, group, or stat. Orders: "
        + str(len(fltOrders))
        + " Types: "
        + str(len(fltTypes))
        + " Values: "
        + str(fc)
        + " AlertTypes: "
        + str(len(alertTypes))
        + " Groups: "
        + str(len(fltGroups))
        + " CRs: "
        + str(len(CRmins))
        + " CDs: "
        + str(len(CDmins))
        + " DRs: "
        + str(len(DRmins))
        + " FLs: "
        + str(len(FLmins))
        + " HRs: "
        + str(len(HRmins))
        + " MAs: "
        + str(len(MAmins))
        + " PEs: "
        + str(len(PEmins))
        + " OQs: "
        + str(len(OQmins))
        + " SRs: "
        + str(len(SRmins))
        + " UTs: "
        + str(len(UTmins))
        + " ERs: "
        + str(len(ERmins))
        + "\r\n"
    )


# Only process if no errors
if errstr == "":
    result = ""
    if logged_state > 0:
        # Delete alerts to be removed and update those to be updated
        udCount = 0
        delCount = 0
        addCount = 0
        conn = dbShared.ghConn()
        # open list of users existing filters
        cursor = conn.cursor()
        cursor.execute(
            "SELECT rowOrder, fltType, fltValue FROM tFilters WHERE galaxy="
            + str(galaxy)
            + " AND userID='"
            + currentUser
            + "';"
        )
        row = cursor.fetchone()
        while row != None:
            rowOrder = row[0]
            fltType = row[1]
            fltValue = row[2]
            fltFound = False
            for x in range(fc):
                if (
                    str(rowOrder) == str(fltOrders[x])
                    and str(fltType) == str(fltTypes[x])
                    and fltValue == fltValues[x]
                ):
                    fltFound = True
                    # update details of filter
                    cursor2 = conn.cursor()
                    tempSQL = (
                        "UPDATE tFilters SET alertTypes="
                        + str(alertTypes[x])
                        + ", CRmin="
                        + str(CRmins[x])
                        + ", CDmin="
                        + str(CDmins[x])
                        + ", DRmin="
                        + str(DRmins[x])
                        + ", FLmin="
                        + str(FLmins[x])
                        + ", HRmin="
                        + str(HRmins[x])
                        + ", MAmin="
                        + str(MAmins[x])
                        + ", PEmin="
                        + str(PEmins[x])
                        + ", OQmin="
                        + str(OQmins[x])
                        + ", SRmin="
                        + str(SRmins[x])
                        + ", UTmin="
                        + str(UTmins[x])
                        + ", ERmin="
                        + str(ERmins[x])
                        + ", minQuality="
                        + str(qualityMins[x])
                        + ", fltGroup='"
                        + fltGroups[x]
                        + "' WHERE userID='"
                        + currentUser
                        + "' AND galaxy="
                        + str(galaxy)
                        + " AND rowOrder="
                        + str(rowOrder)
                        + " AND fltType="
                        + str(fltType)
                        + " AND fltValue='"
                        + fltValue
                        + "';"
                    )
                    cursor2.execute(tempSQL)
                    fltUpdated[x] = 1
                    udCount += cursor2.rowcount

                    cursor2.close()

            if fltFound == False:
                # delete the filter if its not in the list passed
                cursor2 = conn.cursor()
                tempSQL = (
                    "DELETE FROM tFilters WHERE galaxy="
                    + str(galaxy)
                    + " AND userID='"
                    + currentUser
                    + "' AND rowOrder="
                    + str(rowOrder)
                    + " AND fltType="
                    + str(fltType)
                    + " AND fltValue='"
                    + fltValue
                    + "';"
                )
                cursor2.execute(tempSQL)
                delCount += cursor2.rowcount
                cursor2.close()

            row = cursor.fetchone()

        cursor.close()

        # Add new filters
        for x in range(len(fltValues)):
            if fltValues[x] != "" and fltUpdated[x] == 0:
                # if the filter was not marked as updated previously, it does not exist and we need to add it
                cursor2 = conn.cursor()
                tempSQL = (
                    "INSERT INTO tFilters (userID, galaxy, rowOrder, fltType, fltValue, alertTypes, CRmin, CDmin, DRmin, FLmin, HRmin, MAmin, PEmin, OQmin, SRmin, UTmin, ERmin, fltGroup, minQuality) VALUES ('"
                    + currentUser
                    + "', "
                    + str(galaxy)
                    + ", "
                    + str(fltOrders[x])
                    + ", "
                    + str(fltTypes[x])
                    + ", '"
                    + fltValues[x]
                    + "', "
                    + str(alertTypes[x])
                    + ", "
                    + str(CRmins[x])
                    + ", "
                    + str(CDmins[x])
                    + ", "
                    + str(DRmins[x])
                    + ", "
                    + str(FLmins[x])
                    + ", "
                    + str(HRmins[x])
                    + ", "
                    + str(MAmins[x])
                    + ", "
                    + str(PEmins[x])
                    + ", "
                    + str(OQmins[x])
                    + ", "
                    + str(SRmins[x])
                    + ", "
                    + str(UTmins[x])
                    + ", "
                    + str(ERmins[x])
                    + ", '"
                    + fltGroups[x]
                    + "', "
                    + str(qualityMins[x])
                    + ");"
                )
                cursor2.execute(tempSQL)
                addCount += cursor2.rowcount
                cursor2.close()

        conn.close()
        result = (
            "Filter update complete: "
            + str(addCount)
            + " added, "
            + str(udCount)
            + " updated, "
            + str(delCount)
            + " deleted."
        )
    else:
        result = "Error: must be logged in to update alerts"
else:
    result = errstr

print("Content-type: text/xml\n")
doc = minidom.Document()
eRoot = doc.createElement("result")
doc.appendChild(eRoot)

eName = doc.createElement("fltCount")
tName = doc.createTextNode(str(fltCount))
eName.appendChild(tName)
eRoot.appendChild(eName)
eText = doc.createElement("resultText")
tText = doc.createTextNode(result)
eText.appendChild(tText)
eRoot.appendChild(eText)
print(doc.toxml())

if result.find("Error:") > -1:
    sys.exit(500)
else:
    sys.exit(200)
