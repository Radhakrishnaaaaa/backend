import json
from datetime import datetime, timedelta
import base64
from db_connection import db_connection_manage
import sys
import os
import re

conct = db_connection_manage()
def file_get(path):
    # def get_file_single_image(path):
    return path#base64_data

class PurchaseReturn():
    def cmsPurchaseReturnGetOrderId(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            #print(data)
            # databaseTableName = "PtgCms"+data["env_type"]
            # gsipk_table="PurchaseOrder"
            # dynamodb = boto3.client('dynamodb')
            # statement = f"""select pk_id from {databaseTableName} where  gsipk_table = '{gsipk_table}'"""
            # qaData = execute_statement_with_pagination(statement)
            # sorted_pk_ids1 = extract_items_from_array_of_nested_dict(qaData)
            sorted_pk_ids1 = list(db_con.PurchaseOrder.find({}))
            if sorted_pk_ids1:
                sorted_pk_ids = sorted([item["pk_id"] for item in sorted_pk_ids1], reverse=True)
                sorted_pk_ids2 = sorted(sorted_pk_ids, key=lambda x: int(x.replace("OPTG", "")), reverse=False)
                conct.close_connection(client)
                return {"statusCode": 200, "body": sorted_pk_ids2}
            else:
                conct.close_connection(client)
                return {"statusCode": 404, "body": "No Data"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsPurchaseReturnGetInwardId(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            inwardId = data['po_order_id']
            qaData = list(db_con.QATest.find({"all_attributes.po_id": inwardId},
                                             {"all_attributes.inwardId": 1, "all_attributes.parts": 1}))
            if qaData:
                a = [item['all_attributes']['inwardId'] for item in qaData if
                     any(int(k['fail_qty']) > 0 for j, k in item['all_attributes']['parts'].items())]
                #print(a)
                sorted_pk_ids2 = sorted(a, key=lambda x: int(x.split('_')[1][2:]))
                conct.close_connection(client)
                return {"statusCode": 200, "body": sorted_pk_ids2}
            else:
                conct.close_connection(client)
                return {"statusCode": 404, "body": "No Data"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsGetComponentDetailsInsidePurchaseReturnModified(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            #print(data)
            # databaseTableName = "PtgCms"+data["env_type"]             # gsipk_table="QATest"
            po_id = data['po_order_id']
            inwardId = data['inwardId']
            # dynamodb = boto3.client('dynamodb')
            # statement = f"""select * from {databaseTableName} where  gsipk_table = '{gsipk_table}' and all_attributes.inwardId='{inwardId}' and all_attributes.po_id='{po_id}' """
            # qaData = execute_statement_with_pagination(statement)
            sorted_pk_ids_list = list(
                db_con.QATest.find({"all_attributes.inwardId": inwardId, "all_attributes.po_id": po_id}))
            # sorted_pk_ids_list = [sorting_function(item) for item in qaData]
            # category_statement = f"""select gsisk_id,sub_categories,pk_id from {databaseTableName} where gsipk_table='Metadata' and gsipk_id='Electronic' """
            # category_data = execute_statement_with_pagination(category_statement)
            category_data = list(
                db_con.Metadata.find({"gsipk_id": "Electronic"}, {"gsisk_id": 1, "sub_categories": 1, "pk_id": 1}))
            category_data = {item['pk_id'].replace("MDID", "CTID"): {"ctgr_name": item['gsisk_id'],
                                                                     "sub_categories": item['sub_categories']} for item
                             in category_data}
            # inventory = f"select all_attributes.description,all_attributes.package,all_attributes.manufacturer,all_attributes.cmpt_id,all_attributes.prdt_name,all_attributes.sub_ctgr from {databaseTableName} where gsipk_table='Inventory'"
            # inventory = extract_items_from_array_of_nested_dict(execute_statement_with_pagination(inventory))
            inventory = list(db_con.Inventory.find({}, {"all_attributes.description": 1, "all_attributes.package": 1,
                                                        "all_attributes.manufacturer": 1, "all_attributes.cmpt_id": 1,
                                                        "all_attributes.prdt_name": 1, "all_attributes.sub_ctgr": 1}))
            inventory = {item['all_attributes']['cmpt_id']: item['all_attributes'] for item in inventory}
            # return category_data
            b = []
            if sorted_pk_ids_list:
                # return sorted_pk_ids_list
                filtered_list = [
                    {
                        "qa_date": item['all_attributes']["QA_date"] if "QA_date" in item['all_attributes'] else " ",
                        "sender_name": item['all_attributes']["sender_name"] if "sender_name" in item[
                            'all_attributes'] else "",
                        "sender_contact_number": item['all_attributes'][
                            "sender_contact_number"] if "sender_contact_number" in item['all_attributes'] else "",
                        # "invoice": file_get(item['all_attributes']["invoice"]) if "invoice" in item['all_attributes'] else "",
                        # "qa_test": file_get(item['all_attributes']["QATest"]) if "QATest" in item['all_attributes'] else "",
                        "invoice": item["all_attributes"]["invoice"] if "invoice" in item["all_attributes"] else "",
                        "qa_test": item["all_attributes"]["QATest"] if "QATest" in item["all_attributes"] else "",
                        # "photo": item['all_attributes']["photo"] if "photo" in item['all_attributes'] else "",

                        # "photo": {k:file_get(v)  for k, v in item['all_attributes']["photo"].items()} if "photo" in item['all_attributes'] else "",
                        "photo": item["all_attributes"].get("photo", {}),


                        "description": item['all_attributes']["description"] if "description" in item[
                            'all_attributes'] else "",
                        "parts": {
                            part_key: {
                                "cmpt_id": part_data['cmpt_id'],
                                "ctgr_id": part_data['ctgr_id'],
                                "price_per_piece": part_data['price_per_piece'],
                                "description": part_data['description'],
                                "packaging": part_data['packaging'],
                                "fail_qty": part_data['fail_qty'],
                                "batchId": part_data['batchId'],
                                "mfr_prt_num": part_data['mfr_prt_num'],
                                "manufacturer": part_data['manufacturer'],
                                "price": int(float(part_data['price_per_piece']) * float(part_data['fail_qty'])),
                                "pass_qty": part_data['pass_qty'],
                                "qty": part_data['qty'],
                                "department": part_data['department'],
                                "prdt_name": category_data[part_data['ctgr_id']]['sub_categories'][
                                    inventory[part_data['cmpt_id']]['sub_ctgr']] if part_data[
                                                                                        'department'] == 'Electronic' else
                                part_data['prdt_name']
                            }
                            for part_key, part_data in item['all_attributes']['parts'].items()
                            if int(part_data['fail_qty']) > 0

                        }
                    }
                    for item in sorted_pk_ids_list
                ]
                if filtered_list:
                    conct.close_connection(client)
                    return {"statusCode": 200, "body": filtered_list}
                else:
                    conct.close_connection(client)
                    return {"statusCode": 200, "body": "we cant return fail qty is zero"}

            else:
                conct.close_connection(client)
                return {"statusCode": 404, "body": "No Data"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def CmsPurchaseReturnCreateModified(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            all_attributes = {}
            po_id = data['order_id']
            gsipk_table = "PurchaseReturn"
            description = data['description']
            inward_id = data['inward_id']
            result1 = list(db_con.PurchaseOrder.find({"pk_id": po_id}))
            result3 = list(db_con.QATest.find({"all_attributes.inwardId": inward_id}))
            parts = result3[0]['all_attributes']['parts']
            matching_parts = {f"part{index + 1}": value for index, part in enumerate(data['parts']) for key, value in
                              parts.items() if value['mfr_prt_num'] == part['mfr_prt_num']}
            result = list(db_con.PurchaseReturn.find({"gsisk_id": po_id}))
            return_id = f"{data['order_id']}-R1"
            if result:
                if any(item['gsipk_id'] == data['inward_id'] for item in result):
                    return {'statusCode': 400, 'body': "Return already present for given inward id"}
                returnids = sorted([int(item["pk_id"].split("R")[-1]) for item in result], reverse=True)
                return_id = f"{data['order_id']}-R{returnids[0] + 1}"

            sk_timeStamp = (datetime.now()).isoformat()
            parts = {f"part{inx + 1}": value for inx, value in enumerate(data['parts'])}
            if result1:
                vendor_id = [i['all_attributes']['vendor_id'] for i in result1]
                #print(vendor_id)
                result2 = list(db_con.Vendor.find({"pk_id": vendor_id[0]}))
                #print(result2)
                if result2:
                    if parts:
                        all_attributes = {}
                        all_attributes['return_id'] = return_id
                        all_attributes['parts'] = parts
                        all_attributes['invoice'] = [i['all_attributes']['invoice'] for i in result3][0]
                        all_attributes['qa_test'] = [i['all_attributes']['QATest'] for i in result3][0]
                        all_attributes['photo'] = {i: j for i, j in result3[0]['all_attributes']['photo'].items()}
                        all_attributes['inward_id'] = inward_id
                        all_attributes['qa_date'] = [i['all_attributes']['QA_date'] for i in result3][0]
                        all_attributes['sender_name'] = [i['all_attributes']['sender_name'] for i in result3][0]
                        all_attributes['sender_contact_number'] = \
                        [i['all_attributes']['sender_contact_number'] for i in result3][0]
                        all_attributes['status'] = data['status']
                        all_attributes['description'] = description
                        all_attributes['vendor_id'] = [i['all_attributes']['vendor_id'] for i in result2][0]
                        all_attributes['vendor_name'] = [i['all_attributes']['vendor_name'] for i in result2][0]
                        all_attributes['bank_name'] = [i['all_attributes']['bank_name'] for i in result2][0]
                        all_attributes['account_number'] = [i['all_attributes']['account_number'] for i in result2][0]
                        all_attributes['gst_number'] = [i['all_attributes']['gst_number'] for i in result2][0]
                        all_attributes['ifsc_code'] = [i['all_attributes']['ifsc_code'] for i in result2][0]
                        all_attributes['address1'] = [i['all_attributes']['address1'] for i in result2][0]
                        all_attributes['email'] = [i['all_attributes']['email'] for i in result2][0]
                        all_attributes['contact_number'] = [i['all_attributes']['contact_number'] for i in result2][0]
                        all_attributes['order_date'] = [i['sk_timeStamp'] for i in result1][:10][0]
                        all_attributes['total_price'] = [i['all_attributes']['total_price'] for i in result1][0]
                        # return all_attributes
                        # all_attributes=create_nested_dict(all_attributes)
                        item = {
                            "pk_id": return_id,
                            "sk_timeStamp": sk_timeStamp,
                            "all_attributes": all_attributes,
                            "gsipk_table": gsipk_table,
                            "gsisk_id": data['order_id'],
                            "gsipk_id": data['inward_id'],
                            "lsi_key": "--"
                        }
                        updat = db_con.PurchaseReturn.insert_one(item)
                        for i, j in matching_parts.items():
                            cmpt_id = j['cmpt_id']
                            result4 = list(db_con.Inventory.find({"pk_id": cmpt_id}, {"all_attributes.rtn_qty": 1,
                                                                                      "all_attributes.cmpt_id": 1,
                                                                                      "pk_id": 1, "sk_timeStamp": 1}))
                            if result4:
                                inventory_item = result4[0]
                                if 'rtn_qty' in inventory_item:
                                    existing_qty = int(inventory_item['all_attributes']['rtn_qty'])
                                else:
                                    existing_qty = 0
                                new_fail_qty = int(j['fail_qty'])
                                total_qty = existing_qty + new_fail_qty
                                resp = db_con.Inventory.update_one(
                                    {"pk_id": inventory_item['pk_id']},
                                    {"$set": {"all_attributes.rtn_qty": str(total_qty)}}
                                )
                        try:
                            response = {
                                'statusCode': 200,
                                'body': 'Purchase Return added successfully'
                            }
                            return response

                        except Exception as err:
                            exc_type, exc_obj, tb = sys.exc_info()
                            f_name = tb.tb_frame.f_code.co_filename
                            line_no = tb.tb_lineno
                            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
                            return {'statusCode': 400, 'body': 'Bad Request(check data)'}
                    else:
                        return {'statusCode': 204, 'body': "parts are not added please check"}
                else:
                    return {'statusCode': 404, 'body': "vendors data is not there please check"}
            else:
                return {'statusCode': 404, 'body': "po data is not there"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsPurchaseReturnGetInternalDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            return_id = data['return_id']
            result = list(db_con.PurchaseReturn.find({"all_attributes.return_id": return_id}))
            result1 = result[0]
            if result1:

                lst = {
                    "inward_id": result1["all_attributes"]["inward_id"],
                    "invoice": result1["all_attributes"]["invoice"],
                    "parts": result1["all_attributes"]["parts"],
                    "photo": result1["all_attributes"]["photo"],
                    "qa_date": result1["all_attributes"]["qa_date"],
                    "qa_test": result1["all_attributes"]["qa_test"],
                    "return_id": result1["all_attributes"]["return_id"],
                    "sender_contact_number": result1["all_attributes"]["sender_contact_number"],
                    "sender_name": result1["all_attributes"]["sender_name"],
                    "vendor_id": result1["all_attributes"]["vendor_id"],
                    "vendor_name": result1["all_attributes"]["vendor_name"],
                    "address1": result1["all_attributes"]["address1"],
                    "email": result1["all_attributes"]["email"],
                    "bank_name": result1["all_attributes"]["bank_name"],
                    "account_number": result1["all_attributes"]["account_number"],
                    "gst_number": result1["all_attributes"]["gst_number"],
                    "ifsc_code": result1["all_attributes"]["ifsc_code"],
                    "contact_number": result1["all_attributes"]["contact_number"],
                    "description": result1['all_attributes']["description"],
                    "return_date": result1['sk_timeStamp'][:10],
                    "order_date": result1['all_attributes']["order_date"][:10],
                    "received_date": result1['all_attributes']["qa_date"],
                    "order_id": result1['gsisk_id']
                }
                conct.close_connection(client)
                return {'statusCode': 200, 'body': lst}
            else:
                conct.close_connection(client)
                return {'statusCode': 200, 'body': []}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsPurchaseReturnEditGetDetails(request_body):
        # try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            return_id = data['return_id']
            result = list(db_con.PurchaseReturn.find({"all_attributes.return_id": return_id},
                                                     {"all_attributes": 1, "sk_timeStamp": 1}))
            result1 = result[0]
            if result1:
                lst = [{
                    "inward_id": result1["all_attributes"]["inward_id"],
                    "invoice": file_get(result1["all_attributes"]["invoice"]),
                    "parts": result1["all_attributes"]["parts"],
                    # "photo": result1["all_attributes"]["photo"],
                    "photo": {k: file_get(v) for k, v in result1['all_attributes']["photo"].items()},

                    # "photo": result1["all_attributes"]["photo"],
                    "qa_date": result1["all_attributes"]["qa_date"],
                    "qa_test": file_get(result1["all_attributes"]["qa_test"]),
                    "return_id": result1["all_attributes"]["return_id"],
                    "sender_contact_number": result1["all_attributes"]["sender_contact_number"],
                    "sender_name": result1["all_attributes"]["sender_name"],
                    "vendor_id": result1["all_attributes"]["vendor_id"],
                    "vendor_name": result1["all_attributes"]["vendor_name"],
                    "description": result1["all_attributes"]["description"],
                    "status": result1["all_attributes"]["status"]
                }]
                conct.close_connection(client)
                return {'statusCode': 200, 'body': lst}
            else:
                conct.close_connection(client)
                return {'statusCode': 200, 'body': []}
        # except Exception as err:
        #     exc_type, exc_obj, tb = sys.exc_info()
        #     f_name = tb.tb_frame.f_code.co_filename
        #     line_no = tb.tb_lineno
        #     #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
        #     return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsPurchaseReturnEdit(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            return_id = data["return_id"]
            poData = list(db_con.PurchaseReturn.find({"all_attributes.return_id": return_id}))
            if poData:
                pk_id_for_po = poData[0]["pk_id"]
            all_attributes = poData[0]["all_attributes"]
            all_attributes['status'] = data['status']
            all_attributes['description'] = data['description']
            db_con.PurchaseReturn.update_one(
                {"pk_id": pk_id_for_po},
                {"$set": {"all_attributes": all_attributes}}
            )
            return {"statusCode": 200, "body": "po return Details updated successfully"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsPurchaseOrderGetPurchaseReturnList(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            databaseTableName = "PtgCms" + data["env_type"]
            #print(databaseTableName)
            result = list(db_con.PurchaseReturn.find({}))
            if result:
                lst = [
                    {
                        "status": i["all_attributes"]["status"] if "status" in i["all_attributes"] else " ",
                        "return_id": i["all_attributes"]["return_id"] if "return_id" in i["all_attributes"] else " ",
                        "vendor_id": i["all_attributes"]["vendor_id"] if "vendor_id" in i["all_attributes"] else " ",
                        "return_date": i["sk_timeStamp"][:10],
                        "return_value": sum(float(part['price']) for part in i["all_attributes"]["parts"].values()),

                        "order_price": i["all_attributes"]["total_price"] if "total_price" in i[
                            "all_attributes"] else " ",
                        "order_date": i["all_attributes"]["order_date"][:10] if "order_date" in i[
                            "all_attributes"] else " ",
                    }
                    for i in result
                ]

                lst = sorted(lst, key=lambda x: x['return_id'], reverse=True)
                return {'statusCode': 200, 'body': lst}
            else:
                return {'statusCode': 200, 'body': []}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    # def cmsPurchaseOrderGetPurchaseReturnDetails(request_body):
    #     pass

#
#
# import json
# from datetime import datetime,timedelta
# import base64
# from db_connection import db_connection_manage
# import sys
# import os
# import re
#
# conct = db_connection_manage()
#
# class PurchaseReturn():
#     def cmsPurchaseReturnGetOrderId(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             #print(data)
#             sorted_pk_ids1 = list(db_con.PurchaseOrder.find({}))
#             if sorted_pk_ids1:
#                 sorted_pk_ids = sorted([item["pk_id"] for item in sorted_pk_ids1], reverse=True)
#                 #print(sorted_pk_ids)
#                 sorted_pk_ids2 = sorted(sorted_pk_ids, key=lambda x: int(x.replace("OPTG", "")), reverse=False)
#                 conct.close_connection(client)
#                 return {"statusCode": 200, "body": sorted_pk_ids2}
#             else:
#                 conct.close_connection(client)
#                 return{"statusCode":404, "body":"No Data"}
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400,'body': 'Bad Request(check data)'}
#
#     def cmsPurchaseReturnGetInwardId(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             # #print(data)
#             # databaseTableName = "PtgCms"+data["env_type"]
#             # gsipk_table="QATest"
#             # dynamodb = boto3.client('dynamodb')
#             inwardId=data['po_order_id']
#             # statement = f"""select all_attributes.inwardId,all_attributes.parts from {databaseTableName} where  gsipk_table = '{gsipk_table}' and all_attributes.po_id='{inwardId}' """
#             # qaData = execute_statement_with_pagination(statement)
#             # return qaData
#             qaData = list(db_con.QATest.find({"all_attributes.po_id":inwardId}))
#             #print(qaData)
#             if qaData:
#                 a = [item["all_attributes"]['inwardId'] for item in qaData if any(int(k['fail_qty']) > 0 for j, k in item["all_attributes"]['parts'].items())]
#                 #print(a)
#                 sorted_pk_ids2 = sorted(a, key=lambda x:int(x.split('_')[1][2:]))
#                 conct.close_connection(client)
#                 return  {"statusCode":200, "body":sorted_pk_ids2}
#
#             else:
#                 conct.close_connection(client)
#                 return{"statusCode":404, "body":"No Data"}
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400,'body': 'Bad Request(check data)'}
#
#     def cmsGetComponentDetailsInsidePurchaseReturnModified(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             #print(data)
#             # databaseTableName = "PtgCms"+data["env_type"]
#             # gsipk_table="QATest"
#             po_id=data['po_order_id']
#             inwardId=data['inwardId']
#             # dynamodb = boto3.client('dynamodb')
#             # statement = f"""select * from {databaseTableName} where  gsipk_table = '{gsipk_table}' and all_attributes.inwardId='{inwardId}' and all_attributes.po_id='{po_id}' """
#             # qaData = execute_statement_with_pagination(statement)
#             sorted_pk_ids_list = list(db_con.QATest.find({"all_attributes.inwardId":inwardId,"all_attributes.po_id":po_id}))
#             # sorted_pk_ids_list = [sorting_function(item) for item in qaData]
#             # category_statement = f"""select gsisk_id,sub_categories,pk_id from {databaseTableName} where gsipk_table='Metadata' and gsipk_id='Electronic' """
#             # category_data = execute_statement_with_pagination(category_statement)
#             category_data = list(db_con.Metadata.find({"gsipk_id":"Electronic"},{"gsisk_id":1,"sub_categories":1,"pk_id":1}))
#             category_data = {item['pk_id'].replace("MDID","CTID"):{"ctgr_name":item['gsisk_id'],"sub_categories":item['sub_categories']} for item in category_data}
#             # inventory = f"select all_attributes.description,all_attributes.package,all_attributes.manufacturer,all_attributes.cmpt_id,all_attributes.prdt_name,all_attributes.sub_ctgr from {databaseTableName} where gsipk_table='Inventory'"
#             # inventory = extract_items_from_array_of_nested_dict(execute_statement_with_pagination(inventory))
#             inventory = list(db_con.Inventory.find({},{"all_attributes.description":1,"all_attributes.package":1,"all_attributes.manufacturer":1,"all_attributes.cmpt_id":1,"all_attributes.prdt_name":1,"all_attributes.sub_ctgr":1}))
#             inventory = {item["all_attributes"]['cmpt_id']:item for item in inventory}
#             # return category_data
#             b=[]
#             #print("-------------------",category_data)
#             #print("____________",inventory)
#             #print(sorted_pk_ids_list)
#             if sorted_pk_ids_list:
#                 filtered_list = [
#                         {
#                             "qa_date":item['all_attributes']["QA_date"] if "QA_date" in item['all_attributes'] else " ",
#                             "sender_name":item['all_attributes']["sender_name"] if "sender_name" in item['all_attributes'] else "",
#                             "sender_contact_number":item['all_attributes']["sender_contact_number"] if "sender_contact_number" in item['all_attributes'] else "",
#                             "invoice":item['all_attributes']["invoice"] if "invoice" in item['all_attributes'] else "",
#                             "qa_test":item['all_attributes']["QATest"] if "QATest" in item['all_attributes'] else "",
#                             "photo":item['all_attributes']["photo"] if "photo" in item['all_attributes'] else "",
#                             "description":item['all_attributes']["description"] if "description" in item['all_attributes'] else "",
#                             "parts": {
#                                 part_key: {
#                                         "cmpt_id": part_data['cmpt_id'],
#                                         "ctgr_id": part_data['ctgr_id'],
#                                         "price_per_piece": part_data['price_per_piece'],
#                                         "description": part_data['description'],
#                                         "packaging": part_data['packaging'],
#                                         "fail_qty": part_data['fail_qty'],
#                                         "batchId": part_data['batchId'],
#                                         "mfr_prt_num": part_data['mfr_prt_num'],
#                                         "manufacturer": part_data['manufacturer'],
#                                         "price": int(float(part_data['price_per_piece'])*float(part_data['fail_qty'])),
#                                         "pass_qty": part_data['pass_qty'],
#                                         "qty": part_data['qty'],
#                                         "department": part_data['department'],
#                                         "prdt_name": category_data[part_data['ctgr_id']]['sub_categories'][inventory[part_data['cmpt_id']]["all_attributes"]['sub_ctgr']] if part_data['department']=='Electronic' else part_data['prdt_name']
#                                         }
#                                 for part_key, part_data in item['all_attributes']['parts'].items()
#                                 if int(part_data['fail_qty']) >0
#
#                             }
#                         }
#                         for item in sorted_pk_ids_list
#                     ]
#                 if filtered_list:
#                     conct.close_connection(client)
#                     return {"statusCode":200, "body":filtered_list}
#                 else:
#                     conct.close_connection(client)
#                     return {"statusCode":200, "body":"we cant return fail qty is zero"}
#
#             else:
#                 conct.close_connection(client)
#                 return{"statusCode":404, "body":"No Data"}
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400,'body': 'Bad Request(check data)'}
#
#     def CmsPurchaseReturnCreateModified(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             all_attributes = {}
#             po_id = data['order_id']
#             gsipk_table = "PurchaseReturn"
#             description = data['description']
#             inward_id = data['inward_id']
#             result1 = list(db_con.PurchaseOrder.find({"pk_id": po_id}))
#             result3 = list(db_con.QATest.find({"all_attributes.inwardId": inward_id}))
#             parts = result3[0]['all_attributes']['parts']
#             matching_parts = {f"part{index + 1}": value for index, part in enumerate(data['parts']) for key, value in
#                               parts.items() if value['mfr_prt_num'] == part['mfr_prt_num']}
#             result = list(db_con.PurchaseReturn.find({"gsisk_id": po_id}))
#             return_id = f"{data['order_id']}-R1"
#             if result:
#                 if any(item['gsipk_id'] == data['inward_id'] for item in result):
#                     return {'statusCode': 400, 'body': "Return already present for given inward id"}
#                 returnids = sorted([int(item["pk_id"].split("R")[-1]) for item in result], reverse=True)
#                 return_id = f"{data['order_id']}-R{returnids[0] + 1}"
#
#             sk_timeStamp = (datetime.now()).isoformat()
#             parts = {f"part{inx + 1}": value for inx, value in enumerate(data['parts'])}
#             if result1:
#                 vendor_id = [i['all_attributes']['vendor_id'] for i in result1][0]
#                 result2 = list(db_con.Vendors.find({"pk_id": vendor_id}))
#                 if result2:
#                     if parts:
#                         all_attributes = {}
#                         all_attributes['return_id'] = return_id
#                         all_attributes['parts'] = parts
#                         all_attributes['invoice'] = [i['all_attributes']['invoice'] for i in result3][0]
#                         all_attributes['qa_test'] = [i['all_attributes']['QATest'] for i in result3][0]
#                         all_attributes['photo'] = {i: j for i, j in result3[0]['all_attributes']['photo'].items()}
#                         all_attributes['inward_id'] = inward_id
#                         all_attributes['qa_date'] = [i['all_attributes']['QA_date'] for i in result3][0]
#                         all_attributes['sender_name'] = [i['all_attributes']['sender_name'] for i in result3][0]
#                         all_attributes['sender_contact_number'] = \
#                         [i['all_attributes']['sender_contact_number'] for i in result3][0]
#                         all_attributes['status'] = data['status']
#                         all_attributes['description'] = description
#                         all_attributes['vendor_id'] = [i['all_attributes']['vendor_id'] for i in result2][0]
#                         all_attributes['vendor_name'] = [i['all_attributes']['vendor_name'] for i in result2][0]
#                         all_attributes['bank_name'] = [i['all_attributes']['bank_name'] for i in result2][0]
#                         all_attributes['account_number'] = [i['all_attributes']['account_number'] for i in result2][0]
#                         all_attributes['gst_number'] = [i['all_attributes']['gst_number'] for i in result2][0]
#                         all_attributes['ifsc_code'] = [i['all_attributes']['ifsc_code'] for i in result2][0]
#                         all_attributes['address1'] = [i['all_attributes']['address1'] for i in result2][0]
#                         all_attributes['email'] = [i['all_attributes']['email'] for i in result2][0]
#                         all_attributes['contact_number'] = [i['all_attributes']['contact_number'] for i in result2][0]
#                         all_attributes['order_date'] = [i['sk_timeStamp'] for i in result1][:10][0]
#                         all_attributes['total_price'] = [i['all_attributes']['total_price'] for i in result1][0]
#                         # return all_attributes
#                         # all_attributes=create_nested_dict(all_attributes)
#                         item = {
#                             "pk_id": return_id,
#                             "sk_timeStamp": sk_timeStamp,
#                             "all_attributes": all_attributes,
#                             "gsipk_table": gsipk_table,
#                             "gsisk_id": data['order_id'],
#                             "gsipk_id": data['inward_id'],
#                             "lsi_key": "--"
#                         }
#                         updat = db_con.PurchaseReturn.insert_one(item)
#                         for i, j in matching_parts.items():
#                             cmpt_id = j['cmpt_id']
#                             result4 = list(db_con.Inventory.find({"pk_id": cmpt_id}, {"all_attributes.rtn_qty": 1,
#                                                                                       "all_attributes.cmpt_id": 1,
#                                                                                       "pk_id": 1, "sk_timeStamp": 1}))
#                             if result4:
#                                 inventory_item = result4[0]
#                                 if 'rtn_qty' in inventory_item:
#                                     existing_qty = int(inventory_item['all_attributes']['rtn_qty'])
#                                 else:
#                                     existing_qty = 0
#                                 new_fail_qty = int(j['fail_qty'])
#                                 total_qty = existing_qty + new_fail_qty
#                                 resp = db_con.Inventory.update_one(
#                                     {"pk_id": inventory_item['pk_id']},
#                                     {"$set": {"all_attributes.rtn_qty": str(total_qty)}}
#                                 )
#                         try:
#                             response = {
#                                 'statusCode': 200,
#                                 'body': 'Purchase Return added successfully'
#                             }
#                             return response
#
#                         except Exception as err:
#                             exc_type, exc_obj, tb = sys.exc_info()
#                             f_name = tb.tb_frame.f_code.co_filename
#                             line_no = tb.tb_lineno
#                             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#                             return {'statusCode': 400, 'body': 'Bad Request(check data)'}
#                     else:
#                         return {'statusCode': 204, 'body': "parts are not added please check"}
#                 else:
#                     return {'statusCode': 404, 'body': "vendors data is not there please check"}
#             else:
#                 return {'statusCode': 404, 'body': "po data is not there"}
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'body': 'Bad Request(check data)'}
#     # def CmsPurchaseReturnCreateModified(request_body):
#     #     try:
#     #         data = request_body
#     #         env_type = data['env_type']
#     #         db_conct = conct.get_conn(env_type)
#     #         db_con = db_conct['db']
#     #         client = db_conct['client']
#     #         # dynamodb = boto3.client("dynamodb")
#     #         all_attributes = {}
#     #         po_id=data['order_id']
#     #         #print(data)
#     #         # databaseTableName = f"PtgCms{data['env_type']}"
#     #         # s3_bucket_name = "cms-image-data"
#     #         gsipk_table = "PurchaseReturn"
#     #         order_id = data['order_id']
#     #         description = data['description']
#     #         inward_id=data['inward_id']
#     #         # statement = f"""select * from {databaseTableName} where gsipk_table='PurchaseOrder' and pk_id='{po_id}' """
#     #         # result1 = execute_statement_with_pagination(statement)
#     #         result1 = list(db_con.PurchaseOrder.find({"pk_id":po_id}))
#     #         #print(result1[0])
#     #         result3 = list(db_con.QATest.find({"all_attributes.inwardId":inward_id}))
#     #         # statement = f"""select * from {databaseTableName} where gsipk_table='QATest' and all_attributes.inwardId='{inward_id}' """
#     #         # result3 = execute_statement_with_pagination(statement)
#     #         parts=result3[0]['all_attributes']['parts']
#     #         matching_parts = {f"part{index + 1}": value for index, part in enumerate(data['parts']) for key, value in parts.items() if value['mfr_prt_num'] == part['mfr_prt_num']}
#     #         # for i,j in matching_parts.items():
#     #         #     cmpt_id=j['cmpt_id']
#     #         #     statement_inventory = f"""select pk_id,all_attributes.cmpt_id,sk_timeStamp from {databaseTableName} where gsipk_table='Inventory' and pk_id='{cmpt_id}' """
#     #         #     result4 = execute_statement_with_pagination(statement_inventory)
#     #
#     #         # return result4
#     #         # statement2 = f"""select * from {databaseTableName} where gsipk_table='PurchaseReturn' and gsisk_id='{po_id}' """
#     #         # result = execute_statement_with_pagination(statement2)
#     #         result = list(db_con.PurchaseReturn.find({"gsisk_id":po_id}))
#     #         return_id = f"{data['order_id']}-R1"
#     #         # return result
#     #         #print(return_id)
#     #         if result:
#     #             if any(item['gsipk_id']==data['inward_id'] for item in result):
#     #                 return {'statusCode': 400,'body': "Return already present for given inward id"}
#     #             returnids = sorted([int(item["pk_id"].split("R")[-1]) for item in result],reverse=True)
#     #             return_id = f"{data['order_id']}-R{returnids[0]+1}"
#     #
#     #         sk_timeStamp = (datetime.now()).isoformat()
#     #         parts = {f"part{inx+1}":value for inx,value in enumerate(data['parts'])}
#     #         #print(parts)
#     #         if result1:
#     #             vendor_id=[i['all_attributes']['vendor_id'] for i in result1]
#     #             #print(vendor_id)
#     #             # statement1 = f"""select * from {databaseTableName} where gsipk_table='Vendor' and pk_id ='{vendor_id}' """
#     #             # result2 = execute_statement_with_pagination(statement1)
#     #             result2 = list(db_con.Vendor.find({"pk_id":vendor_id[0]}))
#     #             if result2:
#     #                 if parts:
#     #                     all_attributes = {}
#     #                     all_attributes['return_id'] = return_id
#     #                     all_attributes['parts'] = parts
#     #                     all_attributes['invoice'] = [i['all_attributes']['invoice'] for i in result3][0]
#     #                     all_attributes['qa_test'] = [i['all_attributes']['QATest'] for i in result3][0]
#     #                     all_attributes['photo'] = {i: j for i, j in result3[0]['all_attributes']['photo'].items()}
#     #                     all_attributes['inward_id'] =inward_id
#     #                     all_attributes['qa_date'] =[i['all_attributes']['QA_date'] for i in result3][0]
#     #                     all_attributes['sender_name'] = [i['all_attributes']['sender_name'] for i in result3][0]
#     #                     all_attributes['sender_contact_number'] = [i['all_attributes']['sender_contact_number'] for i in result3][0]
#     #                     all_attributes['status'] = data['status']
#     #                     all_attributes['description'] = description
#     #                     all_attributes['vendor_id']=[i['all_attributes']['vendor_id'] for i in result2][0]
#     #                     all_attributes['vendor_name']=[i['all_attributes']['vendor_name'] for i in result2][0]
#     #                     all_attributes['bank_name']=[i['all_attributes']['bank_name'] for i in result2][0]
#     #                     all_attributes['account_number']=[i['all_attributes']['account_number'] for i in result2][0]
#     #                     all_attributes['gst_number']=[i['all_attributes']['gst_number'] for i in result2][0]
#     #                     all_attributes['ifsc_code']=[i['all_attributes']['ifsc_code'] for i in result2][0]
#     #                     all_attributes['address1']=[i['all_attributes']['address1'] for i in result2][0]
#     #                     all_attributes['email']=[i['all_attributes']['email'] for i in result2][0]
#     #                     all_attributes['contact_number']=[i['all_attributes']['contact_number'] for i in result2][0]
#     #                     all_attributes['order_date']=[i['sk_timeStamp'] for i in result1][:10][0]
#     #                     all_attributes['total_price']=[i['all_attributes']['total_price'] for i in result1][0]
#     #                     # return all_attributes
#     #                     # all_attributes=create_nested_dict(all_attributes)
#     #                     item = {
#     #                         "pk_id": {return_id},
#     #                         "sk_timeStamp": {sk_timeStamp},
#     #                         "all_attributes": all_attributes,
#     #                         "gsipk_table": {gsipk_table},
#     #                         "gsisk_id": {data['order_id']},
#     #                         "gsipk_id": {data['inward_id']},
#     #                         "lsi_key": {"--"}
#     #                     }
#     #                     # return item
#     #
#     #                     # transact_items = [{
#     #                     #     'Put': {
#     #                     #         'TableName': gsipk_table,
#     #                     #         'Item': item
#     #                     #     }
#     #                     # }]
#     #                     for i, j in matching_parts.items():
#     #                         cmpt_id = j['cmpt_id']
#     #                         result4 = list(db_con.Inventory.find({"pk_id":cmpt_id},{"all_attributes.rtn_qty":1,"all_attributes.cmpt_id":1,"pk_id":1,"sk_timeStamp":1}))
#     #                         if result4:
#     #                             inventory_item = result4[0]
#     #                             if 'rtn_qty' in inventory_item:
#     #                                 existing_qty = int(inventory_item['rtn_qty'])
#     #                             else:
#     #                                 existing_qty = 0
#     #                             new_fail_qty = int(j['fail_qty'])
#     #                             total_qty=existing_qty+new_fail_qty
#     #                             # transact_items.append({
#     #                             #     'Update': {
#     #                             #         'TableName': databaseTableName,
#     #                             #         'Key': {
#     #                             #             'pk_id': {'S': inventory_item['pk_id']},  # Adjust based on your key structure
#     #                             #             'sk_timeStamp': {'S': inventory_item['sk_timeStamp']}
#     #                             #         },
#     #                             #         'UpdateExpression': 'SET all_attributes.rtn_qty = :rtn_qty',  # Adjust based on your update requirements
#     #                             #         'ExpressionAttributeValues': {
#     #                             #             ':rtn_qty': {'S': str(total_qty)}  # Adjust based on the actual new value
#     #                             #         }
#     #                             #     }
#     #                             # })
#     #                             resp = db_con.Inventory.update_one(
#     #                                 {"pk_id": inventory_item['pk_id']},
#     #                                 {"$set": {"all_attributes.rtn_qty": str(total_qty)}}
#     #                             )
#     #                     try:
#     #                         # response = dynamodb.transact_write_items(
#     #                         #     TransactItems=transact_items
#     #                         # )
#     #                         r = db_con.PurchaseReturn.insert_one(item)
#     #                         response = {
#     #                             'statusCode': 200,
#     #                             'body': 'Purchase Return added successfully'
#     #                         }
#     #                         return response
#     #
#     #                     except Exception as err:
#     #                         exc_type, exc_obj, tb = sys.exc_info()
#     #                         f_name = tb.tb_frame.f_code.co_filename
#     #                         line_no = tb.tb_lineno
#     #                         #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#     #                         return {'statusCode': 400,'body': 'Bad Request(check data)'}
#     #                 else:
#     #                     return {'statusCode':204, 'body':"parts are not added please check"}
#     #             else:
#     #                 return {'statusCode':404, 'body':"vendors data is not there please check"}
#     #         else:
#     #             return {'statusCode':404,'body':"po data is not there"}
#     #     except Exception as err:
#     #         exc_type, exc_obj, tb = sys.exc_info()
#     #         f_name = tb.tb_frame.f_code.co_filename
#     #         line_no = tb.tb_lineno
#     #         #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#     #         return {'statusCode': 400,'body': 'Bad Request(check data)'}
#
#     def cmsPurchaseReturnGetInternalDetails(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             return_id=data['return_id']
#             result = list(db_con.PurchaseReturn.find({"all_attributes.return_id":return_id}))
#             result1 = result[0]
#             if result1:
#
#                 lst = {
#                     "inward_id": result1["all_attributes"]["inward_id"],
#                     "invoice": result1["all_attributes"]["invoice"],
#                     "parts": result1["all_attributes"]["parts"],
#                     "photo": result1["all_attributes"]["photo"],
#                     "qa_date": result1["all_attributes"]["qa_date"],
#                     "qa_test": result1["all_attributes"]["qa_test"],
#                     "return_id": result1["all_attributes"]["return_id"],
#                     "sender_contact_number": result1["all_attributes"]["sender_contact_number"],
#                     "sender_name": result1["all_attributes"]["sender_name"],
#                     "vendor_id": result1["all_attributes"]["vendor_id"],
#                     "vendor_name": result1["all_attributes"]["vendor_name"],
#                     "address1": result1["all_attributes"]["address1"],
#                     "email": result1["all_attributes"]["email"],
#                     "bank_name": result1["all_attributes"]["bank_name"],
#                     "account_number": result1["all_attributes"]["account_number"],
#                     "gst_number": result1["all_attributes"]["gst_number"],
#                     "ifsc_code": result1["all_attributes"]["ifsc_code"],
#                     "contact_number": result1["all_attributes"]["contact_number"],
#                     "description":result1['all_attributes']["description"],
#                     "return_date":result1['sk_timeStamp'][:10],
#                     "order_date":result1['all_attributes']["order_date"][:10],
#                     "received_date":result1['all_attributes']["qa_date"],
#                     "order_id":result1['gsisk_id']
#                 }
#                 conct.close_connection(client)
#                 return {'statusCode': 200, 'body': lst}
#             else:
#                 conct.close_connection(client)
#                 return {'statusCode': 200, 'body': []}
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400,'body': 'Bad Request(check data)'}
#
#     def cmsPurchaseReturnEditGetDetails(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             # databaseTableName = "PtgCms"+data["env_type"]
#             # gsipk_table = 'PurchaseReturn'
#             return_id=data['return_id']
#             # #print(databaseTableName)
#             result = list(db_con.PurchaseReturn.find({"all_attributes.return_id":return_id},{"all_attributes":1,"sk_timeStamp":1}))
#             result1 = result[0]
#             if result1:
#                 lst = [{
#                     "inward_id": result1["all_attributes"]["inward_id"],
#                     "invoice": result1["all_attributes"]["invoice"],
#                     "parts": result1["all_attributes"]["parts"],
#                     "photo": result1["all_attributes"]["photo"],
#                     "qa_date": result1["all_attributes"]["qa_date"],
#                     "qa_test": result1["all_attributes"]["qa_test"],
#                     "return_id": result1["all_attributes"]["return_id"],
#                     "sender_contact_number": result1["all_attributes"]["sender_contact_number"],
#                     "sender_name": result1["all_attributes"]["sender_name"],
#                     "vendor_id": result1["all_attributes"]["vendor_id"],
#                     "vendor_name": result1["all_attributes"]["vendor_name"],
#                     "description":result1["all_attributes"]["description"],
#                     "status":result1["all_attributes"]["status"]
#                 }]
#                 conct.close_connection(client)
#                 return {'statusCode': 200, 'body': lst}
#             else:
#                 conct.close_connection(client)
#                 return {'statusCode': 200, 'body': []}
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400,'body': 'Bad Request(check data)'}
#
#     def cmsPurchaseReturnEdit(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             #print(data)
#             # dynamodb = boto3.client("dynamodb")
#             # databaseTableName = "PtgCms"+data["env_type"]
#             # gsipk_table="PurchaseReturn"
#             return_id=data["return_id"]
#             # data['parts'] = {f"part{inx+1}": part for inx,part in enumerate(data['parts'])}
#             # sk_edit_timeStamp = (datetime.now()).isoformat()
#             # statement = f"""select * from {databaseTableName} where  gsipk_table = '{gsipk_table}' and all_attributes.return_id='{return_id}'  """
#             # poData = execute_statement_with_pagination(statement)
#             poData = list(db_con.PurchaseReturn.find({"all_attributes.return_id":return_id}))
#             # #print(poData)
#             # return qaData
#             if poData:
#                 pk_id_for_po=poData[0]["pk_id"]
#                 sk_timestamp=poData[0]["sk_timeStamp"]
#                 # db = poData[0]
#                 # d = sorting_function(db)
#             # all_attributes = create_nested_dicts(data)
#             all_attributes = poData[0]["all_attributes"]
#             all_attributes['status']=data['status']
#             all_attributes['description']=data['description']
#             db_con.PurchaseReturn.update_one(
#                     {"pk_id": pk_id_for_po},
#                     {"$set": {"all_attributes": all_attributes}}
#             )
#             # return all_attributes
#             # key = {
#             #         "pk_id": pk_id_for_po,
#             #         "sk_timeStamp": sk_timestamp,
#             #     }
#             # update_item = dynamodb.update_item(
#             #     TableName=databaseTableName,
#             #     Key=key,
#             #     UpdateExpression="set all_attributes = :allattrvalue",
#
#             #     ExpressionAttributeValues={
#             #         ":allattrvalue": all_attributes,
#             #     },
#             #     ReturnValues="UPDATED_NEW",
#             #     )
#             # #print(update_item)
#             return {"statusCode": 200, "body": "po return Details updated successfully"}
#
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400,'body': 'Bad Request(check data)'}
#
#     def cmsPurchaseOrderGetPurchaseReturnList(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             databaseTableName = "PtgCms"+data["env_type"]
#             #print(databaseTableName)
#             result = list(db_con.PurchaseReturn.find({}))
#             if result:
#                 lst = [
#                     {
#                         "status": i["all_attributes"]["status"] if "status" in i["all_attributes"] else " ",
#                         "return_id": i["all_attributes"]["return_id"] if "return_id" in i["all_attributes"] else " ",
#                         "vendor_id": i["all_attributes"]["vendor_id"] if "vendor_id" in i["all_attributes"] else " ",
#                         "return_date": i["sk_timeStamp"][:10],
#                         "return_value": sum(float(part['price']) for part in i["all_attributes"]["parts"].values()),
#
#
#
#                         "order_price": i["all_attributes"]["total_price"] if "total_price" in i["all_attributes"] else " ",
#                         "order_date": i["all_attributes"]["order_date"][:10] if "order_date" in i["all_attributes"] else " ",
#                     }
#                     for i in result
#                 ]
#
#                 lst = sorted(lst, key=lambda x: x['return_id'], reverse=True)
#                 return {'statusCode': 200, 'body': lst}
#             else:
#                 return {'statusCode': 200, 'body': []}
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400,'body': 'Bad Request(check data)'}
#
#     # def cmsPurchaseOrderGetPurchaseReturnDetails(request_body):
#     #     pass
#
#
#
