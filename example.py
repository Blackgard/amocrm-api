from __future__ import annotations

from amocrm.v4.models.amoCRM_M import AmoRequestPatchLeads, AmoRequestPostLeads, AmoResponcePatch, \
                                      AmoResponcePatchError, AmoResponcePost, AmoResponcePostError, ModeSaveTokenEnum

from amocrm.v4.amoCRM import AmoCRM, FilterAmoCRM, AmoCRMInit

import json

from loguru import logger
from dotenv import dotenv_values

env = dotenv_values(".env")


if __name__ == "__main__":
    # Set default logger
    main_logger = logger

    # Create filters
    amocrm_filter = FilterAmoCRM(FilterAmoCRM.ACTIONS.LAST_DAY).get_filters()

    # Create init settings
    init_amocrm_data = AmoCRMInit(
        connect_email=env.get("CONNECT_EMAIL", None),
        connect_domain=env.get("CONNECT_DOMAIN", None),
        connect_id=env.get("CONNECT_ID", None),
        connect_secret_key=env.get("CONNECT_SECRET_KEY", None),
        refresh_token=env.get("REFRECH_TOKEN", None),
        access_token=env.get("ACCESS_TOKEN", None),
        redirect_uri=env.get("REDIRECT_URI", None),
        init_code=env.get("INIT_CODE", None),

        mode_save_token={
            "mode": ModeSaveTokenEnum.LOCAL_FILE,
            "path_to_file": "./access_tokens.json"
        },

        check_auth_in_init=True,
        attempts_conn=3,
        debug=env.get("DEBUG", False),
    )
    
    # Create AmoCRM connector object
    amocrm = AmoCRM(init_amocrm_data)
    
    # View AmoCRM statistic
    main_logger.debug(amocrm)

    # Get data
    resp_get = amocrm.get(AmoCRM.ACTION.LEADS, filters=amocrm_filter.get(FilterAmoCRM.TABLE.LEADS))
    if resp_get.status: 
        main_logger.debug(json.dumps(resp_get.data.dict(), indent=4))

    # Get data main block
    resp_get_data = amocrm.get_data(AmoCRM.ACTION.LEADS, filters=amocrm_filter.get(FilterAmoCRM.TABLE.LEADS))
    if resp_get_data.status: 
        main_logger.debug(json.dumps( [item.dict() for item in resp_get_data.data], indent=4))

    # Get data on dataframe
    resp_get_data_df = amocrm.get_data_df(AmoCRM.ACTION.LEADS, filters=amocrm_filter.get(FilterAmoCRM.TABLE.LEADS))
    if resp_get_data_df.status: 
        resp_get_data_df.data.info()

    # Add new deal
    resp_post = amocrm.post(AmoCRM.ACTION.LEADS, data=[AmoRequestPostLeads(name="test", price=100.0)])
    
    # Default deal id
    id_new_deal = 0

    # Let's display the result for all data
    if resp_post.status:
        for data_item in resp_post.data:
            if isinstance(data_item, AmoResponcePostError): 
                main_logger.error(json.dumps(data_item.dict(), indent=4))
            elif isinstance(data_item, AmoResponcePost):
                main_logger.success(json.dumps(data_item.dict(), indent=4))
                id_new_deal = data_item.embedded.leads[0].id


    # View POST answer to AmoCRM 
    main_logger.debug(resp_post)
    
    # Add new deal
    resp_post_complex = amocrm.post(AmoCRM.ACTION.LEADS_COMPLEX, data=[AmoRequestPostLeads(name="test", price=100.0)])

    # Let's display the result for all data
    if resp_post.status:
        for data_item in resp_post.data:
            if isinstance(data_item, AmoResponcePostError): 
                main_logger.error(json.dumps(data_item.dict(), indent=4))
            elif isinstance(data_item, AmoResponcePost):
                main_logger.success(json.dumps(data_item.dict(), indent=4))


    # View POST complex answer to AmoCRM 
    main_logger.debug(resp_post)

    # Update new deal
    resp_patch = amocrm.patch(AmoCRM.ACTION.LEADS, data=[AmoRequestPatchLeads(id=id_new_deal, name="test", price=80.0)])

    if resp_patch.status:
        if isinstance(resp_patch.data, AmoResponcePatchError):
            main_logger.error(json.dumps(resp_patch.data.dict(), indent=4))
        elif isinstance(resp_patch.data, AmoResponcePatch):
            main_logger.success(json.dumps(resp_patch.data.dict(), indent=4))

    # View PATCH answer to AmoCRM 
    main_logger.debug(resp_patch)

    # View AmoCRM statistic
    main_logger.debug(amocrm)