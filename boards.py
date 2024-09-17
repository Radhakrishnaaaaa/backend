import json
from datetime import datetime, timedelta,date
import base64
from db_connection import db_connection_manage
import sys
import binascii
import os, io, zipfile
import re
from cms_utils import find_stock_inwards,batch_number_allocation,get_kit_and_boards_info, file_uploads, find_stock_inward_new
from cms_utils import dynamic_fields

conct = db_connection_manage()


def get_mkitinfo(data):
    cmpt_info = {}
    for key in data:
        pattern = r'M-KIT\d+'
        if re.match(key,pattern):
            for key,value in data[key].items():
                cmpt_id = value['cmpt_id']
                qty = value['provided_qty']
                if cmpt_id in cmpt_info:
                    cmpt_info[cmpt_id] = f"{int(cmpt_info[cmpt_id])+int(qty)}"
                else:
                    cmpt_info[cmpt_id] = qty
    return cmpt_info

class Boards():


    def cmsBomOutwardInfoGetAssignToBoxBuilding(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            outward_id = data.get("outward_id")
            bom_id = data.get("bom_id")

            data1 = list(db_con.Boards.find({
                "$and": [
                    {"all_attributes.outward_id": outward_id},
                    {"all_attributes.bom_id": bom_id}
                ]
            }, {"_id": 0, "pk_id": 1, "all_attributes": 1}))

            resp = {}
            resp["boards"] = {k: v for k, v in data1[0]["all_attributes"]["boards"].items() if any('comment' in board for board in v.values())}
            bomData = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "all_attributes": 1}))
            resp["M_KIT1"] = bomData[0]['all_attributes']['M_parts']
            resp["against_po"] = data1[0]["all_attributes"]["against_po"]
            resp["bom_id"] = bom_id
            resp["outward_id"] = outward_id
            resp["boards_id"] = data1[0]['pk_id']

            # Function to update ptg_stock for each part in M_KIT
            def update_ptg_stock(kit):
                for part_key, part in kit.items():
                    cmpt_id = part["cmpt_id"]
                    inventoryData = list(db_con.Inventory.find({"pk_id": cmpt_id}, {"_id": 0, "all_attributes.qty": 1}))
                    if inventoryData:
                        part["ptg_stock"] = inventoryData[0]["all_attributes"]["qty"]
                return kit

            # Update ptg_stock for M_KIT1
            resp["M_KIT1"] = update_ptg_stock(resp["M_KIT1"])

            box_data = Boards.box_building(data)
            combined_dict = {**resp, **box_data}

            # Update ptg_stock for new M_KITs in box_data
            for key in combined_dict:
                if key.startswith("M_KIT"):
                    combined_dict[key] = update_ptg_stock(combined_dict[key])

            conct.close_connection(client)

            return {"statusCode": 200, "body": combined_dict}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check data)'}

# def box_building(data):
#     env_type = data['env_type']
#     db_conct = conct.get_conn(env_type)
#     db_con = db_conct['db']
#     client = db_conct['client']
#     body = {}
#     bb_id = data.get("bom_id")
#     outward_id = data["outward_id"]
#     data2 = list(db_con.BoxBuilding.find({
#         "$and": [
#             {"all_attributes.bom_id": bb_id},
#             {"all_attributes.outward_id": outward_id}
#         ]
#     }, {"_id": 0, "all_attributes": 1, "pk_id": 1}))

#     if data2:
#         data2 = data2[0]
#         part_info = data2['all_attributes']
#         all_keys = sorted(part_info.keys(), reverse=True)
#         latest_m_kit_key = next((kit_key for kit_key in all_keys if kit_key.startswith('M_KIT')), None)

#         parts_no = 0
#         body = {}
#         top_negative_balance_part = {}
#         for part_name, part_details in data2["all_attributes"][latest_m_kit_key].items():
#             if int(part_details['balance_qty']) < 0:
#                 part_details["qty_per_board"] = part_details["balance_qty"].replace("-", "")
#                 parts_no += 1
#                 top_negative_balance_part["part" + str(parts_no)] = part_details
#         latest_m_kit_key = int(latest_m_kit_key.split("T")[1]) + 1
#         body["M_KIT" + str(latest_m_kit_key)] = top_negative_balance_part
#         body["BB_id"] = data2["pk_id"]

