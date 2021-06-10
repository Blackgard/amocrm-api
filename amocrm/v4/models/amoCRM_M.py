from __future__ import annotations
from enum import Enum

from typing import Any, Optional, Union
from pydantic import BaseModel, HttpUrl
from pydantic.networks import EmailStr


## ---- REQUEST LINK ----

class NavHref(BaseModel):
    href: HttpUrl

class RequestLinks(BaseModel):
    self: NavHref
    next: NavHref
    
class Links(BaseModel):
    self: NavHref

## ---- REQUEST LINK END ----

# ------------------------------

## ---- SUB MODEL ----

class Tags(BaseModel):
    id: int
    name: str

class Companies(BaseModel):
    id: int
    links: Links
    
    class Config:
        fields = {'links': '_links'}

class ContactsShort(BaseModel):
    id: int

class Embedded(BaseModel):
    tags: list[Tags]
    companies: list[Companies]
    contacts: Optional[list[ContactsShort]]
    
class ValuesCustomFields(BaseModel):
    enum_id: Optional[int]
    enum_code: Optional[str]
    value: Union[str, int]
    
class CustomField(BaseModel):
    field_id: int
    field_name: str
    field_code: Optional[str]
    field_type: str
    values: list[ValuesCustomFields]

class ValidationError(BaseModel):
    code: str
    path: str
    detail: str

class ValidationErrors(BaseModel):
    request_id: int
    errors: list[ValidationError]

    
## ---- SUB MODEL END ----

# ------------------------------

## ---- DATA MODEL ----

class Leads(BaseModel):
    id: int
    name: str
    price: int
    responsible_user_id: int
    group_id: int
    status_id: int
    pipeline_id: int
    loss_reason_id: Optional[int]
    created_by: int
    updated_by: int
    created_at: int
    updated_at: int
    closed_at: Optional[int]
    closest_task_at: Optional[int]
    is_deleted: bool
    custom_fields_values: Optional[list[CustomField]]
    score: Optional[int]
    account_id: int
    links: Links
    embedded: Embedded
    
    class Config:
        fields = {
            'embedded': '_embedded',
            'links': '_links'
        }
        
class Contacts(BaseModel):
    id: int
    name: str
    first_name: str
    last_name: Optional[str]
    responsible_user_id: int
    group_id: int
    created_by: int
    updated_by: int
    created_at: int
    updated_at: int
    closest_task_at: Optional[int]
    is_deleted: bool
    custom_fields_values:  Optional[list[CustomField]]
    account_id: int
    links: Links
    embedded: Embedded
    
    class Config:
        fields = {
            'embedded': '_embedded',
            'links': '_links'
        }

class ContactsOptional(BaseModel):
    id: Optional[int]
    is_main: Optional[bool]
    name: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    responsible_user_id: Optional[int]
    group_id: Optional[int]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: Optional[int]
    updated_at: Optional[int]
    closest_task_at: Optional[int]
    is_deleted: Optional[bool]
    custom_fields_values: Optional[list[CustomField]]
    account_id: Optional[int]
    links: Optional[Links]
    embedded: Optional[Embedded]
    
    class Config:
        fields = {
            'embedded': '_embedded',
            'links': '_links'
        }

class EmbeddedLeads(BaseModel):
    tags: Optional[list[Tags]]
    contacts: list[ContactsOptional]
    companies: Optional[list[Companies]]
    
class EmbeddedContact(BaseModel):
    tags: list[Tags]

## ---- DATA MODEL END ----

# ------------------------------

## ---- DATA MODEL LIST ----

class DataLeads(BaseModel):
    leads: list[Leads]

class DataContacts(BaseModel):
    contacts: list[Contacts]

## ---- DATA MODEL LIST END ----

# ------------------------------

## ---- POST BLOCK ----

class AmoResponcePostError(BaseModel):
    validation_errors: list[ValidationErrors]
    title: str 
    type: HttpUrl
    status: int 
    detail: str
        
    class Config:
        fields = {
            'validation_errors': 'validation-errors',
        }

# ~ POST LEADS

class AmoRequestPostLeads(BaseModel):
    name: Optional[str]
    price: Optional[int]
    status_id: Optional[int]
    pipeline_id: Optional[int]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: Optional[int]
    updated_at: Optional[int]
    loss_reason_id: Optional[int]
    responsible_user_id: Optional[int]
    custom_fields_values:  Optional[list[CustomField]]
    embedded: Optional[EmbeddedLeads]
    request_id: Optional[str]
    
    class Config:
        fields = {
            'embedded': '_embedded',
        }

class LeadsPost(BaseModel):
    id: int
    request_id: Optional[str]
    links: Links
    
    class Config:
        fields = {
            'links': '_links'
        }

class DataLeadsPost(BaseModel):
    leads: list[LeadsPost]

# ~ POST CONTACTS

