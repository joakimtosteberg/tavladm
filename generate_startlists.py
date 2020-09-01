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
import json

with open('config.json') as f:
    config = json.load(f)

KEY = config['key']

def call_api(KEY, path):
    url = 'https://eventor.orientering.se/api/' + path
    response = requests.get(url, headers={'ApiKey': KEY})

    return response.text

for eventConfig in config['events']:
    mainEventId = eventConfig['id']
    mainEventInfo = ET.fromstring(call_api(KEY, 'event/' + str(mainEventId)))

    mainEventName = mainEventInfo.find('Name').text
    mainEventRaceId = mainEventInfo.find('EventRace/EventRaceId').text

    filenamePrefix = re.sub(r'[^\w]+', "_", mainEventName)

    by_event_file = open(filenamePrefix + "_startlista_per_startgrupp.html", "w")
    by_event_file.write('<!DOCTYPE html><html><head><meta charset="utf-8"/></head><body>')

    print(mainEventName)

    entriesByClass = {}
    entriesByEvent = {}
    for eventClass in ET.fromstring(call_api(KEY, 'eventclasses?eventId=' + str(mainEventId))).findall('EventClass'):
        entriesByClass[eventClass.find('ClassShortName').text] = {}

    eventClassToBaseClass = {}
    for eventId in eventConfig['subids']:
        classes = ET.fromstring(call_api(KEY, 'eventclasses?eventId=' + str(eventId)))
        for eventClass in classes.findall('EventClass'):
            eventClassId = eventClass.find('EventClassId').text
            eventClassToBaseClass[eventClassId] = {}
            eventClassToBaseClass[eventClassId]['baseClassId'] = eventClass.find('BaseClassId').text
            eventClassToBaseClass[eventClassId]['name'] = eventClass.find('ClassShortName').text
            eventClassToBaseClass[eventClassId]['shortNname'] = eventClass.find('Name').text

        eventInfo = ET.fromstring(call_api(KEY, 'event/' + str(eventId)))
        eventName = eventInfo.find('Name').text
        eventNameShort = eventName
        for replacement in eventConfig['startlist_replacements']:
            eventNameShort = eventNameShort.replace(replacement['search'],
                                                    replacement['replace'])

        entries = ET.fromstring(call_api(KEY, "entries?includeEntryFees=true&includePersonElement=true&includeOrganisationElement=true&eventIds=" + str(eventId)))

        by_event_file.write(f'<div><div style="font-weight:bold; font-size: 20px; margin-top: 30px; margin-bottom: 5px;">{eventName}</div>')
        by_event_file.write('<table>')
        by_event_file.write(f'<table style="text-align:left;"><thead><tr><th>Namn</th><th>Klubb</th><th>Bricknummer</th><th>Klass</th></tr></thead>')

        for entry in entries.findall('Entry'):
            card = ''
            if entry.find("Competitor/CCard"):
                card = entry.find("Competitor/CCard/CCardId").text

            club = ''
            if entry.find("Competitor/Organisation"):
                club = entry.find("Competitor/Organisation/Name").text
                
            className = eventClassToBaseClass[entry.find("EntryClass/EventClassId").text]['name']
            classEntry = {'name': entry.find('Competitor/Person/PersonName/Given').text + ' ' + entry.find('Competitor/Person/PersonName/Family').text,
                          'club': club,
                          'card': card,
                          'class': className}

            if eventNameShort not in entriesByClass[className]:
                entriesByClass[className][eventNameShort] = []
            entriesByClass[className][eventNameShort].append(classEntry)

            by_event_file.write(f'<tr><td>{classEntry["name"]}</td><td>{classEntry["club"]}</td><td>{classEntry["card"]}</td><td>{classEntry["class"]}</td></tr>')
        by_event_file.write('</table></div>')

    by_event_file.write('</table></body></html>')
    by_event_file.close()
                
    by_class_file = open(filenamePrefix + "_startlista_per_klass.html", "w")
    by_class_file.write('<!DOCTYPE html><html><head><meta charset="utf-8"/></head><body>')
    for className in entriesByClass:
        if not entriesByClass[className]:
            continue
        by_class_file.write(f'<div><div style="font-weight:bold; font-size: 20px; margin-top: 30px; margin-bottom: 5px;">{className}</div>')
        by_class_file.write(f'<table style="text-align:left;"><thead><tr><th>Namn</th><th>Klubb</th><th>Bricknummer</th><th>Startgrupp</th></tr></thead>')
        for eventName in entriesByClass[className]:
            for classEntry in entriesByClass[className][eventName]:
                by_class_file.write(f'<tr><td>{classEntry["name"]}</td><td>{classEntry["club"]}</td><td>{classEntry["card"]}</td><td>{eventName}</td></tr>')
        by_class_file.write('</table></div>')
    by_class_file.write('</body></html>')
    by_class_file.close()
