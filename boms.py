import json
from datetime import datetime,date
import base64
from db_connection import db_connection_manage
import sys
import os
import re
from cms_utils import file_uploads,dynamic_fields,batch_number_allocation,find_stock_inwards,get_kit_and_boards_info, find_stock_inward_new


file_up = file_uploads()
dyn_f = dynamic_fields()
conct = db_connection_manage()

def calculate_mean(ratios):
    return (sum(ratios) / len(ratios))
    
# def update_category_info(part_batch_info,category_info,ekitInfo,invent_Ref,partner_name):#Working fine till 2 Aug 12PM
#     resp = {}
#     activity_details = {}
#     #handling component ids
#     for i, item in enumerate(category_info):
#         if item['cmpt_id'] in part_batch_info:
#             # batch_info = {inx:value for inx,value in enumerate(part_batch_info[item['cmpt_id']])}
#             batch_info = part_batch_info
#             missingFields = {
#                     "mfr_prt_num": item.get("mfr_prt_num", "-"),
#                     "date":str(date.today()),
#                     "action":"Utilized",
#                     "Description":"Utilized",
#                     "issued_to":partner_name,
#                     "cmpt_id": item.get("cmpt_id", ""),
#                     "ctgr_id": item.get("ctgr_id", ""),
#                     "prdt_name": item.get("prdt_name", ""),
#                     "description": item.get("description", "-"),
#                     "packaging": item.get("packaging", "-"),
#                     "inventory_position": item.get("inventory_position", "-"),
#                     "closing_qty": f"{int(invent_Ref[item['cmpt_id']])-int(item.get("provided_qty", "0"))}",
#                     "qty": item.get("provided_qty", "0"),
#                     "used_qty":"0"
#                 }
#         else:
#             batch_info = {}
#         var = batch_number_allocation(batch_info,int(item['provided_qty']),item['cmpt_id'],ekitInfo)
#         # print(batch_info,int(item['provided_qty']),item['cmpt_id'],ekitInfo)
#         # return var
#         if var:
#             item['batch_no'] = var['batch_string']
#             missingFields["po_id"] = var['po_id']
#             missingFields['invoice_no'] = var['invoice_no']
#             missingFields['lot_no'] = var['lot_no']
#             missingFields['batchId'] = var['batch_string']
#         else:
#             return None
#         resp[f"part{i+1}"] = item
#         activity_details[item['cmpt_id']] = missingFields
#     return {"activity_details":activity_details,"part_details":resp}

def update_category_info(category_info):
    if category_info:
        return {f'part{i+1}': item for i, item in enumerate(category_info)}
    return category_info

def filter_parts(parts_dict, filter_key):
    return {part_key: part_value for part_key, part_value in parts_dict.items() if int(part_value.get(filter_key, 0)) < 0}

def calculate_difference(parts_dict):
    for part_key, part_value in parts_dict.items():
        required_quantity = int(part_value.get("required_quantity", 0))
        provided_qty = int(part_value.get("provided_qty", 0))
        part_value["required_quantity"] = required_quantity - provided_qty
    return parts_dict
    
def extract_numeric_part(key):
    # Extract the numeric part from the key
    numeric_part = ''.join(c for c in key if c.isdigit())
    print(numeric_part)
    return int(numeric_part) if numeric_part.isdigit() else 0 

def calculate_total_balance_qty(parts_dict):
    total_balance_qty = 0
    for part_key, part_value in parts_dict.items():
        total_balance_qty += int(part_value.get("balance_qty", 0))
    return total_balance_qty

