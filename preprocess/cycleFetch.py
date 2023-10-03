#!/usr/bin/env python
# coding: utf-8

# In[81]:


CYCLE_CACHE_FOLDER_NAME = "cycle_cache"
BASE_URL = "https://proconnectmobiledata.steris.com"
API_KEY = "swq7tTKTFX66nVvMqkJAxjQy4cvVJFHMOmoI0PX823aeAzFub4NwBg=="
API_USERNAME = "ml_api_user"
API_PASSWORD = "lapemla_r__us_iusml_pi_uer"
MAX_CACHE_SPACE = "25GB"


# In[105]:


import json
import os
import uuid
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth
import diskcache
from urllib.parse import urlencode


# In[83]:


# Ensure cache folder exists
if not os.path.isdir(CYCLE_CACHE_FOLDER_NAME):
    os.mkdir(CYCLE_CACHE_FOLDER_NAME)

# Set request context
request_context = uuid.uuid4()


# In[138]:


# utility function to list cycles for a given account and serial number
def list_cycles(acct_no, sn, pmcl, cycle_type, start_dt, end_dt):
    auth = HTTPBasicAuth(API_USERNAME, API_PASSWORD)

    headers = {
        "x-functions-key": API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Server": "Python Server",
        "Host": "proconnectmobiledata.steris.com",
    }

    # Add parameters to body if they exist
    # acct_no and sn are required search parameters
    request_params = {"acct_no": acct_no, "sn": sn}

    if pmcl:
        request_params["pmcl"] = pmcl

    if cycle_type:
        request_params["cycle_type"] = pmcl

    if start_dt:
        request_params["start_dt"] = int(start_dt.timestamp() * 1000)

    if end_dt:
        request_params["end_dt"] = int(end_dt.timestamp() * 1000)

    # Execute the request to list files
    url = f"{BASE_URL}/api/ListCycles?{urlencode(request_params)}"
    response = requests.get(url, auth=auth, headers=headers)
    assert response.status_code == 200, f"HTTP response failed {response.status_code}"
    return response.json()


# In[139]:


# Sample usage
end_dt = datetime.now()
start_dt = end_dt - timedelta(days=30)


# Acct and Serial number should come from one of the other source databases
# print(list_cycles("141575", "3631315021", None, None, start_dt, end_dt))


# In[ ]:


# In[152]:


# utility function to get the cycle json
# utility function to list cycles for a given account and serial number
def fetch_cycle_json(device_cycle_id):
    auth = HTTPBasicAuth(API_USERNAME, API_PASSWORD)

    headers = {
        "x-functions-key": API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Server": "Python Server",
        "Host": "proconnectmobiledata.steris.com",
    }

    # Add parameters to body if they exist
    # acct_no and sn are required search parameters
    request_params = {"device_cycle_ids": device_cycle_id, "preferred_temp_unit": "F"}

    # Execute the request to list files
    url = f"{BASE_URL}/api/GetViewerCycles?{urlencode(request_params)}"
    response = requests.get(url, auth=auth, headers=headers)
    assert response.status_code == 200, f"HTTP response failed {response.status_code}"
    return response.json()


# In[153]:


# Sample for fetching cycle json
# end_dt = datetime.now()
# start_dt = end_dt - timedelta(days=3)
# files = list_cycles("141575", "3631315021", None, None, start_dt, end_dt)
# print(files["cycles"][0])


# In[154]:


# fetch_cycle_json(files["cycles"][0]["device_cycle_id"])


# In[ ]:
