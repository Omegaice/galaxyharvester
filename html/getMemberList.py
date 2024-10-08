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
import ghShared
import cgi

#
form = cgi.FieldStorage()

galaxy = form.getfirst("galaxy", "")
# escape input to prevent sql injection
galaxy = dbShared.dbInsertSafe(galaxy)

# Main program returns a table with top 20 users in galaxy with most resource adds
rowCount = 0
print("Content-type: text/html\n")
print('<table class="userData" width="100%">')
conn = dbShared.ghConn()
cursor = conn.cursor()
if cursor:
    print(
        '<thead><tr class="tableHead"><td>Rank</td><td>Member</td><td>Resources</td></th></thead>'
    )
    sqlStr = (
        "SELECT tUsers.userID, added, pictureName FROM tUsers LEFT JOIN tUserStats ON tUsers.userID = tUserStats.userID WHERE galaxy="
        + galaxy
        + " ORDER BY added DESC LIMIT 20"
    )
    cursor.execute(sqlStr)
    row = cursor.fetchone()

    while row != None:
        rowCount += 1
        print(
            '  <tr class="statRow"><td>'
            + str(rowCount)
            + '</td><td><a href="'
            + ghShared.BASE_SCRIPT_URL
            + "user.py/"
            + row[0]
            + '" class="nameLink"><img src="/images/users/'
            + str(row[2])
            + '" class="tinyAvatar" /><span style="vertical-align:4px;">'
            + row[0]
            + "</span></a></td><td>"
            + str(row[1])
            + "</td>"
        )
        print("  </tr>")
        row = cursor.fetchone()

    cursor.close()
conn.close()
print("  </table>")