class Boms():


    def CmsBomCreate(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            env_type = data.get("env_type","")
            bom_name = data.get("bom_name", "").strip()
            m_part = data.get('M-Category_info',[])
            e_part = data.get('E-Category_info',[])
            vic_part_dict = {}
            mfr_prt_dict = {}
            for part in m_part:
                part.pop('s.no', None)
                vic_part_number = part['vic_part_number']
                qty_per_board = part.get('qty_per_board', 0)
                if not qty_per_board.isdigit():
                    conct.close_connection(client)
                    return {'statusCode': 400, 'body': f"Invalid quantity '{qty_per_board}' for vic_part_number: {vic_part_number}. Please enter a valid number."}
                if vic_part_number in vic_part_dict:
                    vic_part_dict[vic_part_number]['qty_per_board'] = str(int(vic_part_dict[vic_part_number]['qty_per_board']) + int(qty_per_board))
                else:
                    result = db_con.Inventory.find_one(
                        {
                            "all_attributes.mfr_prt_num": part['vic_part_number'],
                            "all_attributes.prdt_name": part['prdt_name']
                        },
                        {
                            "_id": 0,
                            "cmpt_id": "$all_attributes.cmpt_id",
                            "ctgr_id": "$all_attributes.ctgr_id",
                            "ctgr_name": "$all_attributes.ctgr_name",
                            "department": "$all_attributes.department",
                            "technical_details": "$all_attributes.technical_details",
                            "ptg_prt_num": "$all_attributes.ptg_prt_num",
                            "material": "$all_attributes.material",
                            "manufacturer": "$all_attributes.manufacturer" or "$all_attributes.mfr"
                        }
                    )
                    if result:
                        result['qty_per_board'] = qty_per_board
                        part.update(result)
                        vic_part_dict[vic_part_number] = part
                    else:
                        return {'statusCode': 300, 'body': f"No matching record found for mfr_prt_num: {part['vic_part_number']} and prdt_name: {part['prdt_name']}"}
            for part in e_part:
                part.pop('s.no', None)
                mfr_prt_num = part['mfr_prt_num']
                qty_per_board = part.get('qty_per_board', 0)
                if not qty_per_board.isdigit():
                    conct.close_connection(client)
                    return {'statusCode': 400, 'body': f"Invalid quantity '{qty_per_board}' for mfr_prt_num: {mfr_prt_num}. Please enter a valid number."}
                if mfr_prt_num in mfr_prt_dict:
                    mfr_prt_dict[mfr_prt_num]['qty_per_board'] = str(int(mfr_prt_dict[mfr_prt_num]['qty_per_board']) + int(qty_per_board))
                else:
                    result = db_con.Inventory.find_one(
                        {
                            "all_attributes.mfr_prt_num": part['mfr_prt_num'],
                            **{k: part['manufacturer'] for k in ["all_attributes.manufacturer", "all_attributes.mfr"]}
                            # "all_attributes.manufacturer": part['manufacturer']
                        },
                        {
                            "_id": 0,
                            "cmpt_id": "$all_attributes.cmpt_id",
                            "ctgr_id": "$all_attributes.ctgr_id",
                            "ctgr_name": "$all_attributes.ctgr_name",
                            "ptg_prt_num": "$all_attributes.ptg_prt_num",
                            "material": "$all_attributes.material",
                            "sub_ctgr": "$all_attributes.sub_ctgr",
                            "mounting_type": "$all_attributes.mounting_type",
                            "department": "$all_attributes.department",
                            "sub_category": "$gsisk_id",
                            "description": "$all_attributes.description",
                            "foot_print": "$all_attributes.foot_print",
                            "manufacturer": "$all_attributes.manufacturer" or "$all_attributes.mfr"
                        }
                    )
                    if result:
                        result['qty_per_board'] = qty_per_board
                        part.update(result)
                        mfr_prt_dict[mfr_prt_num] = part
                    else:
                        return {'statusCode': 300, 'body': f"No matching record found for mfr_prt_num: {part['mfr_prt_num']} and manufacturer: {part['manufacturer']}"}
            # m_parts = {f"part{inx+1}":item for inx,item in enumerate(m_part)}
            # e_parts = {f"part{inx+1}":item for inx,item in enumerate(e_part)}
            m_parts = {f"part{inx+1}":item for inx,item in enumerate(vic_part_dict.values())}
            e_parts = {f"part{inx+1}":item for inx,item in enumerate(mfr_prt_dict.values())}
            categories = len(set([item['ctgr_id'] for item in vic_part_dict.values()]))+len(set([item['ctgr_id'] for item in mfr_prt_dict.values()]))
            # categories = len(set([item['ctgr_id'] for item in m_part]))+len(set([item['ctgr_id'] for item in e_part]))
            all_attributes = {}
            if m_parts or e_parts:
                result = list(db_con.BOM.find({}))
                bom_id = "01"
                if result:
                    bom_search = any(1 for i in result if i["all_attributes"]["bom_name"].lower() == bom_name.lower())
                    if bom_search:
                        conct.close_connection(client)
                        return {"statusCode": 400, "body": "Bom already exists, please choose another Bom name",}
                    bom_ids = [i["all_attributes"]["bom_id"].replace("PTGBOM", "") for i in result]
                    bom_ids.sort(reverse=True)
                    bom_id = (str(((2 - len(str(int(bom_ids[0]) + 1)))) * "0") + str(int(bom_ids[0]) + 1) if len(str(int(bom_ids[0]))) == 1 else str(int(bom_ids[0]) + 1))
                all_attributes["bom_id"] = "PTGBOM" + bom_id
                all_attributes['description'] = data['bom_description']
                all_attributes['bom_name'] = data['bom_name'].strip()
                all_attributes["created_time"] = (datetime.now()).strftime("%d/%m/%Y")
                all_attributes['total_categories'] = str(categories)
                all_attributes['total_components'] = str(len(e_parts.keys())+len(m_parts.keys()))
                all_attributes["E_parts"] = e_parts
                all_attributes["M_parts"] = m_parts
                item = {
                    "pk_id": "PTGBOM" + bom_id,
                    "sk_timeStamp": (datetime.now()).isoformat(),
                    "all_attributes": all_attributes,
                    "lsi_key": "--",
                }
                try:
                    response = db_con.BOM.insert_one(item)
                    resp = db_con.all_tables.update_one(
                            {"pk_id": "top_ids"},
                            {"$set": {"all_attributes.BOM" : "PTGBOM"+str(bom_id)}}
                        )
                    conct.close_connection(client)
                    return {"statusCode": 200, "body": "New BOM created successfully",}
                except Exception as e:
                    conct.close_connection(client)
                    return {"statusCode": 500, "body": "Error saving item: " + str(e)}
            else:
                conct.close_connection(client)
                return {"statusCode": 400, "body": "Please add components"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request(check data)'}
 
    # def CmsBomCreate(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         env_type = data.get("env_type","")
    #         bom_name = data.get("bom_name", "").strip()
    #         m_parts = {f"part{inx+1}":item for inx,item in enumerate(data.get('M-Category_info',[]))}
    #         e_parts = {f"part{inx+1}":item for inx,item in enumerate(data.get('E-Category_info',[]))}
    #         categories = len(set([item['ctgr_id'] for item in data.get('M-Category_info',[])]))+len(set([item['ctgr_id'] for item in data.get('E-Category_info',[])]))
    #         all_attributes = {}
    #         if m_parts or e_parts:
    #             result = list(db_con.BOM.find({}))
    #             bom_id = "01"
    #             if result:
    #                 bom_search = any(1 for i in result if i["all_attributes"]["bom_name"].lower() == bom_name.lower())
    #                 if bom_search:
    #                     conct.close_connection(client)
    #                     return {"statusCode": 400, "body": "Bom already exists, please choose another Bom name",}
    #                 bom_ids = [i["all_attributes"]["bom_id"].replace("PTGBOM", "") for i in result]
    #                 bom_ids.sort(reverse=True)
    #                 bom_id = (str(((2 - len(str(int(bom_ids[0]) + 1)))) * "0") + str(int(bom_ids[0]) + 1) if len(str(int(bom_ids[0]))) == 1 else str(int(bom_ids[0]) + 1))
    #             all_attributes["bom_id"] = "PTGBOM" + bom_id
    #             all_attributes['description'] = data['bom_description']
    #             all_attributes['bom_name'] = data['bom_name'].strip()
    #             all_attributes["created_time"] = (datetime.now()).strftime("%d/%m/%Y")
    #             all_attributes['total_categories'] = str(categories)
    #             all_attributes['total_components'] = str(len(e_parts.keys())+len(m_parts.keys()))
    #             all_attributes["E_parts"] = e_parts
    #             all_attributes["M_parts"] = m_parts
    #             item = {
    #                 "pk_id": "PTGBOM" + bom_id,
    #                 "sk_timeStamp": (datetime.now()).isoformat(),
    #                 "all_attributes": all_attributes,
    #                 "lsi_key": "--",
    #             }
    #             try:
    #                 response = db_con.BOM.insert_one(item)
    #                 conct.close_connection(client)
    #                 return {"statusCode": 200, "body": "New BOM created successfully",}
    #             except Exception as e:
    #                 conct.close_connection(client)
    #                 return {"statusCode": 500, "body": "Error saving item: " + str(e)}
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 400, "body": "Please add components"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400,'body': 'Bad Request(check data)'}
    
    def cmsDeleteBom(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            bom_id = data['bom_id']
            vendor_parts = list(db_con.Vendor.find({}))
            vendor_parts = {item['all_attributes']['vendor_id']:[part['bom_id'] for key,part in item['all_attributes']['parts'].items()] for item in vendor_parts}
            if any(1 for item in vendor_parts.keys() if bom_id in vendor_parts[item]):
                return {'statusCode':400,'body': 'You cannot delete bom the parts already assigned to vendor'}
            results1 = list(db_con.Clients.find({}))
            if any(data['bom_id'] == k['bom_id'] for i in results1 for k in i['all_attributes']['boms'].values()): 
                return {'statusCode':400,'body': 'You cannot delete this bom_id it is assigned to client'}
            results = list(db_con.BOM.find({"all_attributes.bom_id":bom_id}))
            if results:
                try:
                    db_con.BOM.delete_one({"pk_id": bom_id})
                    conct.close_connection(client)
                    return {"statusCode": 200, "body": "BOM Deleted Successfully"}
                except:
                    conct.close_connection(client)
                    return {"statusCode": 500, "body": "Failed while deleting BOM"}
            else:
                conct.close_connection(client)
                return {"statusCode": 404, "body": "BOM not found"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'error': 'Bad Request(check data)'}
    
    def CmsBomEdit(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            total_components = len(data['E_parts'])+len(data['M_parts'])
            total_categories = len(set([item['ctgr_name'] for item in data.get('M_parts',[])]))+len(set([item['ctgr_name'] for item in data.get('E_parts',[])]))
            e_cmpids = [part['cmpt_id'] for part in data['E_parts']]
            m_cmpids = [part['cmpt_id'] for part in data['M_parts']]
            data['E_parts'] = {f"part{inx+1}": part for inx,part in enumerate(data['E_parts'])}
            data['M_parts'] = {f"part{inx+1}": part for inx,part in enumerate(data['M_parts'])}
            env_type = data["env_type"]
            bom_id = data.get("bom_id","")
            bom_name = data.get("bom_name", "")
            data.pop('env_type')
            if data['E_parts'] or data['M_parts']:
                bom_response = list(db_con.BOM.find({"all_attributes.bom_id":bom_id}))
                response = list(db_con.BOM.find({"all_attributes.bom_id": {"$ne": bom_id}}))
                bom_search = [1 for i in response if i["all_attributes"]["bom_name"].lower() == bom_name.lower()]
                if bom_search:
                    conct.close_connection(client)
                    return {"statusCode": 400, "body": "Given BOM name already exists, please try with other names"}
                if bom_response:
                    pk_id_for_bom=bom_response[0]["pk_id"]
                    sk_timestamp=bom_response[0]["sk_timeStamp"]
                    price_bom = bom_response[0]['all_attributes'].get('price_bom',{})
                    result = bom_response[0]
                    for key in result.keys():
                        pass
                    for part_type in ['E_parts']:
                        if part_type in result:
                            for part in result[part_type].values():
                                ctgr_id = part['ctgr_id']
                                sub_category=part['sub_ctgr']                               
                            metadataid = "MDID" + ctgr_id[4:]
                            metadata_result = list(db_con.Metadata.find({"pk_id":metadataid}))
                            if metadata_result:
                                metadata = {value:key for key,value in metadata_result[0]['sub_categories'].items()}
                                if sub_category in metadata:  
                                    sub_category = metadata[sub_category]
                                else:
                                    pass
                    all_attributes = data
                    all_attributes['total_components'] = str(total_components)
                    all_attributes['total_categories'] = str(total_categories)
                    if price_bom:
                        pb = {}
                        if 'M_parts' in price_bom:
                            m_parts = {}
                            for key in price_bom['M_parts'].keys():
                                if price_bom['M_parts'][key]['cmpt_id'] in m_cmpids:
                                    m_parts[key] = price_bom['M_parts'][key]
                            pb['M_parts'] = m_parts
                        if 'E_parts' in price_bom:
                            e_parts = {}
                            for key in price_bom['E_parts'].keys():
                                if price_bom['E_parts'][key]['cmpt_id'] in e_cmpids:
                                    e_parts[key] = price_bom['E_parts'][key]
                            pb['E_parts'] = e_parts
                        if pb:
                            all_attributes['price_bom'] = pb
                    key = {
                        "pk_id": pk_id_for_bom,
                        "sk_timeStamp": sk_timestamp,
                    }
                    result = db_con.BOM.update_one(
                            {"pk_id": bom_id},
                            {"$set": {"all_attributes": all_attributes}}
                        )
                    conct.close_connection(client)
                    return {"statusCode": 200, "body": "BOM Details updated successfully"}
                else:
                    conct.close_connection(client)
                    return {
                        "statusCode": 404,
                        "body": "Data mismatch error, no entry for the given bom id",
                    }
            else:
                conct.close_connection(client)
                return {"statusCode": 404, "body": "Please add components"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'error': 'Failed while editing bom'}
    
    def CmsBomGetAllData(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            bom_response = list(db_con.BOM.find({}))
            sorted_filtered_data = sorted(
                [
                    {
                        "bom_id": i["all_attributes"]["bom_id"],
                        "bom_name": i["all_attributes"]["bom_name"],
                        "created_date": i["all_attributes"]["created_time"],
                        "total_categories": i["all_attributes"]["total_categories"],
                        "total_components": i["all_attributes"]["total_components"]
                    }
                    for i in bom_response
                ],
                key=lambda x: int(x["bom_id"].replace("PTGBOM","")),
                reverse=True
            )
            if sorted_filtered_data:
                conct.close_connection(client)
                return {"statusCode":200,"body":sorted_filtered_data}
            else:
                conct.close_connection(client)
                return {"statusCode":404,"body":"No Data Found" }
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Failed while fetching bom list'}
    
    # def CmsBomGetInnerDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         env_type = data["env_type"]
    #         bom_name = data.get("bom_name","")
    #         bom_id = data.get("bom_id","")
    #         bom_response = list(db_con.BOM.find({"all_attributes.bom_id":bom_id}))
    #         lst=[]
    #         if bom_response:
    #             result = bom_response
    #             for i in result:
    #                 i = i['all_attributes']
    #                 # return i
    #                 if data["dep_type"]=="Electronic":
    #                     metadata = list(db_con.Metadata.find({"gsipk_id":"Electronic"}))
    #                     e_cat_reference = {
    #                             item['pk_id'].replace("MDID","CTID"):
    #                                 {
    #                                     "category_name":item['gsisk_id'],
    #                                     "sub_categories":{key:value for key,value in item['sub_categories'].items()}
    #                                 } 
    #                             for item in metadata if item['gsipk_id']=='Electronic'
    #                         }
    #                     inventory = list(db_con.Inventory.find({'gsipk_id':'Electronic'},{"_id":0,"all_attributes.mounting_type":1,"all_attributes.manufacturer":1,"all_attributes.description":1,"all_attributes.cmpt_id":1,"all_attributes.qty":1}))
    #                     # return inventory[0]
    #                     inventory = {
    #                             item['all_attributes']['cmpt_id']:
    #                             {
    #                                 "mounting_type":item['all_attributes'].get('mounting_type',''),
    #                                 "manufacturer":item['all_attributes'].get('manufacturer',''),
    #                                 "description":item['all_attributes'].get('description',''),
    #                                 "qty":item['all_attributes'].get('qty','')
    #                             } 
    #                             for item in inventory
    #                         }
    #                     lst = [
    #                             {
    #                                 "sno":part_key,
    #                                 "ptg_prt_num":i["E_parts"][part_key]["ptg_prt_num"],
    #                                 "mfr_part_number":i["E_parts"][part_key]["mfr_prt_num"],
    #                                 "part_name": e_cat_reference[i["E_parts"][part_key]["ctgr_id"]]['sub_categories'][i["E_parts"][part_key]["sub_ctgr"]],
    #                                 "manufacturer":inventory[i["E_parts"][part_key]["cmpt_id"]]["manufacturer"],
    #                                 "device_category":e_cat_reference[i["E_parts"][part_key]["ctgr_id"]]['category_name'],
    #                                 "mounting_type":inventory[i["E_parts"][part_key]["cmpt_id"]]["mounting_type"],
    #                                 "required_quantity":i["E_parts"][part_key]["qty_per_board"],
    #                                 "qty":inventory[i["E_parts"][part_key]["cmpt_id"]]["qty"],
    #                                 "ctgr_id": i["E_parts"][part_key]["ctgr_id"],
    #                                 "cmpt_id":i["E_parts"][part_key]["cmpt_id"]
    #                             } 
    #                         for part_key in i["E_parts"] 
    #                         if part_key.startswith("part")
    #                     ]
    #                 elif data["dep_type"]=="Mechanic":
    #                     metadata = list(db_con.Metadata.find({"gsipk_id":"Mechanic"}))
    #                     m_cat_reference = {
    #                         item['pk_id'].replace("MDID","CTID"):{"category_name":item['gsisk_id']} 
    #                         for item in metadata 
    #                         if item['gsipk_id']=='Mechanic'
    #                         }
    #                     inventory = db_con.Inventory.find({"gsipk_id":"Mechanic"},{"all_attributes.mounting_type":1,"all_attributes.manufacturer":1,"all_attributes.description":1,"all_attributes.cmpt_id":1,"all_attributes.qty":1,"all_attributes.ctgr_name":1,"all_attributes.material":1,"all_attributes.technical_details":1,"all_attributes.prdt_name":1})
    #                     inventory = {
    #                         item['all_attributes']['cmpt_id']:
    #                         {
    #                         #    "mounting_type":item['all_attributes']['mounting_type'],
    #                         #    "manufacturer":item['all_attributes']['manufacturer'],
    #                            "description":item['all_attributes']['description'],
    #                            "qty":item['all_attributes']['qty'],
    #                            "ctgr_name":item['all_attributes']['ctgr_name'],
    #                            "material":item['all_attributes']['material'],
    #                            "technical_details":item['all_attributes']['technical_details'],
    #                            "prdt_name":item['all_attributes']['prdt_name'],
    #                         } 
    #                         for item in inventory
    #                         }
    #                     lst = [
    #                             {
    #                                 "ptg_prt_num":i["M_parts"][part_key]["ptg_prt_num"],       
    #                                 "vic_part_number":i["M_parts"][part_key]["vic_part_number"],
    #                                 "part_name":inventory[i["M_parts"][part_key]["cmpt_id"]]["prdt_name"],
    #                                 "ctgr_name":inventory[i["M_parts"][part_key]["cmpt_id"]]["ctgr_name"],
    #                                 "material":inventory[i["M_parts"][part_key]["cmpt_id"]]["material"],
    #                                 "technical_details":inventory[i["M_parts"][part_key]["cmpt_id"]]["technical_details"],
    #                                 "description":inventory[i["M_parts"][part_key]["cmpt_id"]]["description"],
    #                                 "required_quantity":i["M_parts"][part_key]["qty_per_board"],
    #                                 "qty":inventory[i["M_parts"][part_key]["cmpt_id"]]["qty"],
    #                                 "ctgr_id": i["M_parts"][part_key]["ctgr_id"],
    #                                 "cmpt_id":i["M_parts"][part_key]["cmpt_id"]
    #                             }
    #                         for part_key in i["M_parts"] 
    #                         if part_key.startswith("part")
    #                     ]
    #             resp = { 
    #                     "bom_id": bom_id,
    #                     "bom_name": bom_name,
    #                     "created_date": bom_response[0]["all_attributes"]["created_time"],
    #                     "description": bom_response[0]["all_attributes"]["description"],
    #                     "dep_type":data["dep_type"],
    #                     "parts":lst
    #                 }
    #             return {"statusCode":200,"body":resp}
    #         else:
    #             return {"statusCode":404,"body":"No Data Found" }
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400,'body': 'Bad Request(check data)'}
        


    def CmsBomGetInnerDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            env_type = data["env_type"]
            bom_name = data.get("bom_name","")
            bom_id = data.get("bom_id","")
            bom_response = list(db_con.BOM.find({"all_attributes.bom_id":bom_id}))
            lst=[]
            if bom_response:
                result = bom_response
                for i in result:
                    i = i['all_attributes']
                    # return i
                    if data["dep_type"]=="Electronic":
                        metadata = list(db_con.Metadata.find({"gsipk_id":"Electronic"}))
                        e_cat_reference = {
                                item['pk_id'].replace("MDID","CTID"):
                                    {
                                        "category_name":item['gsisk_id'],
                                        "sub_categories":{key:value for key,value in item['sub_categories'].items()}
                                    } 
                                for item in metadata if item['gsipk_id']=='Electronic'
                            }
                        inventory = list(db_con.Inventory.find({'gsipk_id':'Electronic'},{"_id":0,"all_attributes.mounting_type":1,"all_attributes.manufacturer":1,"all_attributes.description":1,"all_attributes.cmpt_id":1,"all_attributes.qty":1,"all_attributes.hsn_code":1,"all_attributes.foot_print":1}))
                        # return inventory[0]
                        inventory = {
                                item['all_attributes']['cmpt_id']:
                                {
                                    "foot_print":item['all_attributes'].get('foot_print',''),
                                    "hsn_code":item['all_attributes'].get('hsn_code',''),
                                    "mounting_type":item['all_attributes'].get('mounting_type',''),
                                    "manufacturer":item['all_attributes'].get('manufacturer',''),
                                    "description":item['all_attributes'].get('description',''),
                                    "qty":item['all_attributes'].get('qty','')
                                } 
                                for item in inventory
                            }
                        lst = [
                                {
                                    "sno":part_key,
                                    "ptg_prt_num":i["E_parts"][part_key]["ptg_prt_num"],
                                    "mfr_part_number":i["E_parts"][part_key]["mfr_prt_num"],
                                    "part_name": e_cat_reference[i["E_parts"][part_key]["ctgr_id"]]['sub_categories'][i["E_parts"][part_key]["sub_ctgr"]],
                                    "manufacturer":inventory[i["E_parts"][part_key]["cmpt_id"]]["manufacturer"],
                                    "device_category":e_cat_reference[i["E_parts"][part_key]["ctgr_id"]]['category_name'],
                                    "mounting_type":inventory[i["E_parts"][part_key]["cmpt_id"]]["mounting_type"],
                                    "required_quantity":i["E_parts"][part_key]["qty_per_board"],
                                    "qty":inventory[i["E_parts"][part_key]["cmpt_id"]]["qty"],
                                    "ctgr_id": i["E_parts"][part_key]["ctgr_id"],
                                    "cmpt_id":i["E_parts"][part_key]["cmpt_id"],
                                    "description":i["E_parts"][part_key]["description"],
                                    "foot_print":inventory[i["E_parts"][part_key]["cmpt_id"]]["foot_print"],
                                    "hsn_code":inventory[i["E_parts"][part_key]["cmpt_id"]]["hsn_code"]

                                } 
                            for part_key in i["E_parts"] 
                            if part_key.startswith("part")
                        ]
                    elif data["dep_type"]=="Mechanic":
                        metadata = list(db_con.Metadata.find({"gsipk_id":"Mechanic"}))
                        m_cat_reference = {
                            item['pk_id'].replace("MDID","CTID"):{"category_name":item['gsisk_id']} 
                            for item in metadata 
                            if item['gsipk_id']=='Mechanic'
                            }
                        inventory = db_con.Inventory.find({"gsipk_id":"Mechanic"},{"all_attributes.mounting_type":1,"all_attributes.manufacturer":1,"all_attributes.description":1,"all_attributes.cmpt_id":1,"all_attributes.qty":1,"all_attributes.ctgr_name":1,"all_attributes.material":1,"all_attributes.technical_details":1,"all_attributes.prdt_name":1})
                        inventory = {
                            item['all_attributes']['cmpt_id']:
                            {
                            #    "mounting_type":item['all_attributes']['mounting_type'],
                            #    "manufacturer":item['all_attributes']['manufacturer'],
                               "description":item['all_attributes']['description'],
                               "qty":item['all_attributes']['qty'],
                               "ctgr_name":item['all_attributes']['ctgr_name'],
                               "material":item['all_attributes']['material'],
                               "technical_details":item['all_attributes']['technical_details'],
                               "prdt_name":item['all_attributes']['prdt_name'],
                            } 
                            for item in inventory
                            }
                        lst = [
                                {
                                    "ptg_prt_num":i["M_parts"][part_key]["ptg_prt_num"],       
                                    "vic_part_number":i["M_parts"][part_key]["vic_part_number"],
                                    "part_name":inventory[i["M_parts"][part_key]["cmpt_id"]]["prdt_name"],
                                    "ctgr_name":inventory[i["M_parts"][part_key]["cmpt_id"]]["ctgr_name"],
                                    "material":inventory[i["M_parts"][part_key]["cmpt_id"]]["material"],
                                    "technical_details":inventory[i["M_parts"][part_key]["cmpt_id"]]["technical_details"],
                                    "description":inventory[i["M_parts"][part_key]["cmpt_id"]]["description"],
                                    "required_quantity":i["M_parts"][part_key]["qty_per_board"],
                                    "qty":inventory[i["M_parts"][part_key]["cmpt_id"]]["qty"],
                                    "ctgr_id": i["M_parts"][part_key]["ctgr_id"],
                                    "cmpt_id":i["M_parts"][part_key]["cmpt_id"]
                                }
                            for part_key in i["M_parts"] 
                            if part_key.startswith("part")
                        ]
                resp = { 
                        "bom_id": bom_id,
                        "bom_name": bom_name,
                        "created_date": bom_response[0]["all_attributes"]["created_time"],
                        "description": bom_response[0]["all_attributes"]["description"],
                        "dep_type":data["dep_type"],
                        "parts":lst
                    }
                return {"statusCode":200,"body":resp}
            else:
                return {"statusCode":404,"body":"No Data Found" }
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request(check data)'}

    def CmsBomGetDetailsByName(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            bom_id = data.get("bom_id","")
            # pattern     = r"^part\d+$"
            bom_response = list(db_con.BOM.find({"all_attributes.bom_id":bom_id}))
            if bom_response:
                metadata = db_con.Metadata.find({},{"gsisk_id":1,"sub_categories":1,"pk_id":1,"gsipk_id":1})
                e_cat_reference = {item['pk_id'].replace("MDID","CTID"):{"category_name":item['gsisk_id'],"sub_categories":{key:value for key,value in item['sub_categories'].items()}} for item in metadata if item['gsipk_id']=='Electronic'}
                m_cat_reference = {item['pk_id'].replace("MDID","CTID"):{"category_name":item['gsisk_id']} for item in metadata if item['gsipk_id']=='Mechanic'}
                result =bom_response[0]['all_attributes']
                inventory = list(db_con.Inventory.find({},{"all_attributes.mounting_type":1,"all_attributes.manufacturer":1,"all_attributes.description":1,"all_attributes.cmpt_id":1,"all_attributes.material":1,"all_attributes.technical_details":1}))
                # return inventory
                # {
                #     "_id": {
                #         "$oid": "66137f9ca34fc55e904f0f5f"
                #     },
                #     "all_attributes": {
                #         "cmpt_id": "CMPID_00002",
                #         "manufacturer": "qeqwe",
                #         "mounting_type": "TH",
                #         "description": "-"
                #     }
                # }
                valid_c_ids =  [result['M_parts'][part]['cmpt_id'] for part in result.get('M_parts',{}).keys()]+[result['E_parts'][part]['cmpt_id'] for part in result.get('E_parts',{}).keys()]
                inventory = {item['all_attributes']['cmpt_id']:item['all_attributes'] for item in inventory if item['all_attributes']['cmpt_id'] in valid_c_ids}
                # return inventory
                [result['M_parts'][part].update({
                    "ptg_prt_num": result['M_parts'][part]["ptg_prt_num"],
                    "material": inventory[result['M_parts'][part]["cmpt_id"]]['material'],
                    "cmpt_id": result['M_parts'][part]["cmpt_id"],
                    "ctgr_id": result['M_parts'][part]["ctgr_id"],
                    "ctgr_name": m_cat_reference[result['M_parts'][part]["ctgr_id"]]["category_name"],
                    "description": inventory[result['M_parts'][part]["cmpt_id"]]['description'],
                    "vic_part_number": result['M_parts'][part]["vic_part_number"],
                    "qty_per_board": result['M_parts'][part]["qty_per_board"],
                    "department": result['M_parts'][part]["department"],
                    "prdt_name": result['M_parts'][part]["prdt_name"],
                    "technical_details": inventory[result['M_parts'][part]["cmpt_id"]]['technical_details'],
                    "status":result.get("status","")
                    }) for part in result['M_parts'].keys() if result['M_parts'][part]["ctgr_id"] in m_cat_reference.keys() and result['M_parts'][part]["cmpt_id"] in inventory.keys()]
                [result['E_parts'][part].update({
                    "ptg_prt_num": result['E_parts'][part]["ptg_prt_num"],
                    "mounting_type": inventory[result['E_parts'][part]["cmpt_id"]]["mounting_type"],
                    "cmpt_id": result['E_parts'][part]["cmpt_id"],
                    "ctgr_id": result['E_parts'][part]["ctgr_id"],
                    "sub_category": e_cat_reference[result['E_parts'][part]["ctgr_id"]]["sub_categories"][result['E_parts'][part]["sub_ctgr"]],
                    "ctgr_name": e_cat_reference[result['E_parts'][part]["ctgr_id"]]["category_name"],
                    "description": inventory[result['E_parts'][part]["cmpt_id"]]["description"],
                    "qty_per_board": result['E_parts'][part]["qty_per_board"],
                    "department": result['E_parts'][part]["department"], 
                    "mfr_prt_num": result['E_parts'][part]["mfr_prt_num"],
                    "sub_ctgr": result['E_parts'][part]["sub_ctgr"],
                    "manufacturer": inventory[result['E_parts'][part]["cmpt_id"]]["manufacturer"],
                    "status":result.get("status","")
                    }) for part in result['E_parts'].keys() if result['E_parts'][part]["ctgr_id"] in e_cat_reference.keys() and result['E_parts'][part]["cmpt_id"] in inventory.keys()]
                result["status"]=result.get("status","")
                conct.close_connection(client)
                return {'statusCode': 200, 'body': result}
            else:
                conct.close_connection(client)
                return {'statusCode': 404, 'body': "could not find data for the given BOM ID"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request(check data)'}
    
    def cmsBomOutwardInfoSaveAssignToBoxBuilding2(request_body):
        data = request_body
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']  
        bb_id=data.get("BB_id")
        result = list(db_con.BoxBuilding.find({"pk_id":bb_id},{"pk_id":1,"sk_timeStamp":1,"all_attributes":1}))
        board_id=[i["all_attributes"]["boards_id"] for i in result][0]
        board_data = db_con.Boards.find_one({"pk_id":board_id})
        boards = board_data['all_attributes']['boards'] 
        board_keys = list(boards.keys())
        invent_data = list(db_con.Inventory.find({},{"_id":0,"all_attributes.cmpt_id":1,"all_attributes.qty":1,"all_attributes.out_going_qty":1}))
        invent_data = {item['all_attributes']['cmpt_id']:{"qty":item['all_attributes']['qty'],"out_going_qty":item['all_attributes'].get('out_going_qty','0')} for item in invent_data}
        m_parts = []
        m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
        m_parts = list(data[m_kit_key].values())
        if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty'])<int(part['provided_qty'])):
            return {"statusCode":"502","body":"provided quantity is more than the total quantity"}
        if result:
            pk_id=result[0]["pk_id"]
            result=result[0]
            cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
                    for key in data.keys() if key.startswith("M_KIT")
                    for part, details in data[key].items()}       
            for i in range(len(cmpt_id_and_qty)):
                part="part"+str(i+1)
                cmpt_id=cmpt_id_and_qty[part]["cmpt_id"]  
                qty=str(int(invent_data[cmpt_id]["qty"])-int(cmpt_id_and_qty[part]["provided_qty"]))
                out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) +int(cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data[cmpt_id].keys() else (cmpt_id_and_qty[part]["provided_qty"])
                upd = db_con.Inventory.update_one(
                        {"pk_id": cmpt_id},
                        {"$set": {"all_attributes.qty" : qty,"all_attributes.out_going_qty":out_going_qty}}
                    )
            m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
            if m_kit_key:
                res = db_con.BoxBuilding.update_one(
                            {"pk_id": pk_id},
                            {"$set": {f"all_attributes.{m_kit_key}" : data[m_kit_key]}}
                        )
                bom_id=data["bom_id"]
                data_bom = db_con.BOM.find({"pk_id":bom_id},{"sk_timeStamp":1})
                bom_timeStamp= data_bom[0]["sk_timeStamp"]
                response = db_con.BOM.update_one(
                            {"pk_id": bom_id},
                            {"$set": {f"all_attributes.status" : "Bom_assigned"}}
                        )
            if board_keys:
                for key in board_keys:
                    db_con.Boards.update_one({'pk_id': board_id},{"$set": {f"all_attributes.boards.{key}.status" : "Bom_assigned"}})
            if data["boards"]:
                print("boards")
                bk1 = data["all_attributes"]["boards"]
                bk2 = data["boards"]
                combined_dict = {**bk1, **bk2}
                for key in combined_dict:
                    combined_dict[key]['status']="Assigned"
                resp = db_con.BoxBuilding.update_one(
                            {"pk_id": pk_id},
                            {"$set": {"all_attributes.boards" : combined_dict}}
                        )
            conct.close_connection(client)
            return {"statusCode":200,"body":"BoxBuilding updated successfully"}
        else:
            conct.close_connection(client)
            return{"statusCode":404,"body":"No Data Found"}
    
    def cmsBomPriceBom(request_body):
        try:
            print(request_body)
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client'] 
            if data.get('part_information',[])==[]:
                conct.close_connection(client)
                return {'statusCode':400, 'body': f"please provide {data['department'][:1]} - category data"}
            data['part_information'] = [{key:str(value.strip()) for key,value in item.items()} for item in data['part_information']]
            key = data['department'][0:1]+"_parts"
            mfr_prt_nums = [part['mfr_prt_num'].strip().lower() for part in data['part_information']] if data['department']=='Electronic' else [part.get('VIC_Part_No',part.get('mfr_prt_num','')).strip().lower()for part in data['part_information']]
            print(mfr_prt_nums)
            vendors = list(db_con.Vendor.find({},{"all_attributes.vendor_name":1, "all_attributes.vendor_id":1, "all_attributes.vendor_type":1,"all_attributes.vendor_status":1}))
            inventory_ref = list(db_con.Inventory.find({"gsipk_id":data['department']},{"all_attributes.mfr_prt_num":1,"all_attributes.manufacturer":1,"all_attributes.cmpt_id":1,"all_attributes.ctgr_id":1,"all_attributes.sub_ctgr":1,"all_attributes.ptg_prt_num":1,"all_attributes.prdt_name":1}))
            inventory = {}
            for component in inventory_ref:
                inventory[(component['all_attributes']['mfr_prt_num'].strip().lower()+component['all_attributes'].get("manufacturer","").strip()).lower()] = component["all_attributes"]
            inventory_ref = {component['all_attributes']['cmpt_id'] : component['all_attributes'] for component in inventory_ref}
            result = list(db_con.BOM.find({"all_attributes.bom_id":data['bom_id']}))
            category = list(db_con.Metadata.find({}))
            category = {
                    (f"E{item['gsisk_id'].lower().strip()}"
                    if item['gsipk_id'] == 'Electronic'
                    else f"M{item['gsisk_id'].lower().strip()}"
                    ): (
                        {
                            "ctgr_id": item['pk_id'].replace("MDID", "CTID"),
                            "sub_categories": {
                                # key: value for key, value in item['sub_categories'].items()
                                value.lower().strip():key for key, value in item['sub_categories'].items()
                            }
                        }
                        if item['gsipk_id'] == 'Electronic'
                        else
                        {"ctgr_id": item['pk_id'].replace("MDID", "CTID")}
                    )
                    for item in category
                }
            if result:
                bom_parts = list(result[0]['all_attributes'].get(key,{}).values())
                mfr_prt_num_combinations = [(item['mfr_prt_num'].strip()+inventory_ref[item['cmpt_id']].get("manufacturer","").strip()).lower() for item in bom_parts] if data['department']=='Electronic' else [(item['vic_part_number'].strip()+inventory_ref[item['cmpt_id']].get("manufacturer","").strip()).lower() for item in bom_parts]
                qty_pb = {part['mfr_prt_num'].strip().lower()+part.get('manufacturer','').strip().lower():part['qty_per_board'] for part in bom_parts} if data['department']=='Electronic' else {part['vic_part_number'].strip().lower():part['qty_per_board'] for part in bom_parts}
                if vendors:
                    resp = ''
                    vendors = {vendor['all_attributes']['vendor_name'].strip().lower():{"vendor_id":vendor['all_attributes']['vendor_id'],"vendor_name":vendor['all_attributes']['vendor_name'].strip(),"vendor_type":vendor['all_attributes']['vendor_type'],'vendor_status':vendor['all_attributes']['vendor_status']} for vendor in vendors}
                    # return list(vendors.keys())
                    if data['department']=='Mechanic':
                        if "manufacturer" in data['part_information'][0].keys():
                            resp =  {"statusCode":400,"body":"Please upload correct file for m parts"}
                        if any(1 for part in data['part_information'] if part.get('mfr_prt_num',part.get('VIC_Part_No','')).lower().strip() not in qty_pb):
                            resp =  {"statusCode":400,"body":"Please fill correct mfr part number for parts"}
                        if any(1 for part in data['part_information'] if (f"M{part['ctgr_name'].strip().lower()}" not in category) or (inventory[part.get('mfr_prt_num',part.get('VIC_Part_No','')).lower().strip()]['ctgr_id'] != category[f"M{part['ctgr_name'].strip().lower()}"]['ctgr_id'])):
                            resp =  {"statusCode":400,"body":"Please fill correct category for parts"}
                        if any(1 for part in data['part_information'] if inventory[part.get('mfr_prt_num',part.get('VIC_Part_No','')).strip().lower()]['prdt_name'].strip().lower() != part['prdt_name'].strip().lower()):
                            resp =  {"statusCode":400,"body":"Please fill correct part name for parts"}
                        if any(1 for part in data['part_information'] if str(part['qty_per_board'])!=str(qty_pb[part.get('mfr_prt_num',part.get('VIC_Part_No','')).strip().lower()])):
                            resp =  {"statusCode":400,"body":"Quantity per board filled incorrect for parts"}
                        if not any(1 for part in data['part_information'] if ("mfr_prt_num" in part or 'VIC_Part_No' in part) and "prdt_name" in part and "ctgr_name" in part and "description" in part and "qty_per_board" in part and "required_qty" in part and "ordered_qty" in part and "unit_price" in part and "extended_price" in part):
                            resp =  {"statusCode":200,"body":"Please fill all mandatory fields for parts"}
                        if any(1 for part in data['part_information'] if part['vendor'].lower() not in vendors or vendors[part['vendor'].lower()]['vendor_type']=='Electronic' or vendors[part['vendor'].lower()]['vendor_status']=='InActive'):
                            resp =  {'statusCode':400, 'body':'Vendor name does not match any of the active Mechanical vendors'}
                        if resp:
                            conct.close_connection(client)
                            return resp
                        part_information = {
                            f"part{inx+1}":
                                {
                                    "cmpt_id":inventory[(part.get('mfr_prt_num',part.get('VIC_Part_No',''))+part.get("manufacturer","")).lower()]['cmpt_id'],
                                    "ctgr_id":inventory[(part.get('mfr_prt_num',part.get('VIC_Part_No',''))+part.get("manufacturer","")).lower()]['ctgr_id'],
                                    "prdt_name":inventory[(part.get('mfr_prt_num',part.get('VIC_Part_No',''))+part.get("manufacturer","")).lower()]['prdt_name'],
                                    "ptg_prt_num":inventory[(part.get('mfr_prt_num',part.get('VIC_Part_No',''))+part.get("manufacturer","")).lower()]['ptg_prt_num'],
                                    "mfr_prt_num":part.get('mfr_prt_num',part.get('VIC_Part_No','')),
                                    "part_name":part['prdt_name'],
                                    "manufacturer":part.get("manufacturer",""),
                                    "ctgr_name":part['ctgr_name'].strip(),
                                    "description":part['description'],
                                    "qty_per_board":part['qty_per_board'],
                                    "required_qty":part['required_qty'],
                                    "ordered_qty":part['ordered_qty'],
                                    "unit_price":part['unit_price'],
                                    "extended_price":part['extended_price'],
                                    "vendor":vendors[part['vendor'].lower().strip()]['vendor_name'],
                                    "vendor_id":vendors[part['vendor'].lower().strip()]['vendor_id'],
                                    "status":"False",
                                    "module":part.get('module',''),
                                    "moq":part.get('moq(optional)',"--"),
                                    "tax":part.get('tax(optional)',"--"),
                                    "hsn_code":part.get('hsn_code(optional)',"--"),
                                    "gst":part.get('gst(optional)',"--"),
                                    "package":part.get("part_packaging(optional)","--")
                            } 
                        for inx,part in enumerate(data['part_information']) 
                        if (part.get('mfr_prt_num',part.get('VIC_Part_No',''))+part.get("manufacturer","")).lower() in inventory
                        }
                    else:
                        if "manufacturer" not in data['part_information'][0].keys():
                            return {"statusCode":400,"body":"Please upload correct file for e parts"}
                        if any(1 for part in data['part_information'] if part['mfr_prt_num'].strip().lower()+part.get('manufacturer','').strip().lower() not in inventory):
                            resp = {"statusCode":400,"body":"Please fill correct mfr part number and manufacturer for parts"}
                        if any(1 for part in data['part_information'] if (f"E{part['ctgr_name'].strip().lower()}" not in category) or (inventory[part.get('mfr_prt_num','').lower().strip()+part.get('manufacturer','').lower().strip()]['ctgr_id'] != category[f"E{part['ctgr_name'].strip().lower()}"]['ctgr_id'])):
                            resp = {"statusCode":400,"body":"Please fill correct category for parts"}
                        if any(
                            1 for part in data['part_information'] 
                            if (part['part_name'].strip().lower() not in category[f"E{part['ctgr_name'].strip().lower()}"]['sub_categories'])
                            or inventory[part['mfr_prt_num'].strip().lower()+part.get('manufacturer','').strip().lower()]['sub_ctgr'] != category[f"E{part['ctgr_name'].strip().lower()}"]['sub_categories'][part['part_name'].strip().lower()]
                            ):
                            resp = {"statusCode":400,"body":"Please fill correct part name for parts"}
                        if any(1 for part in data['part_information'] if str(part['qty_per_board'])!=str(qty_pb[part['mfr_prt_num'].strip().lower()+part.get('manufacturer','').strip().lower()])):
                            resp = {"statusCode":400,"body":"quantity per board filled incorrect for parts"}
                        if not any(1 for part in data['part_information'] if ("mfr_prt_num" in part and "part_name" in part and "manufacturer" in part and "ctgr_name" in part and "description" in part and "qty_per_board" in part and "required_qty" in part and "ordered_qty" in part and "unit_price" in part and "extended_price" in part)):
                            resp = {"statusCode":200,"body":"Please fill all mandatory fields for parts"}
                        if any(1 for part in data['part_information'] 
                            if part['vendor'].lower() not in vendors.keys() or vendors[part['vendor'].strip().lower()]['vendor_type']=='Mechanic' or 
                            vendors[part['vendor'].lower()]['vendor_status']=='InActive'):
                            resp = {'statusCode':400, 'body':'Vendor name does not match any of the active Electronic vendors'}
                        if resp:
                            conct.close_connection(client)
                            return resp
                        part_information = {
                            f"part{inx+1}":{
                                "cmpt_id":inventory[(part['mfr_prt_num']+part.get("manufacturer","")).lower()]['cmpt_id'],
                                "ctgr_id":inventory[(part['mfr_prt_num']+part.get("manufacturer","")).lower()]['ctgr_id'],
                                "sub_ctgr":inventory[(part['mfr_prt_num']+part.get("manufacturer","")).lower()]['sub_ctgr'],
                                "ptg_prt_num":inventory[(part['mfr_prt_num']+part.get("manufacturer","")).lower()]['ptg_prt_num'],
                                "mfr_prt_num":part["mfr_prt_num"],"prdt_name":part['part_name'],
                                "manufacturer":part.get("manufacturer",""),
                                "ctgr_name":part['ctgr_name'].strip(),
                                "pcb_foot_print":part.get('pcb_foot_print',''),
                                "description":part['description'],
                                "qty_per_board":part['qty_per_board'],
                                "required_qty":part['required_qty'],
                                "ordered_qty":part['ordered_qty'],
                                "unit_price":part['unit_price'],
                                "extended_price":part['extended_price'],
                                "vendor":vendors[part['vendor'].strip().lower()]['vendor_name'],
                                "vendor_id":vendors[part['vendor'].strip().lower()]['vendor_id'],
                                "tp_gst_addtax" : part.get('tp_gst_addtax',"--"),
                                "status":"False",
                                "moq":part.get('moq(optional)',"--"),
                                "tax":part.get('tax(optional)',"--"),
                                "hsn_code":part.get('hsn_code(optional)',"--"),
                                "gst":part.get('gst(optional)',"--"),
                                "package":part.get("part_packaging(optional)","--")
                            } 
                            for inx,part in enumerate(data['part_information']) 
                            if (part['mfr_prt_num']+part.get("manufacturer","")).lower() in inventory
                        }
                    if len(part_information.keys())==len(data['part_information']):
                        data_parts = [(value['mfr_prt_num'].strip()+value.get("manufacturer","").strip()).lower() for key,value in part_information.items()]
                        if any(item not in data_parts for item in mfr_prt_num_combinations):
                            conct.close_connection(client)
                            return {'statusCode': 400,'body': f"Part information should contain part information related to all parts linked to {data['bom_id']}"}
                        bom_details = result[0]
                        category_key = "E_parts" if data['department']=='Electronic' else "M_parts"
                        if "price_bom" in bom_details["all_attributes"]:
                            bom_details["all_attributes"]['price_bom'][category_key] = part_information
                        else:
                            bom_details["all_attributes"]['price_bom'] = {category_key:part_information}
                        resp = db_con.BOM.update_one(
                            {"pk_id": bom_details['all_attributes']['bom_id']},
                            {"$set": {"all_attributes" : bom_details['all_attributes']}}
                        )
                        response = {'statusCode': 200,'body': f"Successfully priced bom {data['department']} components for {data['bom_id']}"}
                    else:
                        response = {'statusCode': 400,'body': "upload correct mfr_part_numbers for parts"}
                else:
                    response = {'statusCode': 400,'body': "Vendors not found" }
            else:
                response = {'statusCode': 400,'body': "BOM not found"}
            conct.close_connection(client)
            return response
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Internal server error'}
    
    def cmsBomGetPriceBomDetailsById(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            env_type = data['env_type']
            attribute_name = 'E_parts' if data['department']=='Electronic' else "M_parts"
            print(attribute_name)
            result = list(db_con.BOM.find({"all_attributes.bom_id":data['bom_id']},{"all_attributes.price_bom":1}))
            print(result)
            if result:
                vendors = list(db_con.Vendor.find({}))
                vendors_ref = {item['all_attributes']['vendor_id']:{part.get('cmpt_id')+part.get('bom_id'):part.get('bom_id') for part in item['all_attributes']['parts'].values()} for item in vendors if 'parts' in item['all_attributes']}
                metadata = list(db_con.Metadata.find({"gsipk_id":data['department']}))
                metadata = {item['pk_id'].replace("MDID","CTID"):{"all_attributes":item['all_attributes'],"sub_categories":item.get("sub_categories",{}),"category_name":item['gsisk_id']} for item in metadata}
                inventory = list(db_con.Inventory.find({"gsipk_id":data['department']},{"all_attributes":1}))
                inventory = {item['all_attributes']['cmpt_id']:item['all_attributes'] for item in inventory}
                parts = []
                result = result[0]
                if attribute_name in result['all_attributes'].get('price_bom',{}):
                    for part in result['all_attributes']['price_bom'][attribute_name].values():
                        print(inventory[part['cmpt_id']])
                        part['description'] = inventory[part['cmpt_id']]['description']
                        if data['department']=='Electronic':
                            part['manufacturer'] = inventory[part['cmpt_id']].get('manufacturer',"-")
                        part['package'] = inventory[part['cmpt_id']].get("package","") if inventory[part['cmpt_id']].get("package","") else part['package']
                        part['ctgr_name'] = metadata[part['ctgr_id']]['category_name']
                        part['part_name'] = metadata[part['ctgr_id']]['sub_categories'][part['sub_ctgr']] if data['department']=='Electronic' else part['prdt_name']
                        part['status'] = True if part['cmpt_id']+data['bom_id'] in vendors_ref[part['vendor_id']].keys() else False
                        part['material'] = inventory[part['cmpt_id']].get('material','-')
                        part['module'] = part.get('module','-')
                        parts.append(part)
                    response =  {'statusCode': 200,'body': parts}
                else:
                    # response =  {'statusCode': 400,'body': f"{attribute_name} not found in price bom details"}
                    response = {'statusCode': 400,'body': []}
            else:
                response =  {'statusCode': 400,'body': []}
            conct.close_connection(client)
            return response
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request(check data)'}
    
    def bomAssignToVendor(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            vendor_id=data["vendor_id"]
            vendor_response = list(db_con.Vendor.find({"pk_id":vendor_id}))
            if vendor_response[0]["all_attributes"]['vendor_status']!='Active':
                conct.close_connection(client)
                return {'statusCode': 400,'body': 'Vendor no longer active'}
            parts = vendor_response[0]["all_attributes"].get("parts",{})
            no_of_parts=len(vendor_response[0]["all_attributes"]["parts"])
            data["part_information"] = [{**part, "bom_id": data["bom_id"]} for part in data["part_information"]]
            data["part_information"] = [{**part, "department": data["department"]} for part in data["part_information"]]
            categories = len(set([value['ctgr_id'] for key,value in vendor_response[0]["all_attributes"]["parts"].items()]))+len(set([part['ctgr_id'] for part in data["part_information"]]))
            components = len(set([value['cmpt_id'] for key,value in vendor_response[0]["all_attributes"]["parts"].items()]))+len(set([part['cmpt_id'] for part in data["part_information"]]))
            result = {f'part{i+no_of_parts+1}': item for i, item in enumerate(data["part_information"])}
            new_parts = {**parts, **result}
            print(new_parts)
            updated_data = {"all_attributes.categories":categories,"all_attributes.product_types":components,"all_attributes.parts":new_parts}
            result = db_con.Vendor.update_one(
                            {"pk_id": vendor_id},
                            {"$set": updated_data}
                        )
            conct.close_connection(client)
            return {"statusCode":200,"body":"assigned vender successfully"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request(check data)'}
     
    def cmsBomGetFinalProductInfo(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            gsipk_table = data['status']
            outward_id = data["outward_id"]
            collection = db_con[gsipk_table]
            # statement = f""" SELECT * FROM {database_table_name} WHERE gsipk_table = '{gsipk_table}' AND all_attributes.outward_id = '{outward_id}' """
            # resp = extract_items_from_array_of_nested_dict(execute_statement_with_pagination(statement))
            resp = list(collection.find({"all_attributes.outward_id": outward_id}))
            unassigned_data = []
            for item in resp:
                kits = item.get("all_attributes", {}).get("kits", {})
                unassigned_batches = {}

                for batch_key, batch_value in kits.items():
                    if "status" in batch_value and batch_value["status"] == "Unassigned":
                        unassigned_batches[batch_key] = batch_value

                if unassigned_batches:
                    # Sort batches based on their keys
                    sorted_batches = dict(sorted(unassigned_batches.items()))
                    # Sort products within each batch based on their keys
                    for batch_key, batch_value in sorted_batches.items():
                        if "product" in batch_value:
                            sorted_products = dict(sorted(batch_value["product"].items(), key=lambda x: x[0]))
                            batch_value["product"] = sorted_products
                        if "status" in batch_value and batch_value["status"] == "Unassigned":
                            batch_value.pop("status", None)
                
                    unassigned_data.append({
                        "outward_id": item["all_attributes"]["outward_id"],
                        "quantity": item["all_attributes"]["quantity"],
                        "against_po": item["all_attributes"]["against_po"],
                        "kits": sorted_batches 
                    })
            response = []
            for transformed_item in unassigned_data:
                sorted_final_batches = {}
                for batch_key, products in sorted(transformed_item["kits"].items()):
                    sorted_products = dict(sorted(products.items()))
                    sorted_final_batches[batch_key] = sorted_products
                transformed_item["kits"] = sorted_final_batches
                response.append(transformed_item)
            if response:
                # Transform unassigned data to the desired format
                transformed_response = {
                    "statusCode": 200,
                    "body": response[0] 
                }
                conct.close_connection(client)
                return transformed_response 
            else:
                conct.close_connection(client)
                return {
                    "statusCode": 404,
                    "body": "No data found"
                }
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request(check data)'}
    
    def CmsInventorySearchSujjestion(request_body):
        # try:
        data = request_body
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        env_type = data.get("env_type","")
        category_name = data["category_name"].strip()
        metadata_table = 'Metadata'
        Inventory_table = 'Inventory'
        if not category_name:
            conct.close_connection(client)
            return{"statusCode": 404, "body": "Please provide a search parameter"}
        select_parameters = {"gsisk_id":1,"sub_categories":1,"pk_id":1}
        query = {"gsipk_id":data['component_type']}
        db = list(db_con.Metadata.find(query,select_parameters))
        matched_values = []
        if data['component_type']=='Electronic':
            category_metadata = {item['pk_id'].replace("MDID","CTID"):{"category_name":item['gsisk_id'],"sub_categories":{key:value for key,value in item['sub_categories'].items()}} for item in db}
            select_parameters = {"all_attributes":1}
            query = {"gsipk_id":data['component_type']}
            db = list(db_con.Inventory.find(query,select_parameters))
            # return db
            [
                matched_values.append([item['all_attributes']['cmpt_id'],
                category_metadata[item['all_attributes']['ctgr_id']]['sub_categories'][item['all_attributes']['sub_ctgr']],
                item['all_attributes']["mfr_prt_num"],category_metadata[item['all_attributes']['ctgr_id']]['category_name'],
                item['all_attributes']["description"],item['all_attributes']["manufacturer"]]) 
                for item in db 
                if item['all_attributes']['ctgr_id'] in category_metadata.keys() and 
                (category_name.lower() in category_metadata[item['all_attributes']['ctgr_id']]['sub_categories'][item['all_attributes']['sub_ctgr']].lower() 
                or category_name.lower() in str(item['all_attributes']["mfr_prt_num"]).lower() 
                or category_name.lower() in category_metadata[item['all_attributes']['ctgr_id']]['category_name'].lower() 
                or category_name.lower() in item['all_attributes']["description"].lower() 
                or category_name.lower() in item['all_attributes']["manufacturer"].lower())
            ]
        else:
            category_metadata = {item['pk_id'].replace("MDID","CTID"):{"category_name":item['gsisk_id']} for item in db}
            select_parameters = {"all_attributes":1}
            query = {"gsipk_id":data['component_type']}
            db = list(db_con.Inventory.find(query,select_parameters))
            [
                matched_values.append([item['all_attributes']['cmpt_id'],item['all_attributes']['prdt_name'],
                item['all_attributes']["mfr_prt_num"],
                category_metadata[item['all_attributes']['ctgr_id']]['category_name'],
                item['all_attributes']["description"]]) 
                for item in db 
                if item['all_attributes']['ctgr_id'] in category_metadata and 
                (category_name.lower() in item['all_attributes']['prdt_name'].lower() 
                or category_name.lower() in str(item['all_attributes']['mfr_prt_num']).lower()
                or category_name.lower() in item['all_attributes']["description"].lower() 
                or category_name.lower() in category_metadata[item['all_attributes']['ctgr_id']]['category_name'].lower()) 
            ]
        if len(matched_values):
            conct.close_connection(client)
            return {'statusCode': 200,'body': matched_values}
        else:
            conct.close_connection(client)
            return {'statusCode': 400,'body': "no data found"}
        # except Exception as err:
        #     exc_type, exc_obj, tb = sys.exc_info()
        #     f_name = tb.tb_frame.f_code.co_filename
        #     line_no = tb.tb_lineno
        #     print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
        #     return {'statusCode': 400,'body': 'Bad Request(check data)'}
    
    def CmsInventorySearchComponent(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            if data['category_type']=='Mechanic':
                select_parameters = {"gsisk_id":1,"pk_id":1}
                query = {"gsipk_id":data['department']}
                metadata = list(db_con.Metadata.find(query,select_parameters))
                category_metadata = {item['pk_id'].replace("MDID","CTID"):{"category_name":item['gsisk_id']}  for item in metadata}
                select_parameters = {"all_attributes.cmpt_id":1,"all_attributes.ctgr_id":1,"all_attributes.ctgr_name":1,"all_attributes.department":1,"all_attributes.description":1,"all_attributes.mfr_prt_num":1,"all_attributes.ptg_prt_num":1,"all_attributes.prdt_name":1,"all_attributes.technical_details":1,"all_attributes.material":1}
                query = {"all_attributes.cmpt_id":data['component_id'],"gsipk_id":"Mechanic"}
                db = list(db_con.Inventory.find(query,select_parameters))[0]
                result={'cmpt_id':db['all_attributes']['cmpt_id'],'ctgr_id':db['all_attributes']['ctgr_id'],'ctgr_name':category_metadata[db['all_attributes']['ctgr_id']]['category_name'],'department':db['all_attributes']['department'],'description':db['all_attributes']['description'],"vic_part_number":db['all_attributes'].get('mfr_prt_num',''),'ptg_prt_num':db['all_attributes']['ptg_prt_num'],'technical_details':db['all_attributes']['technical_details'],'prdt_name':db['all_attributes']['prdt_name'],'qty_per_board':'1','material':db['all_attributes']['material']}
            else:
                select_parameters = {"gsisk_id":1,"sub_categories":1,"pk_id":1}
                query = {"gsipk_id":data['department']}
                metadata = list(db_con.Metadata.find(query,select_parameters))
                category_metadata = {item['pk_id'].replace("MDID","CTID"):{"category_name":item['gsisk_id'],"sub_categories":{key:value for key,value in item['sub_categories'].items()}} for item in metadata}
                select_parameters = {"_id":0,"all_attributes.cmpt_id":1,"all_attributes.ctgr_id":1,"all_attributes.ctgr_name":1,"all_attributes.department":1,"all_attributes.description":1,"all_attributes.mfr_prt_num":1,"all_attributes.ptg_prt_num":1,"all_attributes.mounting_type":1,"all_attributes.sub_ctgr":1,"all_attributes.manufacturer":1}
                query = {"pk_id":data['component_id'],"gsipk_id":"Electronic"}
                db = list(db_con.Inventory.find(query,select_parameters))
                # return db
                if db:
                    db = db[0]
                    result={'cmpt_id':db['all_attributes']['cmpt_id'],'ctgr_id':db['all_attributes']['ctgr_id'],'ctgr_name':category_metadata[db['all_attributes']['ctgr_id']]['category_name'],'department':db['all_attributes']['department'],'description':db['all_attributes']['description'],"mfr_prt_num":db['all_attributes']['mfr_prt_num'],'ptg_prt_num':db['all_attributes']['ptg_prt_num'],'mounting_type':db['all_attributes']['mounting_type'],'sub_ctgr':db['all_attributes']['sub_ctgr'],'sub_category':category_metadata[db['all_attributes']['ctgr_id']]['sub_categories'][db['all_attributes']['sub_ctgr']],'qty_per_board':'1','manufacturer':db['all_attributes']['manufacturer']}
                else:
                    result = "No data found"
            conct.close_connection(client)
            return {"statusCode": 200, "body": result}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request(check data)'}
        
    def CmsVendorGetAllData(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            search_status = data['status']
            lst = [] 
            if data['type']=='Partners':
                partners = list(db_con.Partners.find({"lsi_key":search_status}))
                # statement = f"""select * from {databaseTableName} where gsipk_table = '{gsipk_table}' and lsi_key='{search_status}' """
                # partners = execute_statement_with_pagination(statement=statement)
                # return partners
                # 
                lst = sorted([{
                    'partner_id': item["all_attributes"].get('partner_id',""),
                    'partner_name': item["all_attributes"].get('partner_name',""),
                    'partner_type': [value for value in item["all_attributes"].get('partner_type',{"L":[]})['L']],
                    'contact_details': item["all_attributes"].get('contact_number',""),
                    'email': item["all_attributes"].get('email',"")
                }
                for item in partners], key=lambda x: x['partner_id'], reverse=False)
                
            else:
                query = {"all_attributes.vendor_status":search_status}
                extra_attribute = {} if data['type']=='all_vendors' else {"all_attributes.vendor_type":data['type']}
                query.update(extra_attribute)
                # extra_attribute = '' if data['type']=='all_vendors' else f" and all_attributes.vendor_type='{data['type']}'"
                vendors = list(db_con.Vendor.find(query))
                # statement = f"""select * from {databaseTableName} where gsipk_table = 'Vendor' and all_attributes.vendor_status='{search_status}'{extra_attribute} """
                # vendors = execute_statement_with_pagination(statement=statement)
                lst = sorted([{
                    'vendor_id': item["all_attributes"].get('vendor_id',""),
                    'vendor_type': item["all_attributes"].get('vendor_type',""),
                    'vendor_name': item["all_attributes"].get('vendor_name',""),
                    'categories': item["all_attributes"].get('categories',""),
                    'product_types': item["all_attributes"].get('product_types',""),
                    'contact_details': item["all_attributes"].get('contact_number',""),
                    'email': item["all_attributes"].get('email',"")
                }
                for item in vendors], key=lambda x: int(x['vendor_id'].replace("PTGVEN","")), reverse=False)
            conct.close_connection(client)
            return {'statusCode': 200,'body': lst}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request(check data)'}
    
    # def cmsAssignToEMS(request_body):
    #     # try:
    #     activity = {}
    #     data = request_body
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     env_type = data.get("env_type","")
    #     sk_timeStamp = (datetime.now()).isoformat()
    #     bom_id = data['bom_id']
    #     part_batch_info = find_stock_inwards(bom_id,db_con,'E_parts')
    #     # poids = part_batch_info['pos']
    #     part_batch_info = part_batch_info['part_batch_info']
    #     # return part_batch_info
    #     partner_name = db_con.Partners.find_one({"pk_id":data['partner_id']},{"_id":0,"all_attributes.partner_name":1})
    #     print(f"partner_name is {partner_name['all_attributes']}")
    #     if part_batch_info:
    #         gsipk_table="EMS"
    #         first_record = list(db_con.EMS.find({"pk_id":"BTOUT1"}))
    #         all_tables = list(db_con.all_tables.find({"pk_id":"top_ids"},{"_id":0,"all_attributes.EMS":1,"all_attributes.ActivityId":1}))
    #         update_id = all_tables[0]['all_attributes']['EMS'][5:]
    #         activity_id = all_tables[0]['all_attributes']['ActivityId']
    #         outward_id='1'
    #         if first_record:
    #             outward_id=str(int(update_id)+1)
    #         mean_ecategory_no_numpy=0
    #         # if "mcategoryInfo" in data:
    #         #     data["M-KIT1"] = update_category_info(data.get("mcategoryInfo",{}))
    #         #     mcategory_ratios = [int(item["provided_qty"]) / int(item["required_quantity"]) for item in data["mcategoryInfo"]]
    #         #     mean_mcategory_no_numpy = calculate_mean(mcategory_ratios)
    #         #     for i in data["mcategoryInfo"]:
    #         #         cmpt_id=i["cmpt_id"]
    #         #         invent_data = list(db_con.Inventory.find({"pk_id":cmpt_id},{"pk_id":1,"sk_timeStamp":1,"all_attributes.qty":1}))
    #         #         if int(invent_data[0]['all_attributes']["qty"])>=int(i["provided_qty"]):
    #         #             qty=str(int(invent_data[0]['all_attributes']["qty"])-int(i["provided_qty"]))
    #         #             out_going_qty = str(int(invent_data[0]['all_attributes']["out_going_qty"]) + int(i["provided_qty"])) if "out_going_qty" in invent_data[0].keys() else i["provided_qty"]
    #         #             resp = db_con.Inventory.update_one(
    #         #                 {"pk_id": invent_data[0]["pk_id"]},
    #         #                 {"$set": {"all_attributes.qty" : qty,"all_attributes.out_going_qty":out_going_qty}}
    #         #             )
    #         #         else:
    #         #             conct.close_connection(client)
    #         #             return {"statusCode":"502","body":"provided quantity is more than the total quantity"
    #         #         }
    #         if "ecategoryInfo" in data:
    #             invent_Ref = db_con.Inventory.find({},{"_id":0,"all_attributes.qty":1,"pk_id":1})
    #             invent_Ref = {item['pk_id']:item['all_attributes']['qty'] for item in invent_Ref}
    #             part_info = update_category_info(part_batch_info,data.get("ecategoryInfo",{}),{},invent_Ref,partner_name['all_attributes']['partner_name'])
    #             # return part_info
    #             if part_info:
    #                 data["E-KIT1"] = part_info['part_details']
    #             else:
    #                 return {"statusCode":"200","body":"Not enough parts inwarded for this Bom"}
    #             ecategory_ratios = [int(item["provided_qty"]) / int(item["required_quantity"]) for item in data["ecategoryInfo"]]
    #             mean_ecategory_no_numpy = calculate_mean(ecategory_ratios)
    #             invent_data = list(db_con.Inventory.find({},{"_id":0,"pk_id":1,"sk_timeStamp":1,"all_attributes.qty":1,"all_attributes.out_going_qty":1}))
    #             invent_data = {item['pk_id']:item['all_attributes'] for item in invent_data}
    #             # for item in data["ecategoryInfo"]:
    #             #     print(item['cmpt_id'],item['provided_qty'],invent_data[item['cmpt_id']]["qty"])
    #             if any(1 for item in data["ecategoryInfo"] if int(item['provided_qty'])>int(invent_data[item['cmpt_id']]["qty"])):
    #                 return {"statusCode":"502","body":"provided quantity is more than the total quantity"}
    #             for i in data["ecategoryInfo"]:
    #                 cmpt_id=i["cmpt_id"]
    #                 invent_data = list(db_con.Inventory.find({"pk_id":cmpt_id},{"_id":0,"pk_id":1,"sk_timeStamp":1,"all_attributes.qty":1,"all_attributes.out_going_qty":1}))
    #                 qty=str(int(invent_data[0]['all_attributes']["qty"])-int(i["provided_qty"]))
    #                 out_going_qty = str(int(invent_data[0]['all_attributes']["out_going_qty"]) + int(i["provided_qty"])) if "out_going_qty" in invent_data[0]['all_attributes'].keys() else i["provided_qty"]
    #                 response = db_con.Inventory.update_one(
    #                     {"pk_id": invent_data[0]["pk_id"]},
    #                     {"$set": {"all_attributes.qty" : qty,"all_attributes.out_going_qty":out_going_qty}}
    #                 )
    #         # return part_info['activity_details']
    #         data["mtrl_prcnt"]= str(((mean_ecategory_no_numpy))*100)[:5]
    #         data["order_date"]=sk_timeStamp.split("T")[0]
    #         data.pop("mcategoryInfo", None)
    #         data.pop("ecategoryInfo", None)
    #         del data["env_type"]
    #         data["outward_id"]="BTOUT"+str(outward_id)
    #         item = {
    #             "pk_id":"BTOUT"+str(outward_id),
    #             "sk_timeStamp": sk_timeStamp,
    #             "all_attributes": data,
    #             "gsipk_table":gsipk_table,
    #             "gsisk_id":"--" ,
    #             "lsi_key": data["bom_id"]
    #         }
    #         bom_id=data["bom_id"]
    #         activity_id = int(activity_id)+1
    #         if item:
    #             db_con['ActivityDetails'].insert_one(
    #             {
    #                 "pk_id":f"ACTID{activity_id}",
    #                 "sk_timeStamp": sk_timeStamp,
    #                 "all_attributes": part_info['activity_details'],
    #                 "gsipk_table": "ActivityDetails",
    #                 "gsisk_id": outward_id,
    #                 "lsi_key": "Utilized",
    #                 "gsipk_id":"EMS"
    #             }
    #             )
    #             resp = db_con.EMS.insert_one(item)
    #             resp = db_con.all_tables.update_one(
    #                         {"pk_id": "top_ids"},
    #                         {"$set": {"all_attributes.EMS" : "BTOUT"+str(outward_id),"all_attributes.ActivityId" : f"{activity_id}"}}
    #                     )
    #             resp = db_con.BOM.update_one(
    #                 {"pk_id": bom_id},
    #                 {"$set": {"all_attributes.status" : "Bom_assigned"}}
    #             )
    #             response = {'statusCode': 200, 'body': 'EMS assigned  to BOM successfully'}
    #             return response
    #         else:
    #             return {"statusCode": 400, "body": "no data found"}
    #     else:
    #         return {"statusCode": 200, "body": "No inward found for this bom"}
    #     # except Exception as err:
    #     #     exc_type, exc_obj, tb = sys.exc_info()
    #     #     f_name = tb.tb_frame.f_code.co_filename
    #     #     line_no = tb.tb_lineno
    #     #     print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #     #     return {'statusCode': 400,'body': 'Bad Request(check data)'}
    # def cmsAssignToEMS(request_body):
    #     activity = {}
    #     data = request_body
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     env_type = data.get("env_type", "")
    #     sk_timeStamp = (datetime.now()).isoformat()
    #     bom_id = data['bom_id']
    #     part_batch_info = find_stock_inwards(bom_id, db_con, 'E_parts')
    #     part_batch_info = part_batch_info['part_batch_info']
    #     partner_name = db_con.Partners.find_one({"pk_id": data['partner_id']},
    #                                             {"_id": 0, "all_attributes.partner_name": 1})
    #     # print(f"partner_name is {partner_name['all_attributes']}")
    #     if part_batch_info:
    #         gsipk_table = "EMS"
    #         first_record = list(db_con.EMS.find({"pk_id": "BTOUT1"}))
    #         all_tables = list(db_con.all_tables.find({"pk_id": "top_ids"}, {"_id": 0, "all_attributes.EMS": 1,
    #                                                                         "all_attributes.ActivityId": 1}))
    #         update_id = all_tables[0]['all_attributes']['EMS'][5:]
    #         activity_id = all_tables[0]['all_attributes']['ActivityId']
    #         outward_id = '1'
    #         if first_record:
    #             outward_id = str(int(update_id) + 1)
    #         mean_ecategory_no_numpy = 0
    #         if "ecategoryInfo" in data:
    #             invent_Ref = db_con.Inventory.find({}, {"_id": 0, "all_attributes.qty": 1, "pk_id": 1})
    #             invent_Ref = {item['pk_id']: item['all_attributes']['qty'] for item in invent_Ref}
    #             # print(part_batch_info)
    #             part_info = update_category_info(part_batch_info,data.get("ecategoryInfo",{}),{},invent_Ref,partner_name['all_attributes']['partner_name'])
    #             if part_info:
    #                 data["E-KIT1"] = part_info['part_details']
    #             else:
    #                 return {"statusCode": "200", "body": "Not enough parts inwarded for this Bom"}
    #             id = 1
    #             documents = data['documents']
    #             doc = {}
    #             for inx, docs in enumerate(documents):
    #                 image_path = file_uploads.upload_file("EMS", "PtgCms" + env_type, "",
    #                                                       "E-Kit" + str(id), docs["doc_name"],
    #                                                       docs['doc_body'])
    #                 doc[docs["doc_name"]] = image_path
    #             key = next(k for k in data.keys() if k.startswith("E-KIT"))
    #             data[key]["documents"] = doc
    #             ecategory_ratios = [int(item["provided_qty"]) / int(item["required_quantity"]) for item in
    #                                 data["ecategoryInfo"]]
    #             mean_ecategory_no_numpy = calculate_mean(ecategory_ratios)
    #             invent_data = list(db_con.Inventory.find({}, {"_id": 0, "pk_id": 1, "sk_timeStamp": 1,
    #                                                           "all_attributes.qty": 1,
    #                                                           "all_attributes.out_going_qty": 1}))
    #             invent_data = {item['pk_id']: item['all_attributes'] for item in invent_data}
    #             if any(1 for item in data["ecategoryInfo"] if
    #                    int(item['provided_qty']) > int(invent_data[item['cmpt_id']]["qty"])):
    #                 return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}
    #             for i in data["ecategoryInfo"]:
    #                 cmpt_id = i["cmpt_id"]
    #                 invent_data = list(db_con.Inventory.find({"pk_id": cmpt_id},
    #                                                          {"_id": 0, "pk_id": 1, "sk_timeStamp": 1,
    #                                                           "all_attributes.qty": 1,
    #                                                           "all_attributes.out_going_qty": 1}))
    #                 qty = str(int(invent_data[0]['all_attributes']["qty"]) - int(i["provided_qty"]))
    #                 out_going_qty = str(int(invent_data[0]['all_attributes']["out_going_qty"]) + int(
    #                     i["provided_qty"])) if "out_going_qty" in invent_data[0]['all_attributes'].keys() else i[
    #                     "provided_qty"]
    #                 response = db_con.Inventory.update_one(
    #                     {"pk_id": invent_data[0]["pk_id"]},
    #                     {"$set": {"all_attributes.qty": qty, "all_attributes.out_going_qty": out_going_qty}}
    #                 )
    #         data["mtrl_prcnt"] = str(((mean_ecategory_no_numpy)) * 100)[:5]
    #         data["order_date"] = sk_timeStamp.split("T")[0]
    #         data.pop("mcategoryInfo", None)
    #         data.pop("ecategoryInfo", None)
    #         del data["env_type"]
    #         data["outward_id"] = "BTOUT" + str(outward_id)
    #         data_without_documents = {k: v for k, v in data.items() if k != "documents"}
    #         item = {
    #             "pk_id": "BTOUT" + str(outward_id),
    #             "sk_timeStamp": sk_timeStamp,
    #             "all_attributes": data_without_documents,
    #             "gsipk_table": gsipk_table,
    #             "gsisk_id": "--",
    #             "lsi_key": data["bom_id"]
    #         }
    #         bom_id = data["bom_id"]
    #         activity_id = int(activity_id) + 1
    #         if item:
    #             db_con['ActivityDetails'].insert_one(
    #                 {
    #                     "pk_id": f"ACTID{activity_id}",
    #                     "sk_timeStamp": sk_timeStamp,
    #                     "all_attributes": part_info['activity_details'],
    #                     "gsipk_table": "ActivityDetails",
    #                     "gsisk_id": outward_id,
    #                     "lsi_key": "Utilized",
    #                     "gsipk_id": "EMS"
    #                 }
    #             )
    #             resp = db_con.EMS.insert_one(item)
    #             resp = db_con.all_tables.update_one(
    #                 {"pk_id": "top_ids"},
    #                 {"$set": {"all_attributes.EMS": "BTOUT" + str(outward_id),
    #                           "all_attributes.ActivityId": f"{activity_id}"}}
    #             )
    #             resp = db_con.BOM.update_one(
    #                 {"pk_id": bom_id},
    #                 {"$set": {"all_attributes.status": "Bom_assigned"}}
    #             )
    #             response = {'statusCode': 200, 'body': 'EMS assigned  to BOM successfully'}
    #             return response
    #         else:
    #             return {"statusCode": 400, "body": "no data found"}
    #     else:
    #         return {"statusCode": 200, "body": "No inward found for this bom"}

    # def cmsAssignToEMS(request_body): #Working fine till 2 Aug 12PM
    #     activity = {}
    #     data = request_body
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     env_type = data.get("env_type", "")
    #     sk_timeStamp = (datetime.now()).isoformat()
    #     bom_id = data['bom_id']
    #     # part_batch_info = find_stock_inwards(bom_id, db_con, 'E_parts')
    #     part_batch_info = find_stock_inward_new(bom_id, db_con, 'E_parts')
    #     # part_batch_info = part_batch_info['part_batch_info']
    #     part_batch_info = part_batch_info.get('part_batch_info', None)
    #     if part_batch_info is None:
    #         return {"statusCode": 400, "body": "No inward found for this bom"}
    #     partner_name = db_con.Partners.find_one({"pk_id": data['partner_id']},
    #                                             {"_id": 0, "all_attributes.partner_name": 1})
    #     # print(f"partner_name is {partner_name['all_attributes']}")
    #     if part_batch_info:
    #         gsipk_table = "EMS"
    #         first_record = list(db_con.EMS.find({"pk_id": "BTOUT1"}))
    #         all_tables = list(db_con.all_tables.find({"pk_id": "top_ids"}, {"_id": 0, "all_attributes.EMS": 1,
    #                                                                         "all_attributes.ActivityId": 1}))
    #         update_id = all_tables[0]['all_attributes']['EMS'][5:]
    #         activity_id = all_tables[0]['all_attributes']['ActivityId']
    #         outward_id = '1'
    #         if first_record:
    #             outward_id = str(int(update_id) + 1)
    #         mean_ecategory_no_numpy = 0
    #         if "ecategoryInfo" in data:
    #             invent_Ref = db_con.Inventory.find({}, {"_id": 0, "all_attributes.qty": 1, "pk_id": 1})
    #             invent_Ref = {item['pk_id']: item['all_attributes']['qty'] for item in invent_Ref}
    #             # print(part_batch_info)
    #             part_info = update_category_info(part_batch_info,data.get("ecategoryInfo",{}),{},invent_Ref,partner_name['all_attributes']['partner_name'])
    #             if part_info:
    #                 data["E-KIT1"] = part_info['part_details']
    #             else:
    #                 return {"statusCode": "400", "body": "Not enough parts inwarded for this Bom"}
    #             id = 1
    #             documents = data['documents']
    #             doc = {}
    #             for inx, docs in enumerate(documents):
    #                 image_path = file_uploads.upload_file("EMS", "PtgCms" + env_type, "",
    #                                                       "E-Kit" + str(id), docs["doc_name"],
    #                                                       docs['doc_body'])
    #                 doc[docs["doc_name"]] = image_path
    #             key = next(k for k in data.keys() if k.startswith("E-KIT"))
    #             data[key]["documents"] = doc
    #             ecategory_ratios = [int(item["provided_qty"]) / int(item["required_quantity"]) for item in
    #                                 data["ecategoryInfo"]]
    #             mean_ecategory_no_numpy = calculate_mean(ecategory_ratios)
    #             invent_data = list(db_con.Inventory.find({}, {"_id": 0, "pk_id": 1, "sk_timeStamp": 1,
    #                                                           "all_attributes.qty": 1,
    #                                                           "all_attributes.out_going_qty": 1}))
    #             invent_data = {item['pk_id']: item['all_attributes'] for item in invent_data}
    #             if any(1 for item in data["ecategoryInfo"] if
    #                    int(item['provided_qty']) > int(invent_data[item['cmpt_id']]["qty"])):
    #                 return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}
    #             for i in data["ecategoryInfo"]:
    #                 cmpt_id = i["cmpt_id"]
    #                 invent_data = list(db_con.Inventory.find({"pk_id": cmpt_id},
    #                                                          {"_id": 0, "pk_id": 1, "sk_timeStamp": 1,
    #                                                           "all_attributes.qty": 1,
    #                                                           "all_attributes.out_going_qty": 1}))
    #                 qty = str(int(invent_data[0]['all_attributes']["qty"]) - int(i["provided_qty"]))
    #                 out_going_qty = str(int(invent_data[0]['all_attributes']["out_going_qty"]) + int(
    #                     i["provided_qty"])) if "out_going_qty" in invent_data[0]['all_attributes'].keys() else i[
    #                     "provided_qty"]
    #                 response = db_con.Inventory.update_one(
    #                     {"pk_id": invent_data[0]["pk_id"]},
    #                     {"$set": {"all_attributes.qty": qty, "all_attributes.out_going_qty": out_going_qty}}
    #                 )
    #         data["mtrl_prcnt"] = str(((mean_ecategory_no_numpy)) * 100)[:5]
    #         data["order_date"] = sk_timeStamp.split("T")[0]
    #         data.pop("mcategoryInfo", None)
    #         data.pop("ecategoryInfo", None)
    #         del data["env_type"]
    #         data["outward_id"] = "BTOUT" + str(outward_id)
    #         data_without_documents = {k: v for k, v in data.items() if k != "documents"}
    #         item = {
    #             "pk_id": "BTOUT" + str(outward_id),
    #             "sk_timeStamp": sk_timeStamp,
    #             "all_attributes": data_without_documents,
    #             "gsipk_table": gsipk_table,
    #             "gsisk_id": "--",
    #             "lsi_key": data["bom_id"]
    #         }
    #         bom_id = data["bom_id"]
    #         activity_id = int(activity_id) + 1
    #         if item:
    #             db_con['ActivityDetails'].insert_one(
    #                 {
    #                     "pk_id": f"ACTID{activity_id}",
    #                     "sk_timeStamp": sk_timeStamp,
    #                     "all_attributes": part_info['activity_details'],
    #                     "gsipk_table": "ActivityDetails",
    #                     "gsisk_id": outward_id,
    #                     "lsi_key": "Utilized",
    #                     "gsipk_id": "EMS"
    #                 }
    #             )
    #             resp = db_con.EMS.insert_one(item)
    #             resp = db_con.all_tables.update_one(
    #                 {"pk_id": "top_ids"},
    #                 {"$set": {"all_attributes.EMS": "BTOUT" + str(outward_id),
    #                           "all_attributes.ActivityId": f"{activity_id}"}}
    #             )
    #             resp = db_con.BOM.update_one(
    #                 {"pk_id": bom_id},
    #                 {"$set": {"all_attributes.status": "Bom_assigned"}}
    #             )
    #             response = {'statusCode': 200, 'body': 'EMS assigned  to BOM successfully'}
    #             return response
    #         else:
    #             return {"statusCode": 400, "body": "no data found"}
    #     else:
    #         return {"statusCode": 400, "body": "No inward found for this bom"}

    def cmsAssignToEMS(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client'] 
            env_type = data.get("env_type","")
            sk_timeStamp = (datetime.now()).isoformat()
            gsipk_table="EMS"
            first_record = list(db_con.EMS.find({"pk_id":"BTOUT1"}))
            print(first_record)
            outward_id='1'
            if first_record: 
                update_id = list(db_con.all_tables.find({"pk_id":"top_ids"},{"all_attributes.EMS":1}))
                print(update_id)
                update_id = update_id[0]['all_attributes']['EMS'][5:]
                outward_id=str(int(update_id)+1)
            mean_ecategory_no_numpy=0
            mean_mcategory_no_numpy=0
            if "mcategoryInfo" in data:
                data["M-KIT1"] = update_category_info(data.get("mcategoryInfo",{}))
                mcategory_ratios = [int(item["provided_qty"]) / int(item["required_quantity"]) for item in data["mcategoryInfo"]]
                mean_mcategory_no_numpy = calculate_mean(mcategory_ratios)
                for i in data["mcategoryInfo"]:
                    cmpt_id=i["cmpt_id"]
                    invent_data = list(db_con.Inventory.find({"pk_id":cmpt_id},{"pk_id":1,"sk_timeStamp":1,"all_attributes.qty":1}))
                    if int(invent_data[0]['all_attributes']["qty"])>=int(i["provided_qty"]):
                        qty=str(int(invent_data[0]['all_attributes']["qty"])-int(i["provided_qty"]))
                        out_going_qty = str(int(invent_data[0]['all_attributes']["out_going_qty"]) + int(i["provided_qty"])) if "out_going_qty" in invent_data[0].keys() else i["provided_qty"]
                        resp = db_con.Inventory.update_one(
                            {"pk_id": invent_data[0]["pk_id"]},
                            {"$set": {"all_attributes.qty" : qty,"all_attributes.out_going_qty":out_going_qty}}
                        )
                    else:
                        conct.close_connection(client)
                        return {"statusCode":"502","body":"provided quantity is more than the total quantity"
                    }
            if "ecategoryInfo" in data:
                data["E-KIT1"] = update_category_info(data.get("ecategoryInfo",{}))
                ecategory_ratios = [int(item["provided_qty"]) / int(item["required_quantity"]) for item in data["ecategoryInfo"]]
                mean_ecategory_no_numpy = calculate_mean(ecategory_ratios)
                all_tables = list(db_con.all_tables.find({"pk_id": "top_ids"}, {"_id": 0, "all_attributes.EMS": 1,
                                                                                "all_attributes.ActivityId": 1}))
                update_id = all_tables[0]['all_attributes']['EMS'][5:]
                activity_id = all_tables[0]['all_attributes']['ActivityId']
                outward_id = '1'
                if first_record:
                    outward_id = str(int(update_id) + 1)
                invent_data = list(db_con.Inventory.find({},{"pk_id":1,"sk_timeStamp":1,"all_attributes.qty":1,"all_attributes.out_going_qty":1}))
                invent_data = {item['pk_id']:item['all_attributes'] for item in invent_data}
                # return invent_data
                id = 1
                documents = data['documents']
                doc = {}
                for inx, docs in enumerate(documents):
                    image_path = file_uploads.upload_file("EMS", "PtgCms" + env_type, "",
                                                          "E-Kit" + str(id), docs["doc_name"],
                                                          docs['doc_body'])
                    doc[docs["doc_name"]] = image_path
                key = next(k for k in data.keys() if k.startswith("E-KIT"))
                data[key]["documents"] = doc
                if any(1 for item in data["ecategoryInfo"] if int(item['provided_qty'])>int(invent_data[item['cmpt_id']]["qty"])):
                    return {"statusCode":"502","body":"provided quantity is more than the total quantity"}
                for i in data["ecategoryInfo"]:
                    cmpt_id=i["cmpt_id"]
                    invent_data = list(db_con.Inventory.find({"pk_id":cmpt_id},{"pk_id":1,"sk_timeStamp":1,"all_attributes.qty":1,"all_attributes.out_going_qty":1}))
                    # return invent_data
                    # if int(invent_data[0]['all_attributes']["qty"])>=int(i["provided_qty"]):
                    qty=str(int(invent_data[0]['all_attributes']["qty"])-int(i["provided_qty"]))
                    out_going_qty = str(int(invent_data[0]['all_attributes']["out_going_qty"]) + int(i["provided_qty"])) if "out_going_qty" in invent_data[0]['all_attributes'].keys() else i["provided_qty"]
                    response = db_con.Inventory.update_one(
                        {"pk_id": invent_data[0]["pk_id"]},
                        {"$set": {"all_attributes.qty" : qty,"all_attributes.out_going_qty":out_going_qty}}
                    )
                    # else:
                    #     conct.close_connection(client)
                    #     return {"statusCode":"502","body":"provided quantity is more than the total quantity"}
            data["mtrl_prcnt"]= str(((mean_ecategory_no_numpy))*100)[:5]
            data["order_date"]=sk_timeStamp.split("T")[0]
            data.pop("mcategoryInfo", None)
            data.pop("ecategoryInfo", None)
            del data["env_type"] 
            data["outward_id"]="BTOUT"+str(outward_id)
            data_without_documents = {k: v for k, v in data.items() if k != "documents"}
            item = {
                "pk_id":"BTOUT"+str(outward_id),
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": data_without_documents,
                "gsipk_table":gsipk_table,
                "gsisk_id":"--" ,
                "lsi_key": data["bom_id"] 
            }
            bom_id=data["bom_id"]
            activity_id = int(activity_id) + 1
            if item:
                activity_details = {}
                for part_key, part_value in data["E-KIT1"].items():
                    if part_key.startswith("part"):
                        cmpt_id = part_value.get('cmpt_id','')
                        print("ABCDEF",part_value.get('lot_id',''))
                        activity_details[cmpt_id] = {
                            "mfr_prt_num": part_value.get('mfr_part_number', ''),
                            "date": sk_timeStamp.split('T')[0],
                            "action": "Utilized",
                            # "Description": part_value.get('description',''),
                            "Description": "Utilized",
                            "issued_to": data.get('receiver_name', ''),
                            "po_no": "-",
                            "invoice_no": "-",
                            "cmpt_id": part_value.get('cmpt_id', ''),
                            "ctgr_id": part_value.get('ctgr_id', ''),
                            "prdt_name": part_value.get('part_name', ''),
                            "description": part_value.get('description', ''),
                            "packaging": "-",
                            # "closing_qty": "200",
                            "closing_qty":str(int(part_value.get('qty','0'))- int(part_value.get('provided_qty','0'))),
                            # "qty": "200",
                            "qty": part_value.get('provided_qty','0'),
                            "batchId": part_value.get('batch_no',''),
                            "used_qty": "0",
                            # "lot_no": "testlot",
                            "lot_id": part_value.get('lot_id','')
                        }
                db_con['ActivityDetails'].insert_one(
                    {
                        "pk_id": f"ACTID{activity_id}",
                        "sk_timeStamp": sk_timeStamp,
                        "all_attributes": activity_details,
                        "gsipk_table": "ActivityDetails",
                        "gsisk_id": outward_id,
                        "lsi_key": "Utilized",
                        "gsipk_id": "EMS"
                    }
                )
            if item:
                resp = db_con.EMS.insert_one(item)
                resp = db_con.all_tables.update_one(
                            {"pk_id": "top_ids"},
                            {"$set": {"all_attributes.EMS" : "BTOUT"+str(outward_id),
                                      "all_attributes.ActivityId":f"{activity_id}"}}
                        )
                resp = db_con.BOM.update_one(
                    {"pk_id": bom_id},
                    {"$set": {"all_attributes.status" : "Bom_assigned"}}
                )
                response = {'statusCode': 200, 'body': 'EMS assigned  to BOM successfully'}
                return response
            else:
                return {"statusCode": 400, "body": "no data found"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request(check data)'}

        
    def cmsGetAssignToEMSDocuments(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            pk_id = data['outward_id']
            doc = data['event_key']
            if data['dep_type'] == 'EMS':
                res = db_con[data['dep_type']].find_one({'pk_id': pk_id})
                documents = res["all_attributes"][doc].get('documents',{})
                document_list = [{"doc_name": name, "doc_url": url} for name, url in documents.items()]
                return {'statusCode': 200, 'body': document_list}
            else:
                res = db_con[data['dep_type']].find_one({'all_attributes.outward_id': pk_id})
                documents = res["all_attributes"][doc].get('documents', {})
                document_list = [{"doc_name": name, "doc_url": url} for name, url in documents.items()]
                return {'statusCode': 200, 'body': document_list}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': f'Bad Request(check data): {err} (file: {f_name}, line: {line_no})'}

    def CmsBomGetAllOutwardList(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            bom_id = data['bom_id']
            lst = []
            db = db_con.EMS.find({"lsi_key":bom_id})
            if db:
                lst = sorted([{
                'outward_id': item["all_attributes"]["outward_id"],
                'partner_id': item["all_attributes"]["partner_id"],
                'type': item["all_attributes"]["type"], 
                'boards_qty': item["all_attributes"]["qty"],
                'outward_date': item['sk_timeStamp'][:10],
                'mtrl_prcnt':item["all_attributes"]["mtrl_prcnt"] if "mtrl_prcnt" in item["all_attributes"] else " "

                } for item in db], key=lambda x: int(x['outward_id'].replace("BTOUT", "")), reverse=False)
                conct.close_connection(client)
                return {'statusCode': 200, 'body': lst}
            else:
                conct.close_connection(client)
                return {"statusCode": 400, "body": []}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check data)'}
    

    def CmsOutwardGetBalanceComponentDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            outward_id = data["outward_id"]
            env_type = data.get("env_type", "")
            
            result = db_con.EMS.find_one({"pk_id": outward_id}, {"sk_timeStamp": 1, "all_attributes": 1})
            
            if result:
                part_info = result['all_attributes']
                all_keys = sorted(part_info.keys(), key=extract_numeric_part, reverse=True)
                
                sorted_part_info = {key: part_info[key] for key in all_keys}
                
                latest_e_kit_key, latest_m_kit_key = None, None
                if any(kit_key.startswith('E-KIT') for kit_key in all_keys):
                    latest_e_kit_key = f"E-KIT{max(int(kit_key.replace('E-KIT', '')) for kit_key in all_keys if kit_key.startswith('E-KIT'))}"
                if any(kit_key.startswith('M-KIT') for kit_key in all_keys):
                    latest_m_kit_key = f"M-KIT{max(int(kit_key.replace('M-KIT', '')) for kit_key in all_keys if kit_key.startswith('M-KIT'))}"
                
                kits = {}
                latest_e_kit_info = {}
                latest_m_kit_info = {}
                
                if latest_e_kit_key:
                    latest_e_kit_info = {sub_key: sub_value for sub_key, sub_value in sorted_part_info[latest_e_kit_key].items() if int(sub_value.get("balance_qty", 0)) < 0}
                if latest_m_kit_key:
                    latest_m_kit_info = {
                        sub_key: {
                            "required_quantity": sub_value.get('required_quantity', ''),
                            "ptg_prt_num": sub_value.get('ptg_prt_num', ''),
                            "material": sub_value.get('material', ''),
                            "qty": sub_value.get('qty', ''),
                            "vic_part_number": sub_value.get('vic_part_number', ''),
                            "ctgr_name": sub_value.get('ctgr_name', ''),
                            "description": sub_value.get('description', ''),
                            "balance_qty": sub_value.get('balance_qty', ''),
                            "part_name": sub_value.get('part_name', ''),
                            "technical_details": sub_value.get('technical_details', ''),
                            "provided_qty": sub_value.get('provided_qty', ''),
                            "damage_qty": "0"
                        } for sub_key, sub_value in sorted_part_info[latest_m_kit_key].items()
                        if int(sub_value.get("balance_qty", 0)) < 0
                    }
                
                for kit_key in list(sorted_part_info.keys()):
                    if kit_key.startswith('E-KIT') and kit_key != latest_e_kit_key:
                        sorted_part_info.pop(kit_key, None)
                for kit_key in list(sorted_part_info.keys()):
                    if kit_key.startswith('M-KIT') and kit_key != latest_m_kit_key:
                        sorted_part_info.pop(kit_key, None)
                
                if latest_e_kit_key:
                    sorted_part_info[latest_e_kit_key] = calculate_difference(latest_e_kit_info)
                if latest_m_kit_key:
                    sorted_part_info[latest_m_kit_key] = calculate_difference(latest_m_kit_info)
                
                sorted_part_info["created_date"] = result['sk_timeStamp'][:10]
                
                for key, value in sorted_part_info.items():
                    if key.startswith("E-KIT") or key.startswith("M-KIT"):
                        kits[key] = value
                sorted_part_info["KITS"] = kits
                
                for key in kits:
                    del sorted_part_info[key]
                
                # Add inventory quantity to each component
                for kit_key, kit_info in kits.items():
                    for component_key, component_info in kit_info.items():
                        cmpt_id = component_info.get('cmpt_id', '')
                        inventory_record = db_con.Inventory.find_one({"pk_id": cmpt_id}, {"all_attributes.qty": 1})
                        if inventory_record:
                            component_info['ptg_stock'] = inventory_record['all_attributes'].get('qty', 0)
                
                conct.close_connection(client)
                return {"statusCode": 200, "body": sorted_part_info}
            else:
                conct.close_connection(client)
                return {"statusCode": 400, "body": f"No data found for the provided outward_id: {outward_id}"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            error_message = f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}"
            return {"statusCode": 500, "body": error_message}




    # def CmsOutwardGetBalanceComponentDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         env_type = data.get("env_type", "")
    #         # statement = f"""select sk_timeStamp,all_attributes from {database_table_name} where gsipk_table = '{gsipk_table}' AND pk_id = '{outward_id}'"""
    #         result = db_con.EMS.find({"pk_id":outward_id},{"sk_timeStamp":1,"all_attributes":1})
    #         # result = execute_statement_with_pagination(statement)
    #         if result:
    #             # result = extract_items_from_nested_dict(result[0])
    #             result = result[0]
    #             part_info = result['all_attributes']
    #             # return part_info
    #             # all_keys = sorted(part_info.keys(), reverse=True)
    #             all_keys = sorted(part_info.keys(), key=extract_numeric_part, reverse=True)
    #             all_keys = sorted(part_info.keys(),  reverse=True)
    #             # return all_keys
    #             sorted_part_info = {key: part_info[key] for key in all_keys}
    #             # return sorted_part_info
    #             latest_e_kit_key,latest_m_kit_key = 0,0
    #             if any(1 for kit_key in all_keys if kit_key.startswith('E-KIT')):
    #                 latest_e_kit_key = f'E-KIT{max((int(kit_key.replace("E-KIT","")) for kit_key in all_keys if kit_key.startswith("E-KIT")))}'
    #             if any(1 for kit_key in all_keys if kit_key.startswith('M-KIT')):
    #                 latest_m_kit_key = f'M-KIT{max((int(kit_key.replace("M-KIT","")) for kit_key in all_keys if kit_key.startswith("M-KIT")))}'
    #             kits = {}
    #             latest_e_kit_info = {}
    #             latest_m_kit_info = {}
    #             # return sorted_part_info[latest_e_kit_key]
    #             if latest_e_kit_key: 
    #                 latest_e_kit_info = {sub_key: sub_value for sub_key, sub_value in sorted_part_info[latest_e_kit_key].items() if int(sub_value.get("balance_qty", 0)) < 0}
    #                 # return latest_e_kit_info
    #                 # latest_e_kit_info = {sub_key: sub_value for sub_key, sub_value in sorted_part_info[latest_e_kit_key].items() if int(sub_value.get("balance_qty", 0)) <= 0 and int(sub_value['balance_qty'])!=0}
    #                 # return latest_e_kit_info
    #                 # latest_e_kit_info = {sub_key: sub_value for sub_key, sub_value in sorted_part_info[latest_e_kit_key].items() if int(sub_value.get("balance_qty", 0)) < 0}
    #             if latest_m_kit_key:
    #                 # return latest_e_kit_info
    #                 latest_m_kit_info = {
    #                     sub_key: {
    #                         "required_quantity": sub_value.get('required_quantity',''),
    #                         "ptg_prt_num": sub_value.get('ptg_prt_num',''),
    #                         "material": sub_value.get('material',''),
    #                         "qty": sub_value.get('qty',''),
    #                         "vic_part_number": sub_value.get('vic_part_number',''),
    #                         "ctgr_name": sub_value.get('ctgr_name',''),
    #                         "description": sub_value.get('description',''),
    #                         "balance_qty": sub_value.get('balance_qty',''),
    #                         "part_name": sub_value.get('part_name',''),
    #                         "technical_details": sub_value.get('technical_details',''),
    #                         "provided_qty": sub_value.get('provided_qty',''),
    #                         "damage_qty":"0"
    #                     } for sub_key, sub_value in sorted_part_info[latest_m_kit_key].items() 
    #                     if int(sub_value.get("balance_qty", 0)) < 0
    #                 }
    #                 # latest_m_kit_info = {sub_key: sub_value for sub_key, sub_value in sorted_part_info[latest_m_kit_key].items() if int(sub_value.get("balance_qty", 0)) < 0}
    #             for kit_key in list(sorted_part_info.keys()):
    #                 if kit_key.startswith('E-KIT') and kit_key != latest_e_kit_key:
    #                     sorted_part_info.pop(kit_key, None)
    #             for kit_key in list(sorted_part_info.keys()):
    #                 if kit_key.startswith('M-KIT') and kit_key != latest_m_kit_key:
    #                     sorted_part_info.pop(kit_key, None)
    #             if latest_e_kit_key:
    #                 sorted_part_info[latest_e_kit_key] = calculate_difference(latest_e_kit_info)
    #             if latest_m_kit_key:
    #                 sorted_part_info[latest_m_kit_key] = calculate_difference(latest_m_kit_info)
    #             sorted_part_info["created_date"] = result['sk_timeStamp'][:10]
    #             for key, value in sorted_part_info.items():
    #                 if key.startswith("E-KIT") or key.startswith("M-KIT"):
    #                     kits[key] = value
    #             sorted_part_info["KITS"] = kits 
    #             for key in kits:
    #                 del sorted_part_info[key]
    #             conct.close_connection(client)
    #             return {"statusCode": 200, "body": sorted_part_info}
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 400, "body": f"No data found for the provided outward_id: {outward_id}"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         error_message = f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}"
    #         return {"statusCode": 500, "body": error_message}
        



    
    def CmsBomGetEmsOutwardDetailsbyId(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            outward_id = data["outward_id"]

            def filter_kits(kits):
                filtered_kits = {}
                for key, value in kits.items():
                    if key.startswith("E-KIT") or key.startswith("M_KIT"):
                        new_value = {k: v for k, v in value.items() if k not in ["gateentry", "qatest", "inward", "documents"]}
                        for part_key, part_value in new_value.items():
                            if isinstance(part_value, dict) and "doc_name" in part_value:
                                del part_value["doc_name"]
                        filtered_kits[key] = new_value
                return filtered_kits

            def calculate_total_balance_qty(kit):
                total_balance_qty = 0
                for part in kit.values():
                    if "balance_qty" in part:
                        total_balance_qty += int(part["balance_qty"])
                return total_balance_qty

            if data["dep_type"] == "EMS":
                result = list(db_con.EMS.find({"pk_id": outward_id}, {"sk_timeStamp": 1, "all_attributes": 1}))
                if result:
                    result = result[0]
                    part_info = result['all_attributes']
                    part_info["created_date"] = result['sk_timeStamp'][:10]
                    kits = filter_kits(part_info)
                    kits = {key: value for key, value in sorted(kits.items(), key=lambda item: int(item[0][5:]))}
                    part_info["KITS"] = kits
                    last_e_kit_key = next((kit_key for kit_key in reversed(kits) if kit_key.startswith('E-KIT')), None)
                    last_m_kit_key = next((kit_key for kit_key in reversed(kits) if kit_key.startswith('M_KIT')), None)
                    if last_e_kit_key or last_m_kit_key:
                        last_e_kit_qty = calculate_total_balance_qty(kits[last_e_kit_key]) if last_e_kit_key else 0
                        last_m_kit_qty = calculate_total_balance_qty(kits[last_m_kit_key]) if last_m_kit_key else 0
                        any_negative_balance_qty = any(
                            int(part["balance_qty"]) < 0
                            for kit in (kits.get(last_e_kit_key, {}), kits.get(last_m_kit_key, {}))
                            for part in kit.values()
                            if "balance_qty" in part
                        )
                        part_info["status"] = not any_negative_balance_qty
                    for key in kits:
                        del part_info[key]
                    partner_id = part_info["partner_id"]
                    partner_result = list(db_con.Partners.find({"pk_id": partner_id}, {"all_attributes.partner_name": 1}))
                    if partner_result:
                        partner_name = partner_result[0]['all_attributes']["partner_name"]
                        part_info["partner_name"] = partner_name
                    conct.close_connection(client)
                    return {"statusCode": 200, "body": part_info}
                else:
                    conct.close_connection(client)
                    return {"statusCode": 400, "body": "something went wrong, please try again"}
            else:
                result = list(db_con.BoxBuilding.find({"all_attributes.outward_id": outward_id}))
                if result:
                    result = result[0]
                    part_info = result['all_attributes']
                    part_info["created_date"] = result['sk_timeStamp'][:10]
                    kits = filter_kits(part_info)
                    kits = {key: value for key, value in sorted(kits.items(), key=lambda item: int(item[0][5:]))}
                    last_e_kit_key = next((kit_key for kit_key in reversed(kits) if kit_key.startswith('E-KIT')), None)
                    last_m_kit_key = next((kit_key for kit_key in reversed(kits) if kit_key.startswith('M_KIT')), None)
                    if last_e_kit_key or last_m_kit_key:
                        last_e_kit_qty = calculate_total_balance_qty(kits[last_e_kit_key]) if last_e_kit_key else 0
                        last_m_kit_qty = calculate_total_balance_qty(kits[last_m_kit_key]) if last_m_kit_key else 0
                        any_negative_balance_qty = any(
                            int(part["balance_qty"]) < 0
                            for kit in (kits.get(last_e_kit_key, {}), kits.get(last_m_kit_key, {}))
                            for part in kit.values()
                            if "balance_qty" in part
                        )
                        part_info["status"] = not any_negative_balance_qty
                    for key in kits:
                        if key.startswith('M_KIT'):
                            part_info[key] = kits[key]
                    partner_id = part_info["partner_id"]
                    partner_result = list(db_con.Partners.find({"pk_id": partner_id}, {"all_attributes.partner_name": 1}))
                    if partner_result:
                        partner_name = partner_result[0]['all_attributes']["partner_name"]
                        part_info["partner_name"] = partner_name
                    conct.close_connection(client)
                    return {"statusCode": 200, "body": part_info}
                else:
                    conct.close_connection(client)
                    return {"statusCode": 400, "body": "something went wrong, please try again"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check data)'}





    def CmsEmsSendBalanceKitCreate(request_body):
        data = request_body
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        result = list(db_con.EMS.find({"all_attributes.outward_id": data['outward_id']}, {"pk_id": 1, "sk_timeStamp": 1, "all_attributes": 1}))
        activity = {}
        sk_timeStamp = (datetime.now()).isoformat()
        if result:
            result = result[0]
            all_attributes = result['all_attributes']
            e_pattern = r"^E-KIT\d+$"
            m_pattern = r"^M-KIT\d+$"
            activity_id = db_con.all_tables.find_one({"pk_id": "top_ids"}, {"all_attributes.ActivityId": 1})
            activity_id = int(activity_id['all_attributes'].get('ActivityId', "0")) + 1
            mean_ecategory_no_numpy = 0
            mean_mcategory_no_numpy = 0
            component_twi = []
            partner_name = db_con.Partners.find_one({"pk_id": data['partner_id']}, {"all_attributes.partner_name": 1})
            all_tables = list(db_con.all_tables.find({"pk_id": "top_ids"}, {"_id": 0, "all_attributes.EMS": 1, "all_attributes.ActivityId": 1}))
            update_id = all_tables[0]['all_attributes']['EMS'][5:]
            activity_id = all_tables[0]['all_attributes']['ActivityId']
            outward_id = str(int(update_id) + 1)
            invent_data = list(db_con.Inventory.find({}, {"all_attributes.cmpt_id": 1, "all_attributes.qty": 1, "all_attributes.out_going_qty": 1}))
            invent_data = {item['all_attributes']['cmpt_id']: {"qty": item['all_attributes']['qty'], "out_going_qty": item['all_attributes'].get('out_going_qty', '0')} for item in invent_data}

            if "E-KIT" in data:
                for part in data['E-KIT']:
                    print(part['provided_qty'], invent_data[part['cmpt_id']]['qty'])
                if any(int(part['provided_qty']) > int(invent_data[part['cmpt_id']]['qty']) for part in data['E-KIT']):
                    return {"statusCode": 400, "body": "Quantity of part cannot be more than inventory quantity"}
                e_kit_number = max(int(key.replace("E-KIT", "")) for key in result['all_attributes'].keys() if re.match(e_pattern, key))
                e_kit_key = f'E-KIT{e_kit_number + 1}'
                all_attributes[e_kit_key] = {}
                documents = data['documents']
                doc = {}
                for inx, docs in enumerate(documents):
                    image_path = file_uploads.upload_file("EMS", "PtgCms" + env_type, "", "" + e_kit_key, docs["doc_name"], docs['doc_body'])
                    doc[docs["doc_name"]] = image_path
                all_attributes[e_kit_key]["documents"] = doc

                for inx, value in enumerate(data['E-KIT']):
                    part_key = f"part{inx + 1}"
                    all_attributes[e_kit_key][part_key] = value
                    cmpt_id = all_attributes[e_kit_key][part_key]["cmpt_id"]

                    qty = str(int(invent_data[cmpt_id]["qty"]) - int(all_attributes[e_kit_key][part_key]["provided_qty"]))
                    out_going_qty = str(int(invent_data[cmpt_id].get("out_going_qty", "0")) + int(all_attributes[e_kit_key][part_key]["provided_qty"]))

                    resp = db_con.Inventory.update_one(
                        {"pk_id": cmpt_id},
                        {"$set": {"all_attributes.qty": qty, "all_attributes.out_going_qty": out_going_qty}}
                    )
                ecategory_ratios = [int(item["provided_qty"]) / int(item["required_quantity"]) for item in data["E-KIT"]]
                mean_ecategory_no_numpy = calculate_mean(ecategory_ratios)

            if "M-KIT" in data:
                if any(part['provided_qty'] > invent_data[part['cmpt_id']]['qty'] for part in data['M-KIT']):
                    return {"statusCode": 400, "body": "Quantity of part cannot be more than inventory quantity"}
                m_kit_number = max(int(key.replace("M-KIT", "")) for key in result['all_attributes'].keys() if re.match(m_pattern, key))
                m_kit_key = f'M-KIT{m_kit_number + 1}'
                all_attributes[m_kit_key] = {}
                for inx, value in enumerate(data['M-KIT']):
                    part_key = f"part{inx + 1}"
                    all_attributes[m_kit_key][part_key] = value
                    cmpt_id = all_attributes[m_kit_key][part_key]["cmpt_id"]

                    qty = str(int(invent_data[cmpt_id]["qty"]) - int(all_attributes[m_kit_key][part_key]["provided_qty"]))
                    out_going_qty = str(int(invent_data[cmpt_id].get("out_going_qty", "0")) + int(all_attributes[m_kit_key][part_key]["provided_qty"]))

                    resp = db_con.Inventory.update_one(
                        {"pk_id": cmpt_id},
                        {"$set": {"all_attributes.qty": qty, "all_attributes.out_going_qty": out_going_qty}}
                    )
                mcategory_ratios = [int(item["provided_qty"]) / int(item["required_quantity"]) for item in data["M-KIT"]]
                mean_mcategory_no_numpy = calculate_mean(mcategory_ratios)

            all_attributes["mtrl_prcnt"] = str((float(all_attributes["mtrl_prcnt"]) + float(str(((mean_ecategory_no_numpy) * 100) / 2)[:5])))
            update_item = db_con.EMS.update_one(
                {"pk_id": result['pk_id']},
                {"$set": {"all_attributes": all_attributes}}
            )
            activity_details = {}
            for part_key, part_value in all_attributes.get(e_kit_key, {}).items():
                if part_key.startswith("part"):
                    cmpt_id = part_value.get('cmpt_id', '')
                    activity_details[cmpt_id] = {
                        "mfr_prt_num": part_value.get('mfr_part_number', ''),
                        "date": sk_timeStamp.split('T')[0],
                        "action": "Utilized",
                        "Description": "Utilized",
                        # "issued_to": partner_name['all_attributes']['partner_name'],
                        "issued_to": data.get('receiver_name', ''),
                        "po_no": "-",
                        "invoice_no": "-",
                        "cmpt_id": part_value.get('cmpt_id', ''),
                        "ctgr_id": part_value.get('ctgr_id', ''),
                        "prdt_name": part_value.get('part_name', ''),
                        "description": part_value.get('description', ''),
                        "packaging": "-",
                        "closing_qty": str(int(part_value.get('ptg_stock', '0')) - int(part_value.get('provided_qty', '0'))),
                        "qty": part_value.get('provided_qty', '0'),
                        "batchId": part_value.get('batch_no', ''),
                        "used_qty": "0",
                        "lot_id": part_value.get('lot_id', '')
                    }

            db_con['ActivityDetails'].insert_one(
                {
                    "pk_id": f"ACTID{activity_id}",
                    "sk_timeStamp": sk_timeStamp,
                    "all_attributes": activity_details,
                    "gsipk_table": "ActivityDetails",
                    "gsisk_id": data['outward_id'],
                    "lsi_key": "Utilized",
                    "gsipk_id": "EMS"
                }
            )
            db_con.all_tables.update_one(
                {"pk_id": "top_ids"},
                {"$set": {"all_attributes.ActivityId": activity_id}}
            )
            return {'statusCode': 200, 'body': 'Record updated successfully'}
        else:
            return {'statusCode': 400, 'body': 'No record found for given outward id'}


    # def CmsBomGetEmsOutwardDetailsbyId(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         # env_type = data.get("env_type", "")
    #         # databaseTableName = f"PtgCms{env_type}"
    #         if data["dep_type"] == "EMS":
    #             gsipk_table = "EMS"
    #             # statement = f"""select sk_timeStamp,all_attributes from {databaseTableName} where gsipk_table = '{gsipk_table}' AND pk_id = '{outward_id}'"""
    #             # result = execute_statement_with_pagination(statement)
    #             result = list(db_con.EMS.find({"pk_id":outward_id},{"sk_timeStamp":1,"all_attributes":1}))
    #             # return result
    #             if result:
    #                 # result = extract_items_from_nested_dict(result[0])
    #                 result = result[0]
    #                 part_info = result['all_attributes']
    #                 part_info["created_date"] = result['sk_timeStamp'][:10]
    #                 kits = {}
    #                 for key, value in part_info.items():
    #                     if key.startswith("E-KIT") or key.startswith("M-KIT"):
    #                         kits[key] = value
    #                 # kits = {key: value for key, value in sorted(kits.items())}
    #                 kits = {key: value for key, value in sorted(kits.items(), key=lambda item: int(item[0][5:]))}
    #                 part_info["KITS"] = kits
    #                 last_e_kit_key = next((kit_key for kit_key in reversed(kits) if kit_key.startswith('E-KIT')), None)
    #                 last_m_kit_key = next((kit_key for kit_key in reversed(kits) if kit_key.startswith('M-KIT')), None)
    #                 if last_e_kit_key or last_m_kit_key:
    #                     last_e_kit_qty = calculate_total_balance_qty(kits[last_e_kit_key]) if last_e_kit_key else 0
    #                     # return kits[last_e_kit_key]
    #                     last_m_kit_qty = calculate_total_balance_qty(kits[last_m_kit_key]) if last_m_kit_key else 0
    #                     if last_e_kit_key or last_m_kit_key:
    #                         any_negative_balance_qty = False
    #                         for part_key, part_value in kits.get(last_e_kit_key, {}).items():
    #                             if "balance_qty" in part_value and int(part_value["balance_qty"]) < 0:
    #                                 any_negative_balance_qty = True
    #                                 break
    #                         for part_key, part_value in kits.get(last_m_kit_key, {}).items():
    #                             if "balance_qty" in part_value and int(part_value["balance_qty"]) < 0:
    #                                 any_negative_balance_qty = True
    #                                 break
    #                         part_info["status"] = not any_negative_balance_qty
    #                 for key in kits:
    #                     del part_info[key]
    #                 partner_id=part_info["partner_id"]
    #                 print(partner_id)
    #                 # statement = f"""select all_attributes."partner_name" from {databaseTableName} where gsipk_table = 'Partners' AND pk_id = '{partner_id}'"""
    #                 # partner_name = execute_statement_with_pagination(statement)[0]["partner_name"]
    #                 # return partner_name
    #                 partner_name = list(db_con.Partners.find({"pk_id":partner_id},{"all_attributes.partner_name":1}))[0]['all_attributes']["partner_name"]
    #                 part_info["partner_name"]=partner_name
    #                 conct.close_connection(client)
    #                 return {"statusCode": 200, "body": part_info}
    #             else:
    #                 conct.close_connection(client)
    #                 return {"statusCode": 400, "body": "something went wrong, please try again"}
    #         else:
    #             gsipk_table = "BoxBuilding"
    #             # statement = f"""select * from {databaseTableName} where gsipk_table = '{gsipk_table}' AND all_attributes.outward_id = '{outward_id}'"""
    #             # result = execute_statement_with_pagination(statement)
    #             result = list(db_con.BoxBuilding.find({"all_attributes.outward_id" : outward_id}))
    #             if result:
    #                 # result = extract_items_from_nested_dict(result[0])
    #                 result = result[0]
    #                 part_info = result['all_attributes']
    #                 part_info["created_date"] = result['sk_timeStamp'][:10]
    #                 kits = {}
    #                 for key, value in part_info.items():
    #                     if key.startswith("E-KIT") or key.startswith("M-KIT"):
    #                         kits[key] = value
    #                 # kits = {key: value for key, value in sorted(kits.items())}
    #                 kits = {key: value for key, value in sorted(kits.items(), key=lambda item: int(item[0][5:]))}
    #                 part_info["KITS"] = kits
    #                 last_e_kit_key = next((kit_key for kit_key in reversed(kits) if kit_key.startswith('E-KIT')), None)
    #                 last_m_kit_key = next((kit_key for kit_key in reversed(kits) if kit_key.startswith('M-KIT')), None)
    #                 if last_e_kit_key or last_m_kit_key:
    #                     last_e_kit_qty = calculate_total_balance_qty(kits[last_e_kit_key]) if last_e_kit_key else 0
    #                     last_m_kit_qty = calculate_total_balance_qty(kits[last_m_kit_key]) if last_m_kit_key else 0
    #                     if last_e_kit_key or last_m_kit_key:
    #                         any_negative_balance_qty = False
    #                         for part_key, part_value in kits.get(last_e_kit_key, {}).items():
    #                             if "balance_qty" in part_value and int(part_value["balance_qty"]) < 0:
    #                                 any_negative_balance_qty = True
    #                                 break
    #                         for part_key, part_value in kits.get(last_m_kit_key, {}).items():
    #                             if "balance_qty" in part_value and int(part_value["balance_qty"]) < 0:
    #                                 any_negative_balance_qty = True
    #                                 break
    #                         part_info["status"] = not any_negative_balance_qty
    #                 for key in kits:
    #                     del part_info[key]
    #                 partner_id=part_info["partner_id"]
    #                 partner_name = list(db_con.Partners.find({"pk_id":partner_id},{"all_attributes.partner_name":1}))[0]['all_attributes']["partner_name"]
    #                 part_info["partner_name"]=partner_name
    #                 conct.close_connection(client)
    #                 return {"statusCode": 200, "body": part_info}
    #             else:
    #                 conct.close_connection(client)
    #                 return {"statusCode": 400, "body": "something went wrong, please try again"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}




    # def CmsEmsSendBalanceKitCreate(request_body):
    #     data = request_body
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']

    #     result = list(db_con.EMS.find({"all_attributes.outward_id": data['outward_id']},
    #                                   {"pk_id": 1, "sk_timeStamp": 1, "all_attributes": 1}))
    #     activity = {}
    #     sk_timeStamp = (datetime.now()).isoformat()
    #     if result:
    #         bom_id = result[0]['all_attributes']['bom_id']
    #         # part_batch_info = find_stock_inwards(bom_id, db_con, 'E_parts')
    #         part_batch_info = find_stock_inward_new(bom_id, db_con, 'E_parts')
    #         part_batch_info = part_batch_info['part_batch_info']
    #         if part_batch_info:
    #             result = result[0]
    #             all_attributes = result['all_attributes']
    #             ekitInfo = get_kit_and_boards_info(all_attributes, "EMS")
    #             e_pattern = r"^E-KIT\d+$"
    #             m_pattern = r"^M-KIT\d+$"
    #             activity_id = db_con.all_tables.find_one({"pk_id": "top_ids"}, {"all_attributes.ActivityId": 1})
    #             activity_id = int(activity_id['all_attributes'].get('ActivityId', "0")) + 1
    #             mean_ecategory_no_numpy = 0
    #             partner_name = db_con.Partners.find_one({"pk_id": data['partner_id']},
    #                                                     {"all_attributes.partner_name": 1})
    #             invent_data = list(db_con.Inventory.find({}, {"all_attributes.cmpt_id": 1, "all_attributes.qty": 1,
    #                                                           "all_attributes.out_going_qty": 1}))
    #             invent_data = {item['all_attributes']['cmpt_id']: {"qty": item['all_attributes']['qty'],
    #                                                                "out_going_qty": item['all_attributes'].get(
    #                                                                    'out_going_qty', '0')}
    #                            for item in invent_data}
    #             if "E-KIT" in data:
    #                 if any(int(part['provided_qty']) > int(invent_data[part['cmpt_id']]['qty']) for part in
    #                        data['E-KIT']):
    #                     return {"statusCode": 400, "body": "Quantity of part cannot be more than inventory quantity"}

    #                 e_kit_number = max(int(key.replace("E-KIT", "")) for key in result['all_attributes'].keys() if
    #                                    re.match(e_pattern, key))
    #                 e_kit_key = f'E-KIT{e_kit_number + 1}'
    #                 all_attributes[e_kit_key] = {}
    #                 documents = data['documents']
    #                 doc = {}
    #                 for inx, docs in enumerate(documents):
    #                     image_path = file_uploads.upload_file("EMS", "PtgCms" + env_type, "", "" + e_kit_key,
    #                                                           docs["doc_name"], docs['doc_body'])
    #                     doc[docs["doc_name"]] = image_path
    #                 all_attributes[e_kit_key]["documents"] = doc
    #                 for inx, value in enumerate(data['E-KIT']):
    #                     part_key = f"part{inx + 1}"
    #                     cmpt_id = value['cmpt_id']
    #                     batch_info = {inx: value for inx, value in enumerate(part_batch_info[value['cmpt_id']])}
    #                     qty = str(int(invent_data[cmpt_id]["qty"]) - int(value["provided_qty"]))
    #                     var = batch_number_allocation(part_batch_info, int(value['provided_qty']), value['cmpt_id'],
    #                                                   ekitInfo)
    #                     if var:
    #                         value['batch_no'] = var['batch_string']
    #                         activity[value['cmpt_id']] = {
    #                             "mfr_prt_num": value.get("mfr_prt_num", "-"),
    #                             "date": str(date.today()),
    #                             "action": "Utilized",
    #                             "Description": "Utilized",
    #                             "issued_to": partner_name['all_attributes']['partner_name'],
    #                             "po_no": var['po_id'],
    #                             'invoice_no': var["invoice_no"],
    #                             "cmpt_id": value.get("cmpt_id", ""),
    #                             "ctgr_id": value.get("ctgr_id", ""),
    #                             "prdt_name": value.get("prdt_name", ""),
    #                             "description": value.get("description", ""),
    #                             "packaging": value.get("packaging", ""),
    #                             "inventory_position": value.get("inventory_position", ""),
    #                             "closing_qty": f"{qty}",
    #                             "qty": value['provided_qty'],
    #                             "batchId": var['batch_string'],
    #                             "used_qty": value['provided_qty'],
    #                             "lot_no": var["lot_no"]
    #                         }
    #                     else:
    #                         return None
    #                     all_attributes[e_kit_key][part_key] = value
    #                     cmpt_id = all_attributes[e_kit_key][part_key]["cmpt_id"]
    #                     qty = str(
    #                         int(invent_data[cmpt_id]["qty"]) - int(all_attributes[e_kit_key][part_key]["provided_qty"]))
    #                     out_going_qty = str(int(invent_data[cmpt_id].get("out_going_qty", "0")) + int(
    #                         all_attributes[e_kit_key][part_key]["provided_qty"]))
    #                     db_con.Inventory.update_one(
    #                         {"pk_id": cmpt_id},
    #                         {"$set": {"all_attributes.qty": qty, "all_attributes.out_going_qty": out_going_qty}}
    #                     )
    #                 ecategory_ratios = [int(item["provided_qty"]) / int(item["required_quantity"]) for item in
    #                                     data["E-KIT"]]
    #                 mean_ecategory_no_numpy = calculate_mean(ecategory_ratios)
    #             if "M-KIT" in data:
    #                 if any(part['provided_qty'] > invent_data[part['cmpt_id']]['qty'] for part in data['M-KIT']):
    #                     return {"statusCode": 400, "body": "Quantity of part cannot be more than inventory quantity"}

    #                 m_kit_number = max(int(key.replace("M-KIT", "")) for key in result['all_attributes'].keys() if
    #                                    re.match(m_pattern, key))
    #                 m_kit_key = f'M-KIT{m_kit_number + 1}'
    #                 all_attributes[m_kit_key] = {}
    #                 documents = data['documents']
    #                 doc = {}
    #                 for inx, docs in enumerate(documents):
    #                     image_path = file_uploads.upload_file("BoxBuilding", "PtgCms" + env_type, "", "" + m_kit_key,
    #                                                           docs["doc_name"], docs['doc_body'])
    #                     doc[docs["doc_name"]] = image_path
    #                 all_attributes[m_kit_key]["documents"] = doc
    #                 for inx, value in enumerate(data['M-KIT']):
    #                     part_key = f"part{inx + 1}"
    #                     all_attributes[m_kit_key][part_key] = value
    #                     cmpt_id = all_attributes[m_kit_key][part_key]["cmpt_id"]
    #                     qty = str(
    #                         int(invent_data[cmpt_id]["qty"]) - int(all_attributes[m_kit_key][part_key]["provided_qty"]))
    #                     out_going_qty = str(int(invent_data[cmpt_id].get("out_going_qty", "0")) + int(
    #                         all_attributes[m_kit_key][part_key]["provided_qty"]))
    #                     db_con.Inventory.update_one(
    #                         {"pk_id": cmpt_id},
    #                         {"$set": {"all_attributes.qty": qty, "all_attributes.out_going_qty": out_going_qty}}
    #                     )
    #                 mcategory_ratios = [int(item["provided_qty"]) / int(item["required_quantity"]) for item in
    #                                     data["mcategoryInfo"]]
    #                 mean_mcategory_no_numpy = calculate_mean(mcategory_ratios)
    #             all_attributes["mtrl_prcnt"] = str(
    #                 (float(all_attributes["mtrl_prcnt"]) + float(str(((mean_ecategory_no_numpy) * 100) / 2)[:5])))
    #             db_con.EMS.update_one(
    #                 {"pk_id": result['pk_id']},
    #                 {"$set": {"all_attributes": all_attributes}}
    #             )
    #             db_con['ActivityDetails'].insert_one(
    #                 {
    #                     "pk_id": f"ACTID{activity_id}",
    #                     "sk_timeStamp": sk_timeStamp,
    #                     "all_attributes": activity,
    #                     "gsipk_table": "ActivityDetails",
    #                     "gsisk_id": data['outward_id'],
    #                     "lsi_key": "Utilized",
    #                     "gsipk_id": "EMS"
    #                 })
    #             db_con.all_tables.update_one(
    #                 {"pk_id": "top_ids"},
    #                 {"$set": {"all_attributes.ActivityId": activity_id}}
    #             )
    #             return {'statusCode': 200, 'body': 'Record updated successfully'}
    #         else:
    #             return {'statusCode': 200, 'body': 'Stock not inwarded for this bom'}
    #     else:
    #         return {'statusCode': 400, 'body': 'No record found for given outward id'}


        
    # def CmsEmsSendBalanceKitCreate(request_body):
    #     # print(data)
    #     data = request_body
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     result = list(db_con.EMS.find({"all_attributes.outward_id":data['outward_id']},{"pk_id":1,"sk_timeStamp":1,"all_attributes":1}))
    #     activity = {}
    #     sk_timeStamp = (datetime.now()).isoformat()
    #     if result:
    #         bom_id = result[0]['all_attributes']['bom_id']
    #         part_batch_info = find_stock_inwards(bom_id,db_con,'E_parts')
    #         part_batch_info = part_batch_info['part_batch_info']
    #         if part_batch_info:
    #             result = result[0]
    #             all_attributes = result['all_attributes']
    #             ekitInfo = get_kit_and_boards_info(all_attributes,"EMS")
    #             e_pattern = r"^E-KIT\d+$"
    #             m_pattern = r"^M-KIT\d+$"
    #             activity_id = db_con.all_tables.find_one({"pk_id":"top_ids"},{"all_attributes.ActivityId":1})
    #             activity_id = int(activity_id['all_attributes'].get('ActivityId',"0"))+1
    #             mean_ecategory_no_numpy=0
    #             partner_name = db_con.Partners.find_one({"pk_id":data['partner_id']},{"all_attributes.partner_name":1})
    #             invent_data = list(db_con.Inventory.find({},{"all_attributes.cmpt_id":1,"all_attributes.qty":1,"all_attributes.out_going_qty":1}))
    #             invent_data = {item['all_attributes']['cmpt_id']:{"qty":item['all_attributes']['qty'],"out_going_qty":item['all_attributes'].get('out_going_qty','0')} for item in invent_data}
    #             if "E-KIT" in data:
    #                 if any(1 for part in data['E-KIT'] if int(part['provided_qty'])>int(invent_data[part['cmpt_id']]['qty'])):
    #                     return {"statusCode":400,"body":"Quantity of part cannot be more than inventory quantity"}
    #                 e_kit_number = max(int(key.replace("E-KIT","")) for key in result['all_attributes'].keys() if re.match(e_pattern,key))
    #                 e_kit_key = f'E-KIT{e_kit_number+1}'
    #                 all_attributes[e_kit_key] = {}
    #                 for inx, value in enumerate(data['E-KIT']):
    #                     part_key = f"part{inx+1}"
    #                     cmpt_id = value['cmpt_id']
    #                     batch_info = {inx:value for inx,value in enumerate(part_batch_info[value['cmpt_id']])}
    #                     qty=str(int(invent_data[cmpt_id]["qty"])-int(value["provided_qty"]))
    #                     var = batch_number_allocation(part_batch_info,int(value['provided_qty']),value['cmpt_id'],ekitInfo)
    #                     # return var
    #                     if var:
    #                         value['batch_no'] = var['batch_string']
    #                         activity[value['cmpt_id']] = {
    #                                 "mfr_prt_num": value.get("mfr_prt_num", "-"),
    #                                 "date":str(date.today()),
    #                                 "action":"Utilized",
    #                                 "Description":"Utilized",
    #                                 "issued_to":partner_name['all_attributes']['partner_name'],
    #                                 "po_no":var['po_id'],
    #                                 'invoice_no':var["invoice_no"],
    #                                 "cmpt_id": value.get("cmpt_id", ""),
    #                                 "ctgr_id": value.get("ctgr_id", ""),
    #                                 "prdt_name": value.get("prdt_name", ""),
    #                                 "description": value.get("description", ""),
    #                                 "packaging": value.get("packaging", ""),
    #                                 "inventory_position": value.get("inventory_position", ""),
    #                                 "closing_qty": f"{qty}",
    #                                 "qty": value['provided_qty'],
    #                                 "batchId": var['batch_string'],
    #                                 "used_qty":value['provided_qty'],
    #                                 "lot_no":var["lot_no"]
    #                             }
    #                     else:
    #                         return None
    #                     all_attributes[e_kit_key][part_key] = value
    #                     cmpt_id=all_attributes[e_kit_key][part_key]["cmpt_id"]
    #                     qty=str(int(invent_data[cmpt_id]["qty"])-int(all_attributes[e_kit_key][part_key]["provided_qty"]))
    #                     out_going_qty = str(int(invent_data[cmpt_id].get("out_going_qty","0"))+int(all_attributes[e_kit_key][part_key]["provided_qty"]))
    #                     resp = db_con.Inventory.update_one(
    #                             {"pk_id": cmpt_id},
    #                             {"$set": {"all_attributes.qty" : qty,"all_attributes.out_going_qty":out_going_qty}}
    #                         )
    #                 ecategory_ratios = [int(item["provided_qty"]) / int(item["required_quantity"]) for item in data["E-KIT"]]
    #                 mean_ecategory_no_numpy = calculate_mean(ecategory_ratios)
    #             if "M-KIT" in data:
    #                 if any(1 for part in data['M-KIT'] if part['provided_qty']>invent_data[part['cmpt_id']]['qty']):
    #                     return {"statusCode":400,"body":"Quantity of part cannot be more than inventory quantity"}
    #                 m_kit_number = max(int(key.replace("M-KIT","")) for key in result['all_attributes'].keys() if re.match(m_pattern,key))
    #                 m_kit_key = f'M-KIT{m_kit_number+1}'
    #                 all_attributes[m_kit_key] = {}
    #                 for inx, value in enumerate(data['M-KIT']):
    #                     part_key = f"part{inx+1}"
    #                     all_attributes[m_kit_key][part_key] = value
    #                     cmpt_id=all_attributes[e_kit_key][part_key]["cmpt_id"]
    #                     qty=str(int(invent_data[cmpt_id]["qty"])-int(all_attributes[e_kit_key][part_key]["provided_qty"]))
    #                     out_going_qty = str(int(invent_data[cmpt_id].get("out_going_qty","0"))+int(all_attributes[e_kit_key][part_key]["provided_qty"]))
    #                     resp = db_con.Inventory.update_one(
    #                             {"pk_id": cmpt_id},
    #                             {"$set": {"all_attributes.qty" : qty,"all_attributes.out_going_qty":out_going_qty}}
    #                     )
    #                 mcategory_ratios = [int(item["provided_qty"]) / int(item["required_quantity"]) for item in data["mcategoryInfo"]]
    #                 mean_mcategory_no_numpy = calculate_mean(mcategory_ratios)
    #             all_attributes["mtrl_prcnt"]= str((float(all_attributes["mtrl_prcnt"])+float(str(((mean_ecategory_no_numpy)*100)/2)[:5])))
    #             update_item = db_con.EMS.update_one(
    #                     {"pk_id": result['pk_id']},
    #                     {"$set": {"all_attributes" : all_attributes}}
    #             )
    #             res = db_con['ActivityDetails'].insert_one(
    #                 {
    #                     "pk_id":f"ACTID{activity_id}",
    #                     "sk_timeStamp": sk_timeStamp,
    #                     "all_attributes": activity,
    #                     "gsipk_table": "ActivityDetails",
    #                     "gsisk_id": data['outward_id'],
    #                     "lsi_key": "Utilized",
    #                     "gsipk_id":"EMS"
    #                 })
    #             db_con.all_tables.update_one(
    #                 {"pk_id": "top_ids"},
    #                 {"$set": {"all_attributes.ActivityId" : activity_id}}
    #             )
    #             return {'statusCode': 200,'body': 'Record updated successfully'}
    #         else:
    #             return {'statusCode': 200,'body': 'Stock not inwarded for this bom'}
    #     else:
    #         return {'statusCode': 400,'body': 'No record found for given outward id'}
    
    def cmsFinalProductCreateInPartners(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            documents = data.get('documents', [])
            doc = {}
            for idx, docs in enumerate(documents):
                image_path = file_uploads.upload_file("FinalProduct", "PtgCms" + env_type, "",
                                                      "doc" + str(idx + 1),
                                                      docs["doc_name"], docs['doc_body'])
                doc[docs["doc_name"]] = image_path
            if data['kits']==[]:
                return {"statusCode":400,"body":"not allowed to upload empty file"}
            if any(1 for item in data['kits'] if not item['PCBA_ID'].strip() or not item['Product_ID'].strip() or not item["ALS_ID"].strip() or not item['Display_Number'].strip() or not item['SOM_ID_IMEI_ID'].strip() or not item['E-SIM_NO'].strip() or not item['E-SIM_ID'].strip()):
                return {"statusCode":400,"body":"Data missing/incorrect check excel and try again"}
            unit_no = [product['Product_ID'] for product in data['kits']]
            if len(set(unit_no))<len(unit_no):
                return {"statusCode":400,"body":"unit no should be unique"}
            result = list(db_con.FinalProduct.find({"gsisk_id":data['outward_id']}))
            result1 = list(db_con.FinalProduct.find({},{"_id":0}))
            max_kit_id='1'
            if result:
                final_product_quantity=result[0]['all_attributes']['quantity']
                result = result[0]
                max_kit_id = result['all_attributes']['max_kit_id']
                max_product_id = result['all_attributes']['max_product_id']
                all_attributes = result['all_attributes']
                duplicate_unit_no = []
                unit_nos_to_check = [i['Product_ID'].strip().lower() for i in data['kits']]
                for unit_no_to_check in unit_nos_to_check:
                    if any('Product_ID' in product and product['Product_ID'].strip().lower() == unit_no_to_check for kit in all_attributes['kits'].values() for product in kit.values()):
                        duplicate_unit_no.append(unit_no_to_check)
                
                if duplicate_unit_no:
                    return {'statusCode': 400, 'body': f"Duplicates are repeating: {', '.join(duplicate_unit_no)}"}
        
        
                
                max_kit_id = int(all_attributes['max_kit_id']) + 1
                max_product_id = int(all_attributes['max_product_id']) 
                all_attributes['kits'].update({
                    f"Final_product_batch{max_kit_id}": {
                        "status": "Unassigned",
                        **{f"product{max_product_id+inx+1}": {
                            "final_product_kit_id": f"final_product_kit{max_kit_id}",
                            "pcba_id": item['PCBA_ID'],
                            "product_id": item['Product_ID'],
                            "als_id": item['ALS_ID'],
                            "display_number": item['Display_Number'],
                            "som_id_imei_id": item['SOM_ID_IMEI_ID'],
                            "e_sim_id": item['E-SIM_ID'],
                            "e_sim_no": item['E-SIM_NO'],
                            "date_of_ems": item['Date_Of_EMS'],
                            "ict": item['ICT'],
                            "fct": item['FCT'],
                            "eol": item['EOL'],
                            "date_of_eol": item['Date_Of_EOL'],
                            # "eol_document": item['EOL_Document'],
                            "product_status": "Rejected" if any(value.lower() == 'na' for value in item.values()) else "EOL",
                            
                        } for inx, item in enumerate(data['kits'])}
                    }
                })
                if 'document' in all_attributes:
                    all_attributes['document'].update(doc)
                else:
                    all_attributes['document'] = doc
                all_attributes['max_kit_id'] = f"{max_kit_id}"
                all_attributes['max_product_id'] = f"{max_product_id+ len(data['kits'])}"
                max_product_id_qty = int(all_attributes['max_product_id'])
                print(all_attributes['max_product_id'])
                print(len(data['kits']))
                print(max_product_id_qty)
                print(final_product_quantity)
                if int(max_product_id_qty)>int(final_product_quantity):
                    return {'statusCode': 400, 'body': "you cannot upload boards more than what is ordered"}
                resp = db_con.FinalProduct.update_one(
                    {"pk_id": result['pk_id']},
                    {"$set": {"all_attributes": all_attributes}}
                )
                return {'statusCode': 200,'body': 'Record updated successfully'}
            else:
                max_product_id_qty = len(data['kits'])
                final_product_quantity=data['qty']
                # print(max_product_id_qty)
                # print(final_product_quantity)
                if int(max_product_id_qty)>int(final_product_quantity):
                    return {'statusCode': 400, 'body': "you cannot upload boards more than what is ordered"}
                sk_timeStamp = (datetime.now()).isoformat()
                all_attributes = {}
                all_attributes['bom_id'] = data['bom_id']
                all_attributes['outward_id'] = data['outward_id']
                all_attributes['orderId'] = data['OrderId']
                all_attributes['max_kit_id'] = '1'
                all_attributes['max_product_id'] = len(data['kits'])
                all_attributes['order_date'] = ""
                all_attributes['status'] = ""
                all_attributes['quantity'] = data['qty']
                all_attributes['documents']=doc
                all_attributes['document'] = data['documents']
                all_attributes['receiver_name'] = data['receiver_name']
                all_attributes['against_po'] = data.get('against_po','')
                all_attributes['delivery_end_date'] = data['delivery_end_date']
                all_attributes['sender_name'] = data['sender_name']
                all_attributes['receiver_contact'] = data['receiver_contact']
                all_attributes['sender_name'] = data['sender_name']
                all_attributes['kits']={
                f"Final_product_batch{max_kit_id}": {
                    "status": "Unassigned",
                        **{f"product{inx+1}": {
                            "final_product_kit_id": f"final_product_kit{max_kit_id}",
                            "pcba_id": item['PCBA_ID'],
                            "product_id": item['Product_ID'],
                            "als_id": item['ALS_ID'],
                            "display_number": item['Display_Number'],
                            "som_id_imei_id": item['SOM_ID_IMEI_ID'],
                            "e_sim_id": item['E-SIM_ID'],
                            "e_sim_no": item['E-SIM_NO'],
                            "date_of_ems": item['Date_Of_EMS'],
                            "ict": item['ICT'],
                            "fct": item['FCT'],
                            "eol": item['EOL'],
                            "date_of_eol": item['Date_Of_EOL'],
                            # "eol_document": item['EOL_Document'],
                            "product_status": "Rejected" if any(value.lower() == 'na' for value in item.values()) else "EOL",
                            
                        } for inx, item in enumerate(data['kits'])}
                    }
                }
                item = {
                    "pk_id":data['outward_id']+"_FP",
                    "sk_timeStamp": sk_timeStamp,
                    "all_attributes": all_attributes,
                    "gsisk_id":data['outward_id'] ,
                    "lsi_key": data["bom_id"] 
                }
                resp = db_con.FinalProduct.insert_one(item)
            return {'statusCode': 200,'body': "Data saved successfully"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Internal server error'}
        
    def cmsGetFinalProductDoc(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            outward_id = data['outward_id']
            res = db_con.FinalProduct.find({'all_attributes.outward_id': outward_id})
            doc = []
            for i in res:
                documents = i.get('all_attributes', {}).get('document',{})
                if isinstance(documents, dict):
                    for k, v in documents.items():
                        doc.append({"name": k, "url": v})
            return {'statusCode': 200, 'body':doc}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Internal server error'}
        
    # def cmsGetFinalProductInPartners(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         print(data)
    #         env_type = data['env_type']
    #         result = list(db_con.FinalProduct.find({"gsisk_id":data['outward_id']}))
    #         if result:
    #             response = []
    #             for transformed_item in result:
    #                 sorted_final_batches = {}
    #                 for batch_key, products in sorted(transformed_item["kits"].items(), key=lambda item: int(item[0].split("Final_product_batch")[1])):
    #                     sorted_final_batches[batch_key] = products
    #                 transformed_item["kits"] = sorted_final_batches
    #                 response.append(transformed_item)
    #             return {'statusCode': 200, 'body': response[0]['kits']}
    #         else:
    #             return {'statusCode': 404, 'body': 'no data available for this outward_id'}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request(check data)'}
    
    def cmsGetFinalProductInPartners(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            print(data)
            product_status=data['product_status']
            env_type = data['env_type']
            result = list(db_con.FinalProduct.find({"gsisk_id":data['outward_id']},{"all_attributes.kits":1}))
            if result:
                response = []
                for transformed_item in result:
                    if data['product_status']=="All":
                        sorted_final_batches = {}
                        for batch_key, products in sorted(transformed_item['all_attributes']["kits"].items(), key=lambda item: int(item[0].split("Final_product_batch")[1])):
                            sorted_final_batches[batch_key] = products
                        transformed_item["kits"] = sorted_final_batches
                        response.append(transformed_item)
                        return {'statusCode': 200, 'body': response[0]['kits']}
                    elif data['product_status'] == product_status:
                        sorted_final_batches = {}
                        response = []
                        for batch_key, products in sorted(transformed_item['all_attributes']["kits"].items(), key=lambda item: int(item[0].split("Final_product_batch")[1])):
                            sorted_products = {}
                            for product_id, product in products.items():
                                if isinstance(product, dict) and product.get('product_status') == product_status:
                                    sorted_products[product_id] = product
                            if sorted_products:
                                sorted_final_batches[batch_key] = sorted_products

                        transformed_item["kits"] = sorted_final_batches
                        response.append(transformed_item)

                        return {'statusCode': 200, 'body': response[0]['kits']}
            else:
                return {'statusCode': 404, 'body': 'no data available for this outward_id'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}
    
    def cmsCreateClientInBom(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            env_type=data['env_type']
            gsipk_table='ClientAssign'
            outward_id=data['outward_id']
            result = list(db_con.ClientAssign.find({"gsisk_id":outward_id}))
            result1 = list(db_con.FinalProduct.find({"gsisk_id":data['outward_id']}))
            bom_id=result1[0]['all_attributes']['bom_id']
            common_batches2= dict(
                    (
                        batch_id,
                        {
                            k: v if k != 'status' else 'Assigned'
                            for k, v in result1[0]['all_attributes']['kits'][batch_id].items()
                        }
                    )
                    for batch_id in data['kits'].keys()
                    if batch_id in result1[0]['all_attributes']['kits']
                )
            all_attributes1=result1[0]['all_attributes']
            if result:
                result=result[0]
                all_attributes=result['all_attributes']
                all_attributes['kits'].update(common_batches2)
                resp = db_con.ClientAssign.update_one(
                            {"pk_id": result['pk_id']},
                            {"$set": {"all_attributes": all_attributes}}
                        )
                result1=result1[0]
                all_attributes1=result1['all_attributes']
                all_attributes1['kits'].update(common_batches2)
                resp = db_con.FinalProduct.update_one(
                            {"pk_id": result['pk_id']},
                            {"$set": {"all_attributes": all_attributes}}
                        )
                return {'statusCode': 200,'body': 'Record updated successfully'}
            else:
                sk_timeStamp = (datetime.now()).isoformat()
                all_attributes = {}
                all_attributes['bom_id'] = result1[0]['all_attributes']['bom_id']
                all_attributes['outward_id'] = data['outward_id']
                all_attributes['orderId'] = result1[0]['all_attributes']['orderId']
                all_attributes['order_date'] = ""
                all_attributes['status'] = ""
                all_attributes['quantity'] = result1[0]['all_attributes']['quantity']
                all_attributes['receiver_name'] = result1[0]['all_attributes']['receiver_name']
                all_attributes['against_po'] = data['against_po']
                all_attributes['delivery_end_date'] = data['ded']
                all_attributes['sender_name'] = result1[0]['all_attributes']['sender_name']
                all_attributes['receiver_contact'] = result1[0]['all_attributes']['receiver_contact']
                all_attributes['sender_name'] = result1[0]['all_attributes']['sender_name']
                all_attributes['kits']=common_batches2
                all_attributes1['kits'].update(common_batches2)
                resp = db_con.FinalProduct.update_one(
                            {"pk_id": result1[0]['pk_id']},
                            {"$set": {"all_attributes": all_attributes}}
                        )
                print(all_attributes1)
                item = {
                    "pk_id":data['outward_id']+"_AC",
                    "sk_timeStamp": sk_timeStamp,
                    "all_attributes": all_attributes,
                    "gsipk_table":gsipk_table,
                    "gsisk_id":data['outward_id']
                }
                response = db_con.ClientAssign.insert_one(item)
            return {'statusCode': 200,'body': "Data saved successfully for client"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request(check data)'}
        
    def cmsGetAgainstPo(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            result = list(db_con.Clients.find({},{"all_attributes.orders":1}))
            if result:
                matching_po_ids = {'po_id':k['po_id'] for i in result for j, k in i['all_attributes']['orders'].items() if k['bom_id'] == data['bom_id']}
                if matching_po_ids:
                    return {'statusCode':200,'body':matching_po_ids}
                else:
                    return {'statusCode':200,'body':"NO Data"}
            else:
                return {'statusCode':200,'body':"No Data"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request'}

    def cmsAssignToEMSGetPartnersID(request_body):
        try:
            # print(data) 
            response = []
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            partner_type=data["partner_type"]
            result = list(db_con.Partners.find({"gsipk_id":partner_type},{"all_attributes.partner_id":1,"all_attributes.partner_name":1}))
            result = [{"partner_id":item['all_attributes']['partner_id'],"partner_name":item['all_attributes']['partner_name']} for item in result]
            return {"statusCode": 200, "body": result}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request(check data)'}
        

    
    def cmsUpdateSaveEMSDoc(request_body):
        data = request_body
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        outward_id = data["outward_id"]
        event_key = data["event_key"]
        # deta_type = data["deta_type"]
        partner_id = data["partner_id"]
        bom_id = data["bom_id"]

        # Query the database to find the EMS document with the specified outward_id
        result = db_con.EMS.find_one({"pk_id": outward_id, "lsi_key": bom_id, "all_attributes.partner_id": partner_id}, {"_id": 0, "all_attributes": 1})

        if result:
            all_attributes = result['all_attributes']
            document_uploaded = False

            # Process the file uploads based on the event_key
            for upload_type in ["gateentry", "qatest", "inward"]:
                if upload_type in data and data[upload_type].get('doc_body') and data[upload_type].get('doc_name'):
                    doc_name = data[upload_type]["doc_name"]
                    doc_body = data[upload_type]["doc_body"]

                    # Check if the document has already been uploaded
                    if event_key in all_attributes and upload_type in all_attributes[event_key] and "doc_name" in all_attributes[event_key][upload_type]:
                        continue  # Skip if the document is already uploaded
                    else:
                        file_key = file_uploads.upload_file("EMS", f"PtgCms{env_type}", "", f"{event_key}_{upload_type}", doc_name, doc_body)
                        
                        # Update the EMS document with the file information
                        if event_key not in all_attributes:
                            all_attributes[event_key] = {}
                        if upload_type not in all_attributes[event_key]:
                            all_attributes[event_key][upload_type] = {}
                        all_attributes[event_key][upload_type]["doc_name"] = file_key
                        document_uploaded = True

            if document_uploaded:
                # Update the EMS document in the database
                db_con.EMS.update_one(
                    {"pk_id": outward_id},
                    {"$set": {"all_attributes": all_attributes}}
                )
                return {'statusCode': 200, 'body': "document upload successfully"}
            else:
                return {'statusCode': 400, 'body': "Already documents uploaded"}

        else:
            result1 = db_con.BoxBuilding.find_one({ "gsisk_id": bom_id, "all_attributes.outward_id": outward_id, "all_attributes.partner_id": partner_id}, {"_id": 0, "all_attributes": 1})
            
            if result1:
                all_attributes = result1['all_attributes']
                document_uploaded = False

                # Process the file uploads based on the event_key
                for upload_type in ["gateentry", "qatest", "inward"]:
                    if upload_type in data and data[upload_type].get('doc_body') and data[upload_type].get('doc_name'):
                        doc_name = data[upload_type]["doc_name"]
                        doc_body = data[upload_type]["doc_body"]

                        # Check if the document has already been uploaded
                        if event_key in all_attributes and upload_type in all_attributes[event_key] and "doc_name" in all_attributes[event_key][upload_type]:
                            continue  # Skip if the document is already uploaded
                        else:
                            file_key = file_uploads.upload_file("BoxBuilding", f"PtgCms{env_type}", "", f"{event_key}_{upload_type}", doc_name, doc_body)

                            # Update the EMS document with the file information
                            if event_key not in all_attributes:
                                all_attributes[event_key] = {}
                            if upload_type not in all_attributes[event_key]:
                                all_attributes[event_key][upload_type] = {}
                            all_attributes[event_key][upload_type]["doc_name"] = file_key
                            document_uploaded = True

                if document_uploaded:
                    # Update the EMS document in the BoxBuilding collection
                    db_con.BoxBuilding.update_one(
                        { "gsisk_id": bom_id, "all_attributes.outward_id": outward_id, "all_attributes.partner_id": partner_id},
                        {"$set": {"all_attributes": all_attributes}}
                    )
                    return {'statusCode': 200, 'body': "document upload successfully"}
                else:
                    return {'statusCode': 400, 'body': "Already documents uploaded"}

            return {'statusCode': 404, 'body': "EMS document not found"}
        
    
    def cmsGetEmsUploadDocs(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            event_key = data["event_key"]
            pk_id = data["outward_id"]
            bom_id = data["bom_id"]
            partner_id = data['partner_id']
            
            # Define a function to extract document names
            def extract_doc_name(doc_url):
                return doc_url.split('/')[-1]

            # Function to process results and extract data
            def process_results(result):
                all_attributes = result[0]['all_attributes']
                event_data = all_attributes.get(event_key)
                if event_data is None:
                    return {'statusCode': 404, 'body': f'Event key {event_key} not found in document'}
                
                extracted_data = {}
                for field in ["gateentry", "qatest", "inward"]:
                    if field in event_data:
                        doc_url = event_data[field].get("doc_name", "")
                        doc_name = extract_doc_name(doc_url)
                        extracted_data[field] = {
                            "doc_url": doc_url,
                            "doc_name": doc_name
                        }
                return {'statusCode': 200, 'body': extracted_data}

            # Query the EMS collection
            result = list(db_con.EMS.find({"pk_id": pk_id, "lsi_key": bom_id, "all_attributes.partner_id": partner_id}, {"_id": 0, "all_attributes": 1}))
            if result:
                return process_results(result)
            
            # Query the BoxBuilding collection if no results in EMS
            result = list(db_con.BoxBuilding.find({"gsisk_id": bom_id, "all_attributes.outward_id": pk_id, "all_attributes.partner_id": partner_id}, {"_id": 0, "all_attributes": 1}))
            if result:
                return process_results(result)
            
            # No documents found in either collection
            return {'statusCode': 404, 'body': 'No documents found'}
        
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            error_message = f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}"
            print(error_message)
            return {'statusCode': 400, 'body': error_message}

    def cmsClientAgainstPO(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            # client_id = data['client_id']
            # client_name = data['client_name']
            bom_id = data["bom_id"]
            res = db_con.Clients.find()
            for item in res:
                all_attributes = item.get('all_attributes', {})
                client_id = all_attributes.get('client_id')
                client_name = all_attributes.get('client_name')
                order = all_attributes.get('orders', {})
                if order:
                    for po_key, po_details in order.items():
                        if po_details.get('bom_id') == bom_id:
                            against_po = po_details.get('po_id')
                            return {'statusCode':200, 'body' :{
                                'client_id': client_id,
                                'client_name': client_name,
                                'against_po': against_po
                            }}
            return {'statusCode': 404, 'body': 'Update Client PO for BOM'}
            # result = db_con.Clients.find_one({'all_attributes.client_id': client_id, 'all_attributes.client_name': client_name})
            # orders =  result.get('all_attributes', {}).get('orders', {})
            # po_ids = po_ids = [{'po_id': v['po_id']} for v in orders.values() if 'po_id' in v]
            # return {'statusCode': 200, 'body': po_ids}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': f'Bad Request (check data)'}


    def cmsBomFinalProductFilter(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            res = db_con.FinalProduct.find_one({'all_attributes.outward_id': data['outward_id']})
            kits = res.get('all_attributes', {}).get('kits', {})

            for batch_name, kit_content in kits.items():
                if isinstance(kit_content, dict):
                    for product_name, product_details in kit_content.items():
                        if isinstance(product_details, dict):
                            product_details['select_check'] = (product_details.get('product_status') == 'Product Ready')

            # Filter the result to only includle batches with at least one product having filter_save_status set to True
            filtered_result = {}
            for batch_name, kit_content in kits.items():
                if isinstance(kit_content, dict):
                    filtered_products = {
                        product_name: product_details
                        for product_name, product_details in kit_content.items()
                        if isinstance(product_details, dict) and product_details.get('filter_save_status')
                    }
                    if filtered_products:
                        filtered_result[batch_name] = filtered_products

            if data['status'] == 'All':
                return {'statusCode': 200, 'body': filtered_result}
            else:
                status_filtered_result = {}
                for batch_name, kit_content in filtered_result.items():
                    status_filtered_result[batch_name] = {
                        product_name: product_details
                        for product_name, product_details in kit_content.items()
                        if product_details.get('product_status') == data['status']
                    }
                    status_filtered_result = {batch: products for batch, products in status_filtered_result.items() if products}

                return {'statusCode': 200, 'body': status_filtered_result}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check data)'}



    # def cmsBomFinalProductFilter(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         res = db_con.FinalProduct.find_one({'all_attributes.outward_id': data['outward_id']})
    #         kits = res.get('all_attributes', {}).get('kits', {})
    #         for batch_name, kit_content in kits.items():
    #             if isinstance(kit_content, dict):
    #                 for product_name, product_details in kit_content.items():
    #                     if isinstance(product_details, dict):
    #                         product_details['select_check'] = (product_details.get('product_status') == 'Product Ready')
    #         # result = [
    #         #     product_details
    #         #     for kit_content in kits.values()
    #         #     if isinstance(kit_content, dict)
    #         #     for product_details in kit_content.values()
    #         #     if isinstance(product_details, dict) and product_details.get('status') == data['status']
    #         # ]
    #         # print(result)
    #         if data['status'] == 'All':
    #             return {'statusCode': 200, 'body': kits}
    #         else:
    #             result = {}
    #             for batch_name, kit_content in kits.items():
    #                 result[batch_name] = {}
    #                 if isinstance(kit_content, dict):
    #                     for product_name, product_details in kit_content.items():
    #                         if isinstance(product_details, dict) and product_details.get('product_status') == data['status']:
    #                             result[batch_name][product_name] = product_details
    #             result = {batch: products for batch, products in result.items() if products}
    #             return {'statusCode': 200, 'body': result}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}
    def FinalProductInternalFilterSave(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            res = list(db_con.FinalProduct.find({'all_attributes.outward_id': data['outward_id']},{'_id':0,'all_attributes':1,'pk_id':1,'sk_timeStamp':1}))
            product_ids_to_update = [board['product_id'] for board in data['product_information']]
            if res:   
                for item in res:
                    for kit, boards in item['all_attributes']['kits'].items():
                        for attributes in boards.values():
                            if isinstance(attributes, dict):
                                if attributes.get('product_id') in product_ids_to_update:
                                    attributes['filter_save_status'] = True
                                    for event_board in data['product_information']:
                                        if event_board['product_id'] == attributes.get('product_id'):
                                            attributes['comment']=event_board['comment']
                                            attributes.update((k.lower(), v) for k, v in event_board.items() if k.lower() in attributes)
                    
                    filter_query = {
                        "pk_id": item["pk_id"],
                        "sk_timeStamp": item["sk_timeStamp"]
                    }
                    update_query = {
                        "$set": {
                            "all_attributes": item['all_attributes']
                        }
                    }
                    db_con.FinalProduct.update_one(filter_query, update_query)
                return {'statusCode': 200, 'body': "filtered boards Saved successfully "}
            else:
                return {'statusCode':400,'body':'No data available'}    
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check data)'}
        
    def FinalProductReuploadOfProducts(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            res = list(db_con.FinalProduct.find({'all_attributes.outward_id': data['outward_id']},{'_id':0,'all_attributes':1,'pk_id':1,'sk_timeStamp':1}))
            if res:
                result = res[0]
                boards_filter = {kit['product_id']: kit for kit in data['product_information']}
                boards_filter = list(boards_filter.values())
                error_messages = []
                pcba_ids_matched=[]
                match_found = False
                if 'kit_id' in data:
                    for event_board in data['product_information']:
                        pcba_id_to_match = event_board["product_id"]
                        pcba_ids_to_update = [event_board["product_id"] for event_board in data['product_information']]
                        existing_pcba_ids = [attributes.get('product_id') for boards in result['all_attributes']['kits'].values() for attributes in boards.values() if isinstance(attributes, dict)]
                        unmatched_pcba_ids = [pcba_id for pcba_id in pcba_ids_to_update if pcba_id not in existing_pcba_ids]
                        if unmatched_pcba_ids:
                            return {'statusCode': 400, 'body': f"The following PCBA IDs do not match existing data: {', '.join(unmatched_pcba_ids)}. New PCBA IDs cannot be uploaded."}
                        for kit, boards in result['all_attributes']['kits'].items():
                            for board, attributes in boards.items():
                                if isinstance(attributes,dict):
                                    if attributes['product_id'] == pcba_id_to_match:
                                        if attributes['product_status'] == 'Rejected':
                                            if any(item.lower() == 'na' for inx, value in enumerate(boards_filter) for item in value.values()):
                                                for board_info in data['product_information']:
                                                    board_info['product_status'] = 'Rejected' if any(value.lower() == 'na' for value in board_info.values()) else 'EOL'
                                                    match_found = True
                                                if match_found:
                                                    attributes.update((k.lower(), v) for k, v in event_board.items() if k.lower() in attributes)
                                                # print(attributes)
                                            else:
                                                # print('pooja')
                                                attributes['product_status'] = 'EOL'
                                                attributes.update((k.lower(), v) for k, v in event_board.items() if k.lower() in attributes)
                                                match_found = True
                                                # print(attributes)
                                        elif attributes['product_status'] == 'EOL':
                                            error_messages.append(f"We cannot update boards with {pcba_id_to_match} which are already EMS_done")
                                            return {'statusCode': 400, 'body': error_messages[0]}
                    # print(match_found)
                    if match_found:
                        filter_query = {
                            "pk_id": result["pk_id"],
                            "sk_timeStamp": result["sk_timeStamp"]
                        }

                        update_query = {
                            "$set": {
                                "all_attributes": result["all_attributes"]
                            }
                        }

                        db_con.FinalProduct.update_one(filter_query, update_query)
                        return {'statusCode': 200, 'body': "Updated successfully"}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check data)'}