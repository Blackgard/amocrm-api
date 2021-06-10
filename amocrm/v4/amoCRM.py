from __future__ import annotations

from typing import Any, Tuple, Union, Optional, Final

from pydantic.error_wrappers import ValidationError
from pydantic.typing import NoneType

from amocrm.v4.models.amoCRM_M import AmoRequestPatchContact, AmoRequestPostContact, AmoResponceGet, AmoResponcePostError, \
                            Contacts, DataContacts, DataLeads, Embedded, Leads, Links, RequestAuth, ResponceAuthNotValid, \
                            ResponceAuthValid, AmoCRMInit, ModeSaveTokenEnum, AmoResponcePost, AmoCRMFuncResponce, \
                            AmoRequestPostLeads, AmoRequestPatchLeads, AmoResponcePatch, AmoResponcePatchError, AmoCRMInit

from amocrm.v4.amoCRM_filter import FilterAmoCRM
from amocrm.v4.amoCRM_utils import batch, save_tokens_to_file
from amocrm.v4.errors.amoCRM_E import AuthError

import os
import json
import loguru
import requests

from requests import Response, Request
from pandas import DataFrame, concat



class AmoCRMConst:
    class ACTION:
        LEADS_COMPLEX: Final[str] = 'leads/complex'
        LEADS: Final[str] = 'leads'       # Сделки
        CONTACTS: Final[str] = 'contacts' # Контакты
        CUSTOM_FIELDS: Final[str] = "custom_fields" # Касомные поля
        LEADS_CUSTOM_FIELDS: Final[str] = "leads/custom_fields" # Кастомные поля сделок
        
    class TYPE_AUTH:
        AUTHORIZATION_CODE: Final[str] = 'authorization_code'
        REFRESH_CODE: Final[str] = 'refresh_token'
        
    class AUTH_METHODS:
        ACEESS_TOKEN: Final[str] = 'access_token'
        
    class TOKENS:
        ACCESS: Final[str] = 'access_token'
        REFRESH: Final[str] = 'refresh_token'


