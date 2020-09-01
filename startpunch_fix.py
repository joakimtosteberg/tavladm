__copyright__  = """
Copyright 2020 Joakim Tosteberg (joakim.tosteberg@gmail.com)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License along with this program.  If not, see
<https://www.gnu.org/licenses/>.
"""
__license__ = "AGPLv3"

import sys

if len(sys.argv) < 2:
    print("Missing filename")
    sys.exit(0)

with open(sys.argv[1], "r") as f:
    for row in f:
        columns = row.split()
        if columns[2] != 'Okänd':
            continue
        if len(columns) != 6:
            print("Unable to parse: " + str(columns))
            continue
        card = int(columns[0])
        starttime = columns[4] + ' ' + columns[5]
        converted_card = ((card & 0xFF0000) >> 16) * 100000 + (card & 0xFFFF)
        print(f'{card} {converted_card} {starttime}')
