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

import dbShared
import cgi

try:
    import json
except ImportError:
    import simplejson as json
#
form = cgi.FieldStorage()

q = form.getfirst("query", "")
# escape input to prevent sql injection
q = dbShared.dbInsertSafe(q)

users = [""]
qlen = len(q)
if qlen > 0:
    moreCriteria = " AND SUBSTRING(userID, 1, " + str(qlen) + ") = '" + q + "'"
else:
    moreCriteria = ""

# Main program
print("Content-type: text/html; charset=UTF-8\n")
conn = dbShared.ghConn()
cursor = conn.cursor()
if cursor:
    sqlStr = (
        "SELECT userID FROM tUsers WHERE created IS NOT NULL"
        + moreCriteria
        + " ORDER BY userID"
    )
    cursor.execute(sqlStr)
    row = cursor.fetchone()

    while row != None:
        users.append(row[0])
        row = cursor.fetchone()

    cursor.close()
conn.close()
print(json.dumps({"query": q, "suggestions": users}))