#     conct.close_connection(client)
#     return body


    # def cmsBomOutwardInfoGetAssignToBoxBuilding(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data.get("outward_id")
    #         bom_id = data.get("bom_id")

    #         data1 = list(db_con.Boards.find({
    #             "$and": [
    #                 {"all_attributes.outward_id": outward_id},
    #                 {"all_attributes.bom_id": bom_id}
    #             ]
    #         }, {"_id": 0, "pk_id": 1, "all_attributes": 1}))

    #         resp = {}
    #         resp["boards"] = {k: v for k, v in data1[0]["all_attributes"]["boards"].items() if any('comment' in board for board in v.values())}
    #         bomData = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "all_attributes": 1}))
    #         resp["M_KIT1"] = bomData[0]['all_attributes']['M_parts']
    #         resp["against_po"] = data1[0]["all_attributes"]["against_po"]
    #         resp["bom_id"] = bom_id
    #         resp["outward_id"] = outward_id
    #         resp["boards_id"] = data1[0]['pk_id']

    #         # Query Inventory table to get the qty
    #         cmpt_id = resp["M_KIT1"]["part1"]["cmpt_id"]
    #         inventoryData = list(db_con.Inventory.find({"pk_id": cmpt_id}, {"_id": 0, "all_attributes.qty": 1}))

    #         if inventoryData:
    #             resp["M_KIT1"]["part1"]["ptg_stock"] = inventoryData[0]["all_attributes"]["qty"]

    #         box_data = Boards.box_building(data)
    #         combined_dict = {**resp, **box_data}
    #         conct.close_connection(client)

    #         return {"statusCode": 200, "body": combined_dict}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}

    def box_building(data):
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        body = {}
        bb_id = data.get("bom_id")
        outward_id = data["outward_id"]
        data2 = list(db_con.BoxBuilding.find({
            "$and": [
                {"all_attributes.bom_id": bb_id},
                {"all_attributes.outward_id": outward_id}
            ]
        }, {"_id": 0, "all_attributes": 1, "pk_id": 1}))

        if data2:
            data2 = data2[0]
            part_info = data2['all_attributes']
            all_keys = sorted(part_info.keys(), reverse=True)
            latest_m_kit_key = next((kit_key for kit_key in all_keys if kit_key.startswith('M_KIT')), None)

            parts_no = 0
            body = {}
            top_negative_balance_part = {}
            for part_name, part_details in data2["all_attributes"][latest_m_kit_key].items():
                if int(part_details['balance_qty']) < 0:
                    part_details["qty_per_board"] = part_details["balance_qty"].replace("-", "")
                    parts_no += 1
                    top_negative_balance_part["part" + str(parts_no)] = part_details
            latest_m_kit_key = int(latest_m_kit_key.split("T")[1]) + 1
            body["M_KIT" + str(latest_m_kit_key)] = top_negative_balance_part
            body["BB_id"] = data2["pk_id"]

        conct.close_connection(client)
        return body

    

    # def cmsBomOutwardInfoGetAssignToBoxBuilding(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data.get("outward_id")
    #         bom_id = data.get("bom_id")

    #         data1 = list(db_con.Boards.find({
    #             "$and": [
    #                 {"all_attributes.outward_id": outward_id},
    #                 {"all_attributes.bom_id": bom_id}
    #             ]
    #         }, {"_id": 0, "pk_id": 1, "all_attributes": 1}))

    #         resp = {}
    #         resp["boards"] = data1[0]["all_attributes"]["boards"]
    #         bomData = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "all_attributes": 1}))
    #         resp["M_KIT1"] = bomData[0]['all_attributes']['M_parts']
    #         resp["against_po"] = data1[0]["all_attributes"]["against_po"]
    #         resp["bom_id"] = bom_id
    #         resp["outward_id"] = outward_id
    #         resp["boards_id"] = data1[0]['pk_id']

    #         # Query Inventory table to get the qty
    #         cmpt_id = resp["M_KIT1"]["part1"]["cmpt_id"]
    #         inventoryData = list(db_con.Inventory.find({"pk_id": cmpt_id}, {"_id": 0, "all_attributes.qty": 1}))

    #         if inventoryData:
    #             resp["M_KIT1"]["part1"]["ptg_stock"] = inventoryData[0]["all_attributes"]["qty"]

    #         box_data = Boards.box_building(data)
    #         combined_dict = {**resp, **box_data}
    #         conct.close_connection(client)

    #         return {"statusCode": 200, "body": combined_dict}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}

    # def box_building(data):
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     body = {}
    #     bb_id = data.get("bom_id")
    #     outward_id = data["outward_id"]
    #     data2 = list(db_con.BoxBuilding.find({
    #         "$and": [
    #             {"all_attributes.bom_id": bb_id},
    #             {"all_attributes.outward_id": outward_id}
    #         ]
    #     }, {"_id": 0, "all_attributes": 1, "pk_id": 1}))

    #     if data2:
    #         data2 = data2[0]
    #         part_info = data2['all_attributes']
    #         all_keys = sorted(part_info.keys(), reverse=True)
    #         latest_m_kit_key = next((kit_key for kit_key in all_keys if kit_key.startswith('M_KIT')), None)

    #         parts_no = 0
    #         body = {}
    #         top_negative_balance_part = {}
    #         for part_name, part_details in data2["all_attributes"][latest_m_kit_key].items():
    #             if int(part_details['balance_qty']) < 0:
    #                 part_details["qty_per_board"] = part_details["balance_qty"].replace("-", "")
    #                 parts_no += 1
    #                 top_negative_balance_part["part" + str(parts_no)] = part_details
    #         latest_m_kit_key = int(latest_m_kit_key.split("T")[1]) + 1
    #         body["M_KIT" + str(latest_m_kit_key)] = top_negative_balance_part
    #         body["BB_id"] = data2["pk_id"]

    #     conct.close_connection(client)
    #     return body

    # def cmsBomOutwardInfoGetAssignToBoxBuilding(request_body):
    #     data = request_body
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     outward_id = data.get("outward_id")
    #     bom_id = data.get("bom_id")
    #     data1 = list(db_con.Boards.find({
    #         "$and": [
    #             {
    #                 "all_attributes.outward_id": outward_id,
    #                 "all_attributes.bom_id": bom_id
    #             }
    #         ]

    #     }, {"_id": 0, "pk_id": 1, "all_attributes": 1}))
    #     resp = {}
    #     resp["boards"] = data1[0]["all_attributes"]["boards"]
    #     bomData = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "all_attributes": 1}))
    #     resp["M_KIT1"] = bomData[0]['all_attributes']['M_parts']
    #     resp["against_po"] = data1[0]["all_attributes"]["against_po"]
    #     resp["bom_id"] = bom_id
    #     resp["outward_id"] = outward_id
    #     resp["boards_id"] = (data1[0]['pk_id'])
    #     box_data = Boards.box_building(data)
    #     combined_dict = {**resp, **box_data}
    #     conct.close_connection(client)

    #     return {"statusCode": 200, "body": combined_dict}

    # # except:
    # #     return {"statusCode":404,"error":"there must be some error in b_data"}

    # def box_building(data):
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     body = {}
    #     bb_id = data.get("bom_id")
    #     outward_id = data["outward_id"]
    #     data2 = list(db_con.BoxBuilding.find({
    #         "$and": [
    #             {"all_attributes.bom_id": bb_id},
    #             {"all_attributes.outward_id": outward_id}
    #         ]
    #     }, {"_id": 0, "all_attributes": 1, "pk_id": 1}))
    #     if data2:
    #         data2 = data2[0]

    #         part_info = data2['all_attributes']
    #         all_keys = sorted(part_info.keys(), reverse=True)
    #         latest_m_kit_key = next((kit_key for kit_key in all_keys if kit_key.startswith('M_KIT')), None)

    #         parts_no = 0
    #         body = {}
    #         top_negative_balance_part = {}
    #         for part_name, part_details in data2["all_attributes"][latest_m_kit_key].items():
    #             if int(part_details['balance_qty']) < 0:
    #                 part_details["qty_per_board"] = part_details["balance_qty"].replace("-", "")
    #                 parts_no = parts_no + 1
    #                 top_negative_balance_part["part" + str(parts_no)] = part_details
    #         latest_m_kit_key = int(latest_m_kit_key.split("T")[1]) + 1
    #         body["M_KIT" + str(latest_m_kit_key)] = top_negative_balance_part
    #         body["BB_id"] = data2["pk_id"]
    #     conct.close_connection(client)
    #     return body

    def cmsBomOutwardInfoSaveAssignToBoxBuilding2(request_body):
        data = request_body
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        bb_id = data.get("BB_id")
        result = list(db_con.BoxBuilding.find({"pk_id": bb_id}, {"pk_id": 1, "sk_timeStamp": 1, "all_attributes": 1}))
        board_id = [i["all_attributes"]["boards_id"] for i in result][0]
        board_data = db_con.Boards.find_one({"pk_id": board_id})
        boards = board_data['all_attributes']['boards']
        board_keys = list(boards.keys())
        all_tables = list(db_con.all_tables.find({"pk_id": "top_ids"}, {"_id": 0, "all_attributes.BoxBuilding": 1,
                                                                        "all_attributes.ActivityId": 1}))
        activity_id = all_tables[0]['all_attributes']['ActivityId']
        update_id = all_tables[0]['all_attributes']["BoxBuilding"][3:]
        if result:
            outward_id = str(int(update_id) + 1)
        id = 1
        documents = data['documents']
        doc = {}
        for inx, docs in enumerate(documents):
            image_path = file_uploads.upload_file("BoxBuilding", "PtgCms" + env_type, "",
                                                "M-Kit" + str(id), docs["doc_name"],
                                                docs['doc_body'])
            doc[docs["doc_name"]] = image_path
        invent_data = list(db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1, "all_attributes.qty": 1,
                                                      "all_attributes.out_going_qty": 1}))
        invent_data = {item['all_attributes']['cmpt_id']: {"qty": item['all_attributes']['qty'],
                                                           "out_going_qty": item['all_attributes'].get('out_going_qty',
                                                                                                       '0')} for item in
                       invent_data}
        m_parts = []
        m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
        m_parts = list(data[m_kit_key].values())
        if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
            return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}
        if result:
            pk_id = result[0]["pk_id"]
            result = result[0]
            cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
                               for key in data.keys() if key.startswith("M_KIT")
                               for part, details in data[key].items()}
            for i in range(len(cmpt_id_and_qty)):
                part = "part" + str(i + 1)
                cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
                qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
                out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
                    cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data[cmpt_id].keys() else (
                cmpt_id_and_qty[part]["provided_qty"])
                upd = db_con.Inventory.update_one(
                    {"pk_id": cmpt_id},
                    {"$set": {"all_attributes.qty": qty, "all_attributes.out_going_qty": out_going_qty}}
                )
            m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
            if m_kit_key:
                res = db_con.BoxBuilding.update_one(
                    {"pk_id": pk_id},
                    {"$set": {f"all_attributes.{m_kit_key}": data[m_kit_key],
                              "all_attributes.documents": doc}}
                )
                bom_id = data["bom_id"]
                data_bom = db_con.BOM.find({"pk_id": bom_id}, {"sk_timeStamp": 1})
                bom_timeStamp = data_bom[0]["sk_timeStamp"]
                response = db_con.BOM.update_one(
                    {"pk_id": bom_id},
                    {"$set": {f"all_attributes.status": "Bom_assigned"}}
                )
                activity_id = int(activity_id) + 1
                if result:
                    activity_details = {}
                    for key in data:
                        if key.startswith('M_KIT'):
                            # Access the dictionary for the current M_KIT key
                            m_kit_data = data[key]
                            # Iterate over items of the dictionary for the current M_KIT key
                            for part_key, part_value in m_kit_data.items():
                                if part_key.startswith("part"):
                                    cmpt_id = part_value.get('cmpt_id', '')
                                    activity_details[cmpt_id] = {
                                        "mfr_prt_num": part_value.get('vic_part_number', ''),
                                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Format the date if needed
                                        "action": "Utilized",
                                        "Description": "Utilized",
                                        "issued_to": data.get('receiver_name', ''),
                                        "po_no": "-",
                                        "invoice_no": "-",
                                        "cmpt_id": part_value.get('cmpt_id', ''),
                                        "ctgr_id": part_value.get('ctgr_id', ''),
                                        "prdt_name": part_value.get('prdt_name', ''),
                                        "description": part_value.get('description', ''),
                                        "packaging": "-",
                                        "closing_qty": str(int(part_value.get('ptg_stock', '0')) - int(part_value.get('provided_qty', '0'))),
                                        "qty": part_value.get('provided_qty', '0'),
                                        "batchId": part_value.get('batch_no', ''),
                                        "used_qty": "0",
                                        "lot_id": part_value.get('lot_id', '')
                                    }
                    # for part_key, part_value in data.startswith("M_KIT").items():
                    #     if part_key.startswith("part"):
                    #         cmpt_id = part_value.get('cmpt_id', '')
                    #         activity_details[cmpt_id] = {
                    #             "mfr_prt_num": part_value.get('vic_part_number', ''),
                    #             "date": datetime.now(),
                    #             "action": "Utilized",
                    #             "Description": "Utilized",
                    #             "issued_to": data.get('receiver_name', ''),
                    #             "po_no": "-",
                    #             "invoice_no": "-",
                    #             "cmpt_id": part_value.get('cmpt_id', ''),
                    #             "ctgr_id": part_value.get('ctgr_id', ''),
                    #             "prdt_name": part_value.get('prdt_name', ''),
                    #             "description": part_value.get('description', ''),
                    #             "packaging": "-",
                    #             "closing_qty":str(int(part_value.get('ptg_stock','0'))- int(part_value.get('provided_qty','0'))),
                    #             "qty": part_value.get('provided_qty','0'),
                    #             "batchId": part_value.get('batch_no',''),
                    #             "used_qty": "0",
                    #             "lot_id": part_value.get('lot_id','')
                    #         }
                    db_con['ActivityDetails'].insert_one(
                        {
                            "pk_id": f"ACTID{activity_id}",
                            "sk_timeStamp": str(datetime.now()),
                            "all_attributes": activity_details,
                            "gsipk_table": "ActivityDetails",
                            "gsisk_id": outward_id,
                            "lsi_key": "Utilized",
                            "gsipk_id": "EMS"
                        }
                    )
            # if board_keys:
            #     for key in board_keys:
            #         db_con.Boards.update_one({'pk_id': board_id},
            #                                  {"$set": {f"all_attributes.boards.{key}.status": "Assigned"}})
            if data["boards"]:
                # bk1 = data["all_attributes"]["boards"]
                bk1 = {}
                bk2 = data["boards"]
                combined_dict = {**bk1, **bk2}
                # for key in combined_dict:
                #     combined_dict[key]['status'] = "Assigned"
                resp = db_con.BoxBuilding.update_one(
                    {"pk_id": pk_id},
                    {"$set": {"all_attributes.boards": combined_dict}}
                )
            conct.close_connection(client)
            return {"statusCode": 200, "body": "BoxBuilding updated successfully"}
        else:
            conct.close_connection(client)
            return {"statusCode": 404, "body": "No Data Found"}

    # def cmsBomOutwardInfoSaveAssignToBoxBuilding2(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         bb_id = data.get("BB_id")
    #         sk_timeStamp = (datetime.now()).isoformat()
    #         result = list(
    #             db_con.BoxBuilding.find({"pk_id": bb_id}, {"pk_id": 1, "sk_timeStamp": 1, "all_attributes": 1}))
    #         if not result:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No Data Found"}
    #         board_id = result[0]["all_attributes"]["boards_id"]
    #         board_data = db_con.Boards.find_one({"pk_id": board_id})
    #         if not board_data:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No Board Data Found"}
    #         boards = board_data['all_attributes']['boards']
    #         board_keys = list(boards.keys())
    #         # part_batch_info = find_stock_inwards(data['bom_id'], db_con, 'M_parts')
    #         part_batch_info = find_stock_inward_new(data['bom_id'], db_con, 'M_parts')
    #         part_batch_info = part_batch_info['part_batch_info']
    #         if not part_batch_info:
    #             conct.close_connection(client)
    #             return {'statusCode': 200, 'body': 'No inwards for this bom'}
    #         activity = {}
    #         activity_id_record = db_con.all_tables.find_one({"pk_id": "top_ids"}, {"all_attributes.ActivityId": 1})
    #         activity_id = int(activity_id_record['all_attributes'].get('ActivityId', "0")) + 1
    #         partner_records = db_con.Partners.find({"pk_id": data['partner_id']}, {"all_attributes.partner_name": 1})
    #         partner_name = ""
    #         for partner_record in partner_records:
    #             if 'all_attributes' in partner_record and 'partner_name' in partner_record['all_attributes']:
    #                 partner_name = partner_record['all_attributes']['partner_name']
    #                 break
    #         if not partner_name:
    #             conct.close_connection(client)
    #             return {'statusCode': 404, 'body': 'No Partner Data Found'}
    #         invent_data = list(
    #             db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1, "all_attributes.qty": 1,
    #                                     "all_attributes.out_going_qty": 1}))
    #         invent_data = {item['all_attributes']['cmpt_id']: {"qty": item['all_attributes']['qty'],
    #                                                         "out_going_qty": item['all_attributes'].get(
    #                                                             'out_going_qty', '0')}
    #                     for item in invent_data}
    #         m_parts = []
    #         m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
    #         kit_info = get_kit_and_boards_info(result[0]['all_attributes'], 'BOXBUILDING')
    #         for key, value in data[m_kit_key].items():
    #             print(value['provided_qty'])
    #             print(value['cmpt_id'])
    #             print(kit_info)
    #             var = batch_number_allocation(part_batch_info, int(value['provided_qty']), value['cmpt_id'], kit_info)
    #             if var:
    #                 data[m_kit_key][key]['batch_no'] = var['batch_string']
    #                 activity[value['cmpt_id']] = {
    #                     "mfr_prt_num": value.get("mfr_prt_num", "-"),
    #                     "date": str(date.today()),
    #                     "action": "Utilized",
    #                     "Description": "Utilized",
    #                     "issued_to": partner_name,
    #                     "po_no": var['po_id'],
    #                     'invoice_no': var["invoice_no"],
    #                     "cmpt_id": value.get("cmpt_id", ""),
    #                     "ctgr_id": value.get("ctgr_id", ""),
    #                     "prdt_name": value.get("prdt_name", ""),
    #                     "description": value.get("description", ""),
    #                     "packaging": value.get("packaging", ""),
    #                     "inventory_position": value.get("inventory_position", ""),
    #                     "qty": value['provided_qty'],
    #                     "batchId": var['batch_string'],
    #                     "used_qty": value['provided_qty'],
    #                     "lot_no": var["lot_no"]
    #                 }
    #             else:
    #                 conct.close_connection(client)
    #                 return {'statusCode': 200, 'body': 'Not enough components were procured for this bom'}
    #         m_parts = list(data[m_kit_key].values())
    #         if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
    #             conct.close_connection(client)
    #             return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}
    #         pk_id = result[0]["pk_id"]
    #         cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
    #                         for key in data.keys() if key.startswith("M_KIT")
    #                         for part, details in data[key].items()}
    #         for i in range(len(cmpt_id_and_qty)):
    #             part = "part" + str(i + 1)
    #             cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
    #             qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
    #             activity[cmpt_id]['closing_qty'] = qty
    #             out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
    #                 cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data[cmpt_id].keys() else (
    #                 cmpt_id_and_qty[part]["provided_qty"])
    #             db_con.Inventory.update_one(
    #                 {"pk_id": cmpt_id},
    #                 {"$set": {"all_attributes.qty": qty, "all_attributes.out_going_qty": out_going_qty}}
    #             )
    #         m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
    #         if m_kit_key:
    #             db_con.BoxBuilding.update_one(
    #                 {"pk_id": pk_id},
    #                 {"$set": {f"all_attributes.{m_kit_key}": data[m_kit_key]}}
    #             )
    #         bom_id = data["bom_id"]
    #         data_bom = db_con.BOM.find({"pk_id": bom_id}, {"sk_timeStamp": 1})
    #         bom_timeStamp = data_bom[0]["sk_timeStamp"]
    #         db_con.BOM.update_one(
    #             {"pk_id": bom_id},
    #             {"$set": {f"all_attributes.status": "Bom_assigned"}}
    #         )
    #         boards = data['boards']
    #         if board_keys:
    #             for key in board_keys:
    #                 # db_con.Boards.update_one({'pk_id': board_id},
    #                 #                          {"$set": {f"all_attributes.boards.{key}.status": "Assigned"}})
    #                 filter_criteria = {
    #                     'all_attributes.outward_id': data["outward_id"]
    #                 }
    #                 # Iterate through each board in the boards_kit and set boardkits_status
    #                 for boards_kit, boards_info in boards.items():
    #                     for board, board_info in boards_info.items():
    #                         if isinstance(board_info, dict):
    #                             pcba_id = board_info.get('pcba_id')
    #                             matched = False
    #                             for data_kit, data_boards in data['boards'].items():
    #                                 for data_board, data_board_info in data_boards.items():
    #                                     if data_board_info.get('pcba_id') == pcba_id:
    #                                         db_con.Boards.update_one(
    #                                             filter_criteria,
    #                                             {
    #                                                 '$set': {
    #                                                     f'all_attributes.boards.{boards_kit}.{board}.boardkits_status': "Assigned"
    #                                                 }
    #                                             }
    #                                         )
    #                                         matched = True
    #                                         break
    #                                 if matched:
    #                                     break
    #                             if not matched:
    #                                 print(f"No match found for pcba_id: {pcba_id} in {boards_kit} - {board}")
    #         if data.get("boards"):
    #             # bk1 = data["all_attributes"]["boards"]
    #             bk2 = data["boards"]
    #             # combined_dict = {**bk1, **bk2}
    #             combined_dict = {**bk2}
    #             for key in combined_dict:
    #                 combined_dict[key]['status'] = "Assigned"
    #             for key, value in data["boards"].items():
    #                 if key.startswith("boards_kit"):
    #                     for board_key, board_value in combined_dict.items():
    #                         db_con.BoxBuilding.update_one(
    #                             {"pk_id": pk_id},
    #                             {"$set": {f"all_attributes.boards.{key}": board_value}},
    #                             upsert=True
    #                         )
    #             if board_keys:
    #                 for key in board_keys:
    #                     filter_criteria = {
    #                             'pk_id': data["BB_id"]
    #                         }
    #                     for boards_kit, boards_info in combined_dict.items():
    #                             for board, board_info in boards_info.items():
    #                                 if isinstance(board_info, dict):
    #                                     pcba_id = board_info.get('pcba_id')
    #                                     matched = False
    #                                     for data_kit, data_boards in data['boards'].items():
    #                                         for data_board, data_board_info in data_boards.items():
    #                                             if data_board_info.get('pcba_id') != pcba_id:
    #                                                 db_con.BoxBuilding.update_one(
    #                                                     filter_criteria,
    #                                                     {
    #                                                         '$set': {
    #                                                             f'all_attributes.boards.{boards_kit}.{board}.boardkits_status': "Assigned"
    #                                                         }
    #                                                     },
    #                                                     upsert=False
    #                                                 )
    #                                                 matched = True
    #                                                 break
    #                                         if matched:
    #                                             break
    #                                     if not matched:
    #                                         print(f"No match found for pcba_id: {pcba_id} in {boards_kit} - {board}")
    #             # db_con.BoxBuilding.update_one(
    #             #     {"pk_id": pk_id},
    #             #     {"$set": {"all_attributes.boards": combined_dict}}
    #             # )
    #         if 'documents' in data and data['documents']:
    #             doc = {}
    #             existing_docs = db_con.BoxBuilding.find_one({"pk_id": pk_id}, {"all_attributes.documents": 1})
    #             if existing_docs and 'documents' in existing_docs.get('all_attributes', {}):
    #                 doc.update(existing_docs['all_attributes']['documents'])
    #             for inx, docs in enumerate(data['documents']):
    #                 image_path = file_uploads.upload_file("boxbuilding", "PtgCms" + env_type, "", "E-Kit" + str(inx),
    #                                                     docs["doc_name"], docs['doc_body'])
    #                 doc[docs["doc_name"]] = image_path
    #             db_con.BoxBuilding.update_one(
    #                 {"pk_id": pk_id},
    #                 {"$set": {"all_attributes.documents": doc}},
    #                 upsert=True
    #             )
    #             # db_con.BoxBuilding.insert_one(
    #             #     {"pk_id": pk_id},
    #             #     {"$set": {"all_attributes.documents": doc}}
    #             # )
    #         conct.close_connection(client)
    #         return {"statusCode": 200, "body": "BoxBuilding updated successfully"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': str(err)}
 



    # def cmsBomOutwardInfoSaveAssignToBoxBuilding2(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         bb_id = data.get("BB_id")
    #         sk_timeStamp = (datetime.now()).isoformat()
    #         result = list(
    #             db_con.BoxBuilding.find({"pk_id": bb_id}, {"pk_id": 1, "sk_timeStamp": 1, "all_attributes": 1}))
    #         if not result:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No Data Found"}
    #         board_id = result[0]["all_attributes"]["boards_id"]
    #         board_data = db_con.Boards.find_one({"pk_id": board_id})
    #         if not board_data:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No Board Data Found"}
    #         boards = board_data['all_attributes']['boards']
    #         board_keys = list(boards.keys())
    #         part_batch_info = find_stock_inwards(data['bom_id'], db_con, 'M_parts')
    #         part_batch_info = part_batch_info['part_batch_info']
    #         if not part_batch_info:
    #             conct.close_connection(client)
    #             return {'statusCode': 200, 'body': 'No inwards for this bom'}
    #         activity = {}
    #         activity_id_record = db_con.all_tables.find_one({"pk_id": "top_ids"}, {"all_attributes.ActivityId": 1})
    #         activity_id = int(activity_id_record['all_attributes'].get('ActivityId', "0")) + 1
    #         partner_records = db_con.Partners.find({"pk_id": data['partner_id']}, {"all_attributes.partner_name": 1})
    #         partner_name = ""
    #         for partner_record in partner_records:
    #             if 'all_attributes' in partner_record and 'partner_name' in partner_record['all_attributes']:
    #                 partner_name = partner_record['all_attributes']['partner_name']
    #                 break
    #         if not partner_name:
    #             conct.close_connection(client)
    #             return {'statusCode': 404, 'body': 'No Partner Data Found'}
    #         invent_data = list(
    #             db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1, "all_attributes.qty": 1,
    #                                     "all_attributes.out_going_qty": 1}))
    #         invent_data = {item['all_attributes']['cmpt_id']: {"qty": item['all_attributes']['qty'],
    #                                                         "out_going_qty": item['all_attributes'].get(
    #                                                             'out_going_qty', '0')}
    #                     for item in invent_data}
    #         m_parts = []
    #         m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
    #         kit_info = get_kit_and_boards_info(result[0]['all_attributes'], 'BOXBUILDING')
    #         for key, value in data[m_kit_key].items():
    #             var = batch_number_allocation(part_batch_info, int(value['provided_qty']), value['cmpt_id'], kit_info)
    #             if var:
    #                 data[m_kit_key][key]['batch_no'] = var['batch_string']
    #                 activity[value['cmpt_id']] = {
    #                     "mfr_prt_num": value.get("mfr_prt_num", "-"),
    #                     "date": str(date.today()),
    #                     "action": "Utilized",
    #                     "Description": "Utilized",
    #                     "issued_to": partner_name,
    #                     "po_no": var['po_id'],
    #                     'invoice_no': var["invoice_no"],
    #                     "cmpt_id": value.get("cmpt_id", ""),
    #                     "ctgr_id": value.get("ctgr_id", ""),
    #                     "prdt_name": value.get("prdt_name", ""),
    #                     "description": value.get("description", ""),
    #                     "packaging": value.get("packaging", ""),
    #                     "inventory_position": value.get("inventory_position", ""),
    #                     "qty": value['provided_qty'],
    #                     "batchId": var['batch_string'],
    #                     "used_qty": value['provided_qty'],
    #                     "lot_no": var["lot_no"]
    #                 }
    #             else:
    #                 conct.close_connection(client)
    #                 return {'statusCode': 200, 'body': 'Not enough components were procured for this bom'}
    #         m_parts = list(data[m_kit_key].values())
    #         if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
    #             conct.close_connection(client)
    #             return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}
    #         pk_id = result[0]["pk_id"]
    #         cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
    #                         for key in data.keys() if key.startswith("M_KIT")
    #                         for part, details in data[key].items()}
    #         for i in range(len(cmpt_id_and_qty)):
    #             part = "part" + str(i + 1)
    #             cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
    #             qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
    #             activity[cmpt_id]['closing_qty'] = qty
    #             out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
    #                 cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data[cmpt_id].keys() else (
    #                 cmpt_id_and_qty[part]["provided_qty"])
    #             db_con.Inventory.update_one(
    #                 {"pk_id": cmpt_id},
    #                 {"$set": {"all_attributes.qty": qty, "all_attributes.out_going_qty": out_going_qty}}
    #             )
    #         m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
    #         if m_kit_key:
    #             db_con.BoxBuilding.update_one(
    #                 {"pk_id": pk_id},
    #                 {"$set": {f"all_attributes.{m_kit_key}": data[m_kit_key]}}
    #             )
    #         bom_id = data["bom_id"]
    #         data_bom = db_con.BOM.find({"pk_id": bom_id}, {"sk_timeStamp": 1})
    #         bom_timeStamp = data_bom[0]["sk_timeStamp"]
    #         db_con.BOM.update_one(
    #             {"pk_id": bom_id},
    #             {"$set": {f"all_attributes.status": "Bom_assigned"}}
    #         )
    #         boards = data['boards']
    #         if board_keys:
    #             for key in board_keys:
    #                 # db_con.Boards.update_one({'pk_id': board_id},
    #                 #                          {"$set": {f"all_attributes.boards.{key}.status": "Assigned"}})
    #                 filter_criteria = {
    #                     'all_attributes.outward_id': data["outward_id"]
    #                 }
    #                 # Iterate through each board in the boards_kit and set boardkits_status
    #                 for boards_kit, boards_info in boards.items():
    #                     for board, board_info in boards_info.items():
    #                         if isinstance(board_info, dict):
    #                             pcba_id = board_info.get('pcba_id')
    #                             matched = False
    #                             for data_kit, data_boards in data['boards'].items():
    #                                 for data_board, data_board_info in data_boards.items():
    #                                     if data_board_info.get('pcba_id') == pcba_id:
    #                                         db_con.Boards.update_one(
    #                                             filter_criteria,
    #                                             {
    #                                                 '$set': {
    #                                                     f'all_attributes.boards.{boards_kit}.{board}.boardkits_status': "Assigned"
    #                                                 }
    #                                             }
    #                                         )
    #                                         matched = True
    #                                         break
    #                                 if matched:
    #                                     break
    #                             if not matched:
    #                                 print(f"No match found for pcba_id: {pcba_id} in {boards_kit} - {board}")
    #         if data.get("boards"):
    #             # bk1 = data["all_attributes"]["boards"]
    #             bk2 = data["boards"]
    #             # combined_dict = {**bk1, **bk2}
    #             combined_dict = {**bk2}
    #             for key in combined_dict:
    #                 combined_dict[key]['status'] = "Assigned"
    #             print(combined_dict)
    #             db_con.BoxBuilding.update_one(
    #                 {"pk_id": pk_id},
    #                 {"$set": {"all_attributes.boards": combined_dict}}
    #             )
    #             if board_keys:
    #                 for key in board_keys:
    #                     filter_criteria = {
    #                         'pk_id': data["BB_id"]
    #                     }
    #                 for boards_kit, boards_info in combined_dict.items():
    #                         for board, board_info in boards_info.items():
    #                             if isinstance(board_info, dict):
    #                                 pcba_id = board_info.get('pcba_id')
    #                                 matched = False
    #                                 for data_kit, data_boards in data['boards'].items():
    #                                     for data_board, data_board_info in data_boards.items():
    #                                         if data_board_info.get('pcba_id') == pcba_id:
    #                                             db_con.BoxBuilding.update_one(
    #                                                 filter_criteria,
    #                                                 {
    #                                                     '$set': {
    #                                                         f'all_attributes.boards.{boards_kit}.{board}.boardkits_status': "Assigned"
    #                                                     }
    #                                                 }
    #                                             )
    #                                             matched = True
    #                                             break
    #                                     if matched:
    #                                         break
    #                                 if not matched:
    #                                     print(f"No match found for pcba_id: {pcba_id} in {boards_kit} - {board}")
    #             # db_con.BoxBuilding.update_one(
    #             #     {"pk_id": pk_id},
    #             #     {"$set": {"all_attributes.boards": combined_dict}}
    #             # )
    #         if 'documents' in data and data['documents']:
    #             doc = {}
    #             existing_docs = db_con.BoxBuilding.find_one({"pk_id": pk_id}, {"all_attributes.documents": 1})
    #             if existing_docs and 'documents' in existing_docs.get('all_attributes', {}):
    #                 doc.update(existing_docs['all_attributes']['documents'])
    #             for inx, docs in enumerate(data['documents']):
    #                 image_path = file_uploads.upload_file("boxbuilding", "PtgCms" + env_type, "", "E-Kit" + str(inx),
    #                                                     docs["doc_name"], docs['doc_body'])
    #                 doc[docs["doc_name"]] = image_path
    #             db_con.BoxBuilding.update_one(
    #                 {"pk_id": pk_id},
    #                 {"$set": {"all_attributes.documents": doc}},
    #                 upsert=True
    #             )
    #             # db_con.BoxBuilding.insert_one(
    #             #     {"pk_id": pk_id},
    #             #     {"$set": {"all_attributes.documents": doc}}
    #             # )
    #         conct.close_connection(client)
    #         return {"statusCode": 200, "body": "BoxBuilding updated successfully"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': str(err)}
    



    # def cmsBomOutwardInfoSaveAssignToBoxBuilding2(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         bb_id = data.get("BB_id")
    #         sk_timeStamp = (datetime.now()).isoformat()
    #         result = list(
    #             db_con.BoxBuilding.find({"pk_id": bb_id}, {"pk_id": 1, "sk_timeStamp": 1, "all_attributes": 1}))
    #         if not result:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No Data Found"}
    #         board_id = result[0]["all_attributes"]["boards_id"]
    #         board_data = db_con.Boards.find_one({"pk_id": board_id})
    #         if not board_data:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No Board Data Found"}
    #         boards = board_data['all_attributes']['boards']
    #         board_keys = list(boards.keys())
    #         part_batch_info = find_stock_inwards(data['bom_id'], db_con, 'M_parts')
    #         part_batch_info = part_batch_info['part_batch_info']
    #         if not part_batch_info:
    #             conct.close_connection(client)
    #             return {'statusCode': 200, 'body': 'No inwards for this bom'}
    #         activity = {}
    #         activity_id_record = db_con.all_tables.find_one({"pk_id": "top_ids"}, {"all_attributes.ActivityId": 1})
    #         activity_id = int(activity_id_record['all_attributes'].get('ActivityId', "0")) + 1
    #         partner_records = db_con.Partners.find({"pk_id": data['partner_id']}, {"all_attributes.partner_name": 1})
    #         partner_name = ""
    #         for partner_record in partner_records:
    #             if 'all_attributes' in partner_record and 'partner_name' in partner_record['all_attributes']:
    #                 partner_name = partner_record['all_attributes']['partner_name']
    #                 break
    #         if not partner_name:
    #             conct.close_connection(client)
    #             return {'statusCode': 404, 'body': 'No Partner Data Found'}
    #         invent_data = list(
    #             db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1, "all_attributes.qty": 1,
    #                                     "all_attributes.out_going_qty": 1}))
    #         invent_data = {item['all_attributes']['cmpt_id']: {"qty": item['all_attributes']['qty'],
    #                                                         "out_going_qty": item['all_attributes'].get(
    #                                                             'out_going_qty', '0')}
    #                     for item in invent_data}
    #         m_parts = []
    #         m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
    #         kit_info = get_kit_and_boards_info(result[0]['all_attributes'], 'BOXBUILDING')
    #         for key, value in data[m_kit_key].items():
    #             var = batch_number_allocation(part_batch_info, int(value['provided_qty']), value['cmpt_id'], kit_info)
    #             if var:
    #                 data[m_kit_key][key]['batch_no'] = var['batch_string']
    #                 activity[value['cmpt_id']] = {
    #                     "mfr_prt_num": value.get("mfr_prt_num", "-"),
    #                     "date": str(date.today()),
    #                     "action": "Utilized",
    #                     "Description": "Utilized",
    #                     "issued_to": partner_name,
    #                     "po_no": var['po_id'],
    #                     'invoice_no': var["invoice_no"],
    #                     "cmpt_id": value.get("cmpt_id", ""),
    #                     "ctgr_id": value.get("ctgr_id", ""),
    #                     "prdt_name": value.get("prdt_name", ""),
    #                     "description": value.get("description", ""),
    #                     "packaging": value.get("packaging", ""),
    #                     "inventory_position": value.get("inventory_position", ""),
    #                     "qty": value['provided_qty'],
    #                     "batchId": var['batch_string'],
    #                     "used_qty": value['provided_qty'],
    #                     "lot_no": var["lot_no"]
    #                 }
    #             else:
    #                 conct.close_connection(client)
    #                 return {'statusCode': 200, 'body': 'Not enough components were procured for this bom'}
    #         m_parts = list(data[m_kit_key].values())
    #         if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
    #             conct.close_connection(client)
    #             return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}
    #         pk_id = result[0]["pk_id"]
    #         cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
    #                         for key in data.keys() if key.startswith("M_KIT")
    #                         for part, details in data[key].items()}
    #         for i in range(len(cmpt_id_and_qty)):
    #             part = "part" + str(i + 1)
    #             cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
    #             qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
    #             activity[cmpt_id]['closing_qty'] = qty
    #             out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
    #                 cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data[cmpt_id].keys() else (
    #                 cmpt_id_and_qty[part]["provided_qty"])
    #             db_con.Inventory.update_one(
    #                 {"pk_id": cmpt_id},
    #                 {"$set": {"all_attributes.qty": qty, "all_attributes.out_going_qty": out_going_qty}}
    #             )
    #         m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
    #         if m_kit_key:
    #             db_con.BoxBuilding.update_one(
    #                 {"pk_id": pk_id},
    #                 {"$set": {f"all_attributes.{m_kit_key}": data[m_kit_key]}}
    #             )
    #         bom_id = data["bom_id"]
    #         data_bom = db_con.BOM.find({"pk_id": bom_id}, {"sk_timeStamp": 1})
    #         bom_timeStamp = data_bom[0]["sk_timeStamp"]
    #         db_con.BOM.update_one(
    #             {"pk_id": bom_id},
    #             {"$set": {f"all_attributes.status": "Bom_assigned"}}
    #         )
    #         boards = data['boards']
    #         if board_keys:
    #             for key in board_keys:
    #                 # db_con.Boards.update_one({'pk_id': board_id},
    #                 #                          {"$set": {f"all_attributes.boards.{key}.status": "Assigned"}})
    #                 filter_criteria = {
    #                     'all_attributes.outward_id': data["outward_id"]
    #                 }
    #                 # Iterate through each board in the boards_kit and set boardkits_status
    #                 for boards_kit, boards_info in boards.items():
    #                     for board, board_info in boards_info.items():
    #                         if isinstance(board_info, dict):
    #                             pcba_id = board_info.get('pcba_id')
    #                             matched = False
    #                             for data_kit, data_boards in data['boards'].items():
    #                                 for data_board, data_board_info in data_boards.items():
    #                                     if data_board_info.get('pcba_id') == pcba_id:
    #                                         db_con.Boards.update_one(
    #                                             filter_criteria,
    #                                             {
    #                                                 '$set': {
    #                                                     f'all_attributes.boards.{boards_kit}.{board}.boardkits_status': "Assigned"
    #                                                 }
    #                                             }
    #                                         )
    #                                         matched = True
    #                                         break
    #                                 if matched:
    #                                     break
    #                             if not matched:
    #                                 print(f"No match found for pcba_id: {pcba_id} in {boards_kit} - {board}")
    #         if data.get("boards"):
    #             # bk1 = data["all_attributes"]["boards"]
    #             bk2 = data["boards"]
    #             # combined_dict = {**bk1, **bk2}
    #             combined_dict = {**bk2}
    #             for key in combined_dict:
    #                 combined_dict[key]['status'] = "Assigned"
    #             print(combined_dict)
    #             db_con.BoxBuilding.update_one(
    #                 {"pk_id": pk_id},
    #                 {"$set": {"all_attributes.boards": combined_dict}},
    #                 upsert=True
    #             )
    #             if board_keys:
    #                 for key in board_keys:
    #                     filter_criteria = {
    #                         'pk_id': data["BB_id"]
    #                     }
    #                     for boards_kit, boards_info in combined_dict.items():
    #                             for board, board_info in boards_info.items():
    #                                 if isinstance(board_info, dict):
    #                                     pcba_id = board_info.get('pcba_id')
    #                                     matched = False
    #                                     for data_kit, data_boards in data['boards'].items():
    #                                         for data_board, data_board_info in data_boards.items():
    #                                             if data_board_info.get('pcba_id') == pcba_id:
    #                                                 db_con.BoxBuilding.update_one(
    #                                                     filter_criteria,
    #                                                     {
    #                                                         '$set': {
    #                                                             f'all_attributes.boards.{boards_kit}.{board}.boardkits_status': "Assigned"
    #                                                         }
    #                                                     }
    #                                                 )
    #                                                 matched = True
    #                                                 break
    #                                         if matched:
    #                                             break
    #                                     if not matched:
    #                                         print(f"No match found for pcba_id: {pcba_id} in {boards_kit} - {board}")
    #             # db_con.BoxBuilding.update_one(
    #             #     {"pk_id": pk_id},
    #             #     {"$set": {"all_attributes.boards": combined_dict}}
    #             # )
    #         if 'documents' in data and data['documents']:
    #             doc = {}
    #             existing_docs = db_con.BoxBuilding.find_one({"pk_id": pk_id}, {"all_attributes.documents": 1})
    #             if existing_docs and 'documents' in existing_docs.get('all_attributes', {}):
    #                 doc.update(existing_docs['all_attributes']['documents'])
    #             for inx, docs in enumerate(data['documents']):
    #                 image_path = file_uploads.upload_file("boxbuilding", "PtgCms" + env_type, "", "E-Kit" + str(inx),
    #                                                     docs["doc_name"], docs['doc_body'])
    #                 doc[docs["doc_name"]] = image_path
    #             db_con.BoxBuilding.update_one(
    #                 {"pk_id": pk_id},
    #                 {"$set": {"all_attributes.documents": doc}},
    #                 upsert=True
    #             )
    #             # db_con.BoxBuilding.insert_one(
    #             #     {"pk_id": pk_id},
    #             #     {"$set": {"all_attributes.documents": doc}}
    #             # )
    #         conct.close_connection(client)
    #         return {"statusCode": 200, "body": "BoxBuilding updated successfully"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': str(err)}
    


    
    # def cmsBomOutwardInfoSaveAssignToBoxBuilding2(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         bb_id = data.get("BB_id")
    #         sk_timeStamp = (datetime.now()).isoformat()
    #         result = list(db_con.BoxBuilding.find({"pk_id": bb_id}, {"pk_id": 1, "sk_timeStamp": 1, "all_attributes": 1}))

    #         if not result:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No Data Found"}

    #         board_id = result[0]["all_attributes"]["boards_id"]
    #         board_data = db_con.Boards.find_one({"pk_id": board_id})
    #         if not board_data:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No Board Data Found"}

    #         boards = board_data['all_attributes']['boards']
    #         board_keys = list(boards.keys())

    #         part_batch_info = find_stock_inwards(data['bom_id'], db_con, 'M_parts')
    #         part_batch_info = part_batch_info['part_batch_info']

    #         if not part_batch_info:
    #             conct.close_connection(client)
    #             return {'statusCode': 200, 'body': 'No inwards for this bom'}

    #         activity = {}
    #         activity_id_record = db_con.all_tables.find_one({"pk_id": "top_ids"}, {"all_attributes.ActivityId": 1})
    #         activity_id = int(activity_id_record['all_attributes'].get('ActivityId', "0")) + 1

    #         partner_records = db_con.Partners.find({"pk_id": data['partner_id']}, {"all_attributes.partner_name": 1})
    #         partner_name = ""
    #         for partner_record in partner_records:
    #             if 'all_attributes' in partner_record and 'partner_name' in partner_record['all_attributes']:
    #                 partner_name = partner_record['all_attributes']['partner_name']
    #                 break

    #         if not partner_name:
    #             conct.close_connection(client)
    #             return {'statusCode': 404, 'body': 'No Partner Data Found'}

    #         invent_data = list(db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1, "all_attributes.qty": 1,
    #                                                     "all_attributes.out_going_qty": 1}))
    #         invent_data = {item['all_attributes']['cmpt_id']: {"qty": item['all_attributes']['qty'],
    #                                                         "out_going_qty": item['all_attributes'].get('out_going_qty', '0')}
    #                     for item in invent_data}

    #         m_parts = []
    #         m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
    #         kit_info = get_kit_and_boards_info(result[0]['all_attributes'], 'BOXBUILDING')

    #         for key, value in data[m_kit_key].items():
    #             var = batch_number_allocation(part_batch_info, int(value['provided_qty']), value['cmpt_id'], kit_info)
    #             if var:
    #                 data[m_kit_key][key]['batch_no'] = var['batch_string']
    #                 activity[value['cmpt_id']] = {
    #                     "mfr_prt_num": value.get("mfr_prt_num", "-"),
    #                     "date": str(date.today()),
    #                     "action": "Utilized",
    #                     "Description": "Utilized",
    #                     "issued_to": partner_name,
    #                     "po_no": var['po_id'],
    #                     'invoice_no': var["invoice_no"],
    #                     "cmpt_id": value.get("cmpt_id", ""),
    #                     "ctgr_id": value.get("ctgr_id", ""),
    #                     "prdt_name": value.get("prdt_name", ""),
    #                     "description": value.get("description", ""),
    #                     "packaging": value.get("packaging", ""),
    #                     "inventory_position": value.get("inventory_position", ""),
    #                     "qty": value['provided_qty'],
    #                     "batchId": var['batch_string'],
    #                     "used_qty": value['provided_qty'],
    #                     "lot_no": var["lot_no"]
    #                 }
    #             else:
    #                 conct.close_connection(client)
    #                 return {'statusCode': 200, 'body': 'Not enough components were procured for this bom'}

    #         m_parts = list(data[m_kit_key].values())
    #         if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
    #             conct.close_connection(client)
    #             return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}

    #         pk_id = result[0]["pk_id"]
    #         cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
    #                         for key in data.keys() if key.startswith("M_KIT")
    #                         for part, details in data[key].items()}

    #         for i in range(len(cmpt_id_and_qty)):
    #             part = "part" + str(i + 1)
    #             cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
    #             qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
    #             activity[cmpt_id]['closing_qty'] = qty
    #             out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
    #                 cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data[cmpt_id].keys() else (
    #                         cmpt_id_and_qty[part]["provided_qty"])
    #             db_con.Inventory.update_one(
    #                 {"pk_id": cmpt_id},
    #                 {"$set": {"all_attributes.qty": qty, "all_attributes.out_going_qty": out_going_qty}}
    #             )

    #         m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
    #         if m_kit_key:
    #             db_con.BoxBuilding.update_one(
    #                 {"pk_id": pk_id},
    #                 {"$set": {f"all_attributes.{m_kit_key}": data[m_kit_key]}}
    #             )

    #         bom_id = data["bom_id"]
    #         data_bom = db_con.BOM.find({"pk_id": bom_id}, {"sk_timeStamp": 1})
    #         bom_timeStamp = data_bom[0]["sk_timeStamp"]

    #         db_con.BOM.update_one(
    #             {"pk_id": bom_id},
    #             {"$set": {f"all_attributes.status": "Bom_assigned"}}
    #         )

    #         if board_keys:
    #             for key in board_keys:
    #                 db_con.Boards.update_one({'pk_id': board_id},
    #                                         {"$set": {f"all_attributes.boards.{key}.status": "Assigned"}})

    #         if data.get("boards"):
    #             bk1 = data["all_attributes"]["boards"]
    #             bk2 = data["boards"]
    #             combined_dict = {**bk1, **bk2}
    #             for key in combined_dict:
    #                 combined_dict[key]['status'] = "Assigned"
    #             db_con.BoxBuilding.update_one(
    #                 {"pk_id": pk_id},
    #                 {"$set": {"all_attributes.boards": combined_dict}}
    #             )

    #         if 'documents' in data and data['documents']:
    #             doc = {}
    #             existing_docs = db_con.BoxBuilding.find_one({"pk_id": pk_id}, {"all_attributes.documents": 1})
    #             if existing_docs and 'documents' in existing_docs.get('all_attributes', {}):
    #                 doc.update(existing_docs['all_attributes']['documents'])
                
    #             for inx, docs in enumerate(data['documents']):
    #                 image_path = file_uploads.upload_file("boxbuilding", "PtgCms" + env_type, "", "E-Kit" + str(inx),
    #                                                     docs["doc_name"], docs['doc_body'])
    #                 doc[docs["doc_name"]] = image_path
                
    #             db_con.BoxBuilding.update_one(
    #                     {"pk_id": pk_id},
    #                     {"$set": {"all_attributes.documents": doc}},
    #                     upsert=True
    #                 )

    #             # db_con.BoxBuilding.insert_one(
    #             #     {"pk_id": pk_id},
    #             #     {"$set": {"all_attributes.documents": doc}}
    #             # )

    #         conct.close_connection(client)
    #         return {"statusCode": 200, "body": "BoxBuilding updated successfully"}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': str(err)}






    # def cmsBomOutwardInfoSaveAssignToBoxBuilding2(request_body):
    #     data = request_body
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     bb_id = data.get("BB_id")
    #     sk_timeStamp = (datetime.now()).isoformat()
    #     result = list(db_con.BoxBuilding.find({"pk_id": bb_id}, {"pk_id": 1, "sk_timeStamp": 1, "all_attributes": 1}))
    #     board_id = [i["all_attributes"]["boards_id"] for i in result][0]
    #     board_data = db_con.Boards.find_one({"pk_id": board_id})
    #     boards = board_data['all_attributes']['boards']
    #     board_keys = list(boards.keys())
    #     part_batch_info = find_stock_inwards(data['bom_id'],db_con,'M_parts')
    #     part_batch_info = part_batch_info['part_batch_info']
        
    #     if part_batch_info:
    #         activity = {}
    #         activity_id = db_con.all_tables.find_one({"pk_id":"top_ids"},{"all_attributes.ActivityId":1})
    #         activity_id = int(activity_id['all_attributes'].get('ActivityId',"0"))+1
    #         partner_name = db_con.Partners.find_one({"pk_id":data['partner_id']},{"all_attributes.partner_name":1})
    #         invent_data = list(db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1, "all_attributes.qty": 1,
    #                                                     "all_attributes.out_going_qty": 1}))
    #         invent_data = {item['all_attributes']['cmpt_id']: {"qty": item['all_attributes']['qty'],
    #                                                         "out_going_qty": item['all_attributes'].get('out_going_qty',
    #                                                                                                     '0')} for item in
    #                     invent_data}
    #         m_parts = []
    #         m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
    #         kit_info= get_kit_and_boards_info(result[0]['all_attributes'],'BOXBUILDING')
    #         for key,value in data[m_kit_key].items():
    #             # batch_info = {inx:value for inx,value in enumerate(part_batch_info[value['cmpt_id']])}
    #             var = batch_number_allocation(part_batch_info,int(value['provided_qty']),value['cmpt_id'],kit_info)
    #             # return var
    #             if var:
    #                 data[m_kit_key][key]['batch_no'] = var['batch_string']
    #                 activity[value['cmpt_id']] = {
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
    #                                 # "closing_qty": "",
    #                                 "qty": value['provided_qty'],
    #                                 "batchId": var['batch_string'],
    #                                 "used_qty":value['provided_qty'],
    #                                 "lot_no":var["lot_no"]
    #                             }
    #             else:
    #                 return {'statusCode': 200, 'body': 'Not enough components were procured for this bom'}
    #         m_parts = list(data[m_kit_key].values())
    #         if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
    #             return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}
    #         if result:
    #             pk_id = result[0]["pk_id"]
    #             result = result[0]
    #             cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
    #                             for key in data.keys() if key.startswith("M_KIT")
    #                             for part, details in data[key].items()}
    #             for i in range(len(cmpt_id_and_qty)):
    #                 part = "part" + str(i + 1)
    #                 cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
    #                 qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
    #                 activity[cmpt_id]['closing_qty'] = qty
    #                 out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
    #                     cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data[cmpt_id].keys() else (
    #                 cmpt_id_and_qty[part]["provided_qty"])
    #                 upd = db_con.Inventory.update_one(
    #                     {"pk_id": cmpt_id},
    #                     {"$set": {"all_attributes.qty": qty, "all_attributes.out_going_qty": out_going_qty}}
    #                 )
    #             m_kit_key = next((key for key in data.keys() if key.startswith("M_KIT")), None)
    #             if m_kit_key:
    #                 res = db_con.BoxBuilding.update_one(
    #                     {"pk_id": pk_id},
    #                     {"$set": {f"all_attributes.{m_kit_key}": data[m_kit_key]}}
    #                 )
    #                 bom_id = data["bom_id"]
    #                 data_bom = db_con.BOM.find({"pk_id": bom_id}, {"sk_timeStamp": 1})
    #                 bom_timeStamp = data_bom[0]["sk_timeStamp"]
    #                 response = db_con.BOM.update_one(
    #                     {"pk_id": bom_id},
    #                     {"$set": {f"all_attributes.status": "Bom_assigned"}}
    #                 )
    #             if board_keys:
    #                 for key in board_keys:
    #                     db_con.Boards.update_one({'pk_id': board_id},
    #                                             {"$set": {f"all_attributes.boards.{key}.status": "Assigned"}})
    #             if data["boards"]:
    #                 print("boards")
    #                 bk1 = data["all_attributes"]["boards"]
    #                 bk2 = data["boards"]
    #                 combined_dict = {**bk1, **bk2}
    #                 for key in combined_dict:
    #                     combined_dict[key]['status'] = "Assigned"
    #                 resp = db_con.BoxBuilding.update_one(
    #                     {"pk_id": pk_id},
    #                     {"$set": {"all_attributes.boards": combined_dict}}
    #                 )
    #                 res = db_con['ActivityDetails'].insert_one(
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
    #             conct.close_connection(client)

    #             return {"statusCode": 200, "body": "BoxBuilding updated successfully"}
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No Data Found"}
    #     else:
    #         return {'statusCode': 200, 'body': 'no inwards for this bom'}


