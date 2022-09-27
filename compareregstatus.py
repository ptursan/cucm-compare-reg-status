# -*- coding: utf-8 -*-

import sys
from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from zeep.exceptions import Fault
from zeep.plugins import HistoryPlugin
from requests import Session
from requests.auth import HTTPBasicAuth
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from lxml import etree


if __name__ == "__main__":
    disable_warnings(InsecureRequestWarning)

    # Cluster specific variables
    username = 'administrator'
    password = 'dCloud123!'
    server = 'ucm-sub1.dcloud.cisco.com'

    # Common Plugins
    history = HistoryPlugin()

    # Build Client Object for AXL Service
    axl_wsdl = 'file://C:/Development/Resources/axlsqltoolkit/schema/current/AXLAPI.wsdl'
    axl_location = f'https://{server}:8443/axl/'
    axl_binding = '{http://www.cisco.com/AXLAPIService/}AXLAPIBinding'

    axl_session = Session()
    axl_session.verify = False
    axl_session.auth = HTTPBasicAuth(username, password)

    axl_transport = Transport(cache=SqliteCache(), session=axl_session,
                              timeout=20)
    axl_client = Client(wsdl=axl_wsdl, transport=axl_transport,
                        plugins=[history])
    axl_service = axl_client.create_service(axl_binding, axl_location)

    # Build Client Object for RisPort70 Service

    wsdl = f'https://{server}:8443/realtimeservice2/services/RISService70?wsdl'
    location = f'https://{server}:8443/realtimeservice2/services/RISService70'
    binding = '{http://schemas.cisco.com/ast/soap}RisBinding'
    session = Session()
    session.verify = False
    session.auth = HTTPBasicAuth(username, password)

    transport = Transport(cache=SqliteCache(), session=session, timeout=20)
    client = Client(wsdl=wsdl, transport=transport, plugins=[history])
    service = client.create_service(binding, location)

    def show_history():
        for hist in [history.last_sent, history.last_received]:
            print(etree.tostring(hist["envelope"],
                                 encoding="unicode",
                                 pretty_print=True))

    # Get List of Phones to query via AXL
    # (required when using SelectCmDeviceExt)
    try:
        resp = axl_service.listPhone(searchCriteria={'name': '%'},
                                     returnedTags={'name': ''})
    except Fault:
        show_history()
        raise

    # Build item list for RisPort70 SelectCmDeviceExt
    items = []
    for phone in resp['return'].phone:
        items.append(phone.name)

    if len(items) > 1000:
        print("This demo app only supports under 1000 results")
        print("Exiting...")
        sys.exit()

    # Run SelectCmDeviceExt
    CmSelectionCriteria = {
        'MaxReturnedDevices': '1000',
        'DeviceClass': 'Phone',
        'Model': '255',
        'Status': 'Any',
        'NodeName': '',
        'SelectBy': 'Name',
        'SelectItems': {
            'item': items
        },
        'Protocol': 'Any',
        'DownloadStatus': 'Any'
    }

    StateInfo = ''

    try:
        resp = service.selectCmDeviceExt(
            CmSelectionCriteria=CmSelectionCriteria,
            StateInfo=StateInfo)
    except Fault:
        show_history()
        raise

    snapshot = {}

    CmNodes = resp.SelectCmDeviceResult.CmNodes.item
    for CmNode in CmNodes:
        if len(CmNode.CmDevices.item) > 0:
            # If the node has returned CmDevices, save to the snapshot to
            # later compare
            for item in CmNode.CmDevices.item:
                # Creates a new list if the key in the dictionary isn't yet
                # assigned or simply appends to the entry if there is already
                # a value present
                snapshot.setdefault(CmNode.Name,
                                    []).append({'Name': item.Name,
                                                'Status': item.Status})

    print("Successfully captured current Risport status.")

while True:
    print("Press Enter to query Risport and compare to the initial result")
    print("or Ctrl+C to exit")
    input("...")

    try:
        resp = service.selectCmDeviceExt(
            CmSelectionCriteria=CmSelectionCriteria,
            StateInfo=StateInfo)
    except Fault:
        show_history()
        raise

    no_change = True
    CmNodes = resp.SelectCmDeviceResult.CmNodes.item
    for CmNode in CmNodes:
        # Skip the CmNode if it doesn't contain any entries
        if len(CmNode.CmDevices.item) > 0:
            # Loop through all the returned items and compare the status
            # to that of the snapshot
            for item in CmNode.CmDevices.item:
                for snapshot_item in snapshot[CmNode.Name]:
                    if snapshot_item['Name'] == item.Name and snapshot_item['Status'] != item.Status:
                        print(f"{item.Name} changed status from {snapshot_item['Status']} to {item.Status}")
                        no_change = False

    if no_change:
        print("No difference between snapshot and most recent query detected")
