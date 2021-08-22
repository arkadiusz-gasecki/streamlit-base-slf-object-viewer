# streamlit-base-slf-object-viewer
This application allows to extract base information about structure of Saleforce objects and display in relatively nice format \
Written in python using streamlit micro framework

## running of application
Please refer to [streamlit.io](https://streamlit.io) in order to find out, how to run applications written using this framework

## connection
In order to connect to Salesforce, provide connection details in sidebar form \
url in format: https://...my.salesforce.com \
password in format: password of a user concatenated with rest api token, so {password}{api_token} \
consumer key: client id from rest api application defined in salesforce \
consumer secret: client secret from rest api application defined in salesforce

## autocomplete
In your streamlit instance in share.streamlit.io you can define own secret file. There you can provide connection details and then autopopulate connection form using autocomplete button. \
Secret file has to be defined as follows:

```
auto_complete_password="<put password that you will use in autocomplete form>"

[CONNECTION]
url = "<https://...my.salesforce.com>"
client_id = "<client id from rest api application defined in salesforce>"
client_secret = "<client secret from rest api application defined in salesforce>"
username = "<username>"
password = "<password correspoding to username above>"
token = "<rest_api_token>"
```
Keep in mind that each value has to be provided in quotes, but without ```<>```