class AmoRequestPostContact(BaseModel):
    name: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    responsible_user_id: Optional[int]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: Optional[int]
    updated_at: Optional[int]
    custom_fields_values:  Optional[list[CustomField]]
    embedded: Optional[EmbeddedContact]
    request_id: Optional[str]
    
    class Config:
        fields = {
            'embedded': '_embedded',
        }

class ContactsPost(BaseModel):
    id: int
    request_id: Optional[str]
    links: Links
    
    class Config:
        fields = {
            'links': '_links'
        }

class DataContactsPost(BaseModel):
    contacts: list[ContactsPost]

## ---- POST BLOCK END ----

# ------------------------------

## ---- PATCH BLOCK ----

class AmoResponcePatchError(BaseModel):
    validation_errors: list[ValidationErrors]
    title: str 
    type: HttpUrl
    status: int 
    detail: str
        
    class Config:
        fields = {
            'validation_errors': 'validation-errors',
        }

# ~ PATCH LEADS

class AmoRequestPatchLeads(BaseModel):
    id: int
    name: Optional[str]
    price: Optional[int]
    status_id: Optional[int]
    pipeline_id: Optional[int]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: Optional[int]
    updated_at: Optional[int]
    loss_reason_id: Optional[int]
    responsible_user_id: Optional[int]
    custom_fields_values:  Optional[list[CustomField]]
    embedded: Optional[EmbeddedLeads]
    request_id: Optional[str]
    
    class Config:
        fields = {
            'embedded': '_embedded',
        }

class LeadsPatch(BaseModel):
    id: int
    updated_at: int
    request_id: Optional[str]
    links: Links
    
    class Config:
        fields = {
            'links': '_links'
        }

class DataLeadsPatch(BaseModel):
    leads: list[LeadsPatch]

# ~ PATCH CONTACTS

class AmoRequestPatchContact(BaseModel):
    id: int
    name: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    responsible_user_id: Optional[int]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: Optional[int]
    updated_at: Optional[int]
    custom_fields_values:  Optional[list[CustomField]]
    embedded: Optional[EmbeddedContact]
    request_id: Optional[str]
    
    class Config:
        fields = {
            'embedded': '_embedded',
        }

class ContactsPatch(BaseModel):
    id: int
    updated_at: int
    request_id: Optional[str]
    links: Links
    
    class Config:
        fields = {
            'links': '_links'
        }

class DataContactsPatch(BaseModel):
    contacts: list[ContactsPatch]

## ---- PATCH BLOCK END ----

# ------------------------------
# ------------------------------

### ---- MAIN MODEL ----

class AmoResponceGet(BaseModel):
    page: int
    links: RequestLinks
    embedded: Union[DataLeads, DataContacts, None] 
    
    class Config:
        fields = {
            'page': '_page',
            'links': '_links',
            'embedded': '_embedded'
        }

class AmoResponcePost(BaseModel):
    links: Links
    embedded: Union[DataContactsPost, DataLeadsPost]
    
    class Config:
        fields = {
            'links': '_links',
            'embedded': '_embedded'
        }

class AmoResponcePatch(BaseModel):
    links: Links
    embedded: Union[DataContactsPatch, DataLeadsPatch] 
    
    class Config:
        fields = {
            'links': '_links',
            'embedded': '_embedded'
        }

### ---- MAIN MODEL END ----

# ------------------------------

## ---- INIT MODEL ----

class ModeSaveTokenEnum(str, Enum):
    LOCAL_FILE = "local_file"
    FUNCTION = "function"
    
class ModeSaveToken(BaseModel):
    mode: ModeSaveTokenEnum = ModeSaveTokenEnum.LOCAL_FILE
    path_to_file: Optional[str]

class AmoCRMInit(BaseModel):
    debug: bool = True
    connect_email: EmailStr
    connect_domain: str
    connect_id: str
    connect_secret_key: str
    refresh_token: Optional[str]
    access_token: Optional[str]
    redirect_uri: HttpUrl
    init_code: Optional[str]
    
    mode_save_token: ModeSaveToken = {
        "mode": ModeSaveTokenEnum.LOCAL_FILE,
        "path_to_file": "access_tokens.json"
    }
    check_auth_in_init: bool = True
    attempts_conn: int = 5

## ---- INIT MODEL END ----

# ------------------------------

## ---- AUTH MODEL ----

class RequestAuth(BaseModel):
    client_id: str
    client_secret: str
    grant_type: Optional[str]
    code: Optional[str]
    refresh_token: Optional[str]
    redirect_uri: str

class ResponceAuthValid(BaseModel):
    token_type: str
    expires_in: int
    access_token: str
    refresh_token: str

class ResponceAuthNotValid(BaseModel):
    title: str
    type: HttpUrl
    status: int
    detail: str
    
## ---- AUTH MODEL END ----

# ------------------------------

## ---- FUNC RESPONCE MODEL ----

class AmoCRMFuncResponce(BaseModel):
    status: bool
    detail: str = "Success"
    data: Any

## ---- FUNC RESPONCE MODEL ----

# ------------------------------