#     import re
# import sys


    def cmsBomOutwardInfoGetAssignToBoxBuilding2(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            bb_id = data["bom_id"]
            outward_id = data.get("outward_id")

            data1 = list(db_con.BoxBuilding.find({
                "$and": [
                    {"all_attributes.bom_id": bb_id},
                    {"all_attributes.outward_id": outward_id}
                ]
            }, {"_id": 0, "all_attributes": 1}))

            data2 = list(db_con.Boards.find({"all_attributes.bom_id": bb_id, "all_attributes.outward_id": outward_id},
                                            {"_id": 0, "all_attributes": 1}))

            part_info1 = data2[0]['all_attributes']
            if data1:
                data1 = data1[0]
                part_info = data1['all_attributes']
                all_keys = sorted(part_info.keys(), key=lambda x: [int(i) if i.isdigit() else i for i in re.split(r'(\d+)', x)], reverse=True)
                latest_m_kit_key = next((kit_key for kit_key in all_keys if kit_key.startswith('M_KIT')), None)

                parts_no = 0
                body = {}
                body["BB_id"] = data1["all_attributes"]["BB_id"]
                body["against_po"] = data1["all_attributes"].get("against_po", "")
                top_negative_balance_part = {}

                if latest_m_kit_key and latest_m_kit_key in part_info:
                    for part_name, part_details in part_info[latest_m_kit_key].items():
                        if 'balance_qty' in part_details and int(part_details['balance_qty']) < 0:
                            part_details["qty_per_board"] = part_details["balance_qty"].replace("-", "")
                            parts_no += 1
                            top_negative_balance_part["part" + str(parts_no)] = part_details

                            # Fetch ptg_stock
                            cmpt_id = part_details["cmpt_id"]
                            inventoryData = list(db_con.Inventory.find({"pk_id": cmpt_id}, {"_id": 0, "all_attributes.qty": 1}))
                            part_details["ptg_stock"] = inventoryData[0]["all_attributes"]["qty"] if inventoryData else None

                            # Fetch partner_stock
                            partnersData = list(db_con.Partners.find({
                                "all_attributes.available_stock.M-Kit.part1.cmpt_id": cmpt_id
                            }, {"_id": 0, "all_attributes.available_stock.M-Kit.part1.available_qty": 1}))
                            part_details["partner_stock"] = partnersData[0]["all_attributes"]["available_stock"]["M-Kit"]["part1"]["available_qty"] if partnersData else None

                latest_m_kit_key = int(latest_m_kit_key.split("T")[1]) + 1
                body["M_KIT" + str(latest_m_kit_key)] = top_negative_balance_part

                # Filter boards based on the conditions
                valid_board_kits = {}
                for board_kit, boards in part_info1["boards"].items():
                    filtered_boards = {}
                    for board_id, board_info in boards.items():
                        print(f"Checking board {board_id} in kit {board_kit}")
                        print(f"boardkits_status: {board_info.get('boardkits_status')}, comment: {board_info.get('comment')}")
                        if board_info.get('boardkits_status') == "Unassigned" and board_info.get('comment'):
                            print(f"Adding board {board_id} to filtered_boards")
                            filtered_boards[board_id] = board_info
                    if filtered_boards:
                        print(f"Adding kit {board_kit} to valid_board_kits")
                        valid_board_kits[board_kit] = filtered_boards

                if top_negative_balance_part or valid_board_kits:
                    body.update(valid_board_kits)
                    conct.close_connection(client)
                    return {"statusCode": 200, "body": body}
                else:
                    conct.close_connection(client)
                    return {"statusCode": 404, "body": "NO Data Found"}
            else:
                conct.close_connection(client)
                return {"statusCode": 404, "body": "NO Data Found"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': str(err)}

    # def cmsBomOutwardInfoGetAssignToBoxBuilding2(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         bb_id = data["bom_id"]
    #         outward_id = data.get("outward_id")
    #         data1 = list(db_con.BoxBuilding.find({
    #             "$and": [
    #                 {"all_attributes.bom_id": bb_id},
    #                 {"all_attributes.outward_id": outward_id}
    #             ]
    #         }, {"_id": 0, "all_attributes": 1}))
    #         # print(data1)
    #         data2 = list(db_con.Boards.find({"all_attributes.bom_id": bb_id, "all_attributes.outward_id": outward_id},
    #                                         {"_id": 0, "all_attributes": 1}))
    #         # print(data2)
    #         part_info1 = data2[0]['all_attributes']
    #         if data1:
    #             data1 = data1[0]
    #             part_info = data1['all_attributes']
    #             all_keys = sorted(part_info.keys(), key=lambda x: [int(i) if i.isdigit() else i for i in re.split(r'(\d+)', x)], reverse=True)
    #             latest_m_kit_key = next((kit_key for kit_key in all_keys if kit_key.startswith('M_KIT')), None)
    #             print(latest_m_kit_key)
    #             parts_no = 0
    #             body = {}
    #             body["BB_id"] = data1["all_attributes"]["BB_id"]
    #             body["against_po"] = data1["all_attributes"].get("against_po", "")
    #             top_negative_balance_part = {}
    #             if latest_m_kit_key and latest_m_kit_key in part_info:
    #                 for part_name, part_details in part_info[latest_m_kit_key].items():
    #                     if 'balance_qty' in part_details and int(part_details['balance_qty']) < 0:
    #                         part_details["qty_per_board"] = part_details["balance_qty"].replace("-", "")
    #                         parts_no += 1
    #                         top_negative_balance_part["part" + str(parts_no)] = part_details
    #                         # Fetch ptg_stock
    #                         cmpt_id = part_details["cmpt_id"]
    #                         inventoryData = list(db_con.Inventory.find({"pk_id": cmpt_id}, {"_id": 0, "all_attributes.qty": 1}))
    #                         part_details["ptg_stock"] = inventoryData[0]["all_attributes"]["qty"] if inventoryData else None
    #                         # Fetch partner_stock
    #                         partnersData = list(db_con.Partners.find({
    #                             "all_attributes.available_stock.M-Kit.part1.cmpt_id": cmpt_id
    #                         }, {"_id": 0, "all_attributes.available_stock.M-Kit.part1.available_qty": 1}))
    #                         part_details["partner_stock"] = partnersData[0]["all_attributes"]["available_stock"]["M-Kit"]["part1"]["available_qty"] if partnersData else None
    #             latest_m_kit_key = int(latest_m_kit_key.split("T")[1]) + 1
    #             body["M_KIT" + str(latest_m_kit_key)] = top_negative_balance_part
    #             for board_id, board_info in part_info1["boards"].items():
    #                 if not board_info.get("status", ""):
    #                     # body[board_id] = board_info
    #                     # To get only Unassigned boards from board kits
    #                     for k,v in board_info.items():
    #                         if v.get('boardkits_status') == "Unassigned" and v.get('comment') == "":
    #                             body[board_id] = board_info
    #             if top_negative_balance_part:
    #                 conct.close_connection(client)
    #                 return {"statusCode": 200, "body": body}
    #             else:
    #                 conct.close_connection(client)
    #                 return {"statusCode": 404, "body": "NO Data Found"}
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "NO Data Found"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': str(err)}
    




    # def cmsBomOutwardInfoGetAssignToBoxBuilding2(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         bb_id = data["bom_id"]
    #         outward_id = data.get("outward_id")

    #         data1 = list(db_con.BoxBuilding.find({
    #             "$and": [
    #                 {"all_attributes.bom_id": bb_id},
    #                 {"all_attributes.outward_id": outward_id}
    #             ]
    #         }, {"_id": 0, "all_attributes": 1}))
    #         print(data1)
            
    #         data2 = list(db_con.Boards.find({
    #             "all_attributes.bom_id": bb_id, 
    #             "all_attributes.outward_id": outward_id
    #         }, {"_id": 0, "all_attributes": 1}))
    #         print(data2)

    #         part_info1 = data2[0]['all_attributes']
    #         if data1:
    #             data1 = data1[0]
    #             part_info = data1['all_attributes']
    #             all_keys = sorted(part_info.keys(), key=lambda x: [int(i) if i.isdigit() else i for i in re.split(r'(\d+)', x)], reverse=True)
    #             latest_m_kit_key = next((kit_key for kit_key in all_keys if kit_key.startswith('M_KIT')), None)
    #             print(latest_m_kit_key)

    #             parts_no = 0
    #             body = {}
    #             body["BB_id"] = data1["all_attributes"]["BB_id"]
    #             body["against_po"] = data1["all_attributes"].get("against_po", "")
    #             top_negative_balance_part = {}

    #             if latest_m_kit_key and latest_m_kit_key in part_info:
    #                 for part_name, part_details in part_info[latest_m_kit_key].items():
    #                     if 'balance_qty' in part_details and int(part_details['balance_qty']) < 0:
    #                         part_details["qty_per_board"] = part_details["balance_qty"].replace("-", "")
    #                         parts_no += 1
    #                         top_negative_balance_part["part" + str(parts_no)] = part_details

    #                         # Fetch ptg_stock
    #                         cmpt_id = part_details["cmpt_id"]
    #                         inventoryData = list(db_con.Inventory.find({"pk_id": cmpt_id}, {"_id": 0, "all_attributes.qty": 1}))
    #                         part_details["ptg_stock"] = inventoryData[0]["all_attributes"]["qty"] if inventoryData else None

    #                         # Fetch partner_stock
    #                         partnersData = list(db_con.Partners.find({
    #                             "all_attributes.available_stock.M-Kit.part1.cmpt_id": cmpt_id
    #                         }, {"_id": 0, "all_attributes.available_stock.M-Kit.part1.available_qty": 1}))

    #                         part_details["partner_stock"] = partnersData[0]["all_attributes"]["available_stock"]["M-Kit"]["part1"]["available_qty"] if partnersData else None

    #             latest_m_kit_key = int(latest_m_kit_key.split("T")[1]) + 1
    #             body["M_KIT" + str(latest_m_kit_key)] = top_negative_balance_part

    #             for kit_key, boards in part_info1["boards"].items():
    #                 filtered_boards = {board_id: board_info for board_id, board_info in boards.items() if board_info.get("comment", "")}
    #                 if filtered_boards:
    #                     body[kit_key] = filtered_boards

    #             if top_negative_balance_part:
    #                 conct.close_connection(client)
    #                 return {"statusCode": 200, "body": body}
    #             else:
    #                 conct.close_connection(client)
    #                 return {"statusCode": 404, "body": "NO Data Found"}
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "NO Data Found"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': str(err)}


    
    # def cmsBomOutwardInfoGetAssignToBoxBuilding2(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         bb_id = data["bom_id"]
    #         outward_id = data.get("outward_id")

    #         data1 = list(db_con.BoxBuilding.find({
    #             "$and": [
    #                 {"all_attributes.bom_id": bb_id},
    #                 {"all_attributes.outward_id": outward_id}
    #             ]
    #         }, {"_id": 0, "all_attributes": 1}))
    #         print(data1)
            
    #         data2 = list(db_con.Boards.find({"all_attributes.bom_id": bb_id, "all_attributes.outward_id": outward_id},
    #                                         {"_id": 0, "all_attributes": 1}))
    #         print(data2)

    #         part_info1 = data2[0]['all_attributes']
    #         if data1:
    #             data1 = data1[0]
    #             part_info = data1['all_attributes']
    #             all_keys = sorted(part_info.keys(), key=lambda x: [int(i) if i.isdigit() else i for i in re.split(r'(\d+)', x)], reverse=True)
    #             latest_m_kit_key = next((kit_key for kit_key in all_keys if kit_key.startswith('M_KIT')), None)
    #             print(latest_m_kit_key)

    #             parts_no = 0
    #             body = {}
    #             body["BB_id"] = data1["all_attributes"]["BB_id"]
    #             body["against_po"] = data1["all_attributes"].get("against_po", "")
    #             top_negative_balance_part = {}

    #             if latest_m_kit_key and latest_m_kit_key in part_info:
    #                 for part_name, part_details in part_info[latest_m_kit_key].items():
    #                     if 'balance_qty' in part_details and int(part_details['balance_qty']) < 0:
    #                         part_details["qty_per_board"] = part_details["balance_qty"].replace("-", "")
    #                         parts_no += 1
    #                         top_negative_balance_part["part" + str(parts_no)] = part_details

    #                         # Fetch ptg_stock
    #                         cmpt_id = part_details["cmpt_id"]
    #                         inventoryData = list(db_con.Inventory.find({"pk_id": cmpt_id}, {"_id": 0, "all_attributes.qty": 1}))
    #                         part_details["ptg_stock"] = inventoryData[0]["all_attributes"]["qty"] if inventoryData else None

    #                         # Fetch partner_stock
    #                         partnersData = list(db_con.Partners.find({
    #                             "all_attributes.available_stock.M-Kit.part1.cmpt_id": cmpt_id
    #                         }, {"_id": 0, "all_attributes.available_stock.M-Kit.part1.available_qty": 1}))

    #                         part_details["partner_stock"] = partnersData[0]["all_attributes"]["available_stock"]["M-Kit"]["part1"]["available_qty"] if partnersData else None

    #             latest_m_kit_key = int(latest_m_kit_key.split("T")[1]) + 1
    #             body["M_KIT" + str(latest_m_kit_key)] = top_negative_balance_part

    #             for board_id, board_info in part_info1["boards"].items():
    #                 if not board_info.get("status", ""):
    #                     body[board_id] = board_info

    #             if top_negative_balance_part:
    #                 conct.close_connection(client)
    #                 return {"statusCode": 200, "body": body}
    #             else:
    #                 conct.close_connection(client)
    #                 return {"statusCode": 404, "body": "NO Data Found"}
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "NO Data Found"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': str(err)}


    # def cmsBomOutwardInfoGetAssignToBoxBuilding2(request_body):
    #     data = request_body
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     bb_id = data["bom_id"]
    #     outward_id = data.get("outward_id")
    #     data1 = list(db_con.BoxBuilding.find({
    #         "$and": [
    #             {"all_attributes.bom_id": bb_id},
    #             {"all_attributes.outward_id": outward_id}
    #         ]
    #     }, {"_id": 0, "all_attributes": 1}))
    #     data2 = list(db_con.Boards.find({"all_attributes.bom_id": bb_id, "all_attributes.outward_id": outward_id},
    #                                     {"_id": 0, "all_attributes": 1}))
    #     part_info1 = data2[0]['all_attributes']
    #     if data1:
    #         data1 = data1[0]
    #         part_info = data1['all_attributes']
    #         # all_keys = sorted(part_info.keys(), reverse=True)
    #         all_keys=sorted(part_info.keys(), key=lambda x: [int(i) if i.isdigit() else i for i in re.split(r'(\d+)', x)], reverse=True)
    #         latest_m_kit_key = next((kit_key for kit_key in all_keys if kit_key.startswith('M_KIT')), None)
    #         print(latest_m_kit_key)
    #         parts_no = 0
    #         body = {}
    #         body["BB_id"] = data1["all_attributes"]["BB_id"]
    #         body["against_po"] = data1["all_attributes"].get("against_po", "")
    #         top_negative_balance_part = {}
    #         # return data1["all_attributes"][latest_m_kit_key]
    #         for part_name, part_details in data1["all_attributes"][latest_m_kit_key].items():
    #             if int(part_details['balance_qty']) < 0:
    #                 part_details["qty_per_board"] = part_details["balance_qty"].replace("-", "")
    #                 parts_no = parts_no + 1
    #                 top_negative_balance_part["part" + str(parts_no)] = part_details
    #         # return top_negative_balance_part
    #         latest_m_kit_key = int(latest_m_kit_key.split("T")[1]) + 1
    #         body["M_KIT" + str(latest_m_kit_key)] = top_negative_balance_part
    #         for board_id, board_info in part_info1["boards"].items():
    #             if not board_info.get("status", ""):
    #                 body[board_id] = board_info
    #         if top_negative_balance_part:
    #             conct.close_connection(client)
    #             return {"statusCode": 200, "body": body}
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "NO Data Found"}
    #     else:
    #         conct.close_connection(client)
    #         return {"statusCode": 404, "body": "NO Data Found"}

    # def cmsBomOutwardInfoSaveAssignToBoxBuilding(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         sk_timeStamp = datetime.now().isoformat()
    #         # Process documents
    #         documents = data['documents']
    #         if isinstance(documents, list):
    #             doc = {}
    #             for idx, doc_info in enumerate(documents):
    #                 image_path = file_uploads.upload_file("boxbuilding", "PtgCms" + env_type, "", "E-Kit" + str(idx),
    #                                                     doc_info["doc_name"], doc_info['doc_body'])
    #                 doc[doc_info["doc_name"]] = image_path
    #             data['documents'] = doc
    #         elif isinstance(documents, dict):
    #             for doc_name, doc_url in documents.items():
    #                 if doc_name.endswith(".pdf"):
    #                     data['documents'] = {
    #                         doc_name: doc_url
    #                     }
    #         # Other data processing and insertion into database...
    #         data1 = list(db_con.BoxBuilding.find({'pk_id': "BB_1"}, {}))
    #         box_bilding_id = "1"
    #         bom_id = data['bom_id']
    #         # part_batch_info = find_stock_inwards(bom_id, db_con, 'M_parts').get('part_batch_info', {})
    #         part_batch_info = find_stock_inward_new(bom_id, db_con, 'M_parts').get('part_batch_info', {})
    #         activity = {}
    #         if part_batch_info:
    #             partner_name = db_con.Partners.find_one({"pk_id": data['partner_id']},
    #                                                     {"all_attributes.partner_name": 1})
    #             activity_id = db_con.all_tables.find_one({"pk_id": "top_ids"}, {"all_attributes.ActivityId": 1})
    #             activity_id = int(activity_id['all_attributes'].get('ActivityId', "0")) + 1
    #             if data1:
    #                 statement2 = list(
    #                     db_con.all_tables.find({"pk_id": 'top_ids'}, {"_id": 0, "all_attributes.BoxBuilding": 1}))
    #                 update_id = statement2[0]['all_attributes']["BoxBuilding"][3:]
    #                 box_bilding_id = str(int(update_id) + 1)
    #             data.pop("env_type")
    #             data["BB_id"] = "BB_" + box_bilding_id
    #             # Separate documents from component dataf
    #             component_data = {k: v for k, v in data['M_KIT1'].items() if
    #                             isinstance(v, dict) and 'provided_qty' in v}
    #             for key, value in component_data.items():
    #                 if 'provided_qty' not in value:
    #                     raise KeyError(f"Missing 'provided_qty' in value: {value}")
    #                 var = batch_number_allocation(part_batch_info, int(value['provided_qty']), value['cmpt_id'], {})
    #                 if var:
    #                     data['M_KIT1'][key]['batch_no'] = var['batch_string']
    #                     activity[value['cmpt_id']] = {
    #                         "mfr_prt_num": value.get("mfr_prt_num", "-"),
    #                         "date": str(date.today()),
    #                         "action": "Utilized",
    #                         "Description": "Utilized",
    #                         "issued_to": partner_name['all_attributes']['partner_name'],
    #                         "po_no": var['po_id'],
    #                         'invoice_no': var["invoice_no"],
    #                         "cmpt_id": value.get("cmpt_id", ""),
    #                         "ctgr_id": value.get("ctgr_id", ""),
    #                         "prdt_name": value.get("prdt_name", ""),
    #                         "description": value.get("description", ""),
    #                         "packaging": value.get("packaging", ""),
    #                         "inventory_position": value.get("inventory_position", ""),
    #                         "qty": value['provided_qty'],
    #                         "batchId": var['batch_string'],
    #                         "used_qty": value['provided_qty'],
    #                         "lot_no": var["lot_no"]
    #                     }
    #                 else:
    #                     return {'statusCode': 200, 'body': 'Not enough components were procured for this bom'}
    #             item = {
    #                 "pk_id": "BB_" + box_bilding_id,
    #                 "sk_timeStamp": sk_timeStamp,
    #                 "all_attributes": data,
    #                 "gsipk_table": "BoxBuilding",
    #                 "gsisk_id": data["bom_id"],
    #                 "lsi_key": data['boards_id']
    #             }
    #             boards_id = data.get("boards_id")
    #             data2 = list(db_con.Boards.find({"pk_id": boards_id}, {"_id": 0}))
    #             boards = data2[0]['all_attributes']['boards']
    #             board_keys = list(boards.keys())
    #             invent_data = list(db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1,
    #                                                         "all_attributes.qty": 1,
    #                                                         "all_attributes.out_going_qty": 1}))
    #             invent_data = {
    #                 item['all_attributes']['cmpt_id']:
    #                     {
    #                         "qty": item['all_attributes']['qty'],
    #                         "out_going_qty": item['all_attributes'].get('out_going_qty', "0")
    #                     }
    #                 for item in invent_data
    #             }
    #             m_parts = list(component_data.values())
    #             if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
    #                 return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}
    #             if item:
    #                 cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
    #                                 for part, details in component_data.items()}
    #                 for i in range(len(cmpt_id_and_qty)):
    #                     part = "part" + str(i + 1)
    #                     cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
    #                     qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
    #                     activity[cmpt_id]['closing_qty'] = qty
    #                     out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
    #                         cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data.keys() else (
    #                         cmpt_id_and_qty[part]["provided_qty"])
    #                     response1 = db_con.Inventory.update_one(
    #                         {
    #                             "pk_id": cmpt_id
    #                         },
    #                         {
    #                             "$set": {
    #                                 "all_attributes.qty": qty,
    #                                 "all_attributes.out_going_qty": out_going_qty
    #                             }
    #                         }
    #                     )
    #                 bom_id = data["bom_id"]
    #                 data_bom = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "sk_timeStamp": 1}))
    #                 bom_timeStamp = data_bom[0]["sk_timeStamp"]
    #                 new_document = {}
    #                 for boards_kit, boards_info in item['all_attributes']['boards'].items():
    #                     for board, board_info in boards_info.items():
    #                         if isinstance(board_info, dict):
    #                             pcba_id = board_info.get('pcba_id')
    #                             matched = False
    #                             for data_kit, data_boards in data['boards'].items():
    #                                 for data_board, data_board_info in data_boards.items():
    #                                     if data_board_info.get('pcba_id') == pcba_id:
    #                                         # Assuming you have a filter_criteria defined
    #                                         # Create a new document to insert into BoxBuilding
    #                                         new_document = {
    #                                             'pk_id': item['pk_id'],
    #                                             'sk_timeStamp': item['sk_timeStamp'],
    #                                             'all_attributes': item['all_attributes'],
    #                                             'gsipk_table': item['gsipk_table'],
    #                                             'gsisk_id': item['gsisk_id'],
    #                                             'lsi_key': item['lsi_key']
    #                                         }
    #                                         # Update boardkits_status in the new document
    #                                         new_document['all_attributes']['boards'][boards_kit][board][
    #                                             'boardkits_status'] = 'Assigned'
                    
    #                 # Insert the new document into BoxBuilding
    #                 db_con.BoxBuilding.insert_one(new_document)
    #                 # db_con.BoxBuilding.insert_one(item)
    #                 db_con.all_tables.update_one(
    #                     {'pk_id': "top_ids", 'sk_timeStamp': "123"},
    #                     {'$set': {'all_attributes.BoxBuilding': "BB_" + box_bilding_id}}
    #                 )
    #                 db_con.BOM.update_one(
    #                     {'pk_id': bom_id, 'sk_timeStamp': bom_timeStamp},
    #                     {'$set': {'all_attributes.status': "Bom_assigned"}}
    #                 )
    #                 if board_keys:
    #                     for key in board_keys:
    #                         filter_criteria = {
    #                             'pk_id': data["boards_id"],
    #                             'sk_timeStamp': data2[0]["sk_timeStamp"]
    #                         }
    #                         # Iterate through each board in the boards_kit and set boardkits_status
    #                         for boards_kit, boards_info in boards.items():
    #                             for board, board_info in boards_info.items():
    #                                 if isinstance(board_info, dict):
    #                                     pcba_id = board_info.get('pcba_id')
    #                                     matched = False
    #                                     for data_kit, data_boards in data['boards'].items():
    #                                         for data_board, data_board_info in data_boards.items():
    #                                             if data_board_info.get('pcba_id') == pcba_id:
    #                                                 db_con.Boards.update_one(
    #                                                     filter_criteria,
    #                                                     {
    #                                                         '$set': {
    #                                                             f'all_attributes.boards.{boards_kit}.{board}.boardkits_status': "Assigned"
    #                                                         }
    #                                                     }
    #                                                 )
    #                                                 matched = True
    #                                                 break
    #                                         if matched:
    #                                             break
    #                                     if not matched:
    #                                         print(f"No match found for pcba_id: {pcba_id} in {boards_kit} - {board}")
    #                         # for boards_kit, boards_info in boards.items():
    #                         #     for board, board_info in boards_info.items():
    #                         #         if isinstance(board_info, dict):
    #                         #             db_con.Boards.update_one(
    #                         #                 filter_criteria,
    #                         #                 {
    #                         #                     '$set': {
    #                         #                         f'all_attributes.boards.{boards_kit}.{board}.boardkits_status': "Assigned"
    #                         #                     }
    #                         #                 }
    #                         #             )
    #                 res = db_con['ActivityDetails'].insert_one(
    #                     {
    #                         "pk_id": f"ACTID{activity_id}",
    #                         "sk_timeStamp": sk_timeStamp,
    #                         "all_attributes": activity,
    #                         "gsipk_table": "ActivityDetails",
    #                         "gsisk_id": data['outward_id'],
    #                         "lsi_key": "Utilized",
    #                         "gsipk_id": "EMS"
    #                     })
    #                 db_con.all_tables.update_one(
    #                     {"pk_id": "top_ids"},
    #                     {"$set": {"all_attributes.ActivityId": activity_id}}
    #                 )
    #                 response = {'statusCode': 200, 'body': 'Box Building created successfully'}
    #             else:
    #                 response = {'statusCode': 404, 'body': 'no data found'}
    #             conct.close_connection(client)
    #             return response
    #         else:
    #             return {'statusCode': 200, 'body': 'no inwards for this bom'}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}

    # def cmsBomOutwardInfoSaveAssignToBoxBuilding(request_body):
    #     data = request_body
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     sk_timeStamp = (datetime.now() + timedelta(hours=5, minutes=30)).isoformat()
    #     data1 = list(db_con.BoxBuilding.find({'pk_id': "BB_1"}, {}))
    #     box_bilding_id = "1"
    #     if data1:
    #         statement2 = list(db_con.all_tables.find({"pk_id": 'top_ids'}, {"_id": 0, "all_attributes.BoxBuilding": 1}))
    #         update_id = statement2[0]['all_attributes']["BoxBuilding"][3:]
    #         box_bilding_id = str(int(update_id) + 1)
    #     data.pop("env_type")
    #     for board_id, board_info in data["boards"].items():
    #         board_info["status"] = "Assigned"
    #     data["BB_id"] = "BB_" + box_bilding_id
    #     item = {
    #         "pk_id": "BB_" + box_bilding_id,
    #         "sk_timeStamp": sk_timeStamp,
    #         "all_attributes": data,
    #         "gsipk_table": "BoxBuilding",
    #         "gsisk_id": data["bom_id"],
    #         "lsi_key": data['boards_id']
    #     }
    #     boards_id = data.get("boards_id")
    #     data2 = list(db_con.Boards.find({"pk_id": boards_id}, {"_id": 0}))
    #     boards = data2[0]['all_attributes']['boards']
    #     board_keys = list(boards.keys())
    #     all_tables = list(db_con.all_tables.find({"pk_id": "top_ids"}, {"_id": 0, "all_attributes.BoxBuilding": 1,
    #                                                                             "all_attributes.ActivityId": 1}))
    #     activity_id = all_tables[0]['all_attributes']['ActivityId']
    #     outward_id = '1'
    #     if data1:
    #         outward_id = str(int(update_id) + 1)
    #     invent_data = list(db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1, "all_attributes.qty": 1,
    #                                                   "all_attributes.out_going_qty": 1}))
    #     invent_data = {item['all_attributes']['cmpt_id']: {"qty": item['all_attributes']['qty'],
    #                                                        "out_going_qty": item['all_attributes'].get('out_going_qty',
    #                                                                                                    "0")} for item in
    #                    invent_data}
    #     id = 1
    #     documents = data['documents']
    #     doc = {}
    #     for inx, docs in enumerate(documents):
    #         image_path = file_uploads.upload_file("BoxBuilding", "PtgCms" + env_type, "",
    #                                                 "M-Kit" + str(id), docs["doc_name"],
    #                                                 docs['doc_body'])
    #         doc[docs["doc_name"]] = image_path
    #     m_parts = list(data['M_KIT1'].values())
    #     if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
    #         return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}
    #     if item:
    #         cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
    #                            for part, details in data['M_KIT1'].items()}
    #         for i in range(len(cmpt_id_and_qty)):
    #             part = "part" + str(i + 1)
    #             cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
    #             qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
    #             out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
    #                 cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data.keys() else (
    #             cmpt_id_and_qty[part]["provided_qty"])
    #             response1 = db_con.Inventory.update_one(
    #                 {
    #                     "pk_id": cmpt_id
    #                 },
    #                 {
    #                     "$set": {
    #                         "all_attributes.qty": qty,
    #                         "all_attributes.out_going_qty": out_going_qty
    #                     }
    #                 }
    #             )
    #         item['all_attributes']['documents'] = doc
    #         bom_id = data["bom_id"]
    #         data_bom = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "sk_timeStamp": 1}))
    #         bom_timeStamp = data_bom[0]["sk_timeStamp"]
    #         for boards_kit, boards_info in item['all_attributes']['boards'].items():
    #             for board, board_info in boards_info.items():
    #                 if isinstance(board_info, dict):
    #                     pcba_id = board_info.get('pcba_id')
    #                     print("A",pcba_id)
    #                     matched = False
    #                     for data_kit, data_boards in data['boards'].items():
    #                         for data_board, data_board_info in data_boards.items():
    #                             print("B",data_board_info.get('pcba_id'))
    #                             if data_board_info.get('pcba_id') == pcba_id:
    #                                 # Assuming you have a filter_criteria defined
    #                                 # Create a new document to insert into BoxBuilding
    #                                 new_document = {
    #                                     'pk_id': item['pk_id'],
    #                                     'sk_timeStamp': item['sk_timeStamp'],
    #                                     'all_attributes': item['all_attributes'],
    #                                     'gsipk_table': item['gsipk_table'],
    #                                     'gsisk_id': item['gsisk_id'],
    #                                     'lsi_key': item['lsi_key']
    #                                 }
    #                                 # Update boardkits_status in the new document
    #                                 new_document['all_attributes']['boards'][boards_kit][board][
    #                                     'boardkits_status'] = 'Assigned'
    #         activity_id = int(activity_id) + 1
    #         if item:
    #             activity_details = {}
    #             for part_key, part_value in data["M_KIT1"].items():
    #                 if part_key.startswith("part"):
    #                     cmpt_id = part_value.get('cmpt_id','')
    #                     print("ABCDEF",part_value.get('lot_id',''))
    #                     activity_details[cmpt_id] = {
                            
    #                     }
    #             db_con['ActivityDetails'].insert_one(
    #                 {
    #                     "pk_id": f"ACTID{activity_id}",
    #                     "sk_timeStamp": sk_timeStamp,
    #                     "all_attributes": activity_details,
    #                     "gsipk_table": "ActivityDetails",
    #                     "gsisk_id": outward_id,
    #                     "lsi_key": "Utilized",
    #                     "gsipk_id": "EMS"
    #                 }
    #             )
    #         db_con.BoxBuilding.insert_one(item)
    #         db_con.all_tables.update_one(
    #             {'pk_id': "top_ids", 'sk_timeStamp': "123"},
    #             {'$set': {'all_attributes.BoxBuilding': "BB_" + box_bilding_id,
    #                       "all_attributes.ActivityId":f"{activity_id}"}}
    #         )
    #         db_con.BOM.update_one(
    #             {'pk_id': bom_id, 'sk_timeStamp': bom_timeStamp},
    #             {'$set': {'all_attributes.status': "Bom_assigned"}}
    #         )
    #         if board_keys:
    #             for key in board_keys:
    #                 filter_criteria = {
    #                     'pk_id': data["boards_id"],
    #                     'sk_timeStamp': data2[0]["sk_timeStamp"]
    #                 }
    #                 update_operation = {
    #                     '$set': {
    #                         f'all_attributes.boards.{key}.status': "Assigned"
    #                     }
    #                 }
    #                 # Perform the update operation
    #                 db_con.Boards.update_one(filter_criteria, update_operation)
    #         # else:
    #         #     return {'statusCode': 404, 'body': 'boards b_data not updated'}
    #         conct.close_connection(client)
    #         response = {'statusCode': 200, 'body': 'Box Building created successfully'}
    #     else:
    #         conct.close_connection(client)
    #         response = {'statusCode': 404, 'body': 'no data found'}
    #     conct.close_connection(client)
    #     return response
    # def cmsBomOutwardInfoSaveAssignToBoxBuilding(request_body):
    #     data = request_body
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     sk_timeStamp = (datetime.now() + timedelta(hours=5, minutes=30)).isoformat()
    #     data1 = list(db_con.BoxBuilding.find({'pk_id': "BB_1"}, {}))
    #     box_bilding_id = "1"
    #     if data1:
    #         statement2 = list(db_con.all_tables.find({"pk_id": 'top_ids'}, {"_id": 0, "all_attributes.BoxBuilding": 1}))
    #         update_id = statement2[0]['all_attributes']["BoxBuilding"][3:]
    #         box_bilding_id = str(int(update_id) + 1)
    #     data.pop("env_type")
    #     # for board_id, board_info in data["boards"].items():
    #     #     board_info["status"] = "Assigned"
    #     data["BB_id"] = "BB_" + box_bilding_id
    #     item = {
    #         "pk_id": "BB_" + box_bilding_id,
    #         "sk_timeStamp": sk_timeStamp,
    #         "all_attributes": data,
    #         "gsipk_table": "BoxBuilding",
    #         "gsisk_id": data["bom_id"],
    #         "lsi_key": data['boards_id']
    #     }
    #     boards_id = data.get("boards_id")
    #     data2 = list(db_con.Boards.find({"pk_id": boards_id}, {"_id": 0}))
    #     if not data2:
    #         conct.close_connection(client)
    #         return {"statusCode": 404, "body": "Boards data not found"}
    #     boards = data2[0]['all_attributes']['boards']
    #     board_keys = list(boards.keys())
    #     all_tables = list(db_con.all_tables.find({"pk_id": "top_ids"}, {"_id": 0, "all_attributes.BoxBuilding": 1,
    #                                                                     "all_attributes.ActivityId": 1}))
    #     activity_id = all_tables[0]['all_attributes']['ActivityId']
    #     outward_id = '1'
    #     if data1:
    #         outward_id = str(int(update_id) + 1)
    #     invent_data = list(db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1, "all_attributes.qty": 1,
    #                                                 "all_attributes.out_going_qty": 1}))
    #     invent_data = {item['all_attributes']['cmpt_id']: {"qty": item['all_attributes']['qty'],
    #                                                     "out_going_qty": item['all_attributes'].get('out_going_qty',
    #                                                                                                 "0")} for item in
    #                 invent_data}
    #     id = 1
    #     documents = data['documents']
    #     doc = {}
    #     for inx, docs in enumerate(documents):
    #         image_path = file_uploads.upload_file("BoxBuilding", "PtgCms" + env_type, "",
    #                                             "M-Kit" + str(id), docs["doc_name"],
    #                                             docs['doc_body'])
    #         doc[docs["doc_name"]] = image_path
    #     m_parts = list(data['M_KIT1'].values())
    #     if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
    #         conct.close_connection(client)
    #         return {"statusCode": 502, "body": "provided quantity is more than the total quantity"}
    #     if item:
    #         cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
    #                         for part, details in data['M_KIT1'].items()}
    #         for i in range(len(cmpt_id_and_qty)):
    #             part = "part" + str(i + 1)
    #             cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
    #             qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
    #             out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
    #                 cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data[cmpt_id].keys() else (
    #                 cmpt_id_and_qty[part]["provided_qty"])
    #             response1 = db_con.Inventory.update_one(
    #                 {
    #                     "pk_id": cmpt_id
    #                 },
    #                 {
    #                     "$set": {
    #                         "all_attributes.qty": qty,
    #                         "all_attributes.out_going_qty": out_going_qty
    #                     }
    #                 }
    #             )
    #         item['all_attributes']['documents'] = doc
    #         bom_id = data["bom_id"]
    #         data_bom = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "sk_timeStamp": 1}))
    #         if not data_bom:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "BOM data not found"}
    #         bom_timeStamp = data_bom[0]["sk_timeStamp"]
            
    #         # Ensure Boards get updated correctly
    #         for boards_kit, boards_info in item['all_attributes']['boards'].items():
    #             for board, board_info in boards_info.items():
    #                 if isinstance(board_info, dict):
    #                     pcba_id = board_info.get('pcba_id')
    #                     for data_kit, data_boards in data['boards'].items():
    #                         for data_board, data_board_info in data_boards.items():
    #                             if isinstance(data_board_info, dict):
    #                                 if data_board_info.get('pcba_id') == pcba_id:
    #                                     # Assuming you have a filter_criteria defined
    #                                     # Create a new document to insert into BoxBuilding
    #                                     new_document = {
    #                                         'pk_id': item['pk_id'],
    #                                         'sk_timeStamp': item['sk_timeStamp'],
    #                                         'all_attributes': item['all_attributes'],
    #                                         'gsipk_table': item['gsipk_table'],
    #                                         'gsisk_id': item['gsisk_id'],
    #                                         'lsi_key': item['lsi_key']
    #                                     }
    #                                     # Update boardkits_status in the new document
    #                                     new_document['all_attributes']['boards'][boards_kit][board][
    #                                         'boardkits_status'] = 'Assigned'
    #                                     print(f"Updating boardkits_status for {board} in {boards_kit}")
    #                                     db_con.BoxBuilding.insert_one(new_document)

    #         activity_id = int(activity_id) + 1
    #         if item:
    #             activity_details = {}
    #             for part_key, part_value in data["M_KIT1"].items():
    #                 if part_key.startswith("part"):
    #                     cmpt_id = part_value.get('cmpt_id', '')
    #                     activity_details[cmpt_id] = {
    #                         "mfr_prt_num": part_value.get('vic_part_number', ''),
    #                         "date": sk_timeStamp.split('T')[0],
    #                         "action": "Utilized",
    #                         "Description": "Utilized",
    #                         "issued_to": data.get('receiver_name', ''),
    #                         "po_no": "-",
    #                         "invoice_no": "-",
    #                         "cmpt_id": part_value.get('cmpt_id', ''),
    #                         "ctgr_id": part_value.get('ctgr_id', ''),
    #                         "prdt_name": part_value.get('prdt_name', ''),
    #                         "description": part_value.get('description', ''),
    #                         "packaging": "-",
    #                         "closing_qty":str(int(part_value.get('ptg_stock','0'))- int(part_value.get('provided_qty','0'))),
    #                         "qty": part_value.get('provided_qty','0'),
    #                         "batchId": part_value.get('batch_no',''),
    #                         "used_qty": "0",
    #                         "lot_id": part_value.get('lot_id','')
    #                     }
    #             db_con['ActivityDetails'].insert_one(
    #                 {
    #                     "pk_id": f"ACTID{activity_id}",
    #                     "sk_timeStamp": sk_timeStamp,
    #                     "all_attributes": activity_details,
    #                     "gsipk_table": "ActivityDetails",
    #                     "gsisk_id": outward_id,
    #                     "lsi_key": "Utilized",
    #                     "gsipk_id": "EMS"
    #                 }
    #             )
    #         db_con.BoxBuilding.insert_one(item)
    #         db_con.all_tables.update_one(
    #             {'pk_id': "top_ids", 'sk_timeStamp': "123"},
    #             {'$set': {'all_attributes.BoxBuilding': "BB_" + box_bilding_id,
    #                     "all_attributes.ActivityId": f"{activity_id}"}}
    #         )
    #         db_con.BOM.update_one(
    #             {'pk_id': bom_id, 'sk_timeStamp': bom_timeStamp},
    #             {'$set': {'all_attributes.status': "Bom_assigned"}}
    #         )
    #         if board_keys:
    #             for key in board_keys:
    #                 filter_criteria = {
    #                     'pk_id': data["boards_id"],
    #                     'sk_timeStamp': data2[0]["sk_timeStamp"]
    #                 }
    #                 update_operation = {
    #                     '$set': {
    #                         f'all_attributes.boards.{key}.status': "Assigned"
    #                     }
    #                 }
    #                 # Perform the update operation
    #                 # print(f"Updating Boards collection with filter {filter_criteria} and update {update_operation}")
    #                 # db_con.Boards.update_one(filter_criteria, update_operation)
                    
    #         conct.close_connection(client)
    #         response = {'statusCode': 200, 'body': 'Box Building created successfully'}
    #     else:
    #         conct.close_connection(client)
    #         response = {'statusCode': 404, 'body': 'no data found'}
    #     conct.close_connection(client)
    #     return response

    def cmsBomOutwardInfoSaveAssignToBoxBuilding(request_body):
        data = request_body
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        sk_timeStamp = (datetime.now() + timedelta(hours=5, minutes=30)).isoformat()

        # Fetch or generate box building ID
        data1 = list(db_con.BoxBuilding.find({'pk_id': "BB_1"}, {}))
        box_bilding_id = "1"
        if data1:
            statement2 = list(db_con.all_tables.find({"pk_id": 'top_ids'}, {"_id": 0, "all_attributes.BoxBuilding": 1}))
            update_id = statement2[0]['all_attributes']["BoxBuilding"][3:]
            box_bilding_id = str(int(update_id) + 1)

        data.pop("env_type")
        data["BB_id"] = "BB_" + box_bilding_id
        item = {
            "pk_id": "BB_" + box_bilding_id,
            "sk_timeStamp": sk_timeStamp,
            "all_attributes": data,
            "gsipk_table": "BoxBuilding",
            "gsisk_id": data["bom_id"],
            "lsi_key": data['boards_id']
        }

        # Fetch boards data
        boards_id = data.get("boards_id")
        data2 = list(db_con.Boards.find({"pk_id": boards_id}, {"_id": 0}))
        if not data2:
            conct.close_connection(client)
            return {"statusCode": 404, "body": "Boards data not found"}

        boards = data2[0]['all_attributes']['boards']
        board_keys = list(boards.keys())
        all_tables = list(db_con.all_tables.find({"pk_id": "top_ids"}, {"_id": 0, "all_attributes.BoxBuilding": 1, "all_attributes.ActivityId": 1}))
        activity_id = all_tables[0]['all_attributes']['ActivityId']
        outward_id = '1'
        if data1:
            outward_id = str(int(update_id) + 1)

        invent_data = list(db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1, "all_attributes.qty": 1, "all_attributes.out_going_qty": 1}))
        invent_data = {item['all_attributes']['cmpt_id']: {"qty": item['all_attributes']['qty'], "out_going_qty": item['all_attributes'].get('out_going_qty', "0")} for item in invent_data}

        # Handle document uploads
        documents = data['documents']
        doc = {}
        for inx, docs in enumerate(documents):
            image_path = file_uploads.upload_file("BoxBuilding", "PtgCms" + env_type, "", "M-Kit" + str(id), docs["doc_name"], docs['doc_body'])
            doc[docs["doc_name"]] = image_path

        m_parts = list(data['M_KIT1'].values())
        if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
            conct.close_connection(client)
            return {"statusCode": 502, "body": "provided quantity is more than the total quantity"}

        if item:
            # Update inventory quantities
            cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']} for part, details in data['M_KIT1'].items()}
            for i in range(len(cmpt_id_and_qty)):
                part = "part" + str(i + 1)
                cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
                qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
                out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data[cmpt_id].keys() else (cmpt_id_and_qty[part]["provided_qty"])
                db_con.Inventory.update_one(
                    {"pk_id": cmpt_id},
                    {"$set": {"all_attributes.qty": qty, "all_attributes.out_going_qty": out_going_qty}}
                )
            
            data['documents'] = doc
            bom_id = data["bom_id"]
            data_bom = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "sk_timeStamp": 1}))
            if not data_bom:
                conct.close_connection(client)
                return {"statusCode": 404, "body": "BOM data not found"}
            
            bom_timeStamp = data_bom[0]["sk_timeStamp"]

            # Update boardkits_status in Boards collection
            for boards_kit, boards_info in item['all_attributes']['boards'].items():
                for board, board_info in boards_info.items():
                    if isinstance(board_info, dict):
                        pcba_id = board_info.get('pcba_id')
                        db_con.Boards.update_one(
                            {"pk_id": boards_id, f"all_attributes.boards.{boards_kit}.{board}.pcba_id": pcba_id},
                            {"$set": {f"all_attributes.boards.{boards_kit}.{board}.boardkits_status": "Assigned"}}
                        )
            
            # Insert BoxBuilding record only once
            db_con.BoxBuilding.insert_one(item)

            activity_id = int(activity_id) + 1
            if item:
                activity_details = {}
                for part_key, part_value in data["M_KIT1"].items():
                    if part_key.startswith("part"):
                        cmpt_id = part_value.get('cmpt_id', '')
                        activity_details[cmpt_id] = {
                            "mfr_prt_num": part_value.get('vic_part_number', ''),
                            "date": sk_timeStamp.split('T')[0],
                            "action": "Utilized",
                            "Description": "Utilized",
                            "issued_to": data.get('receiver_name', ''),
                            "po_no": "-",
                            "invoice_no": "-",
                            "cmpt_id": part_value.get('cmpt_id', ''),
                            "ctgr_id": part_value.get('ctgr_id', ''),
                            "prdt_name": part_value.get('prdt_name', ''),
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
                        "gsisk_id": outward_id,
                        "lsi_key": "Utilized",
                        "gsipk_id": "EMS"
                    }
                )
            db_con.all_tables.update_one(
                {'pk_id': "top_ids", 'sk_timeStamp': "123"},
                {'$set': {'all_attributes.BoxBuilding': "BB_" + box_bilding_id, "all_attributes.ActivityId": f"{activity_id}"}}
            )
            db_con.BOM.update_one(
                {'pk_id': bom_id, 'sk_timeStamp': bom_timeStamp},
                {'$set': {'all_attributes.status': "Bom_assigned"}}
            )
            if board_keys:
                for key in board_keys:
                    filter_criteria = {
                        'pk_id': data["boards_id"],
                        'sk_timeStamp': data2[0]["sk_timeStamp"]
                    }
                    update_operation = {
                        '$set': {
                            f'all_attributes.boards.{key}.status': "Assigned"
                        }
                    }
                    # Perform the update operation
                    # db_con.Boards.update_one(filter_criteria, update_operation)
                    
            conct.close_connection(client)
            response = {'statusCode': 200, 'body': 'Box Building created successfully'}
        else:
            conct.close_connection(client)
            response = {'statusCode': 404, 'body': 'no data found'}

        conct.close_connection(client)
        return response
    


    # mcolddef cmsBomOutwardInfoSaveAssignToBoxBuilding(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         sk_timeStamp = datetime.now().isoformat()

    #         # Process documents
    #         documents = data['documents']
    #         if isinstance(documents, list):
    #             doc = {}
    #             for idx, doc_info in enumerate(documents):
    #                 image_path = file_uploads.upload_file("boxbuilding", "PtgCms" + env_type, "", "E-Kit" + str(idx),
    #                                                     doc_info["doc_name"], doc_info['doc_body'])
    #                 doc[doc_info["doc_name"]] = image_path
    #             data['documents'] = doc
    #         elif isinstance(documents, dict):
    #             for doc_name, doc_url in documents.items():
    #                 if doc_name.endswith(".pdf"):
    #                     data['documents'] = {
    #                         doc_name: doc_url
    #                     }

    #         # Other data processing and insertion into database...
    #         data1 = list(db_con.BoxBuilding.find({'pk_id': "BB_1"}, {}))
    #         box_bilding_id = "1"
    #         bom_id = data['bom_id']
    #         part_batch_info = find_stock_inwards(bom_id, db_con, 'M_parts').get('part_batch_info', {})
    #         activity = {}

    #         if part_batch_info:
    #             partner_name = db_con.Partners.find_one({"pk_id": data['partner_id']},
    #                                                     {"all_attributes.partner_name": 1})
    #             activity_id = db_con.all_tables.find_one({"pk_id": "top_ids"}, {"all_attributes.ActivityId": 1})
    #             activity_id = int(activity_id['all_attributes'].get('ActivityId', "0")) + 1

    #             if data1:
    #                 statement2 = list(
    #                     db_con.all_tables.find({"pk_id": 'top_ids'}, {"_id": 0, "all_attributes.BoxBuilding": 1}))
    #                 update_id = statement2[0]['all_attributes']["BoxBuilding"][3:]
    #                 box_bilding_id = str(int(update_id) + 1)

    #             data.pop("env_type")

    #             data["BB_id"] = "BB_" + box_bilding_id

    #             # Separate documents from component dataf
    #             component_data = {k: v for k, v in data['M_KIT1'].items() if
    #                             isinstance(v, dict) and 'provided_qty' in v}

    #             for key, value in component_data.items():
    #                 if 'provided_qty' not in value:
    #                     raise KeyError(f"Missing 'provided_qty' in value: {value}")

    #                 var = batch_number_allocation(part_batch_info, int(value['provided_qty']), value['cmpt_id'], {})

    #                 if var:
    #                     data['M_KIT1'][key]['batch_no'] = var['batch_string']

    #                     activity[value['cmpt_id']] = {
    #                         "mfr_prt_num": value.get("mfr_prt_num", "-"),
    #                         "date": str(date.today()),
    #                         "action": "Utilized",
    #                         "Description": "Utilized",
    #                         "issued_to": partner_name['all_attributes']['partner_name'],
    #                         "po_no": var['po_id'],
    #                         'invoice_no': var["invoice_no"],
    #                         "cmpt_id": value.get("cmpt_id", ""),
    #                         "ctgr_id": value.get("ctgr_id", ""),
    #                         "prdt_name": value.get("prdt_name", ""),
    #                         "description": value.get("description", ""),
    #                         "packaging": value.get("packaging", ""),
    #                         "inventory_position": value.get("inventory_position", ""),
    #                         "qty": value['provided_qty'],
    #                         "batchId": var['batch_string'],
    #                         "used_qty": value['provided_qty'],
    #                         "lot_no": var["lot_no"]
    #                     }
    #                 else:
    #                     return {'statusCode': 200, 'body': 'Not enough components were procured for this bom'}

    #             item = {
    #                 "pk_id": "BB_" + box_bilding_id,
    #                 "sk_timeStamp": sk_timeStamp,
    #                 "all_attributes": data,
    #                 "gsipk_table": "BoxBuilding",
    #                 "gsisk_id": data["bom_id"],
    #                 "lsi_key": data['boards_id']
    #             }

    #             boards_id = data.get("boards_id")
    #             data2 = list(db_con.Boards.find({"pk_id": boards_id}, {"_id": 0}))
    #             boards = data2[0]['all_attributes']['boards']
    #             board_keys = list(boards.keys())
    #             invent_data = list(db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1,
    #                                                         "all_attributes.qty": 1,
    #                                                         "all_attributes.out_going_qty": 1}))

    #             invent_data = {
    #                 item['all_attributes']['cmpt_id']:
    #                     {
    #                         "qty": item['all_attributes']['qty'],
    #                         "out_going_qty": item['all_attributes'].get('out_going_qty', "0")
    #                     }
    #                 for item in invent_data
    #             }

    #             m_parts = list(component_data.values())

    #             if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
    #                 return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}

    #             if item:
    #                 cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
    #                                 for part, details in component_data.items()}

    #                 for i in range(len(cmpt_id_and_qty)):
    #                     part = "part" + str(i + 1)
    #                     cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
    #                     qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
    #                     activity[cmpt_id]['closing_qty'] = qty

    #                     out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
    #                         cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data.keys() else (
    #                         cmpt_id_and_qty[part]["provided_qty"])

    #                     response1 = db_con.Inventory.update_one(
    #                         {
    #                             "pk_id": cmpt_id
    #                         },
    #                         {
    #                             "$set": {
    #                                 "all_attributes.qty": qty,
    #                                 "all_attributes.out_going_qty": out_going_qty
    #                             }
    #                         }
    #                     )

    #                 bom_id = data["bom_id"]
    #                 data_bom = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "sk_timeStamp": 1}))
    #                 bom_timeStamp = data_bom[0]["sk_timeStamp"]

    #                 db_con.BoxBuilding.insert_one(item)

    #                 db_con.all_tables.update_one(
    #                     {'pk_id': "top_ids", 'sk_timeStamp': "123"},
    #                     {'$set': {'all_attributes.BoxBuilding': "BB_" + box_bilding_id}}
    #                 )

    #                 db_con.BOM.update_one(
    #                     {'pk_id': bom_id, 'sk_timeStamp': bom_timeStamp},
    #                     {'$set': {'all_attributes.status': "Bom_assigned"}}
    #                 )

    #                 if board_keys:
    #                     for key in board_keys:
    #                         filter_criteria = {
    #                             'pk_id': data["boards_id"],
    #                             'sk_timeStamp': data2[0]["sk_timeStamp"]
    #                         }

    #                         # Iterate through each board in the boards_kit and set boxbuilding_status
    #                         for boards_kit, boards_info in boards.items():
    #                             for board, board_info in boards_info.items():
    #                                 if isinstance(board_info, dict):
    #                                     pcba_id = board_info.get('pcba_id')
    #                                     matched = False
    #                                     for data_kit, data_boards in data['boards'].items():
    #                                         for data_board, data_board_info in data_boards.items():
    #                                             if data_board_info.get('pcba_id') == pcba_id:
    #                                                 db_con.Boards.update_one(
    #                                                     filter_criteria,
    #                                                     {
    #                                                         '$set': {
    #                                                             f'all_attributes.boards.{boards_kit}.{board}.boardkits_status': "Assigned"
    #                                                         }
    #                                                     }
    #                                                 )
    #                                                 matched = True
    #                                                 break
    #                                         if matched:
    #                                             break
    #                                     if not matched:
    #                                         print(f"No match found for pcba_id: {pcba_id} in {boards_kit} - {board}")
    #                         # for boards_kit, boards_info in boards.items():
    #                         #     for board, board_info in boards_info.items():
    #                         #         if isinstance(board_info, dict):
    #                         #             db_con.Boards.update_one(
    #                         #                 filter_criteria,
    #                         #                 {
    #                         #                     '$set': {
    #                         #                         f'all_attributes.boards.{boards_kit}.{board}.boardkits_status': "Assigned"
    #                         #                     }
    #                         #                 }
    #                         #             )

    #                 res = db_con['ActivityDetails'].insert_one(
    #                     {
    #                         "pk_id": f"ACTID{activity_id}",
    #                         "sk_timeStamp": sk_timeStamp,
    #                         "all_attributes": activity,
    #                         "gsipk_table": "ActivityDetails",
    #                         "gsisk_id": data['outward_id'],
    #                         "lsi_key": "Utilized",
    #                         "gsipk_id": "EMS"
    #                     })

    #                 db_con.all_tables.update_one(
    #                     {"pk_id": "top_ids"},
    #                     {"$set": {"all_attributes.ActivityId": activity_id}}
    #                 )

    #                 response = {'statusCode': 200, 'body': 'Box Building created successfully'}

    #             else:
    #                 response = {'statusCode': 404, 'body': 'no data found'}

    #             conct.close_connection(client)
    #             return response

    #         else:
    #             return {'statusCode': 200, 'body': 'no inwards for this bom'}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}






    # def cmsBomOutwardInfoSaveAssignToBoxBuilding(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         sk_timeStamp = datetime.now().isoformat()
            
    #         # Process documents
    #         documents = data['documents']
    #         if isinstance(documents, list):
    #             doc = {}
    #             for idx, doc_info in enumerate(documents):
    #                 image_path = file_uploads.upload_file("boxbuilding", "PtgCms" + env_type, "", "E-Kit" + str(idx),
    #                                                     doc_info["doc_name"], doc_info['doc_body'])
    #                 doc[doc_info["doc_name"]] = image_path
    #             data['documents'] = doc
    #         elif isinstance(documents, dict):
    #             for doc_name, doc_url in documents.items():
    #                 if doc_name.endswith(".pdf"):
    #                     data['documents'] = {
    #                         doc_name: doc_url
    #                     }
            
    #         # Other data processing and insertion into database...
    #         data1 = list(db_con.BoxBuilding.find({'pk_id': "BB_1"}, {}))
    #         box_bilding_id = "1"
    #         bom_id = data['bom_id']
    #         part_batch_info = find_stock_inwards(bom_id, db_con, 'M_parts').get('part_batch_info', {})
    #         activity = {}

    #         if part_batch_info:
    #             partner_name = db_con.Partners.find_one({"pk_id": data['partner_id']},
    #                                                     {"all_attributes.partner_name": 1})
    #             activity_id = db_con.all_tables.find_one({"pk_id": "top_ids"}, {"all_attributes.ActivityId": 1})
    #             activity_id = int(activity_id['all_attributes'].get('ActivityId', "0")) + 1

    #             if data1:
    #                 statement2 = list(
    #                     db_con.all_tables.find({"pk_id": 'top_ids'}, {"_id": 0, "all_attributes.BoxBuilding": 1}))
    #                 update_id = statement2[0]['all_attributes']["BoxBuilding"][3:]
    #                 box_bilding_id = str(int(update_id) + 1)

    #             data.pop("env_type")
    #             for board_id, board_info in data["boards"].items():
    #                 board_info["status"] = "Assigned"

    #             data["BB_id"] = "BB_" + box_bilding_id

    #             # Separate documents from component data
    #             component_data = {k: v for k, v in data['M_KIT1'].items() if
    #                             isinstance(v, dict) and 'provided_qty' in v}

    #             for key, value in component_data.items():
    #                 if 'provided_qty' not in value:
    #                     raise KeyError(f"Missing 'provided_qty' in value: {value}")

    #                 var = batch_number_allocation(part_batch_info, int(value['provided_qty']), value['cmpt_id'], {})

    #                 if var:
    #                     data['M_KIT1'][key]['batch_no'] = var['batch_string']

    #                     activity[value['cmpt_id']] = {
    #                         "mfr_prt_num": value.get("mfr_prt_num", "-"),
    #                         "date": str(date.today()),
    #                         "action": "Utilized",
    #                         "Description": "Utilized",
    #                         "issued_to": partner_name['all_attributes']['partner_name'],
    #                         "po_no": var['po_id'],
    #                         'invoice_no': var["invoice_no"],
    #                         "cmpt_id": value.get("cmpt_id", ""),
    #                         "ctgr_id": value.get("ctgr_id", ""),
    #                         "prdt_name": value.get("prdt_name", ""),
    #                         "description": value.get("description", ""),
    #                         "packaging": value.get("packaging", ""),
    #                         "inventory_position": value.get("inventory_position", ""),
    #                         "qty": value['provided_qty'],
    #                         "batchId": var['batch_string'],
    #                         "used_qty": value['provided_qty'],
    #                         "lot_no": var["lot_no"]
    #                     }
    #                 else:
    #                     return {'statusCode': 200, 'body': 'Not enough components were procured for this bom'}

    #             item = {
    #                 "pk_id": "BB_" + box_bilding_id,
    #                 "sk_timeStamp": sk_timeStamp,
    #                 "all_attributes": data,
    #                 "gsipk_table": "BoxBuilding",
    #                 "gsisk_id": data["bom_id"],
    #                 "lsi_key": data['boards_id']
    #             }

    #             boards_id = data.get("boards_id")
    #             data2 = list(db_con.Boards.find({"pk_id": boards_id}, {"_id": 0}))
    #             boards = data2[0]['all_attributes']['boards']
    #             board_keys = list(boards.keys())
    #             invent_data = list(db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1,
    #                                                         "all_attributes.qty": 1,
    #                                                         "all_attributes.out_going_qty": 1}))

    #             invent_data = {
    #                 item['all_attributes']['cmpt_id']:
    #                     {
    #                         "qty": item['all_attributes']['qty'],
    #                         "out_going_qty": item['all_attributes'].get('out_going_qty', "0")
    #                     }
    #                 for item in invent_data
    #             }

    #             m_parts = list(component_data.values())

    #             if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
    #                 return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}

    #             if item:
    #                 cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
    #                                 for part, details in component_data.items()}

    #                 for i in range(len(cmpt_id_and_qty)):
    #                     part = "part" + str(i + 1)
    #                     cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
    #                     qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
    #                     activity[cmpt_id]['closing_qty'] = qty

    #                     out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
    #                         cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data.keys() else (
    #                         cmpt_id_and_qty[part]["provided_qty"])

    #                     response1 = db_con.Inventory.update_one(
    #                         {
    #                             "pk_id": cmpt_id
    #                         },
    #                         {
    #                             "$set": {
    #                                 "all_attributes.qty": qty,
    #                                 "all_attributes.out_going_qty": out_going_qty
    #                             }
    #                         }
    #                     )

    #                 bom_id = data["bom_id"]
    #                 data_bom = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "sk_timeStamp": 1}))
    #                 bom_timeStamp = data_bom[0]["sk_timeStamp"]

    #                 db_con.BoxBuilding.insert_one(item)

    #                 db_con.all_tables.update_one(
    #                     {'pk_id': "top_ids", 'sk_timeStamp': "123"},
    #                     {'$set': {'all_attributes.BoxBuilding': "BB_" + box_bilding_id}}
    #                 )

    #                 db_con.BOM.update_one(
    #                     {'pk_id': bom_id, 'sk_timeStamp': bom_timeStamp},
    #                     {'$set': {'all_attributes.status': "Bom_assigned"}}
    #                 )

    #                 if board_keys:
    #                     for key in board_keys:
    #                         filter_criteria = {
    #                             'pk_id': data["boards_id"],
    #                             'sk_timeStamp': data2[0]["sk_timeStamp"]
    #                         }

    #                         update_operation = {
    #                             '$set': {
    #                                 f'all_attributes.boards.{key}.status': "Assigned"
    #                             }
    #                         }

    #                         db_con.Boards.update_one(filter_criteria, update_operation)

    #                 res = db_con['ActivityDetails'].insert_one(
    #                     {
    #                         "pk_id": f"ACTID{activity_id}",
    #                         "sk_timeStamp": sk_timeStamp,
    #                         "all_attributes": activity,
    #                         "gsipk_table": "ActivityDetails",
    #                         "gsisk_id": data['outward_id'],
    #                         "lsi_key": "Utilized",
    #                         "gsipk_id": "EMS"
    #                     })

    #                 db_con.all_tables.update_one(
    #                     {"pk_id": "top_ids"},
    #                     {"$set": {"all_attributes.ActivityId": activity_id}}
    #                 )

    #                 response = {'statusCode': 200, 'body': 'Box Building created successfully'}

    #             else:
    #                 response = {'statusCode': 404, 'body': 'no data found'}

    #             conct.close_connection(client)
    #             return response

    #         else:
    #             return {'statusCode': 200, 'body': 'no inwards for this bom'}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}

    # def cmsBomOutwardInfoSaveAssignToBoxBuilding(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         sk_timeStamp = datetime.now().isoformat()
            
    #         # Process documents
    #         documents = data['documents']
    #         if isinstance(documents, list):
    #             doc = {}
    #             for idx, doc_info in enumerate(documents):
    #                 image_path = file_uploads.upload_file("boxbuilding", "PtgCms" + env_type, "", "E-Kit" + str(idx),
    #                                                     doc_info["doc_name"], doc_info['doc_body'])
    #                 doc[doc_info["doc_name"]] = image_path
    #             data['documents'] = doc
    #         elif isinstance(documents, dict):
    #             for doc_name, doc_url in documents.items():
    #                 if doc_name.endswith(".pdf"):
    #                     data['documents'] = {
    #                         doc_name: doc_url
    #                     }
            
    #         # Other data processing and insertion into database...
    #         data1 = list(db_con.BoxBuilding.find({'pk_id': "BB_1"}, {}))
    #         box_bilding_id = "1"
    #         bom_id = data['bom_id']
    #         part_batch_info = find_stock_inwards(bom_id, db_con, 'M_parts')
    #         part_batch_info = part_batch_info['part_batch_info']
    #         activity = {}

    #         if part_batch_info:
    #             partner_name = db_con.Partners.find_one({"pk_id": data['partner_id']},
    #                                                     {"all_attributes.partner_name": 1})
    #             activity_id = db_con.all_tables.find_one({"pk_id": "top_ids"}, {"all_attributes.ActivityId": 1})
    #             activity_id = int(activity_id['all_attributes'].get('ActivityId', "0")) + 1

    #             if data1:
    #                 statement2 = list(
    #                     db_con.all_tables.find({"pk_id": 'top_ids'}, {"_id": 0, "all_attributes.BoxBuilding": 1}))
    #                 update_id = statement2[0]['all_attributes']["BoxBuilding"][3:]
    #                 box_bilding_id = str(int(update_id) + 1)

    #             data.pop("env_type")
    #             for board_id, board_info in data["boards"].items():
    #                 board_info["status"] = "Assigned"

    #             data["BB_id"] = "BB_" + box_bilding_id

    #             # Separate documents from component data
    #             component_data = {k: v for k, v in data['M_KIT1'].items() if
    #                             isinstance(v, dict) and 'provided_qty' in v}

    #             for key, value in component_data.items():
    #                 if 'provided_qty' not in value:
    #                     raise KeyError(f"Missing 'provided_qty' in value: {value}")

    #                 var = batch_number_allocation(part_batch_info, int(value['provided_qty']), value['cmpt_id'], {})

    #                 if var:
    #                     data['M_KIT1'][key]['batch_no'] = var['batch_string']

    #                     activity[value['cmpt_id']] = {
    #                         "mfr_prt_num": value.get("mfr_prt_num", "-"),
    #                         "date": str(date.today()),
    #                         "action": "Utilized",
    #                         "Description": "Utilized",
    #                         "issued_to": partner_name['all_attributes']['partner_name'],
    #                         "po_no": var['po_id'],
    #                         'invoice_no': var["invoice_no"],
    #                         "cmpt_id": value.get("cmpt_id", ""),
    #                         "ctgr_id": value.get("ctgr_id", ""),
    #                         "prdt_name": value.get("prdt_name", ""),
    #                         "description": value.get("description", ""),
    #                         "packaging": value.get("packaging", ""),
    #                         "inventory_position": value.get("inventory_position", ""),
    #                         "qty": value['provided_qty'],
    #                         "batchId": var['batch_string'],
    #                         "used_qty": value['provided_qty'],
    #                         "lot_no": var["lot_no"]
    #                     }
    #                 else:
    #                     return {'statusCode': 200, 'body': 'Not enough components were procured for this bom'}

    #             item = {
    #                 "pk_id": "BB_" + box_bilding_id,
    #                 "sk_timeStamp": sk_timeStamp,
    #                 "all_attributes": data,
    #                 "gsipk_table": "BoxBuilding",
    #                 "gsisk_id": data["bom_id"],
    #                 "lsi_key": data['boards_id']
    #             }

    #             boards_id = data.get("boards_id")
    #             data2 = list(db_con.Boards.find({"pk_id": boards_id}, {"_id": 0}))
    #             boards = data2[0]['all_attributes']['boards']
    #             board_keys = list(boards.keys())
    #             invent_data = list(db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1,
    #                                                         "all_attributes.qty": 1,
    #                                                         "all_attributes.out_going_qty": 1}))

    #             invent_data = {
    #                 item['all_attributes']['cmpt_id']:
    #                     {
    #                         "qty": item['all_attributes']['qty'],
    #                         "out_going_qty": item['all_attributes'].get('out_going_qty', "0")
    #                     }
    #                 for item in invent_data
    #             }

    #             m_parts = list(component_data.values())

    #             if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
    #                 return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}

    #             if item:
    #                 cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
    #                                 for part, details in component_data.items()}

    #                 for i in range(len(cmpt_id_and_qty)):
    #                     part = "part" + str(i + 1)
    #                     cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
    #                     qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
    #                     activity[cmpt_id]['closing_qty'] = qty

    #                     out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
    #                         cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data.keys() else (
    #                         cmpt_id_and_qty[part]["provided_qty"])

    #                     response1 = db_con.Inventory.update_one(
    #                         {
    #                             "pk_id": cmpt_id
    #                         },
    #                         {
    #                             "$set": {
    #                                 "all_attributes.qty": qty,
    #                                 "all_attributes.out_going_qty": out_going_qty
    #                             }
    #                         }
    #                     )

    #                 bom_id = data["bom_id"]
    #                 data_bom = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "sk_timeStamp": 1}))
    #                 bom_timeStamp = data_bom[0]["sk_timeStamp"]

    #                 db_con.BoxBuilding.insert_one(item)

    #                 db_con.all_tables.update_one(
    #                     {'pk_id': "top_ids", 'sk_timeStamp': "123"},
    #                     {'$set': {'all_attributes.BoxBuilding': "BB_" + box_bilding_id}}
    #                 )

    #                 db_con.BOM.update_one(
    #                     {'pk_id': bom_id, 'sk_timeStamp': bom_timeStamp},
    #                     {'$set': {'all_attributes.status': "Bom_assigned"}}
    #                 )

    #                 if board_keys:
    #                     for key in board_keys:
    #                         filter_criteria = {
    #                             'pk_id': data["boards_id"],
    #                             'sk_timeStamp': data2[0]["sk_timeStamp"]
    #                         }

    #                         update_operation = {
    #                             '$set': {
    #                                 f'all_attributes.boards.{key}.status': "Assigned"
    #                             }
    #                         }

    #                         db_con.Boards.update_one(filter_criteria, update_operation)

    #                 res = db_con['ActivityDetails'].insert_one(
    #                     {
    #                         "pk_id": f"ACTID{activity_id}",
    #                         "sk_timeStamp": sk_timeStamp,
    #                         "all_attributes": activity,
    #                         "gsipk_table": "ActivityDetails",
    #                         "gsisk_id": data['outward_id'],
    #                         "lsi_key": "Utilized",
    #                         "gsipk_id": "EMS"
    #                     })

    #                 db_con.all_tables.update_one(
    #                     {"pk_id": "top_ids"},
    #                     {"$set": {"all_attributes.ActivityId": activity_id}}
    #                 )

    #                 response = {'statusCode': 200, 'body': 'Box Building created successfully'}

    #             else:
    #                 response = {'statusCode': 404, 'body': 'no data found'}

    #             conct.close_connection(client)
    #             return response

    #         else:
    #             return {'statusCode': 200, 'body': 'no inwards for this bom'}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}