class AmoCRM(AmoCRMConst):
    """ Class Api connector to servise https://amocrm.com (AmoCRM).

        Usage:
        >>> from amocr.v4.amoCRM import AmoCRM
        >>> amocrm = AmoCRM(settings) # settings is AmoCRMInit in pydantic model
        >>> is_success, responce_msg, get_responce = amocrm.get(AmoCRM.ACTION.LEADS, filters="limit=10&")
    """
    
    def __init__(self, init_settings: AmoCRMInit, logger: loguru.logger = loguru.logger, *args, **kwargs):
        self.connect_email = init_settings.connect_email
        self.connect_domain = init_settings.connect_domain
        
        self.connect_id = init_settings.connect_id
        self.connect_secret_key = init_settings.connect_secret_key
        
        self.refresh_token = init_settings.refresh_token
        self.access_token = init_settings.access_token
        self.init_code = init_settings.init_code
        
        self.redirect_uri = init_settings.redirect_uri
        self.attempts_conn = init_settings.attempts_conn
        
        # Private
        
        self._debug = init_settings.debug
        self._logger = logger
        
        self._is_need_update_token = None
        self._count_send_request = 0
        
        self._new_access_token = None
        self._new_refresh_token = None
        
        self.__settings = init_settings
        self.__mode_save_token = init_settings.mode_save_token
        
        self.__func_update_token = kwargs.get("func_update_token")
        
        self.init_cheker(*args, **kwargs)
        
    def init_cheker(self, *args, **kwargs):
        if self.__mode_save_token.mode == ModeSaveTokenEnum.LOCAL_FILE:
            self.__func_update_token = save_tokens_to_file
            
            if os.path.exists(self.__mode_save_token.path_to_file):
                with open(self.__mode_save_token.path_to_file) as file:
                    dict_with_tokens = json.loads(file.read())
                    self.access_token = dict_with_tokens.get("access_token", self.access_token)
                    self.refresh_token = dict_with_tokens.get("refresh_token", self.refresh_token)


        if self.__settings.check_auth_in_init and not self.__check_auth(self.access_token, self.refresh_token): 
            self.__check_work_token(self.attempts_conn, *args, **kwargs)

        if self.__settings.check_auth_in_init and self._is_need_update_token:
            raise AuthError("Failed to log in with the specified values! Check your tokens.")
        
    def __str__(self):
        return f"""-------- AMOCRM connector --------
            Email: {self.connect_email} 
            Domain: {self.connect_domain}
            Connect id: {self.connect_id}
            Redirect uri: {self.redirect_uri}
            
            --------  Private --------

            Count send request: {self._count_send_request}
            Is need update token: {self._is_need_update_token}
            Set access token: {bool(self.access_token)}
            Set refresh token: {bool(self.refresh_token)}
            Check auth in init: {self.__settings.check_auth_in_init}
            Mode save tokens: {self.__mode_save_token}
            
            Debug mode active?: {self._debug} 
            Auth work?: {"Not tested" if self._is_need_update_token is None else not self._is_need_update_token}
            """
    
    # CHECKER

    def __check_auth(self, access_token: str, refresh_token: str) -> bool:
        " Check auth to amocrm api with init settings "
        
        isSuccess, err_msg, code = self.__send_check_request(access_token)

        if isSuccess:
            self._is_need_update_token = False
            return True

        body = RequestAuth(
            client_id=self.connect_id,
            client_secret=self.connect_secret_key,
            redirect_uri=self.redirect_uri
        )
        
        if not refresh_token and not access_token:
            body.grant_type = AmoCRM.TYPE_AUTH.AUTHORIZATION_CODE
            body.code = self.init_code
            msg_logger = "Responce new token using main token!"
        elif code == 401:
            body.grant_type = AmoCRM.TYPE_AUTH.REFRESH_CODE
            body.refresh_token = refresh_token
            msg_logger = "Responce new token using refresh token!"
        else:
            self._logger.error('An attempt was made to update the token and the program ended in a block else!')
            self._logger.error(f"refresh_key -> {refresh_token} | status_check -> {(isSuccess, err_msg, code)}")
            return False

        answer = self.oauth2(self.AUTH_METHODS.ACEESS_TOKEN, body=body)
        if isinstance(answer, ResponceAuthNotValid):
            self._is_need_update_token = True
            self._logger.error(f'Token has not been received! Responce message - "{answer.detail}" | Excaption code - "{answer.status}"')
            return False

        self._logger.info(msg_logger)
        self._new_access_token = answer.access_token
        self._new_refresh_token = answer.refresh_token
        self._is_need_update_token = True
        return False

    def __send_check_request(self, access_token: str, action: str='account', version_api: str='v4') -> Tuple[bool, str, int]:
        """ send request for check does the token work.

        Args:
            access_token (str): access token is string
            action (str, optional): action AmoCRM. Defaults to 'account'.
            version_api (str, optional): version api AmoCRM. Defaults to 'v4'.

        Returns:
            Tuple[bool, str, int]:
                is_success[bool]: is success request
                message_responce[str]: responce message from amo_crm
                code_responce[int]: responce code
        """
        url = f"https://{self.connect_domain}.amocrm.ru/api/{version_api}/{action}"
        responce: Response = requests.get(url, headers={ "Authorization" : f"Bearer {access_token}"})
        self._count_send_request += 1
        return self.__check_responce_status_code(responce)

    def __check_responce_status_code(self, responce: Response, is_print_info: bool = True) -> Tuple[bool, str, int]:
        if responce.status_code == 200:
            return (True, '', responce.status_code)
        elif responce.status_code == 204:
            is_print_info and self._logger.info('Responce don\'t have data. status code -> 204')
            return (False, 'Responce don\'t have data. status code -> 204', responce.status_code)
        elif responce.status_code == 401:
            is_print_info and self._logger.error('Unauthorized request, check your token!')
            return (False, 'Unauthorized request, check your token!', responce.status_code)
        elif responce.status_code == 404:
            is_print_info and self._logger.error('Incorrect request, check the correctness of the specified email!')
            return (False, 'Incorrect request, check the correctness of the specified email!', responce.status_code)
        else:
            is_print_info and self._logger.error(f'Incorrect request! code -> {responce.status_code}')
            return (False, 'Incorrect request!', responce.status_code)

    def __check_work_token(self, attempts: int=5, *args, **kwargs) -> bool:
        """Check work token on connect to AmoCRM.

        Args:
            attempts (int, optional): Number of attempts to gain access to AmoCRM. Defaults to 5.

        Returns:
            bool: Status attempts connect. If True -> success.
        """

        if self._new_access_token is None or self._new_refresh_token is None:
            return True
        self._logger.info(f"attempts -> {attempts} | needUpdate -> {self._is_need_update_token}")
        
        if attempts <= 0: return False
        if not self._is_need_update_token: 
            self.access_token = self._new_access_token
            self.refresh_token = self._new_refresh_token
            
            if kwargs.get('is_update_tokens', False):
                if self.__mode_save_token.mode == ModeSaveTokenEnum.LOCAL_FILE: kwargs["path_to_save_file"] = self.__mode_save_token.path_to_file
                return self.__func_update_token(access_token=self.access_token, refresh_token=self.refresh_token, *args, **kwargs)
            return True
        
        self.__check_auth(self._new_access_token, self._new_refresh_token)
        return self.__check_work_token(attempts - 1, is_update_tokens=True, *args, **kwargs)

    # AUTH

    def oauth2(self, action: AmoCRM.AUTH_METHODS, body: RequestAuth=None) -> Union[ResponceAuthValid, ResponceAuthNotValid]:
        """ Get new token use oauth2 method. 
        
        Usage:
        
        >>> # Is valid responce
        >>> body = RequestAuth(connect_id='18f419cf...', connect_secret_key='cuBWt...', grant_type='access_token', code='hPSQ..', redirect_uri='https://...')
        >>> oauth2(AmoCRM.TYPE_AUTH.AUTHORIZATION_CODE, body=body)
        (cls) ResponceAuthValid { token_type: 'Bearer', expires_in: 19839676, access_token: 'eyJ0eXAiOiJK...', refresh_token: 'twi8gZOd86...' }
        
        >>> # Is not valid responce
        >>> body = RequestAuth(connect_id='18f456j7...', connect_secret_key='cu3Wt...', grant_type='refresh_token', refresh_token='hPSQ..', redirect_uri='https://...')
        >>> oauth2(AmoCRM.TYPE_AUTH.AUTHORIZATION_CODE, body=body)
        (cls) ResponceAuthNotValid { title: 'Некорректный тип доступа', type: 'https://...', status: 400, detail: 'Передано некорректное значение' }
        """
        
        url = f"https://{self.connect_domain}.amocrm.ru/oauth2/{action}"
        headers = { "Content-Type" : "application/json" }
        responce = requests.post(url, data=body.json(), headers=headers)
        self._count_send_request += 1
        
        try: data = ResponceAuthValid(**responce.json())
        except ValidationError: data = ResponceAuthNotValid(**responce.json())
        
        return data

    # GET

    def get(self, action: AmoCRM.ACTION, filters: str='', version_api: str='v4', *args, **kwargs) -> AmoCRMFuncResponce:
        """ Get data from action url on dict format.
        # Example
        >>> # Data is correct
        >>> amocrm = AmoCRM(**data)
        >>> amocrm.get(amocrm.ACTION.LEADS)
        AmoCRMFuncResponce(status=True, detail='', data=AmoResponceGet({'_page' : 1, '_links' : {'self': {'href': '', ...}}))

        >>> # Data is not correct
        >>> amocrm = AmoCRM(**data)
        >>> amocrm.get(amocrm.ACTION.LEADS)
        AmoCRMFuncResponce(status=False, detail='Incorrect request!', data=None)
        """
        
        url = kwargs.get('url', None)
        if not url: url = f"https://{self.connect_domain}.amocrm.ru/api/{version_api}/{action}?{filters}"
        if self._debug: self._logger.info(f"Send url -> {url}")
        
        responce = requests.get(url, headers={ "Authorization" : f"Bearer {self.access_token}"})
        self._count_send_request += 1
        
        isAllowed, message, _ = self.__check_responce_status_code(responce)

        if not isAllowed: return AmoCRMFuncResponce(status=False, detail=message, data=None)
        
        data = AmoResponceGet.parse_obj(responce.json())

        return AmoCRMFuncResponce(status=True, data=data)
    
    def get_data_df(self, action: AmoCRM.ACTION, filters: str='', version_api: str='v4', *args, **kwargs) -> AmoCRMFuncResponce:
        """ Get data from action url on Dataframe format. Use 'get' function class.
        # Example
        >>> # Data is correct
        >>> amocrm = AmoCRM(**data)
        >>> amocrm.get_data_df(amocrm.ACTION.LEADS)
        AmoCRMFuncResponce(status=True, detail='', data=Dataframe(*Data in dataframe*))

        >>> # Data is not correct
        >>> amocrm = AmoCRM(**data)
        >>> amocrm.get_data_df(amocrm.ACTION.LEADS)
        AmoCRMFuncResponce(status=False, detail='Incorrect request!', data=Datafame())
        
        >>> # Get all data from amocrm (Using recursion)
        >>> # Receives data from the first page to the last page
        >>> amocrm = AmoCRM(**data)
        >>> amocrm.get_data_df(amocrm.ACTION.LEADS, get_all_data=True)
        AmoCRMFuncResponce(status=True, detail='', data=Dataframe(*Data in dataframe*))
        """
        get_responce = self.get(action=action, filters=filters, version_api=version_api, *args, **kwargs)
        
        if not get_responce.status: return AmoCRMFuncResponce(status=False, detail=get_responce.detail, data=DataFrame())
        if not isinstance(get_responce.data, AmoResponceGet): 
            return AmoCRMFuncResponce(status=False, detail='Type data is not AmoResponceGet!', data=DataFrame())
        
        data_df = self.parse_data_and_create_df(get_responce.data)
        
        if isinstance(data_df, DataFrame) and kwargs.get('get_all_data', False):
            if self._debug: self._logger.warning("Вход в рекурсивный запрос!")
            kwargs['url'] = get_responce.data.links.next.href
            data_df = concat([
                data_df, self.get_data_df(action, version_api=version_api, **kwargs).data
            ]).sort_index()
            if self._debug: self._logger.warning("Выход из рекурсивного запроса!")
        
        return AmoCRMFuncResponce(status=True, data=data_df)

    def get_data(self, action: AmoCRM.ACTION, filters: str='', version_api: str='v4', *args, **kwargs) -> AmoCRMFuncResponce:
        """ Get only data from action url on list format. Use 'get' function class.
        # Example
        >>> # Data is correct
        >>> amocrm = AmoCRM(**data)
        >>> amocrm.get_data(amocrm.ACTION.LEADS)
        AmoCRMFuncResponce(status=True, detail='', data=[(cls) Leads {id: 12653276, name: 'Name', price: 0, ... }])

        >>> # Data is not correct
        >>> amocrm = AmoCRM(**data)
        >>> amocrm.get_data(amocrm.ACTION.LEADS)
        AmoCRMFuncResponce(status=False, detail='Incorrect request!', data=None)
        """
        get_responce = self.get(action=action, filters=filters, version_api=version_api, *args, **kwargs)
        
        if not get_responce.status: return  AmoCRMFuncResponce(status=False, detail=get_responce.detail, data=None)
        if not isinstance(get_responce.data, AmoResponceGet):
            return AmoCRMFuncResponce(status=False, detail='Type data is not AmoResponceGet!', data=None)
        
        data = None
        err_msg = ""
        
        if isinstance(get_responce.data.embedded, DataContacts): data = get_responce.data.embedded.contacts 
        elif isinstance(get_responce.data.embedded, DataLeads): data = get_responce.data.embedded.leads
        else: err_msg = "Data is not allow! Access type = [Contacts, Leads]"
        
        return AmoCRMFuncResponce(status=True, detail=err_msg, data=data)

        # POST

    # POST

    def post(self, action: AmoCRM.ACTION, data: list[Union[AmoRequestPostLeads, AmoRequestPostContact]], version_api: str='v4', 
            max_count: int=50, *args, **kwargs) -> AmoCRMFuncResponce:
        """ Post data to amocrm.

        Args:
            action (AmoCRM.ACTION): Where to send data. For Leads action have 2 action: LEADS and LEADS_COMPLEX.
            data (list[Union[AmoRequestPostLeads, AmoRequestPostContact]]): Sent data.
            version_api (str, optional): Version api amocrm. Defaults to 'v4'.
            max_count (int, optional): Max count product send on batch. Defaults to 50.

        Returns:
            AmoCRMFuncResponce: Request function
            
        Example:
            >>> # Data is correct
            >>> amocrm = AmoCRM(**data)
            >>> data = [AmoRequestPostLeads(name="test", price=100.0, ...)]
            >>> amocrm.post(amocrm.ACTION.LEADS, data=data)
            AmoCRMFuncResponce(status=True, detail='', data=[(cls) Leads {id: 12653276, name: 'Name', price: 0, ... }])

            >>> # Data is not correct
            >>> amocrm = AmoCRM(**data)
            >>> data = []
            >>> amocrm.post(amocrm.ACTION.LEADS, data=data)
            AmoCRMFuncResponce(status=False, detail='Data is empty!', data=None)
        """

        url = kwargs.get('url', None)
        if not url: url = f"https://{self.connect_domain}.amocrm.ru/api/{version_api}/{action}"

        if data == []:  return AmoCRMFuncResponce(status=False, detail='Data is empty!', data=None)
        if self._debug: return AmoCRMFuncResponce(status=False, detail='AMOCRM | Debug mode is On!', data=None)
        
        responce_data = []
        data = list(map(lambda it: it.dict(skip_defaults=True), data))
        if self._debug: self._logger.info(f"POST | Send url -> {url}")

        if action == AmoCRM.ACTION.LEADS_COMPLEX:
            if self._debug: self._logger.warning("Вход в рекурсивный запрос! POST")

            for send_data in batch(data, max_count):
                if send_data == []: break

                responce = requests.post(url, json=send_data, headers={ "Authorization" : f"Bearer {self.access_token}", 
                                                                        "Content-Type": "application/json"})
        
                try: responce_data.append(AmoResponcePost(**responce.json()))
                except ValidationError: responce_data.append(AmoResponcePostError(**responce.json()))
    
                self._count_send_request += 1

            if self._debug: self._logger.warning("Выход из рекурсивного запроса! POST")
        else:
            responce = requests.post(url, json=data, headers={ "Authorization" : f"Bearer {self.access_token}", 
                                                                        "Content-Type": "application/json"})

            try: responce_data.append(AmoResponcePost(**responce.json()))
            except ValidationError: responce_data.append(AmoResponcePostError(**responce.json()))
        
        for item_data in responce_data:
            if isinstance(item_data, AmoResponcePostError): 
                return AmoCRMFuncResponce(status=False, detail="Some part of the data was not sent!", data=responce_data)

        isAllowed, message, _ = self.__check_responce_status_code(responce)
        if not isAllowed: return AmoCRMFuncResponce(status=False, detail=f"{message} | {responce.json()}", data=None)

        return AmoCRMFuncResponce(status=True, data=responce_data)

    # PATCH

    def patch(self, action: AmoCRM.ACTION, data: list[Union[AmoRequestPatchLeads, AmoRequestPatchContact]], version_api: str='v4', 
            *args, **kwargs) -> AmoCRMFuncResponce:
        """ Patch data to amocrm.

        Args:
            action (AmoCRM.ACTION): Where to send data.
            data (list[Union[AmoRequestPatchLeads, AmoRequestPatchContact]]): Sent data
            version_api (str, optional): Version api amocrm. Defaults to 'v4'.

        Returns:
            AmoCRMFuncResponce: Request function
            
        Example:
            >>> # Data is correct
            >>> amocrm = AmoCRM(**data)
            >>> data = [AmoRequestPatchLeads(name="test", price=100.0, ...)]
            >>> amocrm.patch(amocrm.ACTION.LEADS, data=data)
            AmoCRMFuncResponce(status=True, detail='', data=AmoResponcePatch(links={ href="..." }, embedded={...}))

            >>> # Data is not correct
            >>> amocrm = AmoCRM(**data)
            >>> data = []
            >>> amocrm.patch(amocrm.ACTION.LEADS, data=data)
            AmoCRMFuncResponce(status=False, detail='Data is empty!', data=None)
        """
        
        url = kwargs.get('url', None)
        if not url: url = f"https://{self.connect_domain}.amocrm.ru/api/{version_api}/{action}"

        if data == []:  return AmoCRMFuncResponce(status=False, detail='Data is empty!', data=None)
        if self._debug: return AmoCRMFuncResponce(status=False, detail='AMOCRM | Debug mode is On!', data=None)

        data = list(map(lambda it: it.dict(skip_defaults=True), data))
        
        if self._debug: self._logger.info(f"PATCH | Send url -> {url}")
        responce = requests.patch(url, json=data, headers={ "Authorization" : f"Bearer {self.access_token}" })
        self._count_send_request += 1

        try: responce_data = AmoResponcePatch(**responce.json())
        except ValidationError: responce_data = AmoResponcePatchError(**responce.json())

        if isinstance(responce_data, AmoResponcePatchError): 
            return AmoCRMFuncResponce(status=False, detail="Some part of the data was not sent!", data=responce_data)

        return AmoCRMFuncResponce(status=True, data=responce_data)
    
    # PARSE

    def __create_one_dimensional_df_on_leads(self, data: DataLeads) -> DataFrame:
        """ Create new Dataframe from data leads (AmoCrmResponce models).
        Return:
            - Dataframe()
        """
        # non_one_dimensional_fields = ['custom_fields_values', 'links', 'embedded']
        leads_dict: list[dict[str, Union[str, dict]]] = data.dict().get('leads', [])
        
        for index, lead in enumerate(data.leads):
            
            if isinstance(lead.custom_fields_values, list):
                fields_list = []
                for field in lead.custom_fields_values:
                    if not field.values[0].enum_id:
                        field.values[0].enum_id = None
                    fields_list.append(field.dict())
                leads_dict[index]['custom_fields_values'] = fields_list
            
            if isinstance(lead.links, Links):
                leads_dict[index]['link'] = lead.links.self.href
                del leads_dict[index]['links']

            if isinstance(lead.embedded, Embedded):
                tags_list: list[dict[str, Union[str,int]]] = []
                for tag in lead.embedded.tags:
                    tags_list.append({'id': tag.id, 'name': tag.name })
                leads_dict[index]['embedded_tags'] = tags_list
                                
                companies_list: list[dict[str, Union[str,int]]] = []
                for company in lead.embedded.companies:
                    companies_list.append({"id": company.id, "link": company.links.self.href.__str__()})
                else: leads_dict[index]['embedded_companies'] = companies_list
                
                contact_list: list[dict[str, Union[str,int]]] = []
                if lead.embedded.contacts:
                    for contact in lead.embedded.contacts:
                        contact_list.append(contact.id)
                    leads_dict[index]['contact_id'] = None if len(contact_list) == 0 else contact_list[0]
        
                del leads_dict[index]['embedded']

        return DataFrame(data=leads_dict)

    def __create_one_dimensional_df_on_contacts(self, data: DataContacts) -> DataFrame:
        """ Create new Dataframe from data contacts (AmoCrmResponce models).
        Return:
            - Dataframe()
        """
        # non_one_dimensional_fields = ['custom_fields_values', 'links', 'embedded']
        contacts_dict: list[dict[str, Union[str, dict]]] = data.dict().get('contacts', [])
        
        for index, contact in enumerate(data.contacts):
            email = None
            phone = None
            fields_list = []
            
            if isinstance(contact.custom_fields_values, list):
                for field in contact.custom_fields_values:
                    if field.field_code == 'EMAIL': email = field.values[0].value
                    elif field.field_code == 'PHONE': phone = field.values[0].value
                    else: fields_list.append(field.dict())
            elif isinstance(contact.custom_fields_values, NoneType):
                fields_list.append({'values': []})
            
            if isinstance(contact.links, Links):
                contacts_dict[index]['link'] = contact.links.self.href
                del contacts_dict[index]['links']

            tags_list = []
            companies_list = []
            if isinstance(contact.embedded, Embedded):
                for tag in contact.embedded.tags:

                    tags_list.append({"id": tag.id, "name": tag.name})
                for company in contact.embedded.companies:

                    companies_list.append({"id": company.id, "link": company.links.self.href.__str__()})
                del contacts_dict[index]['embedded']
                
            contacts_dict[index]['email'] = email
            contacts_dict[index]['phone'] = phone
            contacts_dict[index]['custom_fields_values'] = fields_list
            contacts_dict[index]['embedded_tags'] = tags_list
            contacts_dict[index]['embedded_companies'] = companies_list
            
        return DataFrame(data=contacts_dict)

    def parse_data_and_create_df(self, data: AmoResponceGet) -> Optional[DataFrame]:

        """ Parse data from get function and create df.
        
        ::Return::
            ~ Dataframe | None
        """
        
        if isinstance(data.embedded, DataLeads):
            return self.__create_one_dimensional_df_on_leads(data.embedded)
        elif isinstance(data.embedded, DataContacts):
            return self.__create_one_dimensional_df_on_contacts(data.embedded)
        
        self._logger.error(f"Data is not allowed type. type -> {type(data.embedded)}")
        return None
