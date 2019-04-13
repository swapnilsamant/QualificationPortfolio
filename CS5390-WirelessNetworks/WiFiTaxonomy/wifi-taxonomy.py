import wifi
import dhcp
import ethernet
import subprocess
import requests
import re

oui_dictionary = {}

def ParseIEEEOui():
	f_data = open('oui.txt','r')
	data = f_data.read()
	for line in data.split('\n'):
		try:
			mac, company = re.search(r'([0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2})\s+\(hex\)\s+(.+)', line).groups()
			oui_dictionary[mac.strip().replace('-',':')] = company.strip()
		except AttributeError:
			continue
	
	return oui_dictionary

dhcp_all_clients_file_location = '/home/pi/python-scripts/all-clients.txt'
finger_bank_api_key = '2ba0f5f263ac1efc35966abdf4ce871dfe11b7ff'
finger_base_url = 'https://fingerbank.inverse.ca/api/v1/combinations/interogate?key=' + finger_bank_api_key

all_client_file = open(dhcp_all_clients_file_location, 'r')

all_clients = all_client_file.readlines()

all_wifi_devices = {}

oui_dictionary = ParseIEEEOui()


for each_line in all_clients:
	#print each_line
	each_line_array = each_line.split("|")
	
	#if each_line_array[0] == 'add':
	mac_addr = each_line_array[1].strip()
	dhcp_finger_print = each_line_array[2].strip()
	vendor_class = each_line_array[3].strip()
	host_name = each_line_array[4].strip()

	if mac_addr not in all_wifi_devices:
		all_wifi_devices[mac_addr] = {}
		all_wifi_devices[mac_addr]['host_name'] = ''
		all_wifi_devices[mac_addr]['dhcp_finger_print'] = ''
		all_wifi_devices[mac_addr]['vendor_class'] = ''
		all_wifi_devices[mac_addr]['wifi_taxonomy'] = ''
		all_wifi_devices[mac_addr]['manufacturer'] = ''
		all_wifi_devices[mac_addr]['dhcp_fingerprint'] = ''
	print mac_addr
	if len(all_wifi_devices[mac_addr]['manufacturer']) <= 0:
		all_wifi_devices[mac_addr]['manufacturer'] = oui_dictionary[mac_addr[0:8].upper()]

	if len(all_wifi_devices[mac_addr]['host_name']) <= 0 and len(host_name) > 0:
		all_wifi_devices[mac_addr]['host_name'] = host_name

	if len(all_wifi_devices[mac_addr]['dhcp_finger_print']) <= 0 and len(dhcp_finger_print) > 0:
		all_wifi_devices[mac_addr]['dhcp_finger_print'] = dhcp_finger_print.strip()

	if len(all_wifi_devices[mac_addr]['dhcp_finger_print']) > 0:
		payload = {"dhcp_fingerprint": all_wifi_devices[mac_addr]['dhcp_finger_print'],
					"mac" : mac_addr.replace(":","").lower()}
		resp = requests.get(url=finger_base_url, json=payload)
		data = resp.json() 
		all_wifi_devices[mac_addr]['dhcp_fingerprint'] = data

	if len(all_wifi_devices[mac_addr]['vendor_class']) <= 0 and len(vendor_class) > 0:
		all_wifi_devices[mac_addr]['vendor_class'] = vendor_class

	if len(all_wifi_devices[mac_addr]['wifi_taxonomy']) <= 0:
		wifi_taxonomy = subprocess.check_output(['hostapd_cli', 'signature', mac_addr])

		if 'FAIL' not in wifi_taxonomy:
			wifi_taxonomy_list = wifi_taxonomy.split('\n')
			if len(wifi_taxonomy_list[1].strip()) > 0:
				all_wifi_devices[mac_addr]['wifi_taxonomy'] = wifi_taxonomy_list[1].strip()
				print wifi.identify_wifi_device(mac_addr, all_wifi_devices[mac_addr]['wifi_taxonomy'])



print '\n\n\n\n\n\n'			
print all_wifi_devices
	#print mac_addr
	#print wifi_taxonomy