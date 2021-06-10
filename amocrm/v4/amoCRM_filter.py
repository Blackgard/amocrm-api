""" Main class FilterAmoCRM work with filter from amocrm """

from __future__ import annotations
from typing import Tuple

import enum
import json
import pytz
import loguru

from datetime import datetime, timedelta


class FilterConst:
    class ACTIONS(enum.Enum):
        LAST_5_AGE = 'LAST_5_AGE'
        LAST_DAY = 'LAST_DAY'
        
    class TYPE(enum.Enum):
        LIMIT = 'limit' # max limit = 250
        ORDER = 'order' # Ex: order[update_at]=desc/asc
        CREATE_AT_FROM = 'filter[created_at][from]' # = timestamp value. Ex: 15314
        CREATE_AT_TO = 'filter[created_at][to]' # = timestamp value. Ex: 15314
        UPDATE_AT_FROM = 'filter[update_at][from]' # = timestamp value. Ex: 15314
        UPDATE_AT_TO = 'filter[update_at][to]' # = timestamp value. Ex: 15314
        
    class TABLE(enum.Enum):
        CONTACTS = 'contacts'
        LEADS = 'leads'

class FilterAmoCRM(FilterConst):
    " Class work with filter getcourse "
    
    def __init__(self, type: FilterAmoCRM.ACTIONS, pytz_timezone: str = "Europe/Moscow", logger: loguru.Logger = loguru.logger):
        self.type = type
        self.filters = {}
        
        self._pytz_timezone_str = pytz_timezone
        self._pytz_timezone = pytz.timezone(pytz_timezone)
        
        self._logger = logger

        if self.type not in FilterAmoCRM.ACTIONS:
            raise ValueError(f"This type '{self.type}' filter not found! Filter is none!")
        self.create_filters()

    def __str__(self):
        return str(self.get_filters())

    def get_datetime_for_filter(self, type: FilterAmoCRM.TYPE, table: FilterAmoCRM.TABLE) -> Tuple[int, int]:
        """ Get from and to datetime filter for table.

        Args:
            type (FilterAmoCRM.TYPE): Type filter
            table (FilterAmoCRM.TABLE): Table for create filter
            
        Returns:
             [Tuple[int,int]]: filters for amocrm model
        """
        _type = type or self.type
        datetime_from = None
        datetime_to = None
        
        if _type == FilterAmoCRM.ACTIONS.LAST_DAY:
            datetime_from = int((datetime.now(self._pytz_timezone) - timedelta(days=1)).timestamp())
            datetime_to = int(datetime.now(self._pytz_timezone).timestamp())
        elif _type == FilterAmoCRM.ACTIONS.LAST_5_AGE:
            datetime_from = int((datetime.now(self._pytz_timezone) - timedelta(weeks=300)).timestamp())
            datetime_to = int(datetime.now(self._pytz_timezone).timestamp())
            
        return datetime_from, datetime_to

    def create_filters(self) -> bool:
        """ Create filters with settings on init class.

        Returns:
            bool: is success create
        """

        for table in FilterAmoCRM.TABLE:
            datetime_from, datetime_to = self.get_datetime_for_filter(self.type, table)
            if not datetime_from or not datetime_to:
                return False

            self.filters[table.value] = f"{FilterAmoCRM.TYPE.LIMIT.value}=250&{FilterAmoCRM.TYPE.CREATE_AT_FROM.value}={datetime_from}&{FilterAmoCRM.TYPE.CREATE_AT_TO.value}={datetime_to}"
        
        return True


    def get_filters(self) -> dict[str, str]:
        """get filters on dict format

        Returns:
            filters [dict[str,str]]: filters for amocrm model
        """
        return self.filters
    
    def get_filters_json(self, *args, **kwargs) -> bytes:
        """Get json encoded filter.
        
        Args and Kwargs for json.dumps.

        Returns:
            filters_json_encoding [bytes]: Json encoded filter
        """

        return json.dumps(self.filters, default=str, *args, **kwargs).encode()