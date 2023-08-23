import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import pprint

current_dir = os.path.dirname(__file__)

CLIENT_FILE = os.path.join(current_dir, "client_secrets_web.json")
SCOPES = ["https://www.googleapis.com/auth/forms.body.readonly", "https://www.googleapis.com/auth/forms", "https://www.googleapis.com/auth/forms.responses.readonly", "https://www.googleapis.com/auth/spreadsheets.readonly"]

#https://www.googleapis.com/auth/gmail.send
#key = "AIzaSyA96YVQLcj58yRcp9095qgpSaauBxFPEnY"

def authenticate_user(creds=None):
	token_path = os.path.join(current_dir, "token.json")
	if os.path.exists(token_path):
			creds = Credentials.from_authorized_user_file(token_path, SCOPES)
		
	if not creds or not creds.valid:
			print(f'--------CREDS: {creds}')
			print(f'----------CLIENT FILE: {CLIENT_FILE}')
			if creds and creds.expired and creds.refresh_token:
					print(f'-------REFRESH CREDS')
					creds.refresh(Request())
			else:
					print(f'-------GET FLOW')
					flow = InstalledAppFlow.from_client_secrets_file(CLIENT_FILE, SCOPES)
					print(f'-------GOT FLOW')
					creds = flow.run_local_server()
					print(f'------GOT CREDS')
			with open(token_path, 'w') as token:
					token.write(creds.to_json())
	return creds

creds = None

#service_gmail = build('gmail', 'v1', credentials=creds)
"""
# region exclude
creds = authenticate_user(creds=creds)

service_forms = build("forms", "v1", credentials=creds)
service_sheets = build('sheets', 'v4', credentials=creds)


form_id = "192tZNUi0LPVw22RWWYk8esjjNQ4KQN8x2q1rQHXPhq0" # consolidation form
#form_id = "1k9lG6y4ragRQkjXjo_92vpuhWmLW-VIvGCOWG0sKSWM" # testing form
sheet_id = "11IRKB-KjUQf3kTn4e6jbx89gYaDJbQ1chenkXrU2XS0"
sheet_name = "Consolidation Responses"

try:
	#results = service_gmail.users().labels().list(userId='me').execute()
	#labels = results.get('labels', [])
	form = service_forms.forms().get(formId=form_id).execute()
	result = service_sheets.spreadsheets().values().get(spreadsheetId=sheet_id, range=sheet_name).execute()

except HttpError as error:
	print(f'An error occured: {error}')


# list of lists where inner list represents a row
values = result.get('values', [])
headers = {}

person = "Shipper"
for i, hd in enumerate(values[0]):
	# keys in headers differ slightly from spreadsheet titles
	# for readability
	# if question titles change THEN CHANGE THEM HERE

	# ensures a clear difference between shipper and consignee
	# details despite questions having same titles
	heading = hd.rstrip()
	if heading == "Consignee's Name":
		person = "Consignee"
	elif heading == "Number of Boxes":
		person = "None"
	
	if person != "None":
		if (heading == "Address" or
		heading == "City" or
		heading == "State/Province" or
		heading == "Zip Code" or
		heading == "Cell Phone Number" or
		heading == "Email"):
			if person == "Shipper":
				h = "Shipper's " + heading
			elif person == "Consignee":
				h = "Consignee's " + heading
			headers[h] = i
			continue
	else:
		h = heading
		if heading == "Actual or Gross Weight":
			h = "weight"
		elif heading == "Does your shipment include lithium batteries?":
			h = "has batteries"
		elif heading == "Would you like insurance for your air freight delivery?":
			h = "insurance"
		if h != heading:
			#print(f'---HEADING: {heading}')
			#print(f'-------HEADER CHANGED TO	{h}\n')
			headers[h] = i
			continue
	headers[heading] = i

#endregion

"""
print(f'------INITIALIZED GOOGLE FORMS SETUP')
# keys defined below must match keys defined in form_autofill.py
# see get_autofill_dict()

headers = {} # remove later
def get_shipper_info(row):
	"""
	row is a list
	"""
	data = {}
	data['shipper_name'] = row[headers["Shipper's Name"]]
	data['shipper_email'] = row[headers["Shipper's Email"]]
	data['shipper_phone'] = row[headers["Shipper's Cell Phone Number"]]
	data['shipper_address'] = row[headers["Shipper's Address"]]
	data['shipper_city'] = row[headers["Shipper's City"]]
	data['shipper_state'] = row[headers["Shipper's State/Province"]]
	data['shipper_zip'] = row[headers["Shipper's Zip Code"]]
	return data

