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
import datetime
import pytz
import json

with open('config.json') as f:
    config = json.load(f)

countryCodes = {}
with open('countries.db', 'r') as f:
    for row in f:
        country=row.strip().split('\t')
        countryCodes[country[0]] = {'name': country[2],
                                    'alpha3': country[1]}

KEY = config['key']

def call_api(KEY, path):
    url = 'https://eventor.orientering.se/api/' + path
    response = requests.get(url, headers={'ApiKey': KEY})

    return response.text

def get_timestring(date, time):
    d = datetime.datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M:%S")
    d = pytz.timezone('Europe/Stockholm').localize(d)
    return d.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

for eventConfig in config['events']:
    mainEventId = eventConfig['id']
    mainEventInfo = ET.fromstring(call_api(KEY, 'event/' + str(mainEventId)))

    mainEventName = mainEventInfo.find('Name').text
    mainEventRaceId = mainEventInfo.find('EventRace/EventRaceId').text

    print(mainEventName)

    mainFees = ET.fromstring(call_api(KEY, 'entryfees/events/' + str(mainEventId)))
    mainFeesByName = {}

    for entryFee in mainFees.findall('EntryFee'):
        feeName = entryFee.find('Name').text
        mainFeesByName[feeName] = {}
        mainFeesByName[feeName]['EntryFeeId'] = entryFee.find('EntryFeeId').text
        mainFeesByName[feeName]['Name'] = feeName
        entryFeeAmount = entryFee.find('Amount')
        mainFeesByName[feeName]['Amount'] = entryFeeAmount.text
        mainFeesByName[feeName]['Currency'] = entryFeeAmount.attrib['currency']
        mainFeesByName[feeName]['Taxable'] = (entryFee.attrib['taxIncluded'] == "Y")
        mainFeesByName[feeName]['ValueOperator'] = entryFee.attrib['valueOperator']
        if entryFee.find('ValidToDate'):
            mainFeesByName[feeName]['ValidTo'] = get_timestring(entryFee.find('ValidToDate/Date').text, entryFee.find('ValidToDate/Clock').text)
        if entryFee.find('ValidFromDate'):
            mainFeesByName[feeName]['ValidFrom'] = get_timestring(entryFee.find('ValidFromDate/Date').text, entryFee.find('ValidFromDate/Clock').text)

    eventClassToBaseClass = {}
    entryFeeToMainFee = {}
    for eventId in eventConfig['subids']:
        classes = ET.fromstring(call_api(KEY, 'eventclasses?eventId=' + str(eventId)))
        for eventClass in classes.findall('EventClass'):
            eventClassId = eventClass.find('EventClassId').text
            eventClassToBaseClass[eventClassId] = {}
            eventClassToBaseClass[eventClassId]['baseClassId'] = eventClass.find('BaseClassId').text
            eventClassToBaseClass[eventClassId]['name'] = eventClass.find('ClassShortName').text
            eventClassToBaseClass[eventClassId]['shortNname'] = eventClass.find('Name').text

        entryFees = ET.fromstring(call_api(KEY, 'entryfees/events/' + str(eventId)))
        for entryFee in entryFees.findall('EntryFee'):
            entryFeeToMainFee[entryFee.find('EntryFeeId').text] = mainFeesByName[entryFee.find('Name').text]


    country = mainEventInfo.find("Organiser/Organisation/Country/Name[@languageId='en']").text
    CountryAlpha3 = mainEventInfo.find("Organiser/Organisation/Country/Alpha3").attrib['value']

    root = ET.Element("EntryList")
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
    root.set('iofVersion', '3.0')
    root.set('xmlns', 'http://www.orienteering.org/datastandard/3.0')
    event = ET.SubElement(root, "Event")
    idNode = ET.SubElement(event, "Id")
    idNode.text = str(mainEventId)
    idNode.set('type', country)
    ET.SubElement(event, "Name").text = mainEventName

    startTime = ET.SubElement(event, "StartTime")
    ET.SubElement(startTime, "Date").text = mainEventInfo.find("StartDate/Date").text
    ET.SubElement(startTime, "Time").text = mainEventInfo.find("StartDate/Clock").text

    endTime = ET.SubElement(event, "EndTime")
    ET.SubElement(endTime, "Date").text = mainEventInfo.find("FinishDate/Date").text
    ET.SubElement(endTime, "Time").text = mainEventInfo.find("FinishDate/Clock").text

    ET.SubElement(event, "Status").text = 'Sanctioned'
    ET.SubElement(event, "Classification").text = "Local"
    ET.SubElement(event, "Form").text = "Individual"
    organiser = ET.SubElement(event, "Organiser")
    organiser.set("type", "Club")
    organiserId = ET.SubElement(organiser, "Id")
    organiserId.set("type", country)
    organiserId.text = mainEventInfo.find("Organiser/Organisation/OrganisationId").text
    ET.SubElement(organiser, "Name").text = mainEventInfo.find("Organiser/Organisation/Name").text
    ET.SubElement(organiser, "ShortName").text = mainEventInfo.find("Organiser/Organisation/ShortName").text
    ET.SubElement(organiser, "MediaName").text = mainEventInfo.find("Organiser/Organisation/MediaName").text
    ET.SubElement(organiser, "ParentOrganisationId").text = mainEventInfo.find("Organiser/Organisation/ParentOrganisation/OrganisationId").text
    organiserCountry = ET.SubElement(organiser, 'Country')
    organiserCountry.set('code', CountryAlpha3)
    organiserCountry.text = country
    
    race = ET.SubElement(event, 'Race')
    ET.SubElement(race, 'RaceNumber').text = "1"
    race.append(startTime)
    position = ET.SubElement(race, 'Position')
    position.set('lng', mainEventInfo.find("EventRace/EventCenterPosition").attrib["x"])
    position.set('lat', mainEventInfo.find("EventRace/EventCenterPosition").attrib["y"])

    entries = ET.fromstring(call_api(KEY, "entries?includeEntryFees=true&includePersonElement=true&includeOrganisationElement=true&eventIds=" + ','.join(map(str, eventConfig['subids']))))

    addedPersons = {}
    for entry in entries.findall('Entry'):
        personEntry = ET.SubElement(root, "PersonEntry")
        personEntry.set('modifyTime', get_timestring(entry.find("ModifyDate/Date").text, entry.find("ModifyDate/Clock").text))
        entryId = ET.SubElement(personEntry, 'Id')
        entryId.set('type', country)
        entryId.text = entry.find('EntryId').text

        person = ET.SubElement(personEntry, 'Person')
        person.set('sex', entry.find('Competitor/Person').attrib['sex'])
        person.set('modifyTime', get_timestring(entry.find("Competitor/Person/ModifyDate/Date").text, entry.find("Competitor/Person/ModifyDate/Clock").text))
        personId = ET.SubElement(person, 'Id')
        personId.set('type', country)
        personId.text = entry.find('Competitor/CompetitorId').text
        personName = ET.SubElement(person, 'Name')
        ET.SubElement(personName, 'Family').text = entry.find('Competitor/Person/PersonName/Family').text
        ET.SubElement(personName, 'Given').text = entry.find('Competitor/Person/PersonName/Given').text
        ET.SubElement(person, 'BirthDate').text = entry.find('Competitor/Person/BirthDate/Date').text
        nationality = entry.find('Competitor/Person/Nationality/CountryId')
        if nationality is None:
            # Assume sweden if no nationality is set
            countryObj = countryCodes['752']
        else:
            countryObj = countryCodes[nationality.attrib['value']]

        nationality = ET.SubElement(person, 'Nationality')
        nationality.set('code', countryObj['alpha3'])
        nationality.text = countryObj['name']

        if personId.text in addedPersons:
            addedPersons[personId.text]['classes'].append(eventClassToBaseClass[entry.find("EntryClass/EventClassId").text]['name'])
        else:
            addedPersons[personId.text] = {'name': entry.find('Competitor/Person/PersonName/Given').text + " " + entry.find('Competitor/Person/PersonName/Family').text,
                                           'classes': [eventClassToBaseClass[entry.find("EntryClass/EventClassId").text]['name']]}

        if entry.find("Competitor/Organisation"):
            organisation = ET.SubElement(personEntry, 'Organisation')
            organisation.set('type', 'Club')
            organisation.set('modifyTime', get_timestring(entry.find("Competitor/Organisation/ModifyDate/Date").text, entry.find("Competitor/Organisation/ModifyDate/Clock").text))
            organisationId = ET.SubElement(organisation, 'Id')
            organisationId.set('type', country)
            organisationId.text = entry.find('Competitor/Organisation/OrganisationId').text
            ET.SubElement(organisation, 'Name').text = entry.find("Competitor/Organisation/Name").text
            ET.SubElement(organisation, 'ShortName').text = entry.find("Competitor/Organisation/ShortName").text
            ET.SubElement(organisation, 'MediaName').text = entry.find("Competitor/Organisation/MediaName").text
            ET.SubElement(organisation, 'ParentOrganisationId').text = entry.find("Competitor/Organisation/ParentOrganisation/OrganisationId").text
            countryObj = None
            if entry.find('Competitor/Organisation/CountryId'):
                countryObj = countryCodes[entry.find('Competitor/Organisation/CountryId').attrib['value']]
            else:
                countryObj = countryCodes[entry.find('Competitor/Organisation/Country/CountryId').attrib['value']]
            organisationCountry = ET.SubElement(organisation, 'Country')
            organisationCountry.set('code', countryObj['alpha3'])
            organisationCountry.text = countryObj['name']

        if entry.find("Competitor/CCard"):
            controlCard = ET.SubElement(personEntry, 'ControlCard')
            controlCard.set("punchingSystem", "SI")
            controlCard.text = entry.find("Competitor/CCard/CCardId").text

        entryClass = ET.SubElement(personEntry, 'Class')
        entryClassId = ET.SubElement(entryClass, 'Id')
        entryClassId.set('type', country)
        entryClassId.text = eventClassToBaseClass[entry.find("EntryClass/EventClassId").text]['baseClassId']
        ET.SubElement(entryClass, 'Name').text = eventClassToBaseClass[entry.find("EntryClass/EventClassId").text]['name']

        ET.SubElement(personEntry, 'RaceNumber').text = "1"

        for entryFee in entry.findall("EntryEntryFee"):
            mainFee = entryFeeToMainFee[entryFee.find("EntryFeeId").text]
            assignedFee = ET.SubElement(personEntry, 'AssignedFee')
            fee = ET.SubElement(assignedFee, 'Fee')
            feeId = ET.SubElement(fee, 'Id')
            feeId.text = mainFee['EntryFeeId']
            ET.SubElement(fee, 'Name').text = mainFee['Name']
            feeId.set('type', country)
            if mainFee['ValueOperator'] == 'percent':
                ET.SubElement(fee, 'Percentage').text = mainFee['Amount']
                fee.set('type', 'Late')
            else:
                feeAmount = ET.SubElement(fee, 'Amount')
                feeAmount.set('currency', mainFee['Currency'])
                feeAmount.text = mainFee['Amount']
                taxableAmount = ET.SubElement(fee, 'TaxableAmount')
                taxableAmount.set('currency', mainFee['Currency'])
                taxableAmount.text = mainFee['Amount'] if mainFee['Taxable'] else "0"

            if 'ValidTo' in mainFee:
                ET.SubElement(fee, 'ValidToTime').text = mainFee['ValidTo']

            if 'ValidFrom' in mainFee:
                ET.SubElement(fee, 'ValidFromTime').text = mainFee['ValidFrom']

        ET.SubElement(personEntry, 'EntryTime').text = get_timestring(entry.find("EntryDate/Date").text, entry.find("EntryDate/Clock").text)
        

    filename = re.sub(r'[^\w]+', "_", mainEventName) + ".xml"
    et = ET.ElementTree(root)
    et.write(filename, 'utf-8', xml_declaration=True)

    for addedPerson in addedPersons:
        if len(addedPersons[addedPerson]['classes']) > 1:
            print(addedPersons[addedPerson])