#   in these code both url adding base64 and s3 url link     
    # def cmsBomOutwardInfoSaveAssignToBoxBuilding(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         sk_timeStamp = (datetime.now()).isoformat()
    #         data1 = list(db_con.BoxBuilding.find({'pk_id': "BB_1"}, {}))
    #         box_bilding_id = "1"
    #         bom_id = data['bom_id']
    #         part_batch_info = find_stock_inwards(bom_id, db_con, 'M_parts')
    #         part_batch_info = part_batch_info['part_batch_info']
    #         activity = {}
    #         if part_batch_info:
    #             partner_name = db_con.Partners.find_one({"pk_id": data['partner_id']},
    #                                                     {"all_attributes.partner_name": 1})
    #             activity_id = db_con.all_tables.find_one({"pk_id": "top_ids"}, {"all_attributes.ActivityId": 1})
    #             activity_id = int(activity_id['all_attributes'].get('ActivityId', "0")) + 1
    #             if data1:
    #                 statement2 = list(
    #                     db_con.all_tables.find({"pk_id": 'top_ids'}, {"_id": 0, "all_attributes.BoxBuilding": 1}))
    #                 update_id = statement2[0]['all_attributes']["BoxBuilding"][3:]
    #                 box_bilding_id = str(int(update_id) + 1)
    #             data.pop("env_type")
    #             for board_id, board_info in data["boards"].items():
    #                 board_info["status"] = "Assigned"
    #                 # board_info["boardstatus"] = "assigned"  # New key added here
    #             data["BB_id"] = "BB_" + box_bilding_id
    #             # Document upload process
    #             documents = data['documents']
    #             doc = {}
    #             for inx, docs in enumerate(documents):
    #                 image_path = file_uploads.upload_file("boxbuilding", "PtgCms" + env_type, "", "E-Kit" + str(inx),
    #                                                     docs["doc_name"], docs['doc_body'])
    #                 doc[docs["doc_name"]] = image_path
    #             key1 = next(k for k in data.keys() if k.startswith("M_KIT"))
    #             data[key1]["documents"] = doc  # Adding uploaded documents to the data
    #             # Separate documents from component data
    #             component_data = {k: v for k, v in data['M_KIT1'].items() if
    #                             isinstance(v, dict) and 'provided_qty' in v}
    #             for key, value in component_data.items():
    #                 print(f"Processing key: {key}, value: {value}")  # Debugging statement
    #                 if 'provided_qty' not in value:
    #                     raise KeyError(f"Missing 'provided_qty' in value: {value}")  # Error handling for missing key
    #                 var = batch_number_allocation(part_batch_info, int(value['provided_qty']), value['cmpt_id'], {})
    #                 if var:
    #                     data['M_KIT1'][key]['batch_no'] = var['batch_string']
    #                     activity[value['cmpt_id']] = {
    #                         "mfr_prt_num": value.get("mfr_prt_num", "-"),
    #                         "date": str(date.today()),
    #                         "action": "Utilized",
    #                         "Description": "Utilized",
    #                         "issued_to": partner_name['all_attributes']['partner_name'],
    #                         "po_no": var['po_id'],
    #                         'invoice_no': var["invoice_no"],
    #                         "cmpt_id": value.get("cmpt_id", ""),
    #                         "ctgr_id": value.get("ctgr_id", ""),
    #                         "prdt_name": value.get("prdt_name", ""),
    #                         "description": value.get("description", ""),
    #                         "packaging": value.get("packaging", ""),
    #                         "inventory_position": value.get("inventory_position", ""),
    #                         "qty": value['provided_qty'],
    #                         "batchId": var['batch_string'],
    #                         "used_qty": value['provided_qty'],
    #                         "lot_no": var["lot_no"]
    #                     }
    #                 else:
    #                     return {'statusCode': 200, 'body': 'Not enough components were procured for this bom'}
    #             item = {
    #                 "pk_id": "BB_" + box_bilding_id,
    #                 "sk_timeStamp": sk_timeStamp,
    #                 "all_attributes": data,
    #                 "gsipk_table": "BoxBuilding",
    #                 "gsisk_id": data["bom_id"],
    #                 "lsi_key": data['boards_id']
    #             }
    #             boards_id = data.get("boards_id")
    #             data2 = list(db_con.Boards.find({"pk_id": boards_id}, {"_id": 0}))
    #             boards = data2[0]['all_attributes']['boards']
    #             board_keys = list(boards.keys())
    #             invent_data = list(db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1,
    #                                                         "all_attributes.qty": 1,
    #                                                         "all_attributes.out_going_qty": 1}))
    #             invent_data = {
    #                 item['all_attributes']['cmpt_id']:
    #                     {
    #                         "qty": item['all_attributes']['qty'],
    #                         "out_going_qty": item['all_attributes'].get('out_going_qty', "0")
    #                     }
    #                 for item in invent_data
    #             }
    #             m_parts = list(component_data.values())
    #             if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
    #                 return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}
    #             if item:
    #                 cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
    #                                 for part, details in component_data.items()}
    #                 for i in range(len(cmpt_id_and_qty)):
    #                     part = "part" + str(i + 1)
    #                     cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
    #                     qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
    #                     activity[cmpt_id]['closing_qty'] = qty
    #                     out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
    #                         cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data.keys() else (
    #                         cmpt_id_and_qty[part]["provided_qty"])
    #                     response1 = db_con.Inventory.update_one(
    #                         {
    #                             "pk_id": cmpt_id
    #                         },
    #                         {
    #                             "$set": {
    #                                 "all_attributes.qty": qty,
    #                                 "all_attributes.out_going_qty": out_going_qty
    #                             }
    #                         }
    #                     )
    #                 bom_id = data["bom_id"]
    #                 data_bom = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "sk_timeStamp": 1}))
    #                 bom_timeStamp = data_bom[0]["sk_timeStamp"]
    #                 db_con.BoxBuilding.insert_one(item)
    #                 db_con.all_tables.update_one(
    #                     {'pk_id': "top_ids", 'sk_timeStamp': "123"},
    #                     {'$set': {'all_attributes.BoxBuilding': "BB_" + box_bilding_id}}
    #                 )
    #                 db_con.BOM.update_one(
    #                     {'pk_id': bom_id, 'sk_timeStamp': bom_timeStamp},
    #                     {'$set': {'all_attributes.status': "Bom_assigned"}}
    #                 )
    #                 if board_keys:
    #                     for key in board_keys:
    #                         filter_criteria = {
    #                             'pk_id': data["boards_id"],
    #                             'sk_timeStamp': data2[0]["sk_timeStamp"]
    #                         }
    #                         update_operation = {
    #                             '$set': {
    #                                 f'all_attributes.boards.{key}.status': "Assigned"
    #                                 # f'all_attributes.boards.{key}.boardstatus': "assigned"  # New key added here
    #                             }
    #                         }
    #                         db_con.Boards.update_one(filter_criteria, update_operation)
    #                 res = db_con['ActivityDetails'].insert_one(
    #                     {
    #                         "pk_id": f"ACTID{activity_id}",
    #                         "sk_timeStamp": sk_timeStamp,
    #                         "all_attributes": activity,
    #                         "gsipk_table": "ActivityDetails",
    #                         "gsisk_id": data['outward_id'],
    #                         "lsi_key": "Utilized",
    #                         "gsipk_id": "EMS"
    #                     })
    #                 db_con.all_tables.update_one(
    #                     {"pk_id": "top_ids"},
    #                     {"$set": {"all_attributes.ActivityId": activity_id}}
    #                 )
    #                 response = {'statusCode': 200, 'body': 'Box Building created successfully'}
    #             else:
    #                 response = {'statusCode': 404, 'body': 'no data found'}
    #             conct.close_connection(client)
    #             return response
    #         else:
    #             return {'statusCode': 200, 'body': 'no inwards for this bom'}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request(check data)'}
 

    # def cmsBomOutwardInfoSaveAssignToBoxBuilding(request_body):
    #     data = request_body
    #     env_type = data['env_type']
    #     db_conct = conct.get_conn(env_type)
    #     db_con = db_conct['db']
    #     client = db_conct['client']
    #     sk_timeStamp = (datetime.now()).isoformat()
    #     data1 = list(db_con.BoxBuilding.find({'pk_id': "BB_1"}, {}))
    #     box_bilding_id = "1"
    #     bom_id = data['bom_id']
    #     part_batch_info = find_stock_inwards(bom_id,db_con,'M_parts')
    #     part_batch_info = part_batch_info['part_batch_info']
    #     # return part_batch_info
    #     activity = {}
    #     if part_batch_info:
    #         partner_name = db_con.Partners.find_one({"pk_id":data['partner_id']},{"all_attributes.partner_name":1})
    #         activity_id = db_con.all_tables.find_one({"pk_id":"top_ids"},{"all_attributes.ActivityId":1})
    #         activity_id = int(activity_id['all_attributes'].get('ActivityId',"0"))+1
    #         if data1:
    #             statement2 = list(db_con.all_tables.find({"pk_id": 'top_ids'}, {"_id": 0, "all_attributes.BoxBuilding": 1}))
    #             update_id = statement2[0]['all_attributes']["BoxBuilding"][3:]
    #             box_bilding_id = str(int(update_id) + 1)
    #         data.pop("env_type")
    #         for board_id, board_info in data["boards"].items():
    #             board_info["status"] = "Assigned"
    #         data["BB_id"] = "BB_" + box_bilding_id
    #         for key,value in data['M_KIT1'].items():
    #             # batch_info = {inx:value for inx,value in enumerate(part_batch_info[value['cmpt_id']])}
    #             var = batch_number_allocation(part_batch_info,int(value['provided_qty']),value['cmpt_id'],{})
    #             if var:
    #                 data['M_KIT1'][key]['batch_no'] = var['batch_string']
    #                 activity[value['cmpt_id']] = {
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
    #                                 # "closing_qty": f"",
    #                                 "qty": value['provided_qty'],
    #                                 "batchId": var['batch_string'],
    #                                 "used_qty":value['provided_qty'],
    #                                 "lot_no":var["lot_no"]
    #                             }
    #             else:
    #                 return {'statusCode': 200, 'body': 'Not enough components were procured for this bom'}
    #         item = {
    #             "pk_id": "BB_" + box_bilding_id,
    #             "sk_timeStamp": sk_timeStamp,
    #             "all_attributes": data,
    #             "gsipk_table": "BoxBuilding",
    #             "gsisk_id": data["bom_id"],
    #             "lsi_key": data['boards_id']
    #         }
    #         boards_id = data.get("boards_id")
    #         data2 = list(db_con.Boards.find({"pk_id": boards_id}, {"_id": 0}))
    #         boards = data2[0]['all_attributes']['boards']
    #         board_keys = list(boards.keys())
    #         invent_data = list(db_con.Inventory.find({}, {"_id": 0, "all_attributes.cmpt_id": 1, "all_attributes.qty": 1,"all_attributes.out_going_qty": 1}))
    #         invent_data = {
    #                         item['all_attributes']['cmpt_id']: 
    #                             {
    #                                 "qty": item['all_attributes']['qty'],
    #                                 "out_going_qty": item['all_attributes'].get('out_going_qty',"0")
    #                             } 
    #                         for item in invent_data
    #                         }
    #         m_parts = list(data['M_KIT1'].values())
    #         if any(1 for part in m_parts if int(invent_data[part['cmpt_id']]['qty']) < int(part['provided_qty'])):
    #             return {"statusCode": "502", "body": "provided quantity is more than the total quantity"}
            
    #         if item:
    #             cmpt_id_and_qty = {part: {"cmpt_id": details['cmpt_id'], "provided_qty": details['provided_qty']}
    #                             for part, details in data['M_KIT1'].items()}
    #             for i in range(len(cmpt_id_and_qty)):
    #                 part = "part" + str(i + 1)
    #                 cmpt_id = cmpt_id_and_qty[part]["cmpt_id"]
    #                 qty = str(int(invent_data[cmpt_id]["qty"]) - int(cmpt_id_and_qty[part]["provided_qty"]))
    #                 activity[cmpt_id]['closing_qty'] = qty
    #                 out_going_qty = str(int(invent_data[cmpt_id]["out_going_qty"]) + int(
    #                     cmpt_id_and_qty[part]["provided_qty"])) if "out_going_qty" in invent_data.keys() else (
    #                 cmpt_id_and_qty[part]["provided_qty"])
    #                 response1 = db_con.Inventory.update_one(
    #                     {
    #                         "pk_id": cmpt_id
    #                     },
    #                     {
    #                         "$set": {
    #                             "all_attributes.qty": qty,
    #                             "all_attributes.out_going_qty": out_going_qty
    #                         }
    #                     }
    #                 )
    #             bom_id = data["bom_id"]
    #             data_bom = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "sk_timeStamp": 1}))
    #             bom_timeStamp = data_bom[0]["sk_timeStamp"]
    #             db_con.BoxBuilding.insert_one(item)
    #             db_con.all_tables.update_one(
    #                 {'pk_id': "top_ids", 'sk_timeStamp': "123"},
    #                 {'$set': {'all_attributes.BoxBuilding': "BB_" + box_bilding_id}}
    #             )
    #             db_con.BOM.update_one(
    #                 {'pk_id': bom_id, 'sk_timeStamp': bom_timeStamp},
    #                 {'$set': {'all_attributes.status': "Bom_assigned"}}
    #             )
    #             if board_keys:
    #                 for key in board_keys:
    #                     filter_criteria = {
    #                         'pk_id': data["boards_id"],
    #                         'sk_timeStamp': data2[0]["sk_timeStamp"]
    #                     }
    #                     update_operation = {
    #                         '$set': {
    #                             f'all_attributes.boards.{key}.status': "Assigned"
    #                         }
    #                     }
    #                     # Perform the update operation
    #                     db_con.Boards.update_one(filter_criteria, update_operation)
                
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
    #             response = {'statusCode': 200, 'body': 'Box Building created successfully'}
    #             # conct.close_connection(client)
    #         else:
    #             # conct.close_connection(client)
    #             response = {'statusCode': 404, 'body': 'no data found'}
    #         conct.close_connection(client)
    #         return response
    #     else:
    #         return {'statusCode': 200, 'body': 'no inwards for this bom'}
    


    # def cmsPartnerSendBoxBuildingInfo(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         bom_id = data["bom_id"]
            
    #         # Query the BoxBuilding collection
    #         results = list(db_con.BoxBuilding.find({
    #             "$and": [
    #                 {"all_attributes.bom_id": bom_id},
    #                 {"all_attributes.outward_id": outward_id}
    #             ]
    #         }, {"_id": 0, "all_attributes": 1}))
            
    #         if not results:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No data found"}

    #         formatted_response = {"statusCode": 200, "body": {"boards": {}}}

    #         for result in results:
    #             formatted_result = {
    #                 "bom_id": result["all_attributes"]["bom_id"],
    #                 "partner_id": result["all_attributes"]["partner_id"],
    #                 "outward_id": result["all_attributes"]["outward_id"],
    #                 "outward_date": result["all_attributes"]["date"],
    #                 "boards_id": result["all_attributes"]["boards_id"],
    #                 "against_po": result["all_attributes"].get("against_po", ''),
    #                 "sender_name": result["all_attributes"]["sender_name"],
    #                 "contact_details": result["all_attributes"]["contact_details"],
    #                 "qty": result["all_attributes"]["qty"],
    #                 "receiver_name": result["all_attributes"]["receiver_name"],
    #                 "receiver_contact_num": result["all_attributes"]["receiver_contact_num"],
    #                 "boards": {}
    #             }

    #             boards_data = result["all_attributes"]["boards"]

    #             for kit_key, kit_value in boards_data.items():
    #                 if kit_key == "status":
    #                     continue
                    
    #                 kit_boards = {}
    #                 all_boards_have_comments = True

    #                 for board_key, board_data in kit_value.items():
    #                     if board_key == "status":
    #                         continue
                        
    #                     board_info = {
    #                         "pcba_id": board_data.get("pcba_id", ""),
    #                         "som_id_imei_id": board_data.get("som_id_imei_id", ""),
    #                         "e_sim_no": board_data.get("e_sim_no", ""),
    #                         "e_sim_id": board_data.get("e_sim_id", ""),
    #                         "status": board_data.get("status", ""),
    #                         "ict": board_data.get("ict", ""),
    #                         "fct": board_data.get("fct", ""),
    #                         "board_status": board_data.get("board_status", ""),
    #                         "filter_save_status": board_data.get("filter_save_status", False),
    #                         "comment": board_data.get("comment", "")
    #                     }
                        
    #                     if 'comment' not in board_data:
    #                         all_boards_have_comments = False

    #                     kit_boards[board_key] = board_info

    #                 # Check if all boards in the kit have comments
    #                 if all_boards_have_comments:
    #                     formatted_result["boards"][kit_key] = {
    #                         **kit_boards,
    #                         "status": kit_value.get("status", "")
    #                     }

    #             formatted_response["body"] = formatted_result
    #             conct.close_connection(client)
    #             return formatted_response

    #         conct.close_connection(client)
    #         return {"statusCode": 404, "body": "No data found"}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}



    # def cmsPartnerSendBoxBuildingInfo(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         bom_id = data["bom_id"]
            
    #         # Query the BoxBuilding collection
    #         results = list(db_con.BoxBuilding.find({
    #             "$and": [
    #                 {"all_attributes.bom_id": bom_id},
    #                 {"all_attributes.outward_id": outward_id}
    #             ]
    #         }, {"_id": 0, "all_attributes": 1}))
            
    #         if not results:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No data found"}

    #         formatted_response = {"statusCode": 200, "body": {"boards": {}}}

    #         for result in results:
    #             formatted_result = {
    #                 "bom_id": result["all_attributes"]["bom_id"],
    #                 "partner_id": result["all_attributes"]["partner_id"],
    #                 "outward_id": result["all_attributes"]["outward_id"],
    #                 "outward_date": result["all_attributes"]["date"],
    #                 "boards_id": result["all_attributes"]["boards_id"],
    #                 "against_po": result["all_attributes"].get("against_po", ''),
    #                 "sender_name": result["all_attributes"]["sender_name"],
    #                 "contact_details": result["all_attributes"]["contact_details"],
    #                 "qty": result["all_attributes"]["qty"],
    #                 "receiver_name": result["all_attributes"]["receiver_name"],
    #                 "receiver_contact_num": result["all_attributes"]["receiver_contact_num"],
    #                 "boards_kits": {}
    #             }

    #             boards_data = result["all_attributes"]["boards"]

    #             for kit_key, kit_value in boards_data.items():
    #                 if kit_key == "status":
    #                     continue
                    
    #                 kit_boards = {}
    #                 all_boards_have_comments = True

    #                 for board_key, board_data in kit_value.items():
    #                     if board_key == "status":
    #                         continue
                        
    #                     board_info = {
    #                         "pcba_id": board_data.get("pcba_id", ""),
    #                         "som_id_imei_id": board_data.get("som_id_imei_id", ""),
    #                         "e_sim_no": board_data.get("e_sim_no", ""),
    #                         "e_sim_id": board_data.get("e_sim_id", ""),
    #                         "status": board_data.get("status", ""),
    #                         "ict": board_data.get("ict", ""),
    #                         "fct": board_data.get("fct", ""),
    #                         "board_status": board_data.get("board_status", ""),
    #                         "filter_save_status": board_data.get("filter_save_status", False),
    #                         "comment": board_data.get("comment", "")
    #                     }
                        
    #                     if 'comment' not in board_data:
    #                         all_boards_have_comments = False

    #                     kit_boards[board_key] = board_info

    #                 # Check if all boards in the kit have comments
    #                 if all_boards_have_comments:
    #                     formatted_result["boards_kits"][kit_key] = {
    #                         "boards": kit_boards,
    #                         "status": kit_value.get("status", "")
    #                     }

    #             formatted_response["body"] = formatted_result
    #             conct.close_connection(client)
    #             return formatted_response

    #         conct.close_connection(client)
    #         return {"statusCode": 404, "body": "No data found"}

    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}



    # def cmsPartnerSendBoxBuildingInfo(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         bom_id = data["bom_id"]
    #         results = list(db_con.BoxBuilding.find({
    #             "$and": [
    #                 {"all_attributes.bom_id": bom_id},
    #                 {"all_attributes.outward_id": outward_id}
    #             ]
    #         }, {"_id": 0, "all_attributes": 1}))

    #         if results:
    #             formatted_response = {"statusCode": 200, "body": {"boards": {}}}

    #             for result in results:
    #                 formatted_result = {
    #                     "boards": {},
    #                     "bom_id": result["all_attributes"]["bom_id"],
    #                     "partner_id": result["all_attributes"]["partner_id"],
    #                     "outward_id": result["all_attributes"]["outward_id"],
    #                     "outward_date": result["all_attributes"]["date"],
    #                     "boards_id": result["all_attributes"]["boards_id"],
    #                     "against_po": result["all_attributes"].get("against_po", ''),
    #                     "sender_name": result["all_attributes"]["sender_name"],
    #                     "contact_details": result["all_attributes"]["contact_details"],
    #                     "qty": result["all_attributes"]["qty"],
    #                     "receiver_name": result["all_attributes"]["receiver_name"],
    #                     "receiver_contact_num": result["all_attributes"]["receiver_contact_num"]
    #                 }

    #                 sorted_boards = {}
    #                 for kit_key, kit_value in sorted(result["all_attributes"]["boards"].items()):
    #                     boards_with_comments = {}
    #                     all_boards_have_comments = True

    #                     for board_key, board_value in sorted(kit_value.items()):
    #                         if isinstance(board_value, dict) and "comment" in board_value and board_value["comment"]:
    #                             boards_with_comments[board_key] = board_value
    #                         else:
    #                             all_boards_have_comments = False
    #                             break  # Exit if any board lacks a comment

    #                     if all_boards_have_comments and boards_with_comments:
    #                         sorted_boards[kit_key] = boards_with_comments

    #                 if sorted_boards:
    #                     formatted_result["boards"] = sorted_boards
    #                     for key in result["all_attributes"]:
    #                         if key.startswith("M_KIT"):
    #                             formatted_result[key] = {part_key: part_value for part_key, part_value in
    #                                                     sorted(result["all_attributes"][key].items())}
    #                     formatted_response["body"] = formatted_result

    #             conct.close_connection(client)
    #             if formatted_response["body"]["boards"]:
    #                 return formatted_response
    #             else:
    #                 return {"statusCode": 404, "body": "No data found"}
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No data found"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}q


    def cmsPartnerSendBoxBuildingInfo(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            outward_id = data["outward_id"]
            bom_id = data["bom_id"]
            results = list(db_con.BoxBuilding.find({
                "$and": [
                    {"all_attributes.bom_id": bom_id},
                    {"all_attributes.outward_id": outward_id}
                ]
            }, {"_id": 0, "all_attributes": 1}))

            if results:
                formatted_response = {"statusCode": 200, "body": {"boards": {}}}
                for result in results:
                    formatted_result = {
                        "boards": {},
                        "bom_id": result["all_attributes"]["bom_id"],
                        "partner_id": result["all_attributes"]["partner_id"],
                        "outward_id": result["all_attributes"]["outward_id"],
                        "outward_date": result["all_attributes"]["date"],
                        "boards_id": result["all_attributes"]["boards_id"],
                        "against_po": result["all_attributes"].get("against_po", ''),
                        "sender_name": result["all_attributes"]["sender_name"],
                        "contact_details": result["all_attributes"]["contact_details"],
                        "qty": result["all_attributes"]["qty"],
                        "receiver_name": result["all_attributes"]["receiver_name"],
                        "receiver_contact_num": result["all_attributes"]["receiver_contact_num"]
                    }
                    sorted_boards = {}
                    for kit_key, kit_value in sorted(result["all_attributes"]["boards"].items()):
                        all_boards_have_comments = all(
                            isinstance(board_value, dict) and "comment" in board_value and board_value.get("comment", "")
                            for board_value in kit_value.values() if isinstance(board_value, dict)
                        )
                        if all_boards_have_comments:
                            sorted_boards[kit_key] = {board_key: board_value for board_key, board_value in
                                                    sorted(kit_value.items())}
                    if sorted_boards:
                        formatted_result["boards"] = sorted_boards
                    for key in result["all_attributes"]:
                        if key.startswith("M_KIT"):
                            formatted_result[key] = {part_key: part_value for part_key, part_value in
                                                    sorted(result["all_attributes"][key].items()) 
                                                    if part_key not in ["qatest", "inward", "gateentry"]}
                    formatted_response["body"] = formatted_result
                    conct.close_connection(client)
                    return formatted_response
            else:
                conct.close_connection(client)
                return {"statusCode": 404, "body": "No data found"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check data)'}



    # [4:51 PM] Manikanta Aleti
    # def cmsPartnerSendBoxBuildingInfo(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         bom_id = data["bom_id"]
    #         results = list(db_con.BoxBuilding.find({
    #             "$and": [
    #                 {"all_attributes.bom_id": bom_id},
    #                 {"all_attributes.outward_id": outward_id}
    #             ]
    #         }, {"_id": 0, "all_attributes": 1}))
    #         if results:
    #             formatted_response = {"statusCode": 200, "body": {"boards": {}}}
    #             for result in results:
    #                 formatted_result = {
    #                     "boards": {},
    #                     "bom_id": result["all_attributes"]["bom_id"],
    #                     "partner_id": result["all_attributes"]["partner_id"],
    #                     "outward_id": result["all_attributes"]["outward_id"],
    #                     "outward_date": result["all_attributes"]["date"],
    #                     "boards_id": result["all_attributes"]["boards_id"],
    #                     "against_po": result["all_attributes"].get("against_po", ''),
    #                     "sender_name": result["all_attributes"]["sender_name"],
    #                     "contact_details": result["all_attributes"]["contact_details"],
    #                     "qty": result["all_attributes"]["qty"],
    #                     "receiver_name": result["all_attributes"]["receiver_name"],
    #                     "receiver_contact_num": result["all_attributes"]["receiver_contact_num"]
    #                 }
    #                 sorted_boards = {}
    #                 for kit_key, kit_value in sorted(result["all_attributes"]["boards"].items()):
    #                     # print(kit_value)
    #                     all_boards_have_comments = all(
    #                         isinstance(board_value, dict) and "comment" in board_value and board_value.get("comment",
    #                                                                                                     "")
    #                         for board_value in kit_value.values() if isinstance(board_value, dict)
    #                     )
    #                     if all_boards_have_comments:
    #                         sorted_boards[kit_key] = {board_key: board_value for board_key, board_value in
    #                                                 sorted(kit_value.items())}
    #                 if sorted_boards:
    #                     formatted_result["boards"] = sorted_boards
    #                 for key in result["all_attributes"]:
    #                     if key.startswith("M_KIT"):
    #                         formatted_result[key] = {part_key: part_value for part_key, part_value in
    #                                                 sorted(result["all_attributes"][key].items())}
    #                 formatted_response["body"] = formatted_result
    #                 conct.close_connection(client)
    #                 return formatted_response
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No data found"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}
 


    # def cmsPartnerSendBoxBuildingInfo(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         bom_id = data["bom_id"]
    #         results = list(db_con.BoxBuilding.find({
    #             "$and": [
    #                 {"all_attributes.bom_id": bom_id},
    #                 {"all_attributes.outward_id": outward_id}
    #             ]
    #         }, {"_id": 0, "all_attributes": 1}))
    #         if results:
    #             formatted_response = {"statusCode": 200, "body": {"boards": {}}}

    #             for result in results:
    #                 formatted_result = {
    #                     "boards": {},
    #                     "bom_id": result["all_attributes"]["bom_id"],
    #                     "partner_id": result["all_attributes"]["partner_id"],
    #                     "outward_id": result["all_attributes"]["outward_id"],
    #                     "outward_date": result["all_attributes"]["date"],
    #                     "boards_id": result["all_attributes"]["boards_id"],
    #                     "against_po": result["all_attributes"].get("against_po", ''),
    #                     "sender_name": result["all_attributes"]["sender_name"],
    #                     "contact_details": result["all_attributes"]["contact_details"],
    #                     "qty": result["all_attributes"]["qty"],
    #                     "receiver_name": result["all_attributes"]["receiver_name"],
    #                     "receiver_contact_num": result["all_attributes"]["receiver_contact_num"]
    #                 }

    #                 sorted_boards = {}
    #                 for kit_key, kit_value in sorted(result["all_attributes"]["boards"].items()):
    #                     boards_with_comments = {}
    #                     for board_key, board_value in sorted(kit_value.items()):
    #                         if isinstance(board_value, dict) and "comment" in board_value and board_value["comment"]:
    #                             boards_with_comments[board_key] = board_value
    #                     if boards_with_comments:
    #                         sorted_boards[kit_key] = boards_with_comments

    #                 formatted_result["boards"] = sorted_boards

    #                 # Iterate through all keys in result["all_attributes"]
    #                 for key in result["all_attributes"]:
    #                     if key.startswith("M_KIT"):
    #                         formatted_result[key] = {part_key: part_value for part_key, part_value in
    #                                                 sorted(result["all_attributes"][key].items())}

    #                 formatted_response["body"] = formatted_result
    #                 conct.close_connection(client)
    #                 return formatted_response

    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No data found"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}



    # def cmsPartnerSendBoxBuildingInfo(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         bom_id = data["bom_id"]
    #         results = list(db_con.BoxBuilding.find({
    #             "$and": [
    #                 {"all_attributes.bom_id": bom_id},
    #                 {"all_attributes.outward_id": outward_id}
    #             ]
    #         }, {"_id": 0, "all_attributes": 1}))
    #         if results:
    #             formatted_response = {"statusCode": 200, "body": {"boards": {}}}

    #             for result in results:
    #                 formatted_result = {
    #                     "boards": {},
    #                     "bom_id": result["all_attributes"]["bom_id"],
    #                     "partner_id": result["all_attributes"]["partner_id"],
    #                     "outward_id": result["all_attributes"]["outward_id"],
    #                     "outward_date": result["all_attributes"]["date"],
    #                     "boards_id": result["all_attributes"]["boards_id"],
    #                     "against_po": result["all_attributes"].get("against_po", ''),
    #                     "sender_name": result["all_attributes"]["sender_name"],
    #                     "contact_details": result["all_attributes"]["contact_details"],
    #                     "qty": result["all_attributes"]["qty"],
    #                     "receiver_name": result["all_attributes"]["receiver_name"],
    #                     "receiver_contact_num": result["all_attributes"]["receiver_contact_num"]
    #                 }

    #                 sorted_boards = {}
    #                 for kit_key, kit_value in sorted(result["all_attributes"]["boards"].items()):
    #                     sorted_boards[kit_key] = {board_key: board_value for board_key, board_value in
    #                                             sorted(kit_value.items())}
    #                 formatted_result["boards"] = sorted_boards

    #                 # Iterate through all keys in result["all_attributes"]
    #                 for key in result["all_attributes"]:
    #                     if key.startswith("M_KIT"):
    #                         formatted_result[key] = {part_key: part_value for part_key, part_value in
    #                                                 sorted(result["all_attributes"][key].items())}

    #                 formatted_response["body"] = formatted_result
    #                 conct.close_connection(client)
    #                 return formatted_response

    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No data found"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}



    # def cmsPartnerSendBoxBuildingInfo(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         bom_id = data["bom_id"]
    #         results = list(db_con.BoxBuilding.find({
    #             "$and": [
    #                 {"all_attributes.bom_id": bom_id},
    #                 {"all_attributes.outward_id": outward_id}
    #             ]
    #         }, {"_id": 0, "all_attributes": 1}))
    #         if results:
    #             formatted_response = {"statusCode": 200, "body": {"boards": {}}}

    #             for result in results:
    #                 formatted_result = {
    #                     "boards": {},
    #                     "bom_id": result["all_attributes"]["bom_id"],
    #                     "partner_id": result["all_attributes"]["partner_id"],
    #                     "outward_id": result["all_attributes"]["outward_id"],
    #                     "outward_date": result["all_attributes"]["date"],
    #                     # date
    #                     "boards_id": result["all_attributes"]["boards_id"],
    #                     "against_po": result["all_attributes"].get("against_po", ''),
    #                     "sender_name": result["all_attributes"]["sender_name"],
    #                     "contact_details": result["all_attributes"]["contact_details"],
    #                     "partner_id": result["all_attributes"]["partner_id"],
    #                     "qty": result["all_attributes"]["qty"],
    #                     "receiver_name": result["all_attributes"]["receiver_name"],
    #                     "receiver_contact_num": result["all_attributes"]["receiver_contact_num"]
    #                 }

    #                 sorted_boards = {}
    #                 for kit_key, kit_value in sorted(result["all_attributes"]["boards"].items()):
    #                     sorted_boards[kit_key] = {board_key: board_value for board_key, board_value in
    #                                               sorted(kit_value.items())}
    #                 formatted_result["boards"] = sorted_boards
                    

    #                 # Iterate through all keys in result["all_attributes"]
    #                 for key in result["all_attributes"]:
    #                     if key.startswith("M_KIT"):
    #                         formatted_result[key] = {part_key: part_value for part_key, part_value in
    #                                                  sorted(result["all_attributes"][key].items())}
                            
    #                 formatted_response["body"] = formatted_result
    #                 conct.close_connection(client)
    #                 return formatted_response

    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No data found"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}


    # def cmsPartnerGetSendBoards1(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         board_status = data['board_status']

    #         results = list(
    #             db_con.Boards.find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1})
    #         )
            
    #         if results:
    #             for item in results:
    #                 boards = item.get("all_attributes", {}).get("boards", {})
                    
    #                 # Filter boards where boardkits_status is "Assigned" and comment is not empty
    #                 filtered_boards = {
    #                     kit: {
    #                         board: attributes for board, attributes in boards.items()
    #                         if attributes['boardkits_status'] == "Assigned" and attributes.get('comment')
    #                     }
    #                     for kit, boards in item['all_attributes']['boards'].items()
    #                     if any(
    #                         attributes['boardkits_status'] == "Assigned" and attributes.get('comment')
    #                         for attributes in boards.values()
    #                     )
    #                 }
                    
    #                 response_body = {
    #                     "bom_id": results[0]["all_attributes"]["bom_id"],
    #                     "outward_id": results[0]["all_attributes"]["outward_id"],
    #                     "sorteddata": filtered_boards
    #                 }
                    
    #                 response = {"statusCode": 200, "body": response_body}
    #                 if response:
    #                     conct.close_connection(client)
    #                     return response
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No data found"}
            
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request(check data)'}



    def cmsPartnerGetSendBoards(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            outward_id = data["outward_id"]
            request_type = data['type']
            
            # Determine the collection to query based on the request type
            collection_name = 'Boards' if request_type == 'EMS' else 'BoxBuilding'
            
            # Fetch the relevant records from the database
            results = list(
                db_con[collection_name].find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1})
            )
            
            if results:
                response_body = {
                    "bom_id": results[0]["all_attributes"]["bom_id"],
                    "outward_id": results[0]["all_attributes"]["outward_id"]
                }
                
                # Process the boards data based on the type
                if request_type == 'EMS':
                    # For EMS type, include all boards
                    boards = results[0].get("all_attributes", {}).get("boards", {})
                    if isinstance(boards, dict):
                        sorted_data = dict(sorted(boards.items(), key=lambda x: int(x[0].replace('boards_kit', ''))))

                         # Fixed From here
                        filtered_data = {}
                        for kit, boards in sorted_data.items():
                            if data['board_status'] == "All":
                                # Include all boards regardless of their status
                                filtered_boards = boards
                            else:
                                # Filter based on the specific board_status
                                filtered_boards = {board: details for board, details in boards.items() if details['board_status'] == data['board_status']}
                            
                            if filtered_boards:
                                filtered_data[kit] = filtered_boards
                        response_body["sorteddata"] = filtered_data
                        # Till here

                        # response_body["sorteddata"] = sorted_data
                    else:
                        response_body["sorteddata"] = {}
                
                elif request_type == 'BOX BUILDING':
                    # For BOX BUILDING type, show all boards and include only 'Assigned' boards in a separate field
                    all_boards = results[0].get("all_attributes", {}).get("boards", {})
                    if isinstance(all_boards, dict):
                        assigned_boards = {
                            kit: {
                                board: attributes for board, attributes in boards.items()
                                if isinstance(attributes, dict) and attributes.get('boardkits_status') == "Assigned"
                            }
                            for kit, boards in all_boards.items()
                        }
                        response_body["sorteddata"] = all_boards
                        # response_body["assigned_boards"] = assigned_boards
                    else:
                        response_body["sorteddata"] = {}

                response = {"statusCode": 200, "body": response_body}
                conct.close_connection(client)
                return response
            
            else:
                conct.close_connection(client)
                return {"statusCode": 404, "body": "No data found"}
        
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}




    # def cmsPartnerGetSendBoards(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         board_status = data['board_status']
    #         request_type = data['type']
            
    #         # Determine the collection to query based on the request type
    #         collection_name = 'Boards' if request_type == 'EMS' else 'BoxBuilding'
            
    #         # Fetch the relevant records from the database
    #         results = list(
    #             db_con[collection_name].find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1})
    #         )
            
    #         if results:
    #             response_body = {
    #                 "bom_id": results[0]["all_attributes"]["bom_id"],
    #                 "outward_id": results[0]["all_attributes"]["outward_id"]
    #             }
                
    #             # Process the boards data based on the type
    #             if request_type == 'EMS':
    #                 # For EMS type, include all boards
    #                 boards = results[0].get("all_attributes", {}).get("boards", {})
    #                 sorted_data = dict(sorted(boards.items(), key=lambda x: int(x[0].replace('boards_kit', ''))))
    #                 response_body["sorteddata"] = sorted_data

    #             elif request_type == 'BOX BUILDING':
    #                 # For BOX BUILDING type, show all boards and include only 'Assigned' boards in a separate field
    #                 all_boards = results[0].get("all_attributes", {}).get("boards", {})
    #                 assigned_boards = {
    #                     kit: {
    #                         board: attributes for board, attributes in boards.items()
    #                         if attributes.get('boardkits_status') == "Assigned"
    #                     }
    #                     for kit, boards in all_boards.items()
    #                 }
    #                 response_body["sorteddata"] = all_boards
    #                 # response_body["assigned_boards"] = assigned_boards

    #             response = {"statusCode": 200, "body": response_body}
    #             conct.close_connection(client)
    #             return response
            
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No data found"}
        
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request(check data)'}



    # def cmsPartnerGetSendBoards(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         board_status = data['board_status']
    #         request_type = data['type']
            
    #         # Determine the collection to query based on the request type
    #         collection_name = 'Boards' if request_type == 'EMS' else 'BoxBuilding'
            
    #         # Fetch the relevant records from the database
    #         results = list(
    #             db_con[collection_name].find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1})
    #         )
            
    #         if results:
    #             response_body = {
    #                 "bom_id": results[0]["all_attributes"]["bom_id"],
    #                 "outward_id": results[0]["all_attributes"]["outward_id"]
    #             }
                
    #             # Filter and process the boards data
    #             for item in results:
    #                 boards = item.get("all_attributes", {}).get("boards", {})
    #                 filtered_boards = {
    #                     kit: {
    #                         board: attributes for board, attributes in boards.items()
    #                         if attributes['boardkits_status'] == "Assigned" and 'comment' in attributes
    #                     }
    #                     for kit, boards in boards.items()
    #                     if any(attributes['boardkits_status'] == "Assigned" and 'comment' in attributes
    #                         for attributes in boards.values())
    #                 }
                    
    #                 if filtered_boards:
    #                     response_body["sorteddata"] = filtered_boards
    #                 else:
    #                     response_body["sorteddata"] = {}

    #             response = {"statusCode": 200, "body": response_body}
    #             conct.close_connection(client)
    #             return response
            
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No data found"}
        
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request(check data)'}



    # def cmsPartnerGetSendBoards(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         board_status = data['board_status']
    #         request_type = data['type']
            
    #         # Determine the collection to query based on the request type
    #         collection_name = 'Boards' if request_type == 'EMS' else 'BoxBuilding'
            
    #         # Fetch the relevant records from the database
    #         results = list(
    #             db_con[collection_name].find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1})
    #         )
            
    #         if results:
    #             response_body = {
    #                 "bom_id": results[0]["all_attributes"]["bom_id"],
    #                 "outward_id": results[0]["all_attributes"]["outward_id"]
    #             }
                
    #             for item in results:
    #                 boards = item.get("all_attributes", {}).get("boards", {})
                    
    #                 if request_type in ["EMS", "BOX BUILDING"]:
    #                     # Filter boards for both EMS and BOX BUILDING types
    #                     filtered_boards = {
    #                         kit: {board: attributes for board, attributes in boards.items()
    #                             if attributes['boardkits_status'] == "Assigned" and 'comment' in attributes}
    #                         for kit, boards in item['all_attributes']['boards'].items()
    #                     }
                        
    #                     response_body["sorteddata"] = filtered_boards
                    
    #                 else:
    #                     # Handle other types if necessary
    #                     response_body["sorteddata"] = boards

    #             response = {"statusCode": 200, "body": response_body}
    #             conct.close_connection(client)
    #             return response
            
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No data found"}
        
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request(check data)'}




    # def cmsPartnerGetSendBoards(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         board_status=data['board_status']
    #         results = list(
    #             db_con.Boards.find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1}))
    #         # return results
    #         response = {"statusCode": 200, "body": results}
    #         if results:
    #             for item in results:
    #                 if data['board_status']=="All":
    #                     boards = item.get("all_attributes", {}).get("boards", {})
    #                     sorted_data = dict(sorted(boards.items(), key=lambda x: int(x[0].replace('boards_kit', ''))))
    #                     response_body = {
    #                         "bom_id": results[0]["all_attributes"]["bom_id"],
    #                         "outward_id": results[0]["all_attributes"]["outward_id"],
    #                         "sorteddata": sorted_data
    #                     }
    #                     response = {"statusCode": 200, "body": response_body}
    #                     if response:
    #                         conct.close_connection(client)
    #                         return response
    #                 elif data['board_status']==board_status:
    #                     filtered_boards = {
    #                         kit: {board: attributes for board, attributes in boards.items() if attributes['board_status'] == board_status}
    #                         for item in results
    #                         for kit, boards in item['all_attributes']['boards'].items()
    #                         if any(attributes['board_status'] == board_status for attributes in boards.values())}
    #                     response_body = {
    #                         "bom_id": results[0]["all_attributes"]["bom_id"],
    #                         "outward_id": results[0]["all_attributes"]["outward_id"],
    #                         "sorteddata": filtered_boards
    #                     }

    #                     response = {"statusCode": 200, "body": response_body}
    #                     if response:
    #                         conct.close_connection(client)
    #                         return response
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No data found"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request(check data)'}
        
    
    def cmsBomGetSendBoards(request_body):
            try:
                data = request_body
                env_type = data['env_type']
                db_conct = conct.get_conn(env_type)
                db_con = db_conct['db']
                client = db_conct['client']
                outward_id = data["outward_id"]
            
                results = list(
                    db_con.Boards.find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1})
                )
            
                if not results:
                    return {"statusCode": 404, "body": "No data found"}
            
                response_data = {
                    "bom_id": results[0]['all_attributes']['bom_id'],
                    "outward_id": results[0]['all_attributes']['outward_id'],
                    "sorteddata": {}
                }
            
                for kit, boards in results[0]['all_attributes']['boards'].items():
                    if kit == "status":
                        continue
                
                    kit_boards_with_comments = {
                        board: board_data
                        for board, board_data in boards.items()
                        if 'kits_send' in board_data
                    }
                
                    # Check if there are boards with comments
                    if kit_boards_with_comments:
                        # Add kits where the number of boards with comments is equal to the total number of boards
                        if len(kit_boards_with_comments) == len(boards):
                            response_data["sorteddata"][kit] = boards
            
                # Check if there is at least one kit with the required conditions
                if not response_data["sorteddata"]:
                    return {"statusCode": 404, "body": "No data found"}
            
                # Add the status field if it exists
                if "status" in results[0]['all_attributes']['boards']:
                    response_data["status"] = results[0]['all_attributes']['boards']['status']
    
                return {"statusCode": 200, "body": response_data}
        
            except Exception as err:
                exc_type, exc_obj, tb = sys.exc_info()
                f_name = tb.tb_frame.f_code.co_filename
                line_no = tb.tb_lineno
                print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
                return {'statusCode': 400, 'body': 'Bad Request (check data)'}
    
 



    
    # def cmsBomGetSendBoards(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
            
    #         results = list(
    #             db_con.Boards.find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1})
    #         )
    #         if not results:
    #             return {"statusCode": 404, "body": "No data found"}
            
    #         response_data = {
    #             "bom_id": results[0]['all_attributes']['bom_id'],
    #             "outward_id": results[0]['all_attributes']['outward_id'],
    #             "sorteddata": {}
    #         }
            
    #         for kit, boards in results[0]['all_attributes']['boards'].items():
    #             if kit == "status":
    #                 continue
                
    #             kit_boards_with_comments = {
    #                 board: board_data 
    #                 for board, board_data in boards.items() 
    #                 if 'comment' in board_data
    #             }
                
    #             # Check if there are boards with comments
    #             if kit_boards_with_comments:
    #                 # Add kits where the number of boards with comments is equal to the total number of boards
    #                 if len(kit_boards_with_comments) == len(boards):
    #                     response_data["sorteddata"][kit] = boards
    #         # Check if there is at least one kit with the required conditions
    #         if not response_data["sorteddata"]:
    #             return {"statusCode": 404, "body": "No data found"}
            
    #         # Add the status field if it exists
    #         if "status" in results[0]['all_attributes']['boards']:
    #             response_data["status"] = results[0]['all_attributes']['boards']['status']

    #         return {"statusCode": 200, "body": response_data}
        
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}


    


    # def cmsBomGetSendBoards(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
            
    #         results = list(
    #             db_con.Boards.find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1})
    #         )
            
    #         if not results:
    #             return {"statusCode": 404, "body": "No data found"}
            
    #         response_data = {
    #             "bom_id": results[0]['all_attributes']['bom_id'],
    #             "outward_id": results[0]['all_attributes']['outward_id'],
    #             "sorteddata": {}
    #         }
            
    #         for kit, boards in results[0]['all_attributes']['boards'].items():
    #             if kit == "status":
    #                 continue
                
    #             kit_boards_with_comments = {
    #                 board: board_data 
    #                 for board, board_data in boards.items() 
    #                 if 'comment' in board_data
    #             }
                
    #             # Check if the status exists
    #             if "status" in boards:
    #                 # Add kits where the number of boards with comments is len(boards) - 1
    #                 if len(kit_boards_with_comments) == len(boards) - 1:
    #                     response_data["sorteddata"][kit] = boards
    #             else:
    #                 # Add kits where all boards have comments
    #                 if len(kit_boards_with_comments) == len(boards):
    #                     response_data["sorteddata"][kit] = boards
            
    #         # Check if there is at least one kit with the required conditions
    #         if not response_data["sorteddata"]:
    #             return {"statusCode": 404, "body": "No data found"}
            
    #         # Add the status field if it exists
    #         if "status" in results[0]['all_attributes']['boards']:
    #             response_data["status"] = results[0]['all_attributes']['boards']['status']

    #         return {"statusCode": 200, "body": response_data}
        
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}





    def cmsPartnerSendBoards(request_body):
        data = request_body
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        # for inx, item in enumerate(data['board_information']):
        #     for key, value in item.items():
        #         if not data['board_information'][inx][key].strip():
        #             return {"statusCode": 400, "body": f"Column name {key} empty for row {inx + 1}"}
        # if not len(data['board_information']):
        #     conct.close_connection(client)
        #     return {"statusCode": 404, "body": "please upload boards info"}
        sk_timeStamp = (datetime.now()).isoformat()
        ems_data = list(db_con.EMS.find({
            "$and": [
                {"lsi_key": data['bom_id']},
                {"all_attributes.type": 'EMS'}
            ]
        }, {"_id": 0, "all_attributes": 1}))
        if ems_data:
            order_quantity = 0
            pattern = r'E-KIT\d+'
            for key in ems_data[0]['all_attributes'].keys():
                # print(key)
                match = re.search(pattern, key)
                if match:                                               
                    for inside_key in ems_data[0]['all_attributes'][key].keys():
                        order_quantity += int(ems_data[0]['all_attributes'][key][inside_key].get('qty', '0'))
            if order_quantity:
                result = list(db_con.Boards.find({"gsipk_id": data['outward_id']}, {"_id": 0}))
                if result:
                    result = result[0]
                    boards_filter = {kit['PCBA_ID']: kit for kit in data['board_information']}
                    boards_filter = list(boards_filter.values())
                    error_messages = []
                    pcba_ids_matched=[]
                    match_found = False
                    if 'kit_id' in data:
                        for event_board in data['board_information']:
                            pcba_id_to_match = event_board["PCBA_ID"]
                            pcba_ids_to_update = [event_board["PCBA_ID"] for event_board in data['board_information']]
                            existing_pcba_ids = [attributes['pcba_id'] for boards in result['all_attributes']['boards'].values() for attributes in boards.values()]
                            unmatched_pcba_ids = [pcba_id for pcba_id in pcba_ids_to_update if pcba_id not in existing_pcba_ids]
                            if unmatched_pcba_ids:
                                return {'statusCode': 400, 'body': f"The following PCBA IDs do not match existing data: {', '.join(unmatched_pcba_ids)}. New PCBA IDs cannot be uploaded."}
                            for kit, boards in result['all_attributes']['boards'].items():
                                for board, attributes in boards.items():
                                    if attributes['pcba_id'] == pcba_id_to_match:
                                        if attributes['board_status'] == 'Rejected':
                                            # if any(item.lower() == 'na' for inx,value in enumerate(boards_filter) for item in value.values()):
                                            #     attributes.update((k.lower(), v) for k, v in event_board.items() if k.lower() in attributes)
                                            #     match_found = True
                                            # else:
                                            #     attributes['board_status']='EMS_Done'
                                            #     attributes.update((k.lower(), v) for k, v in event_board.items() if k.lower() in attributes)
                                            #     match_found=True
                                            if any(item.lower() == 'na' for inx, value in enumerate(boards_filter) for item in value.values()):
                                                for board_info in data['board_information']:
                                                    board_info['board_status'] = 'Rejected' if any(value.lower() == 'na' for value in board_info.values()) else 'EMS_Done'
                                                    match_found = True
                                                if match_found:
                                                    attributes.update((k.lower(), v) for k, v in event_board.items() if k.lower() in attributes)
                                            else:
                                                attributes['board_status'] = 'EMS_Done'
                                                attributes.update((k.lower(), v) for k, v in event_board.items() if k.lower() in attributes)
                                                match_found = True
                                        elif attributes['board_status'] == 'EMS_Done':
                                            
                                            error_messages.append(f"We cannot update boards with {pcba_id_to_match} which are already EMS_done")
                                            return {'statusCode': 400, 'body': error_messages[0]}
                        print(match_found)
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

                            db_con.Boards.update_one(filter_query, update_query)
                            return {'statusCode': 200, 'body': "Updated successfully"}
                        # if not match_found:
                        #     return {'statusCode':400,'body':'we cannot upload new pcb boards while reuploading'}
                    else:
                        existing_quantity = int(result['all_attributes']['max_kit_id'])
                        qty = int(result['all_attributes']['qty'])
                        if existing_quantity + len(data['board_information']) > order_quantity:
                            return {"statusCode": 200, "body": "you cannot upload boards more than what is ordered"}
                        pcb_ids = []
                        _imei_comp = [
                            [pcb_ids.append(result['all_attributes']['boards'][key][inner_key]['pcba_id']) for inner_key
                            in result['all_attributes']['boards'][key].keys() if inner_key.startswith("board")] for key in
                            result['all_attributes']['boards'].keys()]
                        boards_filter = {board['PCBA_ID']: board for board in data['board_information'] if
                                        board['PCBA_ID'] not in pcb_ids}
                        boards_filter = list(boards_filter.values())
                        var = [1 for board in data['board_information'] if board['PCBA_ID'] in pcb_ids]
                        if any(1 for board in data['board_information'] if board['PCBA_ID'] in pcb_ids):
                            return {'statusCode': 400, 'body': f"{len(var)} pcb id already exists"}
                        for event_board in data['board_information']:
                            pcba_id_to_match = event_board["PCBA_ID"]
                            for kit, boards in result['all_attributes']['boards'].items():
                                for board, attributes in boards.items():
                                    if attributes['pcba_id'] == pcba_id_to_match:
                                        if attributes['board_status'] == 'Rejected':
                                            if any(item.lower() == 'na' for inx,value in enumerate(boards_filter) for item in value.values()):
                                                attributes.update((k.lower(), v) for k, v in event_board.items() if k.lower() in attributes)
                                                # print(attributes)
                                                match_found = True
                                            else:
                                                attributes['board_status']='EMS_done'
                                                attributes.update((k.lower(), v) for k, v in event_board.items() if k.lower() in attributes)
                                                match_found=True
                        if not match_found:
                            all_attributes = result['all_attributes']
                            # all_attributes['qty'] = qty+int(b_data['quantity'])
                            quantity = result['all_attributes']['qty']
                            max_kit_id = int(result['all_attributes']['max_kit_id'])
                            boards = int(result['all_attributes']['max_board_id'])
                            boards_qty = int(result['all_attributes']['max_board_id']) + len(data['board_information'])
                            if int(boards_qty) > int(quantity):
                                return {'statusCode': 400, 'body': "you cannot upload boards more than what is ordered"}
                            all_attributes['max_kit_id'] = str(max_kit_id + 1)
                            all_attributes['max_board_id'] = str(boards + len(data['board_information']))
                            all_attributes['boards'].update(
                                {f"boards_kit{max_kit_id + 1}":
                                    {f"board{boards + inx + 1}":
                                        {
                                            "kit_id": f"boards_kit{max_kit_id + 1}",
                                            "pcba_id": item['PCBA_ID'].lower() if item['PCBA_ID'].lower()=='na' else item['PCBA_ID'],
                                            # "als_pcba": item['ALS_PCBA'],
                                            # "display_number": item['Display_Number'],
                                            "som_id_imei_id": item['SOM_ID_IMEI_ID'].lower() if item['SOM_ID_IMEI_ID'].lower()=='na' else item['SOM_ID_IMEI_ID'],
                                            "e_sim_no": item['E_SIM_NO'],
                                            "e_sim_id": item['E_SIM_ID'].lower() if item['E_SIM_ID'].lower()=='na' else item['E_SIM_ID'],
                                            "status": "Unassigned",
                                            "boardkits_status":"Unassigned",
                                            "ict":item['ICT'].lower() if item['ICT'].lower()=='na' else item['ICT'],
                                            "fct":item['FCT'].lower() if item['FCT'].lower()=='na' else item['FCT'],
                                            "board_status": "Rejected" if any(value.lower() == 'na' for value in item.values()) else "EMS_Done"
                                        }
                                        # for inx,item in enumerate(b_data['board_information'])
                                        for inx, item in enumerate(boards_filter)
                                    }
                                }
                            )
                            filter_query = {
                                "pk_id": result["pk_id"],
                                "sk_timeStamp": result["sk_timeStamp"]
                            }

                            update_query = {
                                "$set": {
                                    "all_attributes": all_attributes
                                }
                            }
                            # return all_attributes
                            db_con.Boards.update_one(filter_query, update_query)

                            if len(boards_filter):
                                conct.close_connection(client)
                                return {'statusCode': 200, 'body': f'{len(boards_filter)} Records updated successfully'}
                            else:
                                conct.close_connection(client)
                                return {'statusCode': 400, 'body': f'records already in database'}
                else:
                    for inx, item in enumerate(data['board_information']):
                        for key, value in item.items():
                            if not data['board_information'][inx][key].strip():
                                return {"statusCode": 400, "body": f"Column name {key} empty for row {inx + 1}"}
                    if not len(data['board_information']):
                        conct.close_connection(client)
                        return {"statusCode": 404, "body": "please upload boards info"}
                    boards_filter = {board['PCBA_ID']: board for board in data['board_information']}
                    boards_filter = list(boards_filter.values())
                    print(boards_filter)
                    if len(boards_filter) < len(data['board_information']):
                        return {'statusCode': 400,
                                'body': f"{len(data['board_information']) - len(boards_filter)} records is duplicate check data"}
                    boards_qty = len(data['board_information'])
                    quantity = data['quantity']
                    if int(boards_qty) > int(quantity):
                        conct.close_connection(client)
                        return {'statusCode': 400, 'body': "you cannot upload boards more than what is ordered"}
                    max_kit_id = 0
                    all_attributes = {}
                    all_attributes['bom_id'] = data['bom_id']
                    all_attributes['outward_id'] = data['outward_id']
                    all_attributes['against_po'] = data['against_po']
                    all_attributes['partner_id'] = data['partner_id']
                    all_attributes['qty'] = data.get('quantity', '0')
                    all_attributes['max_kit_id'] = '1'
                    all_attributes['max_board_id'] = len(data['board_information'])
                    all_attributes['type'] = "EMS"
                    all_attributes['reciever_name'] = ''
                    all_attributes['sender_name'] = ''
                    all_attributes['receiver_contact_num'] = ''
                    all_attributes['delivery_end_date'] = data['delivery_end_date']
                    all_attributes['boards'] = {
                        f"boards_kit{max_kit_id + 1}":
                            {
                                f"board{inx + 1}":
                                    {
                                        "kit_id": f"boards_kit{max_kit_id + 1}",
                                        "pcba_id":item['PCBA_ID'].lower() if item['PCBA_ID'].lower()=='na' else item['PCBA_ID'],
                                        # "als_pcba": item['ALS_PCBA'],
                                        # "display_number": item['Display_Number'],
                                        "som_id_imei_id": item['SOM_ID_IMEI_ID'].lower() if item['SOM_ID_IMEI_ID'].lower()=='na' else item['SOM_ID_IMEI_ID'],
                                        "e_sim_no": item['E_SIM_NO'],
                                        "e_sim_id": item['E_SIM_ID'].lower() if item['E_SIM_ID'].lower()=='na' else item['E_SIM_ID'],
                                        "status": "Unassigned",
                                        "boardkits_status":"Unassigned",
                                        "ict":item['ICT'].lower() if item['ICT'].lower()=='na' else item['ICT'],
                                        "fct":item['FCT'].lower() if item['FCT'].lower()=='na' else item['FCT'],
                                        "board_status": "Rejected" if any(value.lower() == 'na' for value in item.values()) else "EMS_Done"

                                    }
                                # for inx,item in enumerate(b_data['board_information'])
                                for inx, item in enumerate(boards_filter)
                            }
                    }
                    item = {
                        "pk_id": f"{data['outward_id']}_BK",
                        "sk_timeStamp": sk_timeStamp,
                        "all_attributes": all_attributes,
                        "gsipk_table": "Boards",
                        "gsipk_id": data['outward_id'],
                        "lsi_key": "Electronic",
                        "gsisk_id": "--"
                    }
                    db_con.Boards.insert_one(item)
                    conct.close_connection(client)
                    return {'statusCode': 200, 'body': f'{len(boards_filter)} Records updated successfully'}
            else:
                conct.close_connection(client)
                return {'statusCode': 400, 'body': f'order_quantity is 0 for the given order'}
        else:
            conct.close_connection(client)
            return {'statusCode': 400, 'body': f'No data found for given outward id'}

 
    def cmsPartnerSaveBoardsFilterSave(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            outward_id = data["outward_id"]
            results = list(
                db_con.Boards.find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1,'pk_id':1,'sk_timeStamp':1}))
            board_ids_to_update = [board['pcba_id'] for board in data['board_information']]
            if results:
                for item in results:
                    for kit, boards in item['all_attributes']['boards'].items():
                        for board, attributes in boards.items():
                            if attributes['pcba_id'] in board_ids_to_update:
                                attributes['filter_save_status'] = True
                                attributes['kits_send'] = "true"
                                for event_board in data['board_information']:
                                    if event_board['pcba_id'] == attributes['pcba_id']:
                                        attributes['comment']=event_board['comment']
                                        # attributes['kits_send'] = event_board['kits_send']
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
                    db_con.Boards.update_one(filter_query, update_query)
                return {'statusCode': 200, 'body': "filtered boards Saved successfully "}
            else:
                return {'statusCode':400,'body':'No data available'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}
 
 


    # def cmsPartnerSaveBoardsFilterSave(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         outward_id = data["outward_id"]
    #         results = list(
    #             db_con.Boards.find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1,'pk_id':1,'sk_timeStamp':1}))
    #         board_ids_to_update = [board['pcba_id'] for board in data['board_information']]
    #         if results:
    #             for item in results:
    #                 for kit, boards in item['all_attributes']['boards'].items():
    #                     for board, attributes in boards.items():
    #                         if attributes['pcba_id'] in board_ids_to_update:
    #                             attributes['filter_save_status'] = True
    #                             for event_board in data['board_information']:
    #                                 if event_board['pcba_id'] == attributes['pcba_id']:
    #                                     attributes['comment']=event_board['comment']
    #                                     attributes.update((k.lower(), v) for k, v in event_board.items() if k.lower() in attributes)
                    
    #                 filter_query = {
    #                     "pk_id": item["pk_id"],
    #                     "sk_timeStamp": item["sk_timeStamp"]
    #                 }
    #                 update_query = {
    #                     "$set": {
    #                         "all_attributes": item['all_attributes']
    #                     }
    #                 }
    #                 db_con.Boards.update_one(filter_query, update_query)
    #             return {'statusCode': 200, 'body': "filtered boards Saved successfully "}
    #         else:
    #             return {'statusCode':400,'body':'No data available'}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request(check data)'} 


    def cmsBoxbuildingDocGet(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            outward_id = data["outward_id"]
            query=list(db_con.BoxBuilding.find({'all_attributes.outward_id':outward_id},{'_id':0,'all_attributes.documents':1}))
            if query:
                doc=query[0]['all_attributes'].get('documents'," ")
                name_list=list(doc.keys())
                url_list=[]
                for i in name_list:
                    url_list.append(doc[i])
                final_list=[]
                for url_list, name_list in zip(url_list, name_list):
                    final_list.append({"doc_url": url_list, "doc_name": name_list})
                return {'statusCode': 200, 'body': final_list}
            else:
                return {'statusCode': 200, 'body': []}
           
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsBoardBulkUpload(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            base64_zip_data = data['zip_data']
            po_id = data['outward_id']
            kit = data['kit']
            zip_data = base64.b64decode(base64_zip_data)
            zip_file = io.BytesIO(zip_data)
            matched_count = 0
            mismatched_count = 0
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                file_names = zip_ref.namelist()
                for file_name in file_names:
                    # file_name_cleaned = file_name.replace("zip/", "").replace(" ", "_").lower()
                    file_name_cleaned = re.sub(r'^[^/]+/', '', file_name).lower()
                    file_data = zip_ref.read(file_name)
                    file_base64 = base64.b64encode(file_data).decode('utf-8')
                    # file_url = file_uploads.upload_excel_and_csv_files("boards", "PtgCms" + env_type, "bulk_documents", kit,
                    #                                            file_name_cleaned, file_base64)
                    file_url = file_uploads.upload_bulk_files("boards", "PtgCms" + env_type, "bulk_documents", kit,
                                                               file_name_cleaned, file_base64)
                    board = db_con.Boards.find_one({'all_attributes.outward_id': po_id})
                    name, ext = os.path.splitext(file_name_cleaned)
                    matched = False
                    if board:
                        kit_key = kit
                        if 'boards' in board['all_attributes']:
                            boards_kit = board['all_attributes']['boards'].get(kit_key, {})
                            for board_key, board_value in boards_kit.items():
                                pcba_id = board_value.get('pcba_id', '').lower()
                                if pcba_id == name:
                                    cleaned_name = name.replace('.','')
                                    result = db_con.Boards.update_one(
                                        {'all_attributes.outward_id': po_id},
                                        {'$set': {
                                            f"all_attributes.boards.{kit_key}.{board_key}.document": {
                                                'doc_name': cleaned_name,
                                                'doc_url': file_url
                                            }
                                        }},
                                        upsert=True
                                    )
                                    matched = True
                                    matched_count += 1
                                    break
                    if not matched:
                        mismatched_count += 1
            return {'statusCode': 200, 'body': f'Bulk files uploaded and processed successfully. Matched: {matched_count}, Mismatched: {mismatched_count}'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': f'Bad Request (check data): {err} (file: {f_name}, line: {line_no})'}
    
    def cmsFinalProductBulkUpload(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            base64_zip_data = data['zip_data']
            po_id = data['outward_id']
            kit = data['kit']
            zip_data = base64.b64decode(base64_zip_data)
            zip_file = io.BytesIO(zip_data)
            matched_count = 0
            mismatched_count = 0
            rejected_count = 0
            product_rejected_count = 0
            other_count = 0
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                file_names = zip_ref.namelist()
                for file_name in file_names:
                    # file_name_cleaned = file_name.replace("zip/", "").replace(" ", "_").lower()
                    file_name_cleaned = re.sub(r'^[^/]+/', '', file_name).lower()
                    file_data = zip_ref.read(file_name)
                    file_base64 = base64.b64encode(file_data).decode('utf-8')
                    # file_url = file_uploads.upload_excel_and_csv_files("finalproduct", "PtgCms" + env_type, "bulk_documents",
                    #                                                    kit,
                    #                                                    file_name_cleaned, file_base64)
                    file_url = file_uploads.upload_bulk_files("finalproduct", "PtgCms" + env_type, "bulk_documents",
                                                                       kit,
                                                                       file_name_cleaned, file_base64)
                    fp = db_con.FinalProduct.find_one({'all_attributes.outward_id': po_id})
                    name, ext = os.path.splitext(file_name_cleaned)
                    matched = False
                    if fp:
                        kit_key = kit
                        if 'kits' in fp['all_attributes']:
                            fp_kit = fp['all_attributes']['kits'].get(kit_key, {})
                            for product_key, product_value in fp_kit.items():
                                if product_key == 'status':
                                    continue
                                product_id = product_value.get('product_id', '').lower()
                                if product_id == name:
                                    cleaned_name = name.replace('.', '')
                                    if product_value.get('product_status') == 'EOL':
                                        result = db_con.FinalProduct.update_one(
                                            {'all_attributes.outward_id': po_id},
                                            {'$set': {
                                                f"all_attributes.kits.{kit_key}.{product_key}.eol_document": {
                                                    'doc_name': cleaned_name,
                                                    'doc_url': file_url
                                                },
                                                f"all_attributes.kits.{kit_key}.{product_key}.product_status": "Product Ready"
                                            }},
                                            upsert=True
                                        )
                                        matched = True
                                        matched_count += 1
                                        break
                                    elif product_value.get('product_status') == 'Rejected':
                                        rejected_count += 1
                                    elif product_value.get('product_status') == 'Product Rejected':
                                        product_rejected_count += 1
                                    else:
                                        other_count +=1
                    if not matched:
                        fp_kit = fp['all_attributes']['kits'].get(kit_key, {})
                        for product_key, product_value in fp_kit.items():
                            if product_key == 'status':
                                continue
                            product_id = product_value.get('product_id', '').lower()
                            if product_id == name:
                                matched = True
                                break
                        if not matched:
                            mismatched_count += 1
                    elif not fp:
                        mismatched_count += 1
            return {'statusCode': 200,
                    'body': f'Bulk files uploaded and processed successfully. Matched: {matched_count}, Mismatched: {mismatched_count}, Rejected: {rejected_count}, Product Rejected: {product_rejected_count}, Others: {other_count}'}
            #                         result = db_con.FinalProduct.update_one(
            #                             {'all_attributes.outward_id': po_id},
            #                             {'$set': {
            #                                 f"all_attributes.kits.{kit_key}.{product_key}.eol_document": {
            #                                     'doc_name': cleaned_name,
            #                                     'doc_url': file_url
            #                                 },
            #                                 f"all_attributes.kits.{kit_key}.{product_key}.product_status": "Product Ready"
            #                             }},
            #                             upsert=True
            #                         )
            #                         matched = True
            #                         matched_count += 1
            #                         break
            #         if not matched:
            #             mismatched_count += 1
            # return {'statusCode': 200,
            #         'body': f'Bulk files uploaded and processed successfully. Matched: {matched_count}, Mismatched: {mismatched_count}'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': f'Bad Request (check data): {err} (file: {f_name}, line: {line_no})'}



    
    def cmsBoardsBoxBuildingStatusUpdate(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            outward_id = data["outward_id"]
            
            # Fetch board data
            boards_data = list(
                db_con.Boards.find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1})
            )

            # Fetch box building data
            boxbuilding_data = list(
                db_con.BoxBuilding.find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1})
            )
            
            if not boards_data or not boxbuilding_data:
                return {"message": "No data found for the given outward_id"}

            # Extract and update attributes from boards_data
            for board in boards_data:
                all_attributes = board.get('all_attributes', {})
                boards = all_attributes.get('boards', {})
                
                for kit_key, kit_data in boards.items():
                    if isinstance(kit_data, dict):
                        for board_id, board_details in kit_data.items():
                            if isinstance(board_details, dict):
                                pcba_id = board_details.get('pcba_id')
                                if pcba_id:
                                    # Check if the board with pcba_id exists in BoxBuilding before updating
                                    existing_board = db_con.BoxBuilding.find_one(
                                        {"all_attributes.outward_id": outward_id, f"all_attributes.boards.{kit_key}.{board_id}.pcba_id": pcba_id},
                                        {"_id": 1}
                                    )
                                    
                                    if existing_board:
                                        # Create the update dictionary
                                        update_dict = {}
                                        for key, value in board_details.items():
                                            update_dict[f"all_attributes.boards.{kit_key}.{board_id}.{key}"] = value

                                        # Update box building data
                                        db_con.BoxBuilding.update_many(
                                            {"all_attributes.outward_id": outward_id, f"all_attributes.boards.{kit_key}.{board_id}.pcba_id": pcba_id},
                                            {"$set": update_dict}
                                        )

            # Fetch updated box building data to return
            updated_boxbuilding_data = list(
                db_con.BoxBuilding.find({"all_attributes.outward_id": outward_id}, {"_id": 0, "all_attributes": 1})
            )

            # return updated_boxbuilding_data
            return {"statusCode": 200, "body":"Success"}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}
