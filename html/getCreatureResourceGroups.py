#!/usr/bin/env python3
"""

Copyright 2020 Paul Willworth <ioscode@gmail.com> & Chet Bortz <thrusterhead@gmail.com>

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

#
form = cgi.FieldStorage()

galaxy = form.getfirst("galaxy", "0")
# escape input to prevent sql injection
galaxy = dbShared.dbInsertSafe(galaxy)

# Main program
clist = ""
containerType = ""

conn = dbShared.ghConn()
cursor = conn.cursor()

if cursor:
    sqlStr = """
    SELECT tResourceGroup.resourceGroup,
         tResourceGroup.groupName,
         COUNT(tResourceTypeCreature.resourceType) AS creatureCount,
         tResourceGroup.containerType
    FROM tResourceGroup
      INNER JOIN tResourceType ON tResourceType.resourceGroup = tResourceGroup.resourceGroup
      INNER JOIN tResourceTypeCreature ON tResourceTypeCreature.resourceType = tResourceType.resourceType
    WHERE tResourceGroup.containerType IN ('bone', 'hide', 'meat', 'milk')
      AND tResourceTypeCreature.galaxy IN (0, %s)
    GROUP BY tResourceGroup.resourceGroup
    ORDER BY tResourceGroup.resourceGroup
  """

    # Execute SQL and fetch first row
    cursor.execute(sqlStr, (galaxy,))
    row = cursor.fetchone()

    clist += '<ul class="schematics">'

    while row != None:
        # Show large container header if container changed
        if row[3] != containerType:
            containerType = row[3]
            clist += (
                '<li><h3><a href="/creatureList.py/%s" class="bigLink">%s</a></h3></li>'
                % (containerType, containerType.title())
            )

        clist += '<li><a href="/creatureList.py/%s">%s</a> (%s)</li>' % (
            row[0],
            row[1],
            row[2],
        )
        row = cursor.fetchone()

    clist += "</ul>"
    cursor.close()
conn.close()

print("Content-type: text/html\n")
print(clist)