def get_consignee_info(row):
	"""
	row is a list
	"""
	data = {}
	data['consignee_name'] = row[headers["Consignee's Name"]]
	data['consignee_email'] = row[headers["Consignee's Email"]]
	data['consignee_phone'] = row[headers["Consignee's Cell Phone Number"]]
	data['consignee_address'] = row[headers["Consignee's Address"]]
	data['consignee_city'] = row[headers["Consignee's City"]]
	data['consignee_state'] = row[headers["Consignee's State/Province"]]
	data['consignee_zip'] = row[headers["Consignee's Zip Code"]]
	return data

def get_order_details(row):
	data = {}
	data['box_num'] = row[headers["Number of Boxes"]]
	data['weight'] = row[headers["weight"]]
	data['pickup_address'] = row[headers["Pickup Address"]]
	data['cargo_description'] = row[headers["Cargo Description"]]
	data['batteries'] = True if row[headers["has batteries"]] == "Yes" else False
	data['total_value'] = row[headers["Total Value of Cargo"]]
	data['insurance'] = row[headers["insurance"]]
	data['notes'] = row[headers["Additional Comments"]]
	data['boxes'] = {}
	for i in range(1, int(data['box_num'])+1):
		data['boxes'][f'{i}'] = {}		# define empty dict first
		data['boxes'][f'{i}']['description'] = row[headers[f"Details (Package {i})"]]
	
	# redefine delivery option
	# if key is left out, option on form is blank
	delivery_option = row[headers["Delivery Option"]].lower().replace(" ", "")
	delivery_keyword = "pickup"
	#print(f'--------DELIVERY OPTION: {delivery_option}')
	if delivery_keyword in delivery_option:
		data['office_pickup'] = True
		#print("OFFICE PICKUP SET TO TRUE FROM FORM RESPONSE")
	else:
		data['office_pickup'] = False
	
	# insurance
	# True if 'Yes' is a substring in the response
	insurance = row[headers["insurance"]].lower()
	#data['insurance'] = True if 'yes' in insurance else False
	if 'yes' in insurance:
		data['insurance'] = True
	elif 'no' in insurance:
		data['insurance'] = False
	else:
		raise AssertionError("Unclear whether customer wants insurance or not based on this response: {insurance}")
	
	return data

def delete_token_file():
    token_path = os.path.join(os.path.dirname(__file__), "token.json")
    try:
        os.remove(token_path)
        print("token.json file deleted.")
    except FileNotFoundError:
        print("token.json file not found.")

def get_response_data(rows=10, startfrom=0):
	"""
	Retrieves data from the last n responses.
	Returns a dict.
	"""
	global values
	data = {}
	for i in range(startfrom, rows + startfrom):
		rnum = len(values)-1-i
		row = values[rnum]
		# about 37 columns in spreadsheet
		# this ensures additional comments are not left out
		# if they are blank
		if len(row) < 37:
			for i in range(0, 37-len(row)):
				row.append('')
		
		data[row[0]] = {}
		data[row[0]]["shipper"] = get_shipper_info(row)
		data[row[0]]["consignee"] = get_consignee_info(row)
		data[row[0]]["order_details"] = get_order_details(row)
		data[row[0]]["response_link"] = row[1]
	return data


#print(get_shipper_info(values[len(values)-1]))
#print(get_consignee_info(values[len(values)-1]))
#print(get_order_details(values[len(values)-1]))

#response = service_forms.forms().responses().list(formId=form_id).execute()
"""
questions = form.get("items", [])
responses_dict = service_forms.forms().responses().list(formId=form_id).execute()

#for item in form.get("items", []):
#	print(item)

# extract the following information:
# shipper info
# consignee info
# delivery option
# insurance
# description

#response = responses[0]	# latest response
#pprint.pprint(responses)

if "responses" in responses_dict:
	responses = responses_dict["responses"]
	#print(responses[0]['responseId'])
	for response in responses:
		rid = response['responseId']
		#r = service_forms.forms().responses().get(formId=form_id, responseId=rid).execute()
else:
	print('No responses found.')
"""