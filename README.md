<h3 align="center">AmoCRM API v4 Libary</h3>

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

---

<p align="center"> Connector to AmoCRM API v4 (<a href="https://www.amocrm.ru/">https://www.amocrm.ru/</a>)
    <br>
</p>

## 📚 Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Available models](#available_models)
- [Usage](#usage)

## 💬 About <a name = "about"></a>

Connector for connecting via api to your AmoCRM system. Allows you to easily receive data on deals and contacts, as well as update them.

## 🧵 Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Pip or poetry

The project uses [Poetry](https://python-poetry.org/) instead of pip. But if you do not want to install the [Poetry](https://python-poetry.org/), for this case, create a file "requirements.txt".

### Init

To get started, you need to import the main class AmoCRM and init class AmoCRMInit. 

```python
from amocrm.v4.amoCRM import AmoCRM, AmoCRMInit
```

Then you need to create a model object AmoCRMInit and set settings value. If you want to use environment variables, then the file [.env.example](https://github.com/Blackgard/amocrm-api/blob/master/.env.example) is prepared for this.

```python
init_amocrm_data = AmoCRMInit(
    connect_email="test@test.ru",
    connect_domain="amocrm-api", 

    connect_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    connect_secret_key="xxXXXxxXxxXXx",
    redirect_uri="https://xxxxxxxxxx.xxx",

    init_code="xХxXxxXxxXXxХХХХxxХХxxХxХxХХххххХxxXXXxxXxxXXx"
)
```

To debug the project, set the debug variable to true

```python
init_amocrm_data.debug = True
```

And now you can transfer the settings to the main model of the AmoCRM class.

```python
amocrm = AmoCRM(init_amocrm_data)
```

## 📌 Available models <a name="available_models"></a>

So far, only two AmoCRM models are available for work:

1. Leads 
2. Contacts 

Further, their list will be replenished.

## 🧰 Usage <a name="usage"></a>

### GET data

To get unprocessed data, you need to use the get method.

```python
>>> response = amocrm.get(AmoCRM.ACTION.LEADS)
>>> response
AmoCRMFuncResponce(status=True, data=AmoResponceGet({'_page' : 1, '_links' : {'self': {'href': '', ...}}))
```

If you need to get only the data part, the get_date method can help you.

```python
>>> response = amocrm.get_data(AmoCRM.ACTION.LEADS)
>>> response
AmoCRMFuncResponce(status=True, data=[Leads(id=12653276, name='Name', price=0, ... ), ...])
```

You can also get data in the form of a Dataframe ([pandas](https://pandas.pydata.org/)). 

```python
>>> response = amocrm.get_data_df(AmoCRM.ACTION.LEADS)
>>> response
AmoCRMFuncResponce(status=True, data=Dataframe(columns=[id, name, price, group_id, ...], data=[...]))
```

This method has an additional boolean parameter "get_all_data" (default False), which allows you to go through all transactions in one function call and collect all this in Dataframe.

```python
>>> response = amocrm.get_data_df(AmoCRM.ACTION.LEADS, get_all_data=True)
```

Also, to obtain specific data, you need to apply the AMoCRM filters. For these purposes, there is a separate class FilterAmoCRM.

```python
>>> from amocrm.v4.amoCRM import FilterAmoCRM
>>> amocrm_filters = FilterAmoCRM(FilterAmoCRM.ACTIONS.LAST_DAY).get_filters()
>>> amocrm_filters
{'contacts': 'limit=10&filter[created_at][from]=1623170867&filter[created_at][to]=...', 'leads': '...'}

>>> amocrm.get(AmoCRM.ACTION.LEADS, filters=amocrm_filters.get(FilterAmoCRM.TABLE.LEADS))
...
```

### For work with POST and PATCH methods

How work with POST and PATCH data, you need use special models:

* AmoRequestPostLeads - How post new leads
* AmoRequestPostContacts - How post new contacts 
* AmoRequestPatchLeads - How update leads
* AmoRequestPatchContacts - How update contacts


Import:
```python
>>> from amocrm.v4.amoCRM import AmoRequestPostLeads, AmoRequestPostContacts, \
                                 AmoRequestPatchLeads, AmoRequestPatchContacts
```

Allow fields methods see [here](https://github.com/Blackgard/amocrm-api/blob/master/amocrm/v4/models/amoCRM_M.py)

### POST data

To create an object in AmoCRM, you need to use the post method.

```python
>>> response = amocrm.post(AmoCRM.ACTION.LEADS, data=[AmoRequestPostLeads(name="test", price=100.0, ...), ...])
>>> response
AmoCRMFuncResponce(status=True, data=AmoResponcePost(links=..., embedded=DataLeadsPost(leads=[LeadsPost(id=1, name="test"))))]))
```

To use the complex addition of deals, you need to call the action "LEADS_COMPLEX". This method accepts an array with objects and, if necessary, splits it into packages of size {max_count}.

```python
>>> amocrm.post(AmoCRM.ACTION.LEADS_COMPLEX, data=[...(> 100)], max_count=50)
1 step: Send data[0:49]
2 step: Send data[50:99]
```

### PATCH data

To update the model data, you must use the patch method. Required parameter is the ID of the object that needs to be updated.

```python
>>> response = amocrm.patch(AmoCRM.ACTION.LEADS, data=[AmoRequestPatchLeads(id=1, name="test", price=100.0, ...), ...])
>>> response
AmoCRMFuncResponce(status=True, data=AmoResponcePatch(links=..., embedded=DataLeadsPatch(leads=[LeadsPatch(id=1, name="test"))))]))
```