import streamlit as st
import streamlit.components.v1 as components
import requests, json
import pandas as pd
import io, base64

# define default style
st.markdown(
        f"""
<style>
    .reportview-container .main .block-container{{
		width: 90%;        
		max-width: 2000px;
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 1rem;
    }}
</style>
""",
        unsafe_allow_html=True,
    )



######################## DEFINITION OF FUNCTIONS #############################################

########### login ##############
def login(url, consumer_key, consumer_secret, username, password):
	url = url.rstrip("/")

	# prepare login statement
	request_url = '/'.join([url,'services','oauth2','token'])
	body = {
		'grant_type': 'password'
	  , 'client_id': consumer_key
	  , 'client_secret': consumer_secret
	  , 'username': username
	  , 'password': password
	}

	login_response = requests.request("POST", request_url, data=body)
	if login_response.status_code != 200:
		st.write("Error "+str(login_response.status_code))
		st.write(json.loads(login_response.text))
	else:
		st.sidebar.write("Login successful")
		response = json.loads(login_response.text)
		st.session_state['token'] = response['access_token']
		st.session_state['url'] = url
		return 'Success'

########### load objects ##############
def load_objects():
	token = st.session_state['token']
	url = st.session_state['url']

	if token is not None:
		#get list of all objects
		request_url = '/'.join([url,'services','data','v51.0','sobjects'])
		header = {
			'Authorization': 'Bearer '+token
		}
		obj_metadata_response = requests.get(request_url, headers=header)
		response = json.loads(obj_metadata_response.text)
		
		dct = {}
		for obj in response['sobjects']:
			dct[obj['label']] = obj['name']
		return dct
	else:
		st.write('Not connected')


########### helper functions ##############
def parse_response(response, params,key='fields'):
	d = {}
	additional_columns = list()
	if key == 'fields':
		additional_columns = list(response[key][0].keys())

	for r in response[key]:
		for p in params:
			d[p] = d.get(p,list())
			if p != 'picklistValues':				
				d[p].append(r[p])
			else:
				d[p].append( ','.join([ '"{}"'.format(e['value']) for e in r[p] ]) )
	return (d, additional_columns)

def prepare_html_table(d, length, params):
	html = '<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">'
	html += '<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>'
	html += '<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js"></script>'
	html += '<script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>'
	html += '<div class="container" style="max-width: 100%"><div class="table-responsive" style="max-height: 500px"><table class="table table-bordered">'
	for k in d:
		html += ("<th>"+str(k)+"</th>")
	for i in range(0,length):
		html += '<tr>'
		for p in params:
			if p.startswith('picklistValues'):
				if isinstance(d[p][i],str) and len(d[p][i]) > 0:
					elem = '<select style="width: 200px">'+"".join(['<option>'+e.replace('"','')+'</option>' for e in d[p][i].split(',')])+'</select>'
				else:
					elem = ''
				html += ('<td>'+elem+'</td>')
			elif p.startswith('referenceTo'):
				if isinstance(d[p][i],list) and len(d[p][i]) > 0:
					html += ('<td>'+str(d[p][i][0])+'</td>')
				else:
					html += ('<td></td>')
			else:
				html += ('<td>'+str(d[p][i])+'</td>')
		html += '</tr>'
	
	html+= '</table></div></div>'

	return html

########### get metadata info about desired object ##############
def show_object(object_name):
	token = st.session_state['token']
	url = st.session_state['url']

	request_url = '/'.join([url,'services','data','v51.0','sobjects',object_name,'describe'])
	header = {
		'Authorization': 'Bearer '+token
	}	
	obj_metadata_response = requests.get(request_url, headers=header)
	response = json.loads(obj_metadata_response.text)
	
	#parse response about object, only columns mentioned below will be provided
	params = ['name', 'label', 'type', 'length', 'nillable', 'referenceTo' ,'picklistValues']
	
	d, additional_columns = parse_response(response, params)
	df = pd.DataFrame(d)
	
	object_structure = prepare_html_table(d, len(d['name']), params)

	#get metadata info about validation rules
	query = "query?q=Select Id,Active,Description,ErrorDisplayField,ErrorMessage From ValidationRule Where EntityDefinition.DeveloperName = '"+object_name+"'"
	request_url = '/'.join([url,'services','data','v51.0','tooling',query])
	header = {
		'Authorization': 'Bearer '+token
	}	
	obj_metadata_response = requests.get(request_url, headers=header)
	response = json.loads(obj_metadata_response.text)
	
	params = ['Id', 'Active', 'Description', 'ErrorDisplayField', 'ErrorMessage' ]
	
	d, _ = parse_response(response, params,key='records')
	validation_rules = None if len(d) == 0 else prepare_html_table(d, len(d['Id']), params)

	return (object_structure, validation_rules, additional_columns, df)

