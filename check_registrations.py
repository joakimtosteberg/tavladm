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

import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime
import pytz
import dateutil
import json
from dateutil import parser

with open('config.json') as f:
    config = json.load(f)

KEY = config['key']

def call_api(KEY, path):
    url = 'https://eventor.orientering.se/api/' + path
    response = requests.get(url, headers={'ApiKey': KEY})

    return response.text

for eventConfig in config['events']:
    mainEventId = eventConfig['id']
    for eventId in eventConfig['subids']:
        eventInfo = ET.fromstring(call_api(KEY, 'event/' + str(eventId)))
        eventName = eventInfo.find('Name').text
        entries = ET.fromstring(call_api(KEY, "entries?includeEntryFees=true&includePersonElement=true&includeOrganisationElement=true&eventIds=" + str(eventId)))
        numEntries = len(entries.findall('Entry'))
        eventUrl = 'https://eventor.orientering.se/EventAdmin/Edit/' + str(eventId)
        if eventInfo.find('EventStatusId').text == '6':
            print(f'{eventName}: ({numEntries}) {eventUrl}')
        else:
            print(f'{eventName}: {numEntries} {eventUrl}')