########### generate link to download CSV file ##############
def get_table_download_link_csv(df,filename):
    csv = df.to_csv().encode()
    b64 = base64.b64encode(csv).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="'+filename+'.csv" target="_blank">Download csv file</a>'
    return href


########### logout ##############
def logout():
	url = st.session_state['url']
	token = st.session_state['token']

	if token is not None:
		# prepare logout statement
		request_url = '/'.join([url,'services','oauth2','revoke'])
		body = {
    		'token': token
		}

		# make logout request
		logout_response = requests.post(request_url, data=body)
		if logout_response.status_code != 200:
			st.write("Error "+str(logout_response.status_code))
			st.write(json.loads(logout_response.text))
		else:
			st.session_state['token'] = None
			st.sidebar.write("Logout successful")

######################## LOGIN FORM SECTION #############################################

# add code that allows to autocomplete values read from secrets file
pwd = st.sidebar.text_input("Autocomplete password", type="password", key='50')
auto = st.sidebar.button('Autocomplete',key='autocomplete')

if auto == True or st.session_state.get('autocomplete_form', 'nok') == 'ok':
	### check if secrets file exists
	secrets_password = None
	try:
		err = 'CONNECTION' not in st.secrets
		secrets_password = st.secrets["auto_complete_password"]
	except:
		st.write('Secrets file not properly defined, autocomplete impossible')

	### if we have password, it means, we could find data in secrets file
	if secrets_password is not None:
		if pwd != secrets_password:
			st.write('Improper autocomplete password.')
		elif pwd == secrets_password or st.session_state.get('autocomplete_form','nok') == 'ok':
			try:
				cached_url      = st.secrets["CONNECTION"]["url"]
				cached_key      = st.secrets["CONNECTION"]["client_id"]
				cached_secret   = st.secrets["CONNECTION"]["client_secret"]
				cached_user     = st.secrets["CONNECTION"]["username"]
				cached_password = st.secrets["CONNECTION"]["password"] + st.secrets["CONNECTION"]["token"]
				st.session_state['autocomplete_form'] = 'ok'
			except:
				st.session_state['autocomplete_form'] = 'nok'

### define empty variables, if data from autocomplete was not delivered
if st.session_state.get('autocomplete_form', '') != 'ok':
	cached_url = ''
	cached_key = ''
	cached_secret = ''
	cached_user = ''
	cached_password = ''

### form to provide all connection details ###
form 		= st.sidebar.form(key='conn_form')
url 		= form.text_input('url', cached_url, key='11')
username 	= form.text_input('username', cached_user, key='12')
password 	= form.text_input('password', cached_password, type="password", key='13')
consumer_key 	= form.text_input('consumer key', cached_key, type="password", key='14')
consumer_secret = form.text_input('consumer secret', cached_secret, type="password", key='15')
submit_connect 	= form.form_submit_button(label='Login')


######################## LOGIN ACTION SECTION #############################################
if submit_connect:
	try:
		status = login(url, consumer_key, consumer_secret, username, password)
		if status == 'Success':
			try:
				st.session_state['objects'] = load_objects()
			except Exception as e:
				st.write("Unexpected error when trying to load objects from Salesforce: {}".format(e))
	except Exception as e:
		st.write("Unexpected error when trying to log in: {}".format(e))




######################## SELECTOR FOR OBJECTS #############################################
if type(st.session_state.get('objects','None')) != type(dict()):
	object_selection = st.selectbox('Select object', (''))
else:
	object_selection = st.selectbox('Select object', st.session_state['objects'].keys())

### define empty variables
object_structure = ''
validation_rules = ''
df = pd.DataFrame()
filename = 'capture'

### get info about object that was selected (if was selected) ###
if object_selection:
	try:
		(object_structure, validation_rules, additional_columns, df) = show_object(st.session_state['objects'][object_selection.strip()])
		filename = st.session_state['objects'][object_selection.strip()]
	except Exception as e:
		st.write("Unexpected error when trying to load information about object {}. Error: {}".format(object_selection, e))


######################## SHOW SELECTED OBJECT #############################################

if object_structure != '':
	st.markdown('## Object structure ##')
	st.markdown(get_table_download_link_csv(df,filename), unsafe_allow_html=True)
	components.html(object_structure,height=500,scrolling=True)

## show validation rules
if validation_rules != '':
	st.markdown('## Validation rules ##')
	components.html(validation_rules,height=500,scrolling=True)


######################## BUTTON TO EXPLICITLY CLOSE CONNECTION #############################################
st.sidebar.markdown("  ")
st.sidebar.markdown("  ")
st.sidebar.markdown("  ")
if st.sidebar.button('Logout', key='logout'):
	try:
		logout()
		### clear variables
		st.session_state['objects'] = None
		object_structure = ''
		validation_rules = ''
		df = pd.DataFrame()
		filename = 'capture'
		raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))
	except Exception as e:
		st.write("Unexpected error when trying to log out: {}".format(e))

### stop which is not really needed
st.stop()
