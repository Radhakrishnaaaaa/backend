import json
from datetime import datetime, timedelta
import base64
from db_connection import db_connection_manage
import sys
import os
import re
import hashlib
import string
import random
import shutil
from cms_utils import file_uploads

fiup = file_uploads()

conct = db_connection_manage()


def check_date_format(value):
    try:
        date_format = "%d/%m/%Y"
        datetime.strptime(value, date_format)
        # #print(datetime.strptime(value, date_format))
    except ValueError:
        return False
    return True


def count_parts_and_documents_in_purchase_orders(response):
    part_count_dict = {}
    document_count_dict = {}
    for purchase_order in response:
        po_id = purchase_order.get("pk_id")
        parts = purchase_order.get("all_attributes", {}).get("parts", {})
        documents = purchase_order.get("all_attributes", {}).get("documents", {})
        part_count = len(parts)
        document_count = len(documents)
        part_count_dict[po_id] = part_count
        document_count_dict[po_id] = document_count
    return part_count_dict, document_count_dict


class inventory_operations():

    # def CmsInventoryCreateComponent(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         sk_timeStamp = (datetime.now()).isoformat()
    #         ctgr_name = data["ctgr_name"]
    #         mfr_prt_num = data["mfr_prt_num"].strip()
    #         data_sheet = data['data_sheet']
    #         ptg_prt_num = data['ptg_prt_num'].strip()
    #         s3_bucket_name = "cms-image-data"
    #         department = data["department"].title()
    #         db = list(db_con.Category.find({"all_attributes.ctgr_name": ctgr_name}))
    #         # print(db)
    #         if not db:
    #             conct.close_connection(client)
    #             return {'statusCode': 401, 'body': f"Category name {ctgr_name} does not exist"}
    #         data = {key.strip().lower().replace(' ', '_'): value for key, value in data.items()}
    #         category_id = db[0]['all_attributes']['ctgr_id']
    #         metadata_id = category_id.replace("CTID", "MDID")
    #         db = list(db_con.Inventory.find({}))
    #         component_ids = []
    #         component_id = '00001'
    #         if db:
    #             for i in db:
    #                 component_ids.append(i["all_attributes"]["cmpt_id"].split("_")[-1])
    #             component_ids.sort(reverse=True)
    #             component_id = str(((5 - len(str(int(component_ids[0]) + 1)))) * "0") + str(int(component_ids[0]) + 1)
    #         db1 = list(db_con.Metadata.find({"pk_id": metadata_id}))
    #         file_type = "pdf"
    #         upload_data_sheet = ''
    #         if data_sheet:
    #             upload_data_sheet = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}", department,
    #                                                          component_id, f"{component_id}file.{file_type}", data_sheet)
    #             # print("data_sheet_path",upload_data_sheet)
    #         upload_image = ''
    #         if upload_data_sheet or data_sheet == "":  # changed
    #             image_type = data['image_type']
    #             img = data['image']
    #             upload_image = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}", department,
    #                                                     component_id, f"{component_id}image.{image_type}", img)
    #             if upload_image or img == '':  # changed
    #                 metadata_attributes = db1[0]['all_attributes']
    #                 metadata_attributes = {value.lower().strip().replace(" ", "_"): key for key, value in
    #                                        metadata_attributes.items()}
    #                 if department == "Electronic":
    #                     sub_category_value = ''
    #                     for i in db1[0]["sub_categories"].keys():
    #                         if db1[0]["sub_categories"][i] == data["sub_category"]:
    #                             sub_category_value = i
    #                     if sub_category_value:
    #                         all_attributes = {
    #                             "cmpt_id": "CMPID" + "_" + component_id.strip(),
    #                             "ctgr_id": category_id.strip(),
    #                             "ctgr_name": ctgr_name,
    #                             "ptg_prt_num": ptg_prt_num.strip(),
    #                             "mfr": data["manufacturer"].strip(),
    #                             "mfr_prt_num": mfr_prt_num.strip(),
    #                             "img_type": image_type,
    #                             "prt_img": str(upload_image),
    #                             "data_sheet": str(upload_data_sheet),
    #                             "sub_ctgr": sub_category_value.strip(),
    #                             "rohs": data["rohs"].strip(),
    #                             "mounting_type": data["mounting_type"].strip(),
    #                             "foot_print": data["foot_print"].strip(),
    #                             "eol_date": data.get("eol_date", ""),
    #                             "rpl_prt_num": data["rpl_prt_num"].strip(),
    #                             "strg_rcmd": data["strg_rcmd"].strip(),
    #                             "hsn_code": data["hsn_code"].strip(),
    #                             "life_cycle": data["life_cycle"].strip(),
    #                             "qty": data["qty"].strip(),
    #                             "description": data["description"].strip()
    #                         }
    #                     else:
    #                         conct.close_connection(client)
    #                         return {"statusCode": 400,
    #                                 "body": f"Given subcategory {sub_category_value} does not belong to category {ctgr_name}"}
    #                 else:
    #                     all_attributes = {
    #                         "cmpt_id": "CMPID" + "_" + component_id.strip(),
    #                         "ctgr_id": category_id.strip(),
    #                         "ctgr_name": ctgr_name,
    #                         "prdt_name": data["prdt_name"],
    #                         "mfr_prt_num": mfr_prt_num,
    #                         "ptg_prt_num": ptg_prt_num.strip(),
    #                         "material": data["material"].strip(),
    #                         "img_type": image_type,
    #                         "dwrng": str(upload_image),
    #                         "qty": data["qty"].strip(),
    #                         "data_sheet": str(upload_data_sheet),
    #                         "mold_required": data["mold_required"].strip(),
    #                         "technical_details": data["technical_details"].strip(),
    #                         "description": data["description"].strip()
    #                     }
    #                 exclude_attributes = ['image', 'part_description', "sub_category", "env_type", "mfr_prt_number",
    #                                       "prt_num", "image_type", "ptg_part_number", "sub_category"]
    #                 for i in data:
    #                     if i not in all_attributes and i not in exclude_attributes:
    #                         if i.lower() in metadata_attributes:
    #                             z = {metadata_attributes[i.lower().strip().replace(" ", "_")]: data[i].strip()}
    #                         else:
    #                             z = {i: data[i].strip()}
    #                         all_attributes.update(z)
    #                 if department == "Electronic":
    #                     for item in db:
    #                         if item["all_attributes"]["mfr_prt_num"] == mfr_prt_num and item["all_attributes"]["mfr"] == \
    #                                 data['manufacturer']:
    #                             conct.close_connection(client)
    #                             return {'statusCode': 400, 'body': f"Manufacturing number {mfr_prt_num} already exists"}
    #                 else:
    #                     for item in db:
    #                         if item["all_attributes"]["mfr_prt_num"] == mfr_prt_num:
    #                             conct.close_connection(client)
    #                             return {'statusCode': 400, 'body': f"Manufacturing number {mfr_prt_num} already exists"}
    #                 item = {
    #                     "pk_id": "CMPID" + "_" + component_id,
    #                     "sk_timeStamp": sk_timeStamp,
    #                     "all_attributes": all_attributes,
    #                     "gsipk_table": "Inventory",
    #                     "gsipk_id": department,
    #                     "lsi_key": ptg_prt_num
    #                 }
    #                 if department == "Electronic":
    #                     item["gsisk_id"] = data["sub_category"].strip()
    #                 else:
    #                     item["gsisk_id"] = "--"
    #                 try:
    #                     db_con.Inventory.insert_one(item)

    #                     response = {'statusCode': 200, 'body': f"New component added in {ctgr_name} category successfully"}
    #                 except Exception as e:

    #                     response = {'statusCode': 500, 'body': 'Error saving item: ' + str(e)}
    #                 conct.close_connection(client)
    #                 return response
    #             else:
    #                 conct.close_connection(client)
    #                 return {"statusCode": 400, "body": f"Failed while uploading Image for component"}
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 400, "body": f"Failed while uploading datasheet for component"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400,'body': 'Internal server error'}



    def CmsInventoryCreateComponent(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()
            ctgr_name = data["ctgr_name"]
            mfr_prt_num = data["mfr_prt_num"].strip()
            data_sheet = data['data_sheet']
            ptg_prt_num = data['ptg_prt_num'].strip()
            s3_bucket_name = "cms-image-data"
            department = data["department"].title()
            db = list(db_con.Category.find({"all_attributes.ctgr_name": ctgr_name}))
            # print(db)
            if not db:
                conct.close_connection(client)
                return {'statusCode': 401, 'body': f"Category name {ctgr_name} does not exist"}
            data = {key.strip().lower().replace(' ', '_'): value for key, value in data.items()}
            category_id = db[0]['all_attributes']['ctgr_id']
            metadata_id = category_id.replace("CTID", "MDID")
            db = list(db_con.Inventory.find({}))
            component_ids = []
            component_id = '00001'
            if db:
                for i in db:
                    component_ids.append(i["all_attributes"]["cmpt_id"].split("_")[-1])
                component_ids.sort(reverse=True)
                component_id = str(((5 - len(str(int(component_ids[0]) + 1)))) * "0") + str(int(component_ids[0]) + 1)
            db1 = list(db_con.Metadata.find({"pk_id": metadata_id}))
            file_type = "pdf"
            upload_data_sheet = ''
            if data_sheet:
                upload_data_sheet = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}", department,
                                                             component_id, f"{component_id}file.{file_type}", data_sheet)
                print("data_sheet_path",upload_data_sheet)
            upload_image = ''
            if upload_data_sheet or data_sheet == "":  # changed
                image_type = data['image_type']
                img = data['image']
                upload_image = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}", department,
                                                        component_id, f"{component_id}image.{image_type}", img)
                if upload_image or img == '':  # changed
                    metadata_attributes = db1[0]['all_attributes']
                    metadata_attributes = {value.lower().strip().replace(" ", "_"): key for key, value in
                                           metadata_attributes.items()}
                    if department == "Electronic":
                        sub_category_value = ''
                        for i in db1[0]["sub_categories"].keys():
                            if db1[0]["sub_categories"][i] == data["sub_category"]:
                                sub_category_value = i
                        if sub_category_value:
                            all_attributes = {
                                "cmpt_id": "CMPID" + "_" + component_id.strip(),
                                "ctgr_id": category_id.strip(),
                                "ctgr_name": ctgr_name,
                                "ptg_prt_num": ptg_prt_num.strip(),
                                "mfr": data["manufacturer"].strip(),
                                "mfr_prt_num": mfr_prt_num.strip(),
                                "img_type": image_type,
                                "prt_img": str(upload_image),
                                "data_sheet": str(upload_data_sheet),
                                "sub_ctgr": sub_category_value.strip(),
                                "rohs": data["rohs"].strip(),
                                "mounting_type": data["mounting_type"].strip(),
                                "foot_print": data["foot_print"].strip(),
                                "eol_date": data.get("eol_date", ""),
                                "rpl_prt_num": data["rpl_prt_num"].strip(),
                                "strg_rcmd": data["strg_rcmd"].strip(),
                                "hsn_code": data["hsn_code"].strip(),
                                "life_cycle": data["life_cycle"].strip(),
                                "qty": data["qty"].strip(),
                                "description": data["description"].strip()
                            }
                        else:
                            conct.close_connection(client)
                            return {"statusCode": 400,
                                    "body": f"Given subcategory {sub_category_value} does not belong to category {ctgr_name}"}
                    else:
                        all_attributes = {
                            "cmpt_id": "CMPID" + "_" + component_id.strip(),
                            "ctgr_id": category_id.strip(),
                            "ctgr_name": ctgr_name,
                            "prdt_name": data["prdt_name"],
                            "mfr_prt_num": mfr_prt_num,
                            "ptg_prt_num": ptg_prt_num.strip(),
                            "material": data["material"].strip(),
                            "hsn_code": data["hsn_code"].strip(),
                            "img_type": image_type,
                            "dwrng": str(upload_image),
                            "qty": data["qty"].strip(),
                            "data_sheet": str(upload_data_sheet),
                            "mold_required": data["mold_required"].strip(),
                            "technical_details": data["technical_details"].strip(),
                            "description": data["description"].strip()
                        }
                    exclude_attributes = ['image', 'part_description', "sub_category", "env_type", "mfr_prt_number",
                                          "prt_num", "image_type", "ptg_part_number", "sub_category"]
                    for i in data:
                        if i not in all_attributes and i not in exclude_attributes:
                            if i.lower() in metadata_attributes:
                                z = {metadata_attributes[i.lower().strip().replace(" ", "_")]: data[i].strip()}
                            else:
                                z = {i: data[i].strip()}
                            all_attributes.update(z)
                    if department == "Electronic":
                        for item in db:
                            if item["all_attributes"]["mfr_prt_num"] == mfr_prt_num and item["all_attributes"]["mfr"] == \
                                    data['manufacturer']:
                                conct.close_connection(client)
                                return {'statusCode': 400, 'body': f"Manufacturing number {mfr_prt_num} already exists"}
                    else:
                        for item in db:
                            if item["all_attributes"]["mfr_prt_num"] == mfr_prt_num:
                                conct.close_connection(client)
                                return {'statusCode': 400, 'body': f"Manufacturing number {mfr_prt_num} already exists"}
                    item = {
                        "pk_id": "CMPID" + "_" + component_id,
                        "sk_timeStamp": sk_timeStamp,
                        "all_attributes": all_attributes,
                        "gsipk_table": "Inventory",
                        "gsipk_id": department,
                        "lsi_key": ptg_prt_num
                    }
                    if department == "Electronic":
                        item["gsisk_id"] = data["sub_category"].strip()
                    else:
                        item["gsisk_id"] = "--"
                    try:
                        db_con.Inventory.insert_one(item)

                        response = {'statusCode': 200, 'body': f"New component added in {ctgr_name} category successfully"}
                    except Exception as e:

                        response = {'statusCode': 500, 'body': 'Error saving item: ' + str(e)}
                    conct.close_connection(client)
                    return response
                else:
                    conct.close_connection(client)
                    return {"statusCode": 400, "body": f"Failed while uploading Image for component"}
            else:
                conct.close_connection(client)
                return {"statusCode": 400, "body": f"Failed while uploading datasheet for component"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Internal server error'}

    def cmsInventoryGetAllComponentsForCategory(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            category_name = data["category_name"]
            department = data["department"]
            category_id = data['category_id']
            db = list(db_con.Inventory.find({"gsipk_id": department, "all_attributes.ctgr_id": category_id}))
            # #print(db)
            lst = []
            db = [i["all_attributes"] for i in db]
            if department == "Electronic":
                sub_cats = list(
                    db_con.Metadata.find({"gsisk_id": category_name, "gsipk_id": "Electronic"}, {"sub_categories": 1}))
                sub_cats = {key: value for key, value in sub_cats[0]['sub_categories'].items()}
                for i in db:
                    i["sub_ctgr"] = sub_cats[i["sub_ctgr"]]
                    dt = {k: v for k, v in i.items()}
                    dt['ctgr_name'] = category_name
                    lst.append(dt)
            else:
                for i in db:
                    dt = {k: v for k, v in i.items()}
                    lst.append(dt)
            lst = sorted(lst, key=lambda x: x['cmpt_id'], reverse=True)
            conct.close_connection(client)
            return {"statusCode": 200, "body": lst}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    # def CmsInventoryGetAllData(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         pattern = r"attribute\d"
    #         data = {key.strip().lower().replace(' ', '_'): value for key, value in data.items()}
    #         env_type = data["env_type"]
    #         component_id = data["cmpt_id"]
    #         department = data["department"]
    #         ctgr_id = list(db_con.Inventory.find({"pk_id": component_id}))
    #         # #print(ctgr_id)
    #         ctgr_id = ctgr_id[0]['all_attributes']['ctgr_id']
    #         category_name = data["ctgr_name"]
    #         category_attributes = list(db_con.Metadata.find({"pk_id": ctgr_id.replace("CTID", "MDID")}))
    #         product_attributes = category_attributes[0]['all_attributes']
    #         ctgr_name = category_attributes[0]['gsisk_id']
    #         product_attributes = {key: value for key, value in product_attributes.items()}
    #         if category_name and component_id:
    #             result = list(db_con.Inventory.find({"pk_id": component_id, "gsipk_id": department}))
    #             if department == "Electronic":
    #                 if not result:
    #                     conct.close_connection(client)
    #                     return {"statusCode": 404, "body": "No data found", }
    #                 result = result[0]
    #                 # print(result)
    #                 sub_category = result["all_attributes"]["sub_ctgr"]
    #                 sub_category = category_attributes[0]['sub_categories'][sub_category]
    #                 if 'prt_img' in result['all_attributes']:
    #                     # if os.path.isfile(result["all_attributes"]["prt_img"]):
    #                     # print(True)
    #                     var = file_uploads.get_file_single_image(result["all_attributes"]["prt_img"])
    #                     # print("var",var,result["all_attributes"]["prt_img"])
    #                 new_result = {
    #                     "ctgr_name": ctgr_name,
    #                     "cmpt_id": component_id,
    #                     "data_sheet": file_uploads.get_file_single_image(
    #                         result["all_attributes"]["data_sheet"]) if 'data_sheet' in result['all_attributes'] else '',
    #                     "prt_img": file_uploads.get_file_single_image(
    #                         result["all_attributes"]["prt_img"]) if 'prt_img' in result['all_attributes'] else '',
    #                     "mounting_type": result["all_attributes"].get("mounting_type", ''),
    #                     "ptg_prt_num": result["all_attributes"].get("ptg_prt_num", ''),
    #                     "life_cycle": result["all_attributes"].get("life_cycle", ''),
    #                     "description": result["all_attributes"].get("description", ''),
    #                     "qty": result["all_attributes"].get("qty", ''),
    #                     "foot_print": result["all_attributes"].get("foot_print", ''),
    #                     "department": result.get("gsipk_id", ''),
    #                     "ctgr_id": result["all_attributes"].get("ctgr_id", ''),
    #                     "mfr_prt_num": result["all_attributes"].get("mfr_prt_num", ''),
    #                     "hsn_code": result["all_attributes"].get("hsn_code", ''),
    #                     "rohs": result["all_attributes"].get("rohs", ''),
    #                     "rpl_prt_num": result["all_attributes"].get("rpl_prt_num", ''),
    #                     "eol_date": result["all_attributes"].get("eol_date", ''),
    #                     "mfr": result["all_attributes"].get("mfr", ''),
    #                     "prt_image_name": result["all_attributes"].get("prt_image_name", ''),
    #                     "data_sheet_name": result["all_attributes"].get("data_sheet_name", ''),
    #                     "sub_ctgr": sub_category,
    #                     "strg_rcmd": result["all_attributes"].get("strg_rcmd", ''),
    #                     "opt_tem": result["all_attributes"].get("opt_tem", "-"),
    #                     "value": result["all_attributes"].get("value", "-")
    #                 }
    #                 attributes = {product_attributes[key]: result["all_attributes"][key] for key in
    #                               result["all_attributes"].keys() if key in product_attributes.keys()}
    #                 additional_attributes = {key: result["all_attributes"][key]
    #                                          for key in result["all_attributes"].keys()
    #                                          if key not in ["ctgr_name", "mfr_prt_num", "file_type", "img_type",
    #                                                         "prt_image_name", "data_sheet_name", "part_image", "rohs",
    #                                                         "sub_ctgr", "data_sheet", "qty", "category_name",
    #                                                         "eol_date", "rpl_prt_num", "manufacturer", "mfr", "image",
    #                                                         "hsn_code", "ptg_prt_num", "quantity", "sub_category",
    #                                                         "foot_print", "ctgr_id", "department", "cmpt_id",
    #                                                         "life_cycle", "image_type", "description", "prt_img",
    #                                                         "mounting_type", "strg_rcmd", "ptg_part_number", "package",
    #                                                         "manufacturer", "categoryId", "opt_tem",
    #                                                         "value"] and key not in product_attributes.keys() and not re.match(
    #                         pattern, key)}
    #                 attributes.update(additional_attributes)
    #                 component_id = result['all_attributes']['cmpt_id']
    #                 new_result["product_attributes"] = attributes
    #             else:
    #                 result = result[0]
    #                 new_result = {
    #                     "ctgr_name": ctgr_name,
    #                     "cmpt_id": component_id,
    #                     "data_sheet": file_uploads.get_file_single_image(
    #                         result["all_attributes"]["data_sheet"]) if 'data_sheet' in result['all_attributes'] else '',
    #                     "prt_img": file_uploads.get_file_single_image(result["all_attributes"]["dwrng"]) if 'dwrng' in
    #                                                                                                         result[
    #                                                                                                             'all_attributes'] else '',
    #                     # "data_sheet":result["all_attributes"].get("data_sheet", ''),
    #                     # "prt_img":result["all_attributes"].get("dwrng", ''),
    #                     "prdt_name": result["all_attributes"].get("prdt_name", ''),
    #                     "ptg_prt_num": result["all_attributes"].get("ptg_prt_num", ''),
    #                     "material": result["all_attributes"].get("material", ''),
    #                     "qty": result["all_attributes"].get("qty", ''),
    #                     "mold_required": result["all_attributes"].get("mold_required", ''),
    #                     "technical_details": result["all_attributes"].get("technical_details", ''),
    #                     "description": result["all_attributes"].get("description", ''),
    #                     "ctgr_id": result["all_attributes"].get("ctgr_id", ''),
    #                     "mfr_prt_num": result["all_attributes"].get("mfr_prt_num", ''),
    #                     "prt_image_name": result["all_attributes"].get("prt_image_name", ''),
    #                     "data_sheet_name": result["all_attributes"].get("data_sheet_name", ''),
    #                     "department": result.get("gsipk_id", ''),

    #                 }
    #                 attributes = {product_attributes[key]: result["all_attributes"][key] for key in
    #                               result["all_attributes"].keys() if key in product_attributes.keys()}
    #                 additional_attributes = {key: result["all_attributes"][key]
    #                                          for key in result["all_attributes"].keys()
    #                                          if key not in ["ctgr_name", "cmpt_id", "dwrng", "mfr_prt_num", "ctgr_id",
    #                                                         "prt_image_name", "data_sheet_name", "department",
    #                                                         "img_type", "qty", "description", "technical_details",
    #                                                         "mold_required", "prdt_name", "ptg_prt_num", "material",
    #                                                         "module",
    #                                                         "data_sheet", ] and key not in product_attributes.keys() and not re.match(
    #                         pattern, key)}
    #                 attributes.update(additional_attributes)
    #                 component_id = result['all_attributes']['cmpt_id']
    #                 new_result["product_attributes"] = attributes
    #             sorted_product_attributes = {
    #                 key: new_result["product_attributes"][key]
    #                 for key in sorted(new_result["product_attributes"].keys())
    #             }
    #             new_result["product_attributes"] = sorted_product_attributes
    #             conct.close_connection(client)
    #             return {"statusCode": 200, "body": new_result}
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 404, "body": "No data found for the given category details", }
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Internal server error'}

    def CmsInventoryGetAllData(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            pattern = r"attribute\d"
            data = {key.strip().lower().replace(' ', '_'): value for key, value in data.items()}
            env_type = data["env_type"]
            component_id = data["cmpt_id"]
            department = data["department"]
            ctgr_id = list(db_con.Inventory.find({"pk_id": component_id}))
            # #print(ctgr_id)
            ctgr_id = ctgr_id[0]['all_attributes']['ctgr_id']
            category_name = data["ctgr_name"]
            category_attributes = list(db_con.Metadata.find({"pk_id": ctgr_id.replace("CTID", "MDID")}))
            product_attributes = category_attributes[0]['all_attributes']
            ctgr_name = category_attributes[0]['gsisk_id']
            product_attributes = {key: value for key, value in product_attributes.items()}
            if category_name and component_id:
                result = list(db_con.Inventory.find({"pk_id": component_id, "gsipk_id": department}))
                if department == "Electronic":
                    if not result:
                        conct.close_connection(client)
                        return {"statusCode": 404, "body": "No data found", }
                    result = result[0]
                    # print(result)
                    sub_category = result["all_attributes"]["sub_ctgr"]
                    sub_category = category_attributes[0]['sub_categories'][sub_category]
                    if 'prt_img' in result['all_attributes']:
                        # if os.path.isfile(result["all_attributes"]["prt_img"]):
                        # print(True)
                        var = file_uploads.get_file_single_image(result["all_attributes"]["prt_img"])
                        # print("var",var,result["all_attributes"]["prt_img"])
                    new_result = {
                        "ctgr_name": ctgr_name,
                        "cmpt_id": component_id,
                        "data_sheet": file_uploads.get_file_single_image(
                            result["all_attributes"]["data_sheet"]) if 'data_sheet' in result['all_attributes'] else '',
                        "prt_img": file_uploads.get_file_single_image(
                            result["all_attributes"]["prt_img"]) if 'prt_img' in result['all_attributes'] else '',
                        "mounting_type": result["all_attributes"].get("mounting_type", ''),
                        "ptg_prt_num": result["all_attributes"].get("ptg_prt_num", ''),
                        "life_cycle": result["all_attributes"].get("life_cycle", ''),
                        "description": result["all_attributes"].get("description", ''),
                        "qty": result["all_attributes"].get("qty", ''),
                        "foot_print": result["all_attributes"].get("foot_print", ''),
                        "department": result.get("gsipk_id", ''),
                        "ctgr_id": result["all_attributes"].get("ctgr_id", ''),
                        "mfr_prt_num": result["all_attributes"].get("mfr_prt_num", ''),
                        "hsn_code": result["all_attributes"].get("hsn_code", ''),
                        "rohs": result["all_attributes"].get("rohs", ''),
                        "rpl_prt_num": result["all_attributes"].get("rpl_prt_num", ''),
                        "eol_date": result["all_attributes"].get("eol_date", ''),
                        "mfr": result["all_attributes"].get("mfr", ''),
                        "prt_image_name": result["all_attributes"].get("prt_image_name", ''),
                        "data_sheet_name": result["all_attributes"].get("data_sheet_name", ''),
                        "sub_ctgr": sub_category,
                        "strg_rcmd": result["all_attributes"].get("strg_rcmd", ''),
                        "opt_tem": result["all_attributes"].get("opt_tem", "-"),
                        "value": result["all_attributes"].get("value", "-")
                    }
                    attributes = {product_attributes[key]: result["all_attributes"][key] for key in
                                  result["all_attributes"].keys() if key in product_attributes.keys()}
                    additional_attributes = {key: result["all_attributes"][key]
                                             for key in result["all_attributes"].keys()
                                             if key not in ["ctgr_name", "mfr_prt_num", "file_type", "img_type",
                                                            "prt_image_name", "data_sheet_name", "part_image", "rohs",
                                                            "sub_ctgr", "data_sheet", "qty", "category_name",
                                                            "eol_date", "rpl_prt_num", "manufacturer", "mfr", "image",
                                                             "ptg_prt_num", "quantity", "sub_category","hsn_code",
                                                            "foot_print", "ctgr_id", "department", "cmpt_id",
                                                            "life_cycle", "image_type", "description", "prt_img",
                                                            "mounting_type", "strg_rcmd", "ptg_part_number", "package",
                                                            "manufacturer", "categoryId", "opt_tem",
                                                            "value"] and key not in product_attributes.keys() and not re.match(
                            pattern, key)}
                    print("additional attr",additional_attributes)
                    attributes.update(additional_attributes)
                    component_id = result['all_attributes']['cmpt_id']
                    new_result["product_attributes"] = attributes
                else:
                    result = result[0]
                    new_result = {
                        "ctgr_name": ctgr_name,
                        "cmpt_id": component_id,
                        "data_sheet": file_uploads.get_file_single_image(
                            result["all_attributes"]["data_sheet"]) if 'data_sheet' in result['all_attributes'] else '',
                        "prt_img": file_uploads.get_file_single_image(result["all_attributes"]["dwrng"]) if 'dwrng' in
                                                                                                            result[
                                                                                                                'all_attributes'] else '',
                        # "data_sheet":result["all_attributes"].get("data_sheet", ''),
                        # "prt_img":result["all_attributes"].get("dwrng", ''),
                        "prdt_name": result["all_attributes"].get("prdt_name", ''),
                        "ptg_prt_num": result["all_attributes"].get("ptg_prt_num", ''),
                        "material": result["all_attributes"].get("material", ''),
                        "qty": result["all_attributes"].get("qty", ''),
                        "mold_required": result["all_attributes"].get("mold_required", ''),
                        "technical_details": result["all_attributes"].get("technical_details", ''),
                        "description": result["all_attributes"].get("description", ''),
                        "hsn_code": result["all_attributes"].get("hsn_code", ''),
                        "ctgr_id": result["all_attributes"].get("ctgr_id", ''),
                        "mfr_prt_num": result["all_attributes"].get("mfr_prt_num", ''),
                        "prt_image_name": result["all_attributes"].get("prt_image_name", ''),
                        "data_sheet_name": result["all_attributes"].get("data_sheet_name", ''),
                        "department": result.get("gsipk_id", ''),

                    }
                    attributes = {product_attributes[key]: result["all_attributes"][key] for key in
                                  result["all_attributes"].keys() if key in product_attributes.keys()}
                    additional_attributes = {key: result["all_attributes"][key]
                                             for key in result["all_attributes"].keys()
                                             if key not in ["ctgr_name", "cmpt_id", "dwrng", "mfr_prt_num", "ctgr_id",
                                                            "prt_image_name", "data_sheet_name", "department",
                                                            "img_type", "qty", "description", "technical_details",
                                                            "mold_required", "prdt_name", "ptg_prt_num", "material",
                                                            "module",'hsn_code'
                                                            "data_sheet", ] and key not in product_attributes.keys() and not re.match(
                            pattern, key)}
                    additional_attributes.pop('hsn_code', None)
                    attributes.update(additional_attributes)
                    component_id = result['all_attributes']['cmpt_id']
                    new_result["product_attributes"] = attributes
                sorted_product_attributes = {
                    key: new_result["product_attributes"][key]
                    for key in sorted(new_result["product_attributes"].keys())
                }
                new_result["product_attributes"] = sorted_product_attributes
                conct.close_connection(client)
                return {"statusCode": 200, "body": new_result}
            else:
                conct.close_connection(client)
                return {"statusCode": 404, "body": "No data found for the given category details", }
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Internal server error'}

#     import json
# import os
# import sys
# from pymongo import MongoClient

#     import json
# import os
# import sys
# from pymongo import MongoClient

    def CmsInventoryEditDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            data = {key.strip().lower().replace(' ', '_'): value for key, value in data.items()}
            
            if data["department"] == "Electronic":
                cmpt_id = data["cmpt_id"]
                dep_type = data["department"]
                cmpt = list(db_con.Inventory.find({"pk_id": cmpt_id, "gsipk_id": dep_type}))

                if not cmpt:
                    return {"statusCode": 400, "body": json.dumps("Component not found")}
                
                file_type = data["file_type"]
                main_dict = {key: value for key, value in data.items()}
                main_dict.pop("env_type")
                main_dict.pop("department")
                main_dict.pop("img_type")
                main_dict.pop("file_type")
                main_dict.pop("sub_ctgr")
                ctgr_id = data['ctgr_id']
                mtdt_id = ctgr_id.replace('CTID', 'MDID')
                metadata = list(db_con.Metadata.find({"pk_id": mtdt_id}))
                
                if not metadata:
                    return {"statusCode": 400, "body": json.dumps("Metadata not found")}
                
                metadata = {k.lower().strip().replace(' ', '_'): v for v, k in metadata[0]['all_attributes'].items()}
                
                if data.get('data_sheet'):
                    upload_data_sheet = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}", "Electronic",
                                                                data['cmpt_id'].replace("CMPID_", ""),
                                                                f"{data['cmpt_id'].replace('CMPID_', '')}file.pdf",
                                                                data['data_sheet'])
                    main_dict["data_sheet"] = upload_data_sheet
                    main_dict['data_sheet_name'] = data['data_sheet_name']
                else:
                    if cmpt[0]['all_attributes'].get('data_sheet'):
                        filename = f"cms-image-data/PtgCms{data['env_type']}/componentdata/{dep_type}/{data['cmpt_id'].replace('CMPID_', '')}/{data['cmpt_id'].replace('CMPID_', '')}file.pdf"
                        if os.path.isfile(filename):
                            os.remove(filename)
                    main_dict["data_sheet"] = ''
                    main_dict['data_sheet_name'] = ''
                
                if data.get('prt_img'):
                    upload_image = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}", "Electronic",
                                                            data['cmpt_id'].replace("CMPID_", ""),
                                                            f"{data['cmpt_id'].replace('CMPID_', '')}image.jpg",
                                                            data['prt_img'])
                    main_dict['prt_img'] = upload_image
                    main_dict['prt_image_name'] = data['prt_image_name']
                else:
                    if cmpt[0]['all_attributes'].get('prt_img'):
                        imagename = f"cms-image-data/PtgCms{data['env_type']}/componentdata/{dep_type}/{data['cmpt_id'].replace('CMPID_', '')}/{data['cmpt_id'].replace('CMPID_', '')}image.{cmpt[0]['all_attributes']['img_type']}"
                        if os.path.isfile(imagename):
                            os.remove(imagename)
                    main_dict["prt_img"] = ''
                    main_dict['prt_image_name'] = ''
                
                cmpt_db = {k: v for k, v in cmpt[0]['all_attributes'].items()}
                data_db = {(metadata[key.lower().strip().replace(' ', '_')] if key.lower().strip().replace(' ',
                                                                                                        '_') in metadata else key): value
                        for key, value in main_dict.items()}
                key_value_pairs = {**cmpt_db, **data_db}
                result = db_con.Inventory.update_one(
                    {"all_attributes.cmpt_id": cmpt_id},
                    {"$set": {"all_attributes": key_value_pairs}}
                )
                conct.close_connection(client)
                return {"statusCode": 200, "body": json.dumps("Electric component details changed successfully")}
            
            elif data["department"] == "Mechanic":
                cmpt_id = data["cmpt_id"]
                dep_type = data["department"]
                cmpt = list(db_con.Inventory.find({"pk_id": cmpt_id, "gsipk_id": dep_type}))
                
                if not cmpt:
                    return {"statusCode": 400, "body": json.dumps("Component not found")}
                
                file_type = data["file_type"]
                ctgr_id = data['ctgr_id']
                mtdt_id = ctgr_id.replace('CTID', 'MDID')
                main_dict = {key: value for key, value in data.items()}
                metadata = list(db_con.Metadata.find({"pk_id": mtdt_id}))
                
                if not metadata:
                    return {"statusCode": 400, "body": json.dumps("Metadata not found")}
                
                metadata = {k.strip().replace(' ', '_').lower(): v for v, k in metadata[0]['all_attributes'].items()}
                main_dict.pop("env_type")
                main_dict.pop("department")
                main_dict.pop("file_type")
                main_dict["data_sheet"] = ''
                main_dict['dwrng'] = ''
                main_dict['prt_image_name'] = ''
                main_dict['data_sheet_name'] = ''
                
                if data.get('data_sheet'):
                    main_dict['data_sheet'] = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}",
                                                                    dep_type, data['cmpt_id'].replace("CMPID_", ""),
                                                                    f"{data['cmpt_id'].replace('CMPID_', '')}file.pdf",
                                                                    data['data_sheet'])
                    main_dict['data_sheet_name'] = data['data_sheet_name']
                else:
                    if cmpt[0]['all_attributes'].get('data_sheet'):
                        filename = cmpt[0]['all_attributes']['data_sheet']
                        if os.path.isfile(filename):
                            os.remove(filename)
                    main_dict["data_sheet"] = ''
                    main_dict['data_sheet_name'] = ''
                
                if data.get('prt_img'):
                    main_dict['dwrng'] = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}", dep_type,
                                                                cmpt_id, f"{cmpt_id}image.jpg", data['prt_img'])
                    main_dict['prt_image_name'] = data['prt_image_name']
                else:
                    if cmpt[0]['all_attributes'].get('dwrng'):
                        imagename = cmpt[0]['all_attributes']['dwrng']
                        if os.path.isfile(imagename):
                            os.remove(imagename)
                    main_dict["dwrng"] = ''
                    main_dict['prt_image_name'] = ''
                
                main_dict.pop("img_type")
                main_dict.pop("prt_img")
                cmpt_db = {k: str(v) for k, v in cmpt[0]['all_attributes'].items()}
                data_db = {(metadata[key.lower().strip().replace(' ', '_')] if key.lower().strip().replace(' ',
                                                                                                        '_') in metadata else key): str(
                    value) for key, value in main_dict.items()}
                key_value_pairs = {**cmpt_db, **data_db}
                result = db_con.Inventory.update_one(
                    {"pk_id": cmpt_id},
                    {"$set": {"all_attributes": key_value_pairs}}
                )
                conct.close_connection(client)
                return {"statusCode": 200, "body": json.dumps("Mechanic category details changed successfully")}
        
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            error_message = f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}"
            print(error_message)
            return {'statusCode': 400, 'body': 'Internal server error'}




    # def CmsInventoryEditDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         data = {key.strip().lower().replace(' ', '_'): value for key, value in data.items()}
    #         if data["department"] == "Electronic":
    #             cmpt_id = data["cmpt_id"]
    #             dep_type = data["department"]
    #             cmpt = list(db_con.Inventory.find({"pk_id": cmpt_id, "gsipk_id": dep_type}))
    #             # return cmpt
    #             file_type = data["file_type"]
    #             main_dict = {key: value for key, value in data.items()}
    #             main_dict.pop("env_type")
    #             main_dict.pop("department")
    #             main_dict.pop("img_type")
    #             main_dict.pop("file_type")
    #             main_dict.pop("sub_ctgr")
    #             ctgr_id = data['ctgr_id']
    #             mtdt_id = ctgr_id.replace('CTID', 'MDID')
    #             metadata = list(db_con.Metadata.find({"pk_id": mtdt_id}))
    #             metadata = {k.lower().strip().replace(' ', '_'): v for v, k in metadata[0]['all_attributes'].items()}
    #             if data['data_sheet']:
    #                 upload_data_sheet = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}", "Electronic",
    #                                                              data['cmpt_id'].replace("CMPID_", ""),
    #                                                              f"{data['cmpt_id'].replace("CMPID_", "")}file.pdf",
    #                                                              data['data_sheet'])
    #                 main_dict["data_sheet"] = upload_data_sheet
    #                 main_dict['data_sheet_name'] = data['data_sheet_name']
    #             else:
    #                 if cmpt[0]['all_attributes']['data_sheet']:
    #                     filename = f"cms-image-data/PtgCms{data['env_type']}/componentdata/{dep_type}/{data['cmpt_id'].replace("CMPID_", "")}/{data['cmpt_id'].replace("CMPID_", "")}file.pdf"
    #                     os.remove(filename)
    #                 main_dict["data_sheet"] = ''
    #                 main_dict['data_sheet_name'] = ''
    #             if data['prt_img']:
    #                 upload_image = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}", "Electronic",
    #                                                         data['cmpt_id'].replace("CMPID_", ""),
    #                                                         f"{data['cmpt_id'].replace("CMPID_", "")}image.jpg",
    #                                                         data['prt_img'])
    #                 main_dict['prt_img'] = upload_image
    #                 main_dict['prt_image_name'] = data['prt_image_name']
    #             else:
    #                 if cmpt[0]['all_attributes']['prt_img']:
    #                     imagename = f"cms-image-data/PtgCms{data['env_type']}/componentdata/{dep_type}/{data['cmpt_id'].replace("CMPID_", "")}/{data['cmpt_id'].replace("CMPID_", "")}image.{cmpt[0]['all_attributes']['img_type']}"
    #                     if os.path.isfile(imagename):
    #                         os.remove(imagename)
    #                 main_dict["prt_img"] = ''
    #                 main_dict['prt_image_name'] = ''
    #             cmpt_db = {k: v for k, v in cmpt[0]['all_attributes'].items()}
    #             data_db = {(metadata[key.lower().strip().replace(' ', '_')] if key.lower().strip().replace(' ',
    #                                                                                                        '_') in metadata else key): value
    #                        for key, value in main_dict.items()}
    #             key_value_pairs = {**cmpt_db, **data_db}
    #             result = db_con.Inventory.update_one(
    #                 {"all_attributes.cmpt_id": cmpt_id},
    #                 {"$set": {"all_attributes": key_value_pairs}}
    #             )
    #             conct.close_connection(client)
    #             return {"statusCode": 200, "body": json.dumps("Electric component details changed successfully")}
    #         elif data["department"] == "Mechanic":
    #             cmpt_id = data["cmpt_id"]
    #             dep_type = data["department"]
    #             cmpt = list(db_con.Inventory.find({"pk_id": cmpt_id, "gsipk_id": dep_type}))
    #             file_type = data["file_type"]
    #             ctgr_id = data['ctgr_id']
    #             mtdt_id = ctgr_id.replace('CTID', 'MDID')
    #             main_dict = {key: value for key, value in data.items()}
    #             metadata = list(db_con.Metadata.find({"pk_id": mtdt_id}))
    #             metadata = {k.strip().replace(' ', '_').lower(): v for v, k in metadata[0]['all_attributes'].items()}
    #             main_dict.pop("env_type")
    #             main_dict.pop("department")
    #             main_dict.pop("file_type")
    #             main_dict["data_sheet"] = ''
    #             main_dict['dwrng'] = ''
    #             main_dict['prt_image_name'] = ''
    #             main_dict['data_sheet_name'] = ''
    #             if data['data_sheet']:
    #                 main_dict['data_sheet'] = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}",
    #                                                                    dep_type, data['cmpt_id'].replace("CMPID_", ""),
    #                                                                    f"{data['cmpt_id'].replace("CMPID_", "")}file.pdf",
    #                                                                    data['data_sheet'])
    #                 # #print(main_dict['data_sheet'])
    #                 main_dict['data_sheet_name'] = data['data_sheet_name']
    #             else:
    #                 if cmpt[0]['all_attributes']['data_sheet']:
    #                     filename = cmpt[0]['all_attributes']['data_sheet']
    #                     os.remove(filename)
    #                 main_dict["data_sheet"] = ''
    #                 main_dict['data_sheet_name'] = ''
    #             if data['prt_img']:
    #                 main_dict['dwrng'] = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}", dep_type,
    #                                                               cmpt_id, f"{cmpt_id}image.jpg", data['prt_img'])
    #                 main_dict['prt_image_name'] = data['prt_image_name']
    #             else:
    #                 if cmpt[0]['all_attributes']['dwrng']:
    #                     imagename = cmpt[0]['all_attributes']['dwrng']
    #                     os.remove(imagename)
    #                 main_dict["dwrng"] = ''
    #                 main_dict['prt_image_name'] = ''
    #             main_dict.pop("img_type")
    #             main_dict.pop("prt_img")
    #             cmpt_db = {k: str(v) for k, v in cmpt[0]['all_attributes'].items()}
    #             data_db = {(metadata[key.lower().strip().replace(' ', '_')] if key.lower().strip().replace(' ',
    #                                                                                                        '_') in metadata else key): str(
    #                 value) for key, value in main_dict.items()}
    #             key_value_pairs = {**cmpt_db, **data_db}
    #             # return key_value_pairs
    #             result = db_con.Inventory.update_one(
    #                 {"pk_id": cmpt_id},
    #                 {"$set": {"all_attributes": key_value_pairs}}
    #             )
    #             conct.close_connection(client)
    #             return {"statusCode": 200, "body": json.dumps("Mechanic category details changed successfully")}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400,'body': 'Internal server error'}

    def CmsInventoryDeleteComponent(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            category = data["cmpt_id"]
            env_type = data["env_type"]
            department = data['type']
            mfr_prt_num = None
            result_list_all = []
            category_items = []
            result_list = []
            for componentId in category:
                results = list(db_con.Inventory.find({"all_attributes.cmpt_id": componentId, "gsipk_id": department}))
                if len(results) > 0:
                    result = results[0]
                    componentId = result["all_attributes"]["cmpt_id"]
                    mfr_prt_num = result["all_attributes"]["mfr_prt_num"]
                    sorted_bom_data = db_con.Bom.find({})
                    sorted_po_data = db_con.PurchaseOrder.find({})
                    vendor_data = db_con.Vendor.find({})
                    result_for_bom = set(
                        componentId for item in sorted_bom_data
                        for part_type in ['E_parts', 'M_parts']
                        for part_no, part in item.get('all_attributes', {}).get(part_type, {}).items()
                        if part.get('cmpt_id') == componentId
                    )
                    result_for_po = set([
                        mfr_prt_num
                        for order in sorted_po_data
                        for part_name, part in order['all_attributes'].get('parts', {}).items()
                        if part.get('mfr_prt_num') == mfr_prt_num
                    ])
                    result_for_vendor = set([
                        mfr_prt_num
                        for order in vendor_data
                        for part_name, part in order['all_attributes'].get('parts', {}).items()
                        if part.get('mfr_prt_num') == mfr_prt_num

                    ])
                    result_list = [result for sublist in [result_for_bom, result_for_po, result_for_vendor] for result in
                                   sublist if result]
                    if result_list:
                        result_list_all.extend(result_list)
                    # If result_list is not present, prepare category_items for deletion
                    if not result_list:
                        category_items.append(componentId)
            if result_list_all:
                conct.close_connection(client)
                return {"statusCode": 409, "body": "Component is present in BOM or Vendor or PurchaseOrder"}
            elif category_items:
                for componentId in category_items:
                    comp_folder = f"cms-image-data/PtgCms{env_type}/componentdata/{department}/{componentId.replace('CMPID_', '')}/"
                    if os.path.isdir(comp_folder):
                        shutil.rmtree(comp_folder)
                    db_con.Inventory.delete_one({"pk_id": componentId})
                conct.close_connection(client)
                return {"statusCode": 200, "body": "Components Deleted Successfully"}
            else:
                conct.close_connection(client)
                return {"statusCode": 404, "body": "No components found"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'There is an AWS Lambda Data Capturing Error'}

    def CmsInventoryUploadCsv(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            category_twi, component_twi = [], []
            null_entries = ['na', '-', '--', 'null', 'nil', 'nill', 'n/a', '']
            sk_timeStamp = (datetime.now()).isoformat()
            if len(data['parts']) > 25:
                return {"statusCode": 400, "body": "Please upload a maximum of 25 parts only"}
            # mandatory_e_columns = ["department", "categoryname", "productname", "manufacturer", "mfrpartnumber",
            #                        "mountingtype", "footprint", "lifecycle", "rohs", "msl"]
            mandatory_e_columns = ["department", "categoryname", "productname", "manufacturer", "mfrpartnumber",
                                   "mountingtype", "lifecycle", "rohs"]
            mandatory_m_columns = ["department", "categoryname", "productname", "mfrpartnumber", "mold_required",
                                   "material"]
            all_columns = ["department", "categoryname", "productname", "manufacturer", "mfrpartnumber", "mountingtype",
                           "footprint", "quantity", "lifecycle", "rohs", "msl", "hsn_code", "description", "eoldate",
                           "replacementpartnumber", "image", "datasheet", "imagetype", "filetype", "technicaldetails",
                           "mold_required", "material"]
            mf_part_ids = [(str(row['mfrPartNumber']) + str(row.get('manufacturer', ''))).strip().lower() for row in
                           data['parts'] if row]
            mfprtids = list(db_con.Inventory.find({},
                                                  {"pk_id": 1, "all_attributes.mfr_prt_num": 1, "all_attributes.mfr": 1,
                                                   "all_attributes.rpl_prt_num": 1, "gsipk_id": 1}))
            mpids = [item['all_attributes']['mfr_prt_num'] for item in mfprtids]
            rpns = [item['all_attributes']['rpl_prt_num'] for item in mfprtids if
                    'rpl_prt_num' in item and item['all_attributes']['rpl_prt_num'] and item['all_attributes'][
                        'rpl_prt_num'] not in null_entries]
            mf_pr_ids = [
                (item['all_attributes']['mfr_prt_num'] + item['all_attributes'].get('mfr', "")).lower() if item[
                                                                                                               'gsipk_id'] == 'Electronic' else
                item['all_attributes']['mfr_prt_num'].lower() for item in mfprtids]
            max_cmptid = max([int(item['pk_id'].replace("CMPID_", "")) for item in mfprtids]) if mfprtids else 0
            if len(set(mf_part_ids)) < len(mf_part_ids):
                return {"statusCode": 409, "body": "Duplicate mfr part number in csv"}
            if any(str(mpid).lower() for mpid in mf_part_ids if str(mpid).lower() in mf_pr_ids):
                return {"statusCode": 409, "body": "Duplicate mfr part number found in db"}
            # return mf_part_ids,mf_pr_ids
            category = list(db_con.Metadata.find({}, {"pk_id": 1, "sub_categories": 1, "gsisk_id": 1, "gsipk_id": 1,
                                                      "all_attributes": 1, "sk_timeStamp": 1}))
            category = {
                (f"E{item['gsisk_id'].lower()}" if item[
                                                       'gsipk_id'] == 'Electronic' else f"M{item['gsisk_id'].lower()}"): (
                    {
                        "ctgr_id": item['pk_id'].replace("MDID", "CTID"),
                        "sub_categories": {
                            str(value).strip().lower(): key for key, value in item['sub_categories'].items()
                        },
                        "attributes": {
                            value.strip().lower(): key for key, value in item['all_attributes'].items()
                        },
                        "max_subcategory": max(
                            [int(key.replace("sub_category", "")) for key in item['sub_categories'].keys()])
                    }
                    if item['gsipk_id'] == 'Electronic'
                    else {"ctgr_id": item['pk_id'].replace("MDID", "CTID"), "ctgr_name": item['gsisk_id'],
                          "attributes": {
                              value.strip().lower(): key for key, value in item['all_attributes'].items()
                          }
                          }
                )

                for item in category
            }
            for inx, part in enumerate(data['parts']):
                cat_str = f"{part['department'].upper()[:1]}{str(part['categoryName']).lower().strip()}"
                if cat_str not in category:
                    return {'statusCode': 400, 'body': f'Category does not exist check row {inx + 1}'}
                image = str(part["image"]) if "http" in str(part["image"]) else ""
                dataSheet = str(part["dataSheet"]) if "http" in str(part["dataSheet"]) else ""
                imageType = str(part['imageType']) if image else ''
                mfrPartNumber = str(part["mfrPartNumber"])
                department = part['department']
                category_name = str(part["categoryName"]).lower()
                category_id = category[cat_str]['ctgr_id']
                metadata_id = category_id.replace("CTID", "MDID")
                digits = string.digits
                letters = string.ascii_uppercase
                random_string = "".join(random.choices(digits + letters, k=3))
                hashed_value = hashlib.sha256(random_string.encode()).hexdigest()
                truncated_hash = hashed_value[:6].upper()
                cmpt_id = "CMPID_" + str(((5 - len(str(max_cmptid + 1)))) * "0") + str(max_cmptid + 1) if len(
                    str(max_cmptid + 1)) < 5 else "CMPID_" + str(max_cmptid + 1)
                upload_image = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}", department,
                                                        cmpt_id.replace("CMPID_", ""),
                                                        f"{cmpt_id.replace("CMPID_", "")}image.jpg", image) if part[
                                                                                                                   'image'] and str(
                    part['image']).lower() not in null_entries else ""
                if upload_image or image in null_entries:
                    upload_data_sheet = file_uploads.upload_file("componentdata", f"PtgCms{data['env_type']}",
                                                                 department, cmpt_id.replace("CMPID_", ""),
                                                                 f"{cmpt_id.replace("CMPID_", "")}file.pdf",
                                                                 part['dataSheet']) if part['dataSheet'] and str(
                        part['dataSheet']).lower() not in null_entries else ""
                    if upload_data_sheet or dataSheet in null_entries:
                        if str(part['department']).lower() == 'mechanic':
                            if any(1 for key in part.keys() if
                                   str(part[key]).lower() in null_entries and key.lower() in mandatory_m_columns):
                                return {'statusCode': 400,
                                        'body': f'please fill the mandatory for the excel upload of components check row {inx + 1} and below'}
                            if part['mold_required'].lower() not in ["notreq", "req"]:
                                return {'statusCode': 400,
                                        'body': f'Please select correct mold required value for components (notreq/req) check row {inx + 1} and below'}
                            cmpt_id = "CMPID_" + str(((5 - len(str(max_cmptid + 1)))) * "0") + str(
                                max_cmptid + 1) if len(str(max_cmptid + 1)) < 5 else "CMPID_" + str(max_cmptid + 1)
                            all_attributes = {
                                "cmpt_id": cmpt_id,
                                "ctgr_id": category_id,
                                "department": str(part['department']).title().strip(),
                                "ctgr_name": str(part['categoryName']).title().strip(),
                                "ptg_prt_num": f"PTG{truncated_hash}",
                                "prdt_name": str(part["productName"]).strip(),
                                "mfr_prt_num": str(part['mfrPartNumber']).strip(),
                                "material": str(part["material"]).strip(),
                                "img_type": str(imageType) if image not in null_entries else '',
                                "dwrng": str(upload_image),
                                "qty": "0",
                                "data_sheet": str(upload_data_sheet),
                                "mold_required": str(part["mold_required"]).strip().lower(),
                                "technical_details": str(part["technicalDetails"]).strip(),
                                "description": str(part["description"]).strip()
                            }
                        elif str(part['department']).lower() == 'electronic':
                            eol_date = str(part['eolDate']).replace("-", '/')
                            if part['replacementPartNumber'] in rpns:
                                return {'statusCode': 400,
                                        'body': f'replacement part already in use for another component check row {inx + 1} and below'}
                            if part['mountingType'] not in ["SMD", "TH", "Others"]:
                                return {'statusCode': 400,
                                        'body': f'Please select correct mounting type for components (SMD/TH/Others) check row {inx + 1} and below'}
                            if part['lifeCycle'] != 'Active':
                                if str(part['replacementPartNumber']).lower() not in null_entries or part[
                                    'replacementPartNumber'] in mpids:
                                    pass
                                else:
                                    if any(1 for item in data['parts'] if
                                           part['replacementPartNumber'] == item['mfrPartNumber']) or part[
                                        'mfrPartNumber'] == part['replacementPartNumber']:
                                        return {'statusCode': 400,
                                                'body': f'please give valid replacement part numbers check row {inx + 1} and below'}
                                if any(1 for key in part.keys() if
                                       part[key] in null_entries and key in mandatory_e_columns):
                                    return {'statusCode': 400,
                                            'body': f'all fields are mandatory for the excel upload of components check row {inx + 1} and below'}
                                # if str(part['eolDate']).lower() not in null_entries and not check_date_format(eol_date):
                                if str(part['eolDate']).lower() not in null_entries and str(part['eolDate']).lower() == 'na' and not check_date_format(eol_date):
                                    return {'statusCode': 400,
                                            'body': f"EOL date should be in the format DD/MM/YYYY or DD-MM-YYYY check row {inx + 1} and below"}
                            else:
                                if any(1 for key in part.keys() if
                                       key.lower() in mandatory_e_columns and str(part[key]).lower() in null_entries):
                                    return {'statusCode': 400,
                                            'body': f"please fill mandatory fields for the excel upload of components check row {inx + 1} and below"}
                            if part['lifeCycle'] not in ["EOL", "NRND", "Active", "Obsolete"]:
                                return {'statusCode': 400,
                                        'body': f'Please select correct lifeCycle for components ("EOL"/"NRND"/"Active"/"Obsolete") check row {inx + 1} and below'}
                            if part['rohs'].lower() not in ["yes", "no"]:
                                return {'statusCode': 400,
                                        'body': f'Please select correct rohs value for components (yes/no) check row {inx + 1} and below'}
                            if str(part['productName']).lower().strip() in category[cat_str]['sub_categories']:
                                sub_category = category[cat_str]['sub_categories'][
                                    str(part['productName']).lower().strip()]
                            else:
                                max_sc = category[cat_str]['max_subcategory'] + 1
                                sub_category = f"""sub_category{max_sc}"""
                                category[cat_str]['max_subcategory'] = max_sc
                                category[cat_str]['sub_categories'][
                                    str(part['productName']).strip().lower()] = f"""sub_category{max_sc}"""
                                sub_cat = {key: value for value, key in category[cat_str]['sub_categories'].items()}
                                if any(1 for item in category_twi if item['filter']['pk_id'] == metadata_id):
                                    inx = [inx for inx, item in enumerate(category_twi) if
                                           item['filter']['pk_id'] == metadata_id][0]
                                    category_twi.pop(inx)
                                category_twi.append({
                                    'filter': {'pk_id': metadata_id},  # Filter for the first document
                                    'update': {'$set': {'sub_categories': sub_cat}},  # Update for the first document
                                })
                            all_attributes = {
                                "cmpt_id": cmpt_id,
                                "ctgr_id": category_id,
                                "ctgr_name": str(part['categoryName']).strip(),
                                "department": str(part['department']).title().strip(),
                                "ptg_prt_num": f"PTG{truncated_hash}",
                                "mfr": str(part['manufacturer']).strip(),
                                "manufacturer": str(part['manufacturer']).strip(),
                                "mfr_prt_num": str(part['mfrPartNumber']).strip(),
                                "img_type": str(imageType) if image else '',
                                "prt_img": str(upload_image),
                                "data_sheet": str(upload_data_sheet),
                                "sub_ctgr": sub_category,
                                "rohs": str(part["rohs"]).lower().strip(),
                                "mounting_type": str(part["mountingType"]).strip(),
                                "foot_print": str(part["footPrint"]).strip(),
                                "strg_rcmd": str(part.get("msl", '')),
                                "life_cycle": str(part["lifeCycle"]).strip(),
                                "qty": '0',
                                "value": str(part["value"]).strip(),
                                "opt_tem": str(part["opt_tem"]).strip(),
                                "description": str(part["description"]).strip()
                            }
                            if str(part['eolDate']).lower() not in null_entries and str(part["lifeCycle"]) != 'Active':
                                # all_attributes["eol_date"] = eol_date
                                if eol_date == 'NA/undefined/20undefined':
                                    all_attributes["eol_date"] = 'NA'
                                else:
                                    all_attributes["eol_date"] = eol_date
                            if str(part['replacementPartNumber']).lower() not in null_entries and str(
                                    part["lifeCycle"]) != 'Active':
                                all_attributes["rpl_prt_num"] = str(part.get("replacementPartNumber", ""))
                            if str(part['hsn_code']).lower() not in null_entries:
                                all_attributes["hsn_code"] = str(part.get("hsn_code", ""))
                        else:
                            return {"statusCode": 400, "body": "Department can be from the options Electronic/Mechanic"}
                        predefined_attrs = list(category[cat_str]['attributes'].keys())
                        part_attributes = [key for key in part.keys() if key.lower() not in all_columns]
                        part_attributes = part_attributes + predefined_attrs
                        for key in part_attributes:
                            if key.strip().lower() in predefined_attrs:
                                all_attributes[category[cat_str]['attributes'][key.lower()]] = str(part.get(key, 'n/a'))
                            else:
                                all_attributes[key] = str(part[key])
                        component_data = {
                            "pk_id": cmpt_id,
                            "sk_timeStamp": sk_timeStamp,
                            "all_attributes": all_attributes,
                            "gsipk_table": "Inventory",
                            "gsipk_id": str(department).title(),
                            "lsi_key": f"PTG{truncated_hash}",
                            "gsisk_id": '--'
                        }
                        if part['department'] == 'Electronic':
                            component_data['gsisk_id'] = part['productName']
                        component_twi.append(component_data)
                        max_cmptid += 1
                    else:
                        return {'statusCode': 400,
                                'body': f'Failed while uploading datasheet for row {inx + 1} please upload a public url'}
                else:
                    return {'statusCode': 400,
                            'body': f'Failed while uploading image for row {inx + 1} please upload a public url'}
            if len(component_twi):
                if len(category_twi):
                    for item in category_twi:
                        db_con.Metadata.update_one(item['filter'], item['update'])
                db_con.Inventory.insert_many(component_twi)
                msg = f"{len(component_twi)} Components created successfully" if component_twi else "No Component created"
                return {'statusCode': 200, 'body': msg}
            else:
                return {'statusCode': 400, 'body': "No components added please check the data and try again"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Internal server error'}

    def cmsInventoryClassificationPartsCount(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']

            part_name = data["part_name"]
            mfr_prt_num = data["mfr_prt_num"]
            # #print(MT_ID)


            # Modified to use MongoDB statement directly
            bom_response = list(db_con.Inventory.find({"$and": [
                {"gsipk_table": "Inventory"},
                {"all_attributes.mfr_prt_num": mfr_prt_num},
                {"gsisk_id": part_name}
            ]}))

            if bom_response:
                result_values = {
                    "received_parts": bom_response[0]["all_attributes"].get("rcd_qty", 0),
                    "returned_parts": bom_response[0]["all_attributes"].get("rtn_qty", 0),
                    "outgoing_parts": bom_response[0]["all_attributes"].get("out_going_qty", 0)
                }
                if result_values:
                    return {
                        "statusCode": 200,
                        "body": result_values
                    }
                else:
                    return {
                        "statusCode": 404,
                        "body": []
                    }
            else:

                # Modified to use MongoDB statement directly
                bom_response1 = list(db_con.Inventory.find({"$and": [
                    {"gsipk_table": "Inventory"},
                    {"all_attributes.mfr_prt_num": mfr_prt_num},
                    {"all_attributes.prdt_name": part_name}
                ]}))

                result_values = {
                    "received_parts": bom_response1[0]["all_attributes"].get("rcd_qty", 0),
                    "returned_parts": bom_response1[0]["all_attributes"].get("rtn_qty", 0),
                    "outgoing_parts": bom_response1[0]["all_attributes"].get("out_going_qty", 0)
                }
                if result_values:
                    return {
                        "statusCode": 200,
                        "body": result_values
                    }
                else:
                    return {
                        "statusCode": 404,
                        "body": []
                    }

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsClassificationPartsSearchSuggestion(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']

            Category_table = 'Inventory'

            metadata_statement_mechanic = {
                "gsipk_table": Category_table,
                "gsipk_id": 'Mechanic'
            }
            response_items_mechanic = list(db_con.Inventory.find(metadata_statement_mechanic,
                                                                 {"all_attributes.mfr_prt_num": 1,
                                                                  "all_attributes.ctgr_id": 1,
                                                                  "all_attributes.prdt_name": 1, "_id": 0}))

            metadata_statement_electronic = {
                "gsipk_table": Category_table,
                "gsipk_id": 'Electronic'
            }
            response_items_electronic = list(db_con.Inventory.find(metadata_statement_electronic,
                                                                   {"all_attributes.mfr_prt_num": 1,
                                                                    "all_attributes.ctgr_id": 1, "gsisk_id": 1,
                                                                    "_id": 0}))

            combined_response = response_items_mechanic + response_items_electronic

            # Transforming keys and combining data
            for item in combined_response:
                item["sub_category"] = item.pop("gsisk_id", None) or item["all_attributes"].get("prdt_name", None)

            # Modifying response format to match the desired structure
            formatted_response = [
                {"ctgr_id": item["all_attributes"]["ctgr_id"], "mfr_prt_num": item["all_attributes"]["mfr_prt_num"],
                 "sub_category": item["sub_category"]}
                for item in combined_response
            ]

            if formatted_response:
                return {
                    "statusCode": 200,
                    "body": formatted_response
                }
            else:
                return {
                    "statusCode": 404,
                    "body": []
                }

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}



    def cmsInventoryGetAllBomid(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            # print(data)

            env_type = data["env_type"]
            databaseTableName = "PtgCms" + data["env_type"]

            # Fetching BOM names and IDs from the database
            bom_data = list(db_con.BOM.find({}, {"all_attributes.bom_id": 1, "all_attributes.bom_name": 1, "_id": 0}))

            # Formatting the response as per the desired structure
            formatted_response = [
                {"bom_id": item["all_attributes"]["bom_id"], "bom_name": item["all_attributes"]["bom_name"]}
                for item in bom_data
            ]

            if formatted_response:
                return {
                    "statusCode": 200,
                    "body": formatted_response
                }
            else:
                return {
                    "statusCode": 404,
                    "body": []
                }
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}


    def cmsGetInventoryStockDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            # print(data)

            env_type = data['env_type']
            gsipk_table = 'Inventory'
            databaseTableName = f"PtgCms{env_type}"
            department = data['department']

            # Assuming 'Inventory' is a collection in the MongoDB database
            result = list(db_con.Inventory.find({"gsipk_table": gsipk_table, "gsipk_id": department}, {"_id": 0}))

            electronic_list = []
            mechanic_list = []

            if result:
                for i in result:
                    quantity = int(i['all_attributes']['qty'])
                    if quantity == 0:
                        status = 'Out of stock'
                    elif quantity >= 100:
                        status = 'In stock'
                    elif quantity < 100:
                        status = 'Running out of stock'

                    meta_id = i['all_attributes']['ctgr_id'].replace('CTID', 'MDID')

                    if i['gsipk_id'] == 'Electronic':
                        # Assuming 'Metadata' is another collection in the MongoDB database
                        result1 = list(db_con.Metadata.find({"gsipk_table": "Metadata", "gsipk_id": "Electronic"}))
                        for m in result1:
                            if m['pk_id'] == meta_id and i['all_attributes']['sub_ctgr'] in m['sub_categories']:
                                i['all_attributes']['sub_ctgr'] = m['sub_categories'][i['all_attributes']['sub_ctgr']]
                                electronic_list.append(i)
                    else:
                        key = 'part_name'
                        value = i['all_attributes']['prdt_name']
                        a = {
                            key: value,
                            "ctgr_name": i['all_attributes']['ctgr_name'],
                            "quantity": i['all_attributes']['qty'],
                            "mfr_prt_num": i['all_attributes']['mfr_prt_num'],
                            "ptg_prt_num": i['all_attributes']['ptg_prt_num'],
                            "status": status
                        }
                        mechanic_list.append(a)

                # Combining electronic and mechanic lists
                mechanic_list.extend(electronic_list)

                return {'statusCode': 200, 'body': mechanic_list}
            else:
                return {'statusCode': 404, 'body': "No Data"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsVendorGetByComponentId(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            # print(data)
            response = []

            env_type = data['env_type']
            dataBaseTableName = f"PtgCms{env_type}"
            gsipk_table = "Vendor"

            # Assuming 'Vendor' is a collection in the MongoDB database
            result = list(db_con.Vendor.find({"gsipk_table": gsipk_table, "all_attributes.vendor_status": "Active"}))

            for vendor in result:
                vendor_parts = vendor['all_attributes'].get('parts', {})
                component = [
                    (vendor_parts[key]["mfr_prt_num"], vendor_parts[key]["gst"], vendor_parts[key]["unit_price"]) for
                    key in vendor_parts.keys() if vendor_parts[key].get('cmpt_id') == data['cmpt_id']]
                if component:
                    response.append({
                        "vendor_name": vendor['all_attributes']['vendor_name'],
                        "vendor_id": vendor['pk_id'],
                        "mfr_part_number": component[0][0] if component[0] else None,
                        "tax": component[0][1] if component[0] else None,
                        "price": component[0][2] if component[0] else None
                    })

            return {"statusCode": 200, "body": response}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsVendorGetOrderDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            # print(data)

            env_type = data["env_type"]
            databaseTableName = "PtgCms" + data["env_type"]
            vendor_id = data["vendor_id"]

            # Assuming 'PurchaseOrder' is a collection in the MongoDB database
            bom_response = list(db_con.PurchaseOrder.find({"gsipk_table": "PurchaseOrder", "lsi_key": vendor_id}))

            # Sort the bom_response based on the "pk_id" in descending order
            bom_response.sort(key=lambda x: x.get("pk_id"), reverse=True)

            if bom_response:
                # Count the number of parts and documents in each purchase order
                part_count_dict, document_count_dict = count_parts_and_documents_in_purchase_orders(bom_response)

                # Add the part count and document count information to the response
                for purchase_order in bom_response:
                    po_id = purchase_order.get("pk_id")
                    purchase_order["part_count"] = part_count_dict.get(po_id, 0)
                    purchase_order["document_count"] = document_count_dict.get(po_id, 0)
                    # purchase_order["order_date"] = format_date(purchase_order.get("sk_timeStamp", ""))

                # Extract only the parts and document count information from the response
                count_response = [
                    {
                        "order_id": po.get("pk_id"),
                        "status": po.get("all_attributes", {}).get("status", 0),
                        "total_price": po.get("all_attributes", {}).get("total_price", 0),
                        "order_date": datetime.strptime(po.get("sk_timeStamp", ""), "%Y-%m-%dT%H:%M:%S.%f").strftime(
                            "%Y-%m-%d"),
                        "deliver_date": po.get("all_attributes", {}).get("deo", 0),
                        "part_count": po.get("part_count", 0),
                        "document_count": po.get("document_count", 0)
                    } for po in bom_response
                ]

                return {
                    "statusCode": 200,
                    "body": count_response
                }
            else:
                return {
                    "statusCode": 200,
                    "body": "No data found"
                }

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsVendorGetTopFive(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            # print(data)
            response = []
            # Assuming 'Vendor' is a collection in the MongoDB database
            vendor_collection = db_con.Vendor
            # Forming the MongoDB query
            query = {
                "gsipk_table": "Vendor",
                "all_attributes.vendor_status": "Active"
            }
            # Execute the query
            result = list(vendor_collection.find(query))
            # Process the results
            for vendor in result:
                vendor_parts = vendor['all_attributes'].get('parts', {})
                component = [(vendor_parts[key]["mfr_prt_num"], vendor_parts[key]["tax"],
                              vendor_parts[key]["unit_price"], vendor_parts[key]["moq"]) for key in vendor_parts.keys()
                             if vendor_parts[key]['cmpt_id'] == data['cmpt_id']]
                if component:
                    response.append({
                        "vendor_id": vendor['pk_id'],
                        "rating": vendor["all_attributes"]['vendor_rating'],
                        "mfr_part_number": component[0][0] if component[0] else None,
                        "tax": component[0][1] if component[0] else None,
                        "unit_price": component[0][2] if component[0] else None,
                        "moq": component[0][3] if component[0] else None
                    })
            # Sort the response based on unit_price and return the top five
            response = sorted(response, key=lambda x: int(x["unit_price"]))
            return {"statusCode": 200, "body": response[:5]}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'error': 'Bad Request(check data)'}

    def cmsVendorGetInnerOrderDetails(request_body):
        try:
            data = request_body
            env_type = data.get('env_type', '')
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            # #print(data)
            # env_type = data.get("env_type", "")
            # database_table_name = f"PtgCms{env_type}"
            po_id = data.get("po_id", "")
            purchase_table = 'PurchaseOrder'

            # Assuming 'PurchaseOrder' and 'Metadata' are collections in the MongoDB database
            purchase_order_collection = db_con.PurchaseOrder
            metadata_collection = db_con.Metadata

            # Forming the MongoDB query to fetch purchase order details
            query = {
                "gsipk_table": purchase_table,
                "pk_id": po_id
            }
            response_items = list(purchase_order_collection.find(query))
            # return {'statusCode':433,'body':response_items}
            # Fetching category information from the Metadata collection
            category_query = {
                "gsipk_table": "Metadata"
            }
            categories = metadata_collection.find(category_query)
            category_dict = {}
            # return {'statusCode':200,"body":categories}
            for category in categories:
                pk_id = category.get("pk_id", "").replace("MDID", "CTID")
                if category.get("gsipk_id") == "Electronic":
                    sub_categories = {
                        key: value for key, value in category.get("sub_categories", {}).items()
                    }
                    category_dict[pk_id] = {
                        "ctgr_name": category.get("gsisk_id", ""),
                        "sub_categories": sub_categories
                    }
                else:
                    category_dict[pk_id] = {
                        "ctgr_name": category.get("gsisk_id", "")
                    }
            # return {'statusCode':433,'body':category_dict}
            # Forming the query to fetch inventory details
            inventory_query = {
                "gsipk_table": "Inventory"
            }
            inventory_items = list(db_con.Inventory.find(inventory_query))
            inventory_dict = {item['all_attributes']["cmpt_id"]: item['all_attributes'] for item in inventory_items}
            # return {'statusCode':467,'body':inventory_dict.get()}
            parts_list = []
            for entry in response_items:
                docs = [{"content": value, 'document_name': value.split("/")[-1]} for key, value in
                        entry['all_attributes']['documents'].items()]
                # return {'statusCode':66545,'body':docs}

                formatted_documents = file_uploads.get_file(docs)
                parts = entry.get('all_attributes', {}).get('parts', {})
                formatted_parts = []
                for key, value in parts.items():
                    cmpt_id = value.get('cmpt_id', '')
                    part_info = {
                        "cmpt_id": value.get('cmpt_id', ''),
                        "ctgr_id": value.get('ctgr_id', ''),
                        "received_qty": value.get('received_qty', ''),
                        "description": inventory_dict.get(value.get('cmpt_id', ''), {}).get('description', ''),
                        "packaging": inventory_dict.get(value.get('cmpt_id', ''), {}).get('package', ''),
                        "unit_price": value.get('unit_price', ''),
                        "mfr_prt_num": value.get('mfr_prt_num', ''),
                        "manufacturer": inventory_dict.get(value.get('cmpt_id', ''), {}).get('mfr', ''),
                        "price": value.get('price', ''),
                        "qty": value.get('qty', ''),
                        "ctgr_name": category_dict.get(value.get('ctgr_id', ''), {}).get('ctgr_name', ''),
                        "department": value.get('department', '')
                    }
                    if value.get('department', '') == 'Electronic':
                        sub_category = category_dict.get(value.get('ctgr_id', ''), {}).get('sub_categories', {}).get(
                            inventory_dict.get(value['cmpt_id'], {}).get('sub_ctgr', ''), '')
                        part_info["prdt_name"] = sub_category
                    else:
                        part_info["prdt_name"] = inventory_dict[value['cmpt_id']]['prdt_name']
                    formatted_parts.append(part_info)

                part_details = {
                    "documents": formatted_documents,
                    "part": formatted_parts,
                    "payment_terms": entry.get('all_attributes', {}).get('payment_terms', ''),
                    "terms_and_conditions": entry.get('all_attributes', {}).get('terms_and_conditions', '')
                }
                parts_list.append(part_details)
            # return {'statusCode':433,'body':parts_list}

            if parts_list:
                return {"statusCode": 200, "body": parts_list}
            else:
                return {"statusCode": 404, "body": "No data Found"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {"statusCode": 400, "body": "Bad Request (check data)"}

    def cmsInventoryGetInnerBom(request_body):
        try:
            data = request_body
            env_type = data.get('env_type', '')
            db_conct = db_connection_manage().get_conn(env_type)
            db_con = db_conct['db']
            bom_name = data.get("bom_name", "")
            bom_id = data.get("bom_id", "")
            department = data.get("dep_type", "")
            # department = data.get("dep_type", "")

            # Fetch BOM details from MongoDB
            bom_collection = db_con[f"PtgCms{env_type}"]
            bom_query = {
                "gsipk_table": "BOM",
                "all_attributes.bom_id": bom_id
            }
            # bom_result = list(bom_collection.find(bom_query, {"all_attributes": 1}))
            bom_result = list(db_con.BOM.find({"all_attributes.bom_id": bom_id}, {"all_attributes": 1, "_id": 0}))
            # return {"statusCode":200,"body":bom_result}

            lst = []
            if bom_result:
                for item in bom_result:
                    item = item['all_attributes']
                    # Fetch category data from MongoDB
                    category_collection = db_con[f"PtgCms{env_type}"]
                    category_query = {
                        "gsipk_table": "Metadata"
                    }
                    # category_result = list(category_collection.find(category_query, {"pk_id": 1, "sub_categories": 1, "gsisk_id": 1, "gsipk_id": 1}))
                    category_result = list(
                        db_con.Metadata.find({}, {"pk_id": 1, "sub_categories": 1, "gsisk_id": 1, "gsipk_id": 1}))
                    category_data = {}
                    for category_item in category_result:
                        pk_id = category_item['pk_id'].replace("MDID", "CTID")
                        if category_item['gsipk_id'] == 'Electronic':
                            category_data[pk_id] = {
                                "ctgr_name": category_item['gsisk_id'],
                                "sub_categories": {key: value for key, value in category_item['sub_categories'].items()}
                            }
                        else:
                            category_data[pk_id] = {"ctgr_name": category_item['gsisk_id']}
                    # print(category_data)
                    # Fetch inventory data from MongoDB
                    # inventory_collection = db_con[f"PtgCms{env_type}"]
                    # inventory_query = {
                    #     "gsipk_table": "Inventory"
                    # }
                    # inventory_result = list(inventory_collection.find(inventory_query, {"all_attributes": 1}))
                    inventory_result = list(db_con.Inventory.find({}, {"all_attributes": 1}))
                    # print(inventory_result)
                    inventory_data = {item['all_attributes']['cmpt_id']: item['all_attributes'] for item in
                                      inventory_result}
                    # print(inventory_data.keys())
                    for part_key, part_info in item["E_parts"].items():
                        if part_key.startswith("part"):
                            if part_info.get("department") == department:
                                d = {}
                                cmp_id = part_info["cmpt_id"]
                                # print(cmp_id)
                                ctgr_id = part_info['ctgr_id']
                                # print(ctgr_id)
                                d["ptg_prt_num"] = part_info["ptg_prt_num"]
                                d["mfr_part_number"] = part_info["mfr_prt_num"]
                                d["part_name"] = category_data[ctgr_id].get('sub_categories', {}).get(
                                    part_info["sub_ctgr"], '')
                                # d["part_name"] = category_data[ctgr_id]['sub_categories'][part_info["sub_ctgr"]]
                                d["manufacturer"] = inventory_data[cmp_id].get("mfr", {})
                                d["device_category"] = category_data[ctgr_id]['ctgr_name']
                                d["cmpt_id"] = inventory_data[cmp_id]["cmpt_id"]
                                d["ctgr_name"] = category_data[ctgr_id]['ctgr_name']
                                d["mounting_type"] = part_info["mounting_type"]
                                d["sub_ctgr"] = category_data[ctgr_id]['sub_categories'][part_info["sub_ctgr"]]
                                d["department"] = part_info["department"]
                                d["required_quantity"] = part_info["qty_per_board"]
                                d['sub_category'] = category_data[ctgr_id]['sub_categories'][part_info["sub_ctgr"]]
                                d["qty"] = inventory_data[cmp_id]["qty"]
                                lst.append(d)
                                # print(d)
                    for part_key, part_info in item["M_parts"].items():
                        if part_key.startswith("part"):
                            if part_info.get("department") == department:
                                d = {}
                                cmp_id = part_info["cmpt_id"]
                                ctgr_id = part_info['ctgr_id']
                                d["part_name"] = inventory_data[cmp_id]["prdt_name"]
                                d["vic_part_number"] = part_info["vic_part_number"]
                                d["cmpt_id"] = inventory_data[cmp_id]["cmpt_id"]
                                d["ctgr_name"] = category_data[ctgr_id]['ctgr_name']
                                d["department"] = part_info["department"]
                                d["required_quantity"] = part_info["qty_per_board"]
                                d["qty"] = inventory_data[cmp_id]["qty"]
                                lst.append(d)
                                # print(d)

                resp = {
                    "bom_id": bom_id,
                    "bom_name": bom_name,
                    "dep_type": data["dep_type"],
                    "parts": lst
                }
                return {"statusCode": 200, "body": resp}
            else:
                return {"statusCode": 404, "body": []}
        except Exception as err:
            exc_type, _, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check event)'}



    # def cmsGetInventoryStockDetailsModified(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         department = data['department']
    #         query = {"gsipk_id": department}
    #         result = list(db_con.Inventory.find(query, {'_id': 0, 'all_attributes': 1, 'gsipk_id': 1}))

    #         mechanic_list = []
    #         for item in result:
    #             status = 'Out_of_Stock' if int(item['all_attributes']['qty']) == 0 else 'In_stock' if int(
    #                 item['all_attributes']['qty']) >= 100 else 'Running_out_of_stock'
    #             meta_id = item['all_attributes']['ctgr_id'].replace('CTID', 'MDID')
    #             metadata_item = list(db_con.Metadata.find({'pk_id': meta_id}))
    #             if metadata_item:
    #                 metadata_item = metadata_item[0]
    #                 sub_ctgr = metadata_item.get('sub_categories', {}).get(item['all_attributes'].get('sub_ctgr', ''),
    #                                                                        '') if item['gsipk_id'] == 'Electronic' else \
    #                 item['all_attributes']['prdt_name']
    #                 mechanic_list.append({
    #                     'sub_ctgr' if item['gsipk_id'] == 'Electronic' else 'part_name': sub_ctgr,
    #                     'ctgr_name': metadata_item['gsisk_id'],
    #                     'quantity': item['all_attributes']['qty'],
    #                     'mfr_prt_num': item['all_attributes']['mfr_prt_num'],
    #                     'ptg_prt_num': item['all_attributes']['ptg_prt_num'],
    #                     'status': status
    #                 })

    #         if mechanic_list:
    #             if data['stock_status'] == "All":
    #                 sorted_mechanic_list = sorted(mechanic_list, key=lambda x: (
    #                     x.get('sub_ctgr', '') if 'sub_ctgr' in x else x.get('part_name', '')).casefold())
    #                 return {'statusCode': 200, 'body': sorted_mechanic_list}
    #             filtered_list = [i for i in mechanic_list if i['status'] == data['stock_status']]
    #             sorted_filtered_list = sorted(filtered_list, key=lambda x: (
    #                 x.get('sub_ctgr', '') if 'sub_ctgr' in x else x.get('part_name', '')).casefold())
    #             return {'statusCode': 200, 'body': sorted_filtered_list}
    #         else:
    #             return {'statusCode': 404, 'body': "No Data"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request(check data)'}




    def cmsGetInventoryStockDetailsModified(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            department = data['department']
            query = {"gsipk_id": department}
            result = list(db_con.Inventory.find(query, {'_id': 0, 'all_attributes': 1, 'gsipk_id': 1}))

            mechanic_list = []
            for item in result:
                status = 'Out_of_Stock' if int(item['all_attributes']['qty']) == 0 else 'In_stock' if int(
                    item['all_attributes']['qty']) >= 100 else 'Running_out_of_stock'
                meta_id = item['all_attributes']['ctgr_id'].replace('CTID', 'MDID')
                metadata_item = list(db_con.Metadata.find({'pk_id': meta_id}))
                if metadata_item:
                    metadata_item = metadata_item[0]
                    sub_ctgr = metadata_item.get('sub_categories', {}).get(item['all_attributes'].get('sub_ctgr', ''),
                                                                           '') if item['gsipk_id'] == 'Electronic' else \
                    item['all_attributes']['prdt_name']
                    mechanic_list.append({
                        'sub_ctgr' if item['gsipk_id'] == 'Electronic' else 'part_name': sub_ctgr,
                        'ctgr_name': metadata_item['gsisk_id'],
                        'quantity': item['all_attributes']['qty'],
                        'manufacturer': item['all_attributes']['prdt_name'] if department == "Mechanic" else item['all_attributes']['mfr'],
                        'mfr_prt_num': item['all_attributes']['mfr_prt_num'],
                        'ptg_prt_num': item['all_attributes']['ptg_prt_num'],
                        'status': status
                    })

            if mechanic_list:
                if data['stock_status'] == "All":
                    sorted_mechanic_list = sorted(mechanic_list, key=lambda x: (
                        x.get('sub_ctgr', '') if 'sub_ctgr' in x else x.get('part_name', '')).casefold())
                    return {'statusCode': 200, 'body': sorted_mechanic_list}
                filtered_list = [i for i in mechanic_list if i['status'] == data['stock_status']]
                sorted_filtered_list = sorted(filtered_list, key=lambda x: (
                    x.get('sub_ctgr', '') if 'sub_ctgr' in x else x.get('part_name', '')).casefold())
                return {'statusCode': 200, 'body': sorted_filtered_list}
            else:
                return {'statusCode': 404, 'body': "No Data"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}







    def get_inventory_stock_detailsmodified(request_body):

        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            department = data['department']
            query = {'gsipk_table': 'Inventory', 'gsipk_id': department}
            result = list(db_con.Inventory.find(query, {'_id': 0, 'all_attributes': 1, 'gsipk_id': 1}))
            mechanic_list = []
            for item in result:
                status = 'Out_of_Stock' if int(item['all_attributes']['qty']) == 0 else 'In_stock' if int(
                    item['all_attributes']['qty']) >= 100 else 'Running_out_of_stock'
                meta_id = item['all_attributes']['ctgr_id'].replace('CTID', 'MDID')
                metadata_item = db_con.Metadata.find({'gsipk_table': 'Metadata', 'pk_id': meta_id})
                if metadata_item:
                    #  if item['gsipk_id'] == 'Electronic':
                    #       sub_ctgr = metadata_item.get('sub_categories', {}).get(item['all_attributes']['sub_ctgr'], {})
                    #       part_name = ''
                    #  else:
                    #       sub_ctgr = {}
                    #       part_name = item['all_attributes']['prdt_name']
                    mechanic_list.append({
                        'sub_ctgr' if item['gsipk_id'] == 'Electronic' else 'part_name': metadata_item.get(
                            'sub_categories', {}).get(item['all_attributes']['sub_ctgr'], {}) if item[
                                                                                                     'gsipk_id'] == 'Electronic' else
                        item['all_attributes']['prdt_name'],
                        'ctgr_name': metadata_item['gsisk_id'],
                        'quantity': item['all_attributes']['qty'],
                        'mfr_prt_num': item['all_attributes']['mfr_prt_num'],
                        'ptg_prt_num': item['all_attributes']['ptg_prt_num'],
                        'status': status
                    })
            # print("mechanic list:", mechanic_list)
            if mechanic_list:
                if data['stock_status'] == "All":
                    sorted_mechanic_list = sorted(mechanic_list, key=lambda x: (
                        x.get('sub_ctgr', '') if 'sub_ctgr' in x else x.get('part_name', '')).casefold())
                    return {'statusCode': 200, 'body': sorted_mechanic_list}
                filtered_list = [i for i in mechanic_list if i['status'] == data['stock_status']]
                sorted_filtered_list = sorted(filtered_list, key=lambda x: (
                    x.get('sub_ctgr', '') if 'sub_ctgr' in x else x.get('part_name', '')).casefold())
                return {'statusCode': 400, 'body': sorted_filtered_list}
            else:
                return {'statusCode': 404, 'body': "No Data"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsComponentGetRackDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = db_connection_manage().get_conn(env_type)
            db_con = db_conct['db']
            department = data['department']
            cmpt_id = data["cmpt_id"]

            # Query MongoDB for inventory positions
            inventory_results = list(db_con.inward.find({"gsipk_table": "inward"}, {"all_attributes.parts": 1}))

            result = []
            unique_positions = set()

            # Iterate through inventory entries and filter duplicates
            for parts_dict in inventory_results:
                for part in parts_dict.get("all_attributes", {}).get("parts", {}).values():
                    if part.get("cmpt_id") == cmpt_id:
                        inventory_position = part.get("inventory_position")
                        # Check if inventory position is not a duplicate
                        if inventory_position not in unique_positions:
                            result.append({"inventory_position": inventory_position})
                            unique_positions.add(inventory_position)


            # Query MongoDB for return quantity
            inventory1 = list(
                db_con.Inventory.find({"gsipk_table": "Inventory", "gsipk_id": department, "pk_id": cmpt_id}))
            rtn_qty = inventory1[0].get('all_attributes', {}).get('rtn_qty') if inventory1 else None

            # print(rtn_qty)
            response_body = {

                "inventory_position": result,
                "rtn_qty": rtn_qty if rtn_qty is not None else "0"
            }
            if response_body:

                return {"statusCode": 200,
                        "body": response_body}
            else:
                return {"statusCode": 400,
                        "body": "No data found"}

        except Exception as err:
            exc_type, _, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check data)'}



    def CmsVendorGetDetailsByName(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            # print(data)

            if data["type"] == "Vendor":
                env_type = data.get("env_type", "")

                metadata_table = 'Metadata'
                gsipk_table = 'Vendor'
                component_table = 'Inventory'
                vendor_name = data.get("vendor_name", "")

                vendor_id = data["vendor_id"]

                db_response = list(db_con.Vendor.find({"pk_id": vendor_id, "all_attributes.vendor_name": vendor_name},
                                                      {"sk_timeStamp": 1, "all_attributes": 1}))
                if db_response:

                    category = list(
                        db_con.Metadata.find({}, {"pk_id": 1, "sub_categories": 1, "gsisk_id": 1, "gsipk_id": 1}))
                    category = {
                        item['pk_id'].replace("MDID", "CTID"): (
                            {
                                "ctgr_name": item['gsisk_id'],
                                "sub_categories": {
                                    key: value for key, value in item['sub_categories'].items()
                                }
                            }
                            if item['gsipk_id'] == 'Electronic'
                            else {"ctgr_name": item['gsisk_id']}
                        )
                        for item in category
                    }

                    inventory = list(db_con.Inventory.find(
                        {"all_attributes.description": 1, "all_attributes.package": 1, "all_attributes.manufacturer": 1,
                         "all_attributes.cmpt_id": 1, "all_attributes.prdt_name": 1, "all_attributes.sub_ctgr": 1}, {}))
                    inventory = {item['cmpt_id']: item for item in inventory}
                    db = db_response[0]['all_attributes']
                    # boms = f"""select all_attributes.bom_id,all_attributes.bom_name from {databaseTableName} where gsipk_table='BOM'"""
                    # boms = execute_statement_with_pagination(boms)
                    boms = list(db_con.BOM.find({"all_attributes.bom_id": 1, "all_attributes.bom_name": 1}, {}))
                    boms = {item['bom_id']: item['bom_name'] for item in boms}

                    unique_part_ids = set()
                    unique_parts = {}
                    for key in db['parts'].keys():
                        part = db['parts'][key]
                        part_id = part['cmpt_id']
                        # if part_id not in unique_part_ids:
                        #     unique_part_ids.add(part_id)
                        if part['department'] == 'Electronic':
                            modified_key = {
                                "cmpt_id": part['cmpt_id'],
                                "ctgr_id": part['ctgr_id'],
                                "ctgr_name": category[part['ctgr_id']]['ctgr_name'],
                                "department": part['department'],
                                "bom_id": part['bom_id'],
                                "bom_name": boms[part['bom_id']],
                                "ctgr_name": part['ctgr_name'],
                                "dscription": part['description'],
                                "gst": part['gst'],
                                "mfr_prt_num": part['mfr_prt_num'],
                                "module": part['module'],
                                "material": part['material'],
                                "part_name": category[part['ctgr_id']]['sub_categories'][
                                    inventory[part['cmpt_id']]['sub_ctgr']]
                            }
                            corrected_dict = {**modified_key, **{sub_key: value for sub_key, value in part.items() if
                                                                 sub_key not in modified_key}}
                            unique_parts[key] = corrected_dict
                        else:
                            part['bom_name'] = boms[part['bom_id']]
                            part['prdt_name'] = inventory[part['cmpt_id']]['prdt_name']
                            part['part_name'] = inventory[part['cmpt_id']]['prdt_name']
                            part['ctgr_name'] = category[part['ctgr_id']]['ctgr_name']
                            unique_parts[key] = part
                    db['parts'] = unique_parts
                    db['vendor_date'] = db_response[0]['sk_timeStamp'][:10]
                    docs = [{"document": value, 'name': value.split("/")[-1]} for key, value in db['documents'].items()]
                    db['documents'] = docs
                else:
                    return {'statusCode': 404, 'body': "could not find data for the given Vendor name"}
            else:
                env_type = data.get("env_type", "")
                databaseTableName = f"PtgCms{env_type}"
                metadata_table = 'Metadata'
                gsipk_table = 'Partners'
                component_table = 'Inventory'
                vendor_name = data.get("vendor_name", "")
                # dynamodb = boto3.client('dynamodb')
                vendor_id = data["vendor_id"]

                db_response = list(db_con.Partners.find({"sk_timeStamp": 1, "all_attributes": 1}, {"pk_id": vendor_id,
                                                                                                   "all_attributes.partner_name": vendor_name}))

                if db_response:

                    category = list(
                        db_con.Metadata.find({"pk_id": 1, "sub_categories": 1, "gsisk_id": 1, "gsipk_id": 1}, {}))
                    category = {
                        item['pk_id'].replace("MDID", "CTID"): (
                            {
                                "ctgr_name": item['gsisk_id'],
                                "sub_categories": {
                                    key: value for key, value in item['sub_categories'].items()
                                }
                            }
                            if item['gsipk_id'] == 'Electronic'
                            else {"ctgr_name": item['gsisk_id']}
                        )
                        for item in category
                    }

                    inventory = list(db_con.Inventory.find(
                        {"all_attributes.description": 1, "all_attributes.package": 1, "all_attributes.manufacturer": 1,
                         "all_attributes.cmpt_id": 1, "all_attributes.prdt_name": 1}, {}))
                    inventory = {item['cmpt_id']: item for item in inventory}
                    db = db_response[0]['all_attributes']
                    db['vendor_date'] = db_response[0]['sk_timeStamp'][:10]
                    docs = [{"document": value, 'name': value.split("/")[-1]} for key, value in db['documents'].items()]
                    db['documents'] = docs
                else:
                    return {'statusCode': 404, 'body': "could not find data for the given Vendor name"}
                    # Calculate overall status based on the status of individual parts
            overall_status = all(part_info.get("status", False) for part_info in db.get("parts", {}).values())
            # Add overall status to the response
            db["overall_parts_status"] = overall_status
            return {'statusCode': 200, 'body': db}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def CmsInventoryGeneratePtgPartNumber(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            # print(data)
            env_type = data.get("env_type", "")
            if env_type:
                department = data["department"]
                ctgr_name = data["ctgr_name"].strip()
                # print(ctgr_name)
                mfr_prt_num = data["mfr_prt_num"].strip()
                if department == "Electronic":
                    sub_category = data["sub_category"].strip()
                    if not ctgr_name or not mfr_prt_num or not sub_category:
                        return {'statusCode': 400, 'body': 'Missing required parameters'}
                    # print(ctgr_name)
                    db = list(db_con.Category.find({"all_attributes.ctgr_name": ctgr_name, "gsipk_id": "Electronic"}))
                    # return db
                    if db == False:
                        return {'statusCode': 401, 'body': f"Category name {ctgr_name} does not exist"}
                    db = list(db_con.Inventory.find({}))
                    # print("wertwetr", db)
                    digits = string.digits
                    letters = string.ascii_uppercase
                    random_string = "".join(random.choices(digits + letters, k=3))
                    # print(random_string)
                    hashed_value = hashlib.sha256(random_string.encode()).hexdigest()
                    truncated_hash = hashed_value[:6].upper()
                    # print(truncated_hash)
                    return {'statusCode': 200, 'body': "PTG" + truncated_hash}
                elif department == "Mechanic":
                    prdt_name = data["prdt_name"]
                    if not ctgr_name or not mfr_prt_num or not prdt_name:
                        return {'statusCode': 400, 'body': 'Missing required parameters'}
                    db = list(db_con.Category.find({"all_attributes.ctgr_name": ctgr_name, "gsipk_id": "Mechanic"}))
                    # print(db)
                    if not db:
                        return {'statusCode': 401, 'body': f"Category name {ctgr_name} does not exist"}
                    db = list(db_con.Inventory.find({}))
                    digits = string.digits
                    letters = string.ascii_uppercase
                    random_string = "".join(random.choices(digits + letters, k=3))
                    hashed_value = hashlib.sha256(random_string.encode()).hexdigest()
                    truncated_hash = hashed_value[:7].upper()
                    # print(truncated_hash)
                    return {'statusCode': 200, 'body': "PTG" + truncated_hash}
            else:
                return {"statusCode": 400, "body": "something went wrong, please try agian"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def cmsComponentReplacementPart(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            if data['rpl_prt_num']:
                # print(data)
                a = []
                inventory_data = list(db_con.Inventory.find({}, {"all_attributes.mfr_prt_num": 1}))
                a = [i['all_attributes']['mfr_prt_num'] for i in inventory_data]
                if data['rpl_prt_num'] in ["-", "na", "NA"]:
                    return {'statusCode': 400, 'body': ""}
                return {'statusCode': 400, 'body': ""} if data['rpl_prt_num'] in a else {'statusCode': 200,
                                                                                         'body': 'replacement part number does not exist'}
            else:
                return {'statusCode': 400, 'body': ""}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Something went wrong'}

    # case '/cmsComponentGlobalSearch':
    # return inventory_operations.cmsComponentGlobalSearch(request_data)
    def cmsComponentGlobalSearch(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            search_query = data["search_query"].lower()
            category_data = list(
                db_con.Metadata.find({}, {"gsipk_id": 1, "gsisk_id": 1, "sub_categories": 1, "pk_id": 1}))
            category_data = {item['pk_id'].replace("MDID", "CTID"): {"ctgr_name": item['gsisk_id'],
                                                                     "sub_categories": item[
                                                                         'sub_categories']} if item.get('gsipk_id',
                                                                                                        "") == "Electronic" else {
                "ctgr_name": item['gsisk_id']} for item in category_data}
            inventory = list(db_con.Inventory.find({}, {"pk_id": 1, "all_attributes.vendor_name": 1,
                                                        "all_attributes.vendor_type": 1, "gsipk_id": 1,
                                                        "all_attributes.prdt_name": 1, "all_attributes.ctgr_name": 1,
                                                        "all_attributes.manufacturer": 1,
                                                        "all_attributes.mfr_prt_num": 1,
                                                        "all_attributes.description": 1, "all_attributes.cmpt_id": 1,
                                                        "all_attributes.sub_ctgr": 1, "all_attributes.ctgr_id": 1,
                                                        "gsipk_table": 1}))
            # print(inventory)
            vendor = list(
                db_con.Vendor.find({}, {"pk_id": 1, "all_attributes.vendor_name": 1, "all_attributes.vendor_type": 1}))
            # print(vendor)
            vndr_inv_data = inventory + vendor
            # print(vndr_inv_data)
            top_list = []
            final_list = [
                top_list.append(
                    {"vendor_id": item['pk_id'], "vendor_name": item['all_attributes']['vendor_name'],
                     "vendor_type": item['all_attributes']['vendor_type']}
                )
                if item['pk_id'].startswith("PTGVEN") and search_query in item['all_attributes']['vendor_name'].lower()
                else top_list.append(
                    {"component_id": item['all_attributes']['cmpt_id'], "department": item['gsipk_id'],
                     "ctgr_name": category_data[item['all_attributes']['ctgr_id']]['ctgr_name'],
                     "sub_categories": category_data[item['all_attributes']['ctgr_id']]['sub_categories'][
                         item['all_attributes']['sub_ctgr']], "manufacturer": item['all_attributes']['manufacturer'],
                     "mfr_prt_num": item['all_attributes']['mfr_prt_num']}
                )
                if item['pk_id'].startswith("CMPID_") and item['gsipk_id'] == 'Electronic' and (
                        search_query in category_data[item['all_attributes']['ctgr_id']]['sub_categories'][
                    item['all_attributes']['sub_ctgr']].lower()
                        or search_query in item['all_attributes']['mfr_prt_num'].lower()
                )
                else top_list.append(
                    {"component_id": item['all_attributes']['cmpt_id'], "department": item['gsipk_id'],
                     "ctgr_name": category_data[item['all_attributes']['ctgr_id']]['ctgr_name'],
                     "prdt_name": item['all_attributes']['prdt_name'],
                     "mfr_prt_num": item['all_attributes']['mfr_prt_num']}
                )
                if item['pk_id'].startswith("CMPID_") and item['gsipk_id'] == 'Mechanic' and (
                        search_query in item['all_attributes']['prdt_name'].lower()
                        or search_query in item['all_attributes']['mfr_prt_num'].lower()

                )
                else None
                for item in vndr_inv_data
            ]
            if final_list:
                return {"statusCode": 200, "body": top_list}
            else:
                return {'statusCode': 404, 'body': "NO data"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def CmsSubCategoriesGetByCategoryName(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            category = data['ctgr_id']
            db = list(db_con.Metadata.find({"pk_id": category.replace('CTID', 'MDID')}))
            result = {}
            if db:
                db = db[0]
                result['sub_categories'] = sorted(list(db['sub_categories'].values()))
                conct.close_connection(client)
                return {'statusCode': 200, 'body': result}
            else:
                conct.close_connection(client)
                return {'statusCode': 404, 'body': "No subcategories found for given category name"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}
    
    def ComponentActivityDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            cmptId = data['cmpt_id']
            response  = []
            activity = list(db_con.ActivityDetails.find({},{"_id":0,f"all_attributes.{cmptId}":1}))
            # activity = [{'all_attributes': {'CMPID_00058': {'mfr_prt_num': '123123QWER', 'date': '2024-05-22', 'action': 'Purchased', 'Description': 'Purchased', 'issued_to': 'Peopletech Group', 'po_no': 'OPTG86', 'invoice_no': 'jjlk121212', 'cmpt_id': 'CMPID_00058', 'ctgr_id': 'CTID_00014', 'prdt_name': 'inner_outward', 'description': 'odsfojdsj', 'packaging': ' ', 'inventory_position': 'qwerty', 'qty': '10', 'pass_qty': '10', 'fail_qty': '0', 'batchId': 'BTC28', 'used_qty': '0', 'lot_no': 'testlot'}}}]
            for inx,item in enumerate(activity):
                if cmptId in item['all_attributes']:
                    response.append(item['all_attributes'][cmptId])
            
            # Fetch lot id's from QATest
            qa = db_con.QATest.find(
                {f"all_attributes.parts": {"$exists": True}},
                {"_id": 0, "all_attributes.parts": 1}
            )
            lot_ids = {}
            for item in qa:
                parts = item.get('all_attributes', {}).get('parts', {})
                for part_key, part_value in parts.items():
                    cmpt_id = part_value.get('cmpt_id')
                    lot_id = part_value.get('lot_id')
                    if cmpt_id and lot_id:
                        lot_ids[cmpt_id] = lot_id
                    else:
                        lot_ids[cmpt_id] = ''
            for item in response:
                cmpt_id = item.get('cmpt_id')
                if cmpt_id in lot_ids:
                    item['lot_id'] = lot_ids[cmpt_id]
            return {'statusCode': 200, 'body': response}
        except:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            # print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}
        

    
    def CmsInventoryUpdateStock(request_body):
        try:
            data = request_body
            print(data)
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()
            print(db_con)
            cmpt_id=data['cmpt_id']    
            component_result = list(db_con.Inventory.find({"all_attributes.cmpt_id":cmpt_id},{"_id":0,"all_attributes.qty":1,'pk_id':1,'sk_timeStamp':1,"all_attributes.qty":1}))
            cpmt_qty=[i['all_attributes']['qty'] for i in component_result][0]
            inward_result= list(db_con.inward.find({},{"_id":0,'pk_id':1,'sk_timeStamp':1,"all_attributes.parts":1,'gsipk_id':1,"all_attributes.batchId":1,"all_attributes.po_id":1,"all_attributes.inwardId":1,
            "all_attributes.bom_id":1,"all_attributes.po_id":1,"all_attributes.invoice_num":1}))
            all_tables= list(db_con.all_tables.find({},{"_id":0,"all_attributes.ActivityDetails":1,'pk_id':1,"sk_timeStamp":1}))
            # return {'statusCode':200,'body':all_tables}
            sorted_parts=sorted(["BTC"+j['batchId'][3:] for k in inward_result for j in k['all_attributes'].get('parts',{}).values() if j['cmpt_id'] ==data['cmpt_id']])
            print(sorted_parts)
            print(cmpt_id)
            activity_details = list(db_con.ActivityDetails.find({f'all_attributes.{cmpt_id}.cmpt_id': cmpt_id},{'_id':0,f'all_attributes.{cmpt_id}.cmpt_id':1,f'all_attributes.{cmpt_id}.qty':1,f'all_attributes.{cmpt_id}.name':1,f'all_attributes.{cmpt_id}.emp_id':1}))
            # return {'statusCode':200,'body':activity_details}
            update_qty=0
            total_quantity=0
            latest_batch = max((j['batchId'] for k in inward_result for j in k.get('all_attributes', {}).get('parts', {}).values() if j['cmpt_id'] == data['cmpt_id']), key=lambda x: int(str(x)[3:]), default=None)
            inward_all_attributes={}
            reversed_btach_ids=[]
            batch_ids=[]
            po_ids=[]
            invoice_nos=[]
            
            if data['action']=="Reduced_Stock":
                Closing_Quantity=int(cpmt_qty)-int(data['Quantity'])
                if activity_details and data['emp_id'] in activity_details[0]['all_attributes'].get(cmpt_id, {}).get('emp_id', []):
                    for batch_id in sorted_parts:
                        for k in inward_result:
                            for part in k['all_attributes']['parts'].values():
                                if part['cmpt_id']==data['cmpt_id']:
                                    if 'batchId' in part and part['batchId'] == batch_id:
                                        if 'remaining_qty' in part and part.get('remaining_qty') !=0:
                                            if k.get('gsipk_id') is not None and k.get('gsipk_id').startswith('R'):
                                                part['batchId']='R'+part['batchId']
                                        else:
                                            if part.get('remaining_qty')==0:
                                                continue
                                        part['batchId']=part['batchId']
                                        reversed_btach_ids.append(part['batchId'])
                    reversed_btach_ids.reverse()
                    for reverse_batch_id in reversed_btach_ids:
                        for k in inward_result:
                            po_no_list = k['all_attributes'].get('po_id','')
                            po_id = ''.join(po_no_list)
                            invoice_list=k['all_attributes'].get('invoice_num','')
                            invoice_no=''.join(invoice_list)
                            # po_id += po_id_no
                            # print(po_id)
                            for part in k['all_attributes']['parts'].values():
                                if (reverse_batch_id[1:] if reverse_batch_id.startswith('R') else reverse_batch_id) in part['batchId']:
                                    qty_needed = int(data['Quantity']) - total_quantity
                                    if 'remaining_qty' in part:
                                        print(part['batchId'])
                                        remaining_qty = int(part['remaining_qty'])
                                        if remaining_qty >= 0:
                                            if remaining_qty >= qty_needed:
                                                total_quantity += qty_needed
                                                part['remaining_qty']= int(remaining_qty - qty_needed)
                                                # print(part['remaining_qty'])
                                                batch_ids.append(reverse_batch_id)
                                            else:
                                                total_quantity += remaining_qty
                                                part['remaining_qty'] = 0
                                                batch_ids.append(reverse_batch_id)
                                                qty_needed = int(data['Quantity']) - total_quantity
                                            # print(batch_ids)
                                    else:
                                        # print(part['batchId'])
                                        batch_qty = int(part['pass_qty']) 
                                        
                                        if batch_qty >= qty_needed:
                                            total_quantity += qty_needed
                                            part['remaining_qty'] = batch_qty - qty_needed
                                            # print(part['remaining_qty'])
                                            batch_ids.append(reverse_batch_id)
                                            po_ids.append(po_id)  # Append po_id when condition is met
                                            invoice_nos.append(invoice_no) 

                                        else:
                                            total_quantity += batch_qty
                                            part['remaining_qty'] = 0
                                            batch_ids.append(reverse_batch_id)
                                            po_ids.append(po_id)  # Append po_id when condition is met
                                            invoice_nos.append(invoice_no) 
                                            qty_needed = int(data['Quantity']) - total_quantity
                                    if total_quantity >= int(data['Quantity']):
                                        break
                            if total_quantity >= int(data['Quantity']):

                                break
    
                                    
                                            

                                
                    for k in inward_result: [part.update({'batchId': part['batchId'][1:]}) for part in k['all_attributes']['parts'].values() if 'batchId' in part and part['batchId'].startswith('R')]

                    print(total_quantity)
                    print(batch_ids)
                    if total_quantity < int(data['Quantity']):
                        return {'statusCode':200,'body':f"Desired Quantity not available in batches is {total_quantity} can not update when there is insufficient stock"}
                    else:
                        for k in inward_result:
                            db_con.inward.update_one(
                            {"pk_id": k["pk_id"]},  # Assuming _id is the unique identifier of the document
                            {"$set": {"all_attributes.parts": k["all_attributes"]["parts"]}}
                            )
                    

                else:
                    for batch_id in sorted_parts:
                        for k in inward_result:
                            po_no_list = k['all_attributes'].get('po_id', '')  # Get the list of po_id
                            po_id = ''.join(po_no_list) 
                            invoice_list = k['all_attributes'].get('invoice_num', '')  # Get the list of invoice_num
                            invoice_no = ''.join(invoice_list)
                            pk_id = k['pk_id']
                            sk_timeStamp = k['sk_timeStamp']
                            
                            for part in k['all_attributes']['parts'].values():
                                if 'batchId' in part and part['batchId'] == batch_id:
                                    if part["cmpt_id"] == data["cmpt_id"]:
                                        batch_qty = int(part['pass_qty'])
                                        
                                        if total_quantity < int(data['Quantity']):
                                            qty_needed = int(data['Quantity']) - total_quantity
                                            if batch_qty >= qty_needed:
                                                total_quantity += qty_needed
                                                part['remaining_qty'] = batch_qty - qty_needed
                                                batch_ids.append(batch_id)
                                                po_ids.append(po_id)  # Append po_id when condition is met
                                                invoice_nos.append(invoice_no)  # Append invoice_no when condition is met
                                            else:
                                                total_quantity += batch_qty
                                                part['remaining_qty'] = 0
                                                batch_ids.append(batch_id)
                                                po_ids.append(po_id)  # Append po_id when condition is met
                                                invoice_nos.append(invoice_no)  # Append invoice_no when condition is met
                                                
                                        if total_quantity >= int(data['Quantity']):
                                            break  # Break the parts loop if total_quantity meets or exceeds Quantity
                            
                            if total_quantity >= int(data['Quantity']):
                                break  # Break the inward_result loop if total_quantity meets or exceeds Quantity

                        if total_quantity >= int(data['Quantity']):
                            break  # Break the sorted_parts loop if total_quantity meets or exceeds Quantity

                    if total_quantity < int(data['Quantity']):
                        return {'statusCode': 200, 'body': f"Desired Quantity not available in batches, only {total_quantity} available. Cannot update due to insufficient stock."}
                    else:
                        for k in inward_result:
                            db_con.inward.update_one(
                                {"pk_id": k["pk_id"]},
                                {"$set": {"all_attributes.parts": k["all_attributes"]["parts"]}}
                            )
            
            elif data['action']=='Damaged_Stock':
                Closing_Quantity=int(cpmt_qty)
                batchids=data['batch_id']
                for batchId in batchids:
                    for k in inward_result:
                        po_no_list = k['all_attributes'].get('po_id','')
                        po_id = ''.join(po_no_list)
                        invoice_list=k['all_attributes'].get('invoice_num','')
                        invoice_no=''.join(invoice_list)
                        update=False
                        for  part in k['all_attributes']['parts'].values():
                            if part['cmpt_id'] == data['cmpt_id'] and part['batchId']==batchId:
                                part['damaged_qty']=data['Quantity']
                                update=True
                                po_ids.append(po_id)
                                invoice_nos.append(invoice_no)
                                # print(part)
                        if update:
                            db_con.inward.update_one(
                                {"pk_id": k["pk_id"]},
                                {"$set": {"all_attributes.parts": k["all_attributes"]["parts"]}}
                            )
                
                           
            elif data['action']=='Add_Stock':

                Closing_Quantity=int(cpmt_qty)+int(data['Quantity'])
                latest_batch = max((j['batchId'] for k in inward_result for j in k.get('all_attributes', {}).get('parts', {}).values() if j['cmpt_id'] == data['cmpt_id']), key=lambda x: int(str(x)[3:]), default=None)
                # latest_batch = max((j['batch_id'] for k in inward_result for j in k['all_attributes'].get('parts',{}).values()), key=lambda x: int(x[3:]))
                inward_all_attributes['action']=data['action']
                inward_all_attributes['description']=data['description']
                inward_all_attributes['Lot_no']=''
                inward_all_attributes['batchId'] = "BTC"+str(int(latest_batch[3:])+1)
                inward_all_attributes['issued_to']="PTG"
                inward_all_attributes['pass_qty']=data['Quantity']
                inward_all_attributes['po_no']='__'
                inward_all_attributes['Invoice']='__'
                inward_all_attributes['name']=data['name']
                inward_all_attributes['emp_id']=data['emp_id']
                inward_all_attributes['remaining_qty']=0
                inward_all_attributes['Closing_Quantity']=Closing_Quantity
                inward_all_attributes['cmpt_id']=data['cmpt_id']
                item1={
                "pk_id":"BTC"+str(int(latest_batch[3:])+1),
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": {'parts':{'part1':inward_all_attributes}},
                "gsipk_table": "inward",
                "gsipk_id":"RBTC"+str(int(latest_batch[3:])+1),
                "lsi_key": data['action'],
                    }
                
                existing_record = list(db_con.inward.find({
                    "all_attributes.parts.part1.cmpt_id": data['cmpt_id'],
                    "gsipk_id": {"$regex": "^R"}
                }, {'_id': 0}))
                # return {'statusCode':200,'body':existing_record}
                print(existing_record)
                if existing_record:
                    # Update the existing record
                    db_con.inward.update_one(
                        {"pk_id": existing_record[0]["pk_id"]},
                        {"$set": {
                            "all_attributes.parts.part1.remaining_qty": int(existing_record[0]["all_attributes"]["parts"]["part1"]["remaining_qty"]) + int(data['Quantity']),
                            "all_attributes.parts.part1.Closing_Quantity": Closing_Quantity
                        }}
                    )
                else:
                    # Insert a new record
                    db_con.inward.insert_one(item1)

            all_attributes={}
            activity_id=str(int(all_tables[0]['all_attributes']['ActivityDetails'][5:])+1)
            # po_id=""
            all_attributes['closing_qty']=Closing_Quantity
            all_attributes["date"]=sk_timeStamp[:10]
            all_attributes['action']=data['action']
            all_attributes['description']=data['description']
            all_attributes['lot_no']="lot_no"
            all_attributes['batchId']=(
                    data['batch_id'] if data['action'] == "Damaged_Stock" 
                    else "BTC" + str(int(latest_batch[3:]) + 1) if data['action'] == "Add_Stock" 
                    else batch_ids
                )
            all_attributes['issued_to']=data['name']
            all_attributes['qty']=data['Quantity']
            all_attributes['po_no']= "__" if data['action']=='Add_Stock' else po_ids
            all_attributes['emp_id']=data['emp_id']
            all_attributes['name']=data['name']
            all_attributes['invoice_no']="__" if data['action']=='Add_Stock' else invoice_nos
            all_attributes['cmpt_id']=data["cmpt_id"]

            # all_attributes.update({key: [i[key] for i in k['all_attributes']['parts'].values() if i['cmpt_id'] == data['cmpt_id']][0] for key in ['ctgr_id', 'mfr_prt_num', 'prdt_name', 'pass_qty', 'fail_qty','inventory_position',"packaging"]})

            
            item = {    
                "pk_id":"ACTID"+activity_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": {data['cmpt_id']:all_attributes},
                "gsipk_table": "ActivityDetails",
                "gsipk_id":"__",
                "lsi_key": data['action'],
            }
            

            key = {"pk_id": all_tables[0]['pk_id'],"sk_timeStamp": all_tables[0]['sk_timeStamp']}
            update_query={"$set":{"all_attributes.ActivityDetails":"ACTID"+activity_id}}
            db_con.all_tables.update_one(key,update_query)
            if data['action'] == "Reduced_Stock":
                update_query1 = {"$set": {"all_attributes.qty": int(component_result[0]['all_attributes'].get('qty', 0)) - int(data['Quantity'])}}
                key1 = {"pk_id": component_result[0]['pk_id'], "sk_timeStamp": component_result[0]['sk_timeStamp']}
                db_con.Inventory.update_one(key1, update_query1)

            elif data['action'] == "Add_Stock":
                update_query1 = {"$set": {"all_attributes.qty": int(component_result[0]['all_attributes'].get('qty', 0)) + int(data['Quantity'])}}
                key1 = {"pk_id": component_result[0]['pk_id'], "sk_timeStamp": component_result[0]['sk_timeStamp']}
                db_con.Inventory.update_one(key1, update_query1)

            # Log the activity regardless of the action
            db_con.ActivityDetails.insert_one(item)

            conct.close_connection(client)
            return {"statusCode": 200, "body": "stock is updated for the given component"}   
        except  Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Internal server error'}
       
    # def CmsInventoryGetInwardIdsForDamaged(request_body):
    #     try:
    #         data = request_body
    #         print(data)
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         sk_timeStamp = (datetime.now()).isoformat()
    #         damage_batch_ids=[]
    #         cmpt_id=data['cmpt_id']
    #         component_result = list(db_con.Inventory.find({"all_attributes.cmpt_id":cmpt_id},{"_id":0,"all_attributes.qty":1,'pk_id':1,'sk_timeStamp':1,"all_attributes.qty":1}))
    #         cpmt_qty=[i['all_attributes']['qty'] for i in component_result][0]
    #         if int(data['damaged_qty'])>int(cpmt_qty):
    #             return {"statusCode":400,'body':"we can not give damaged quantity more than existing component quantity"}

    #         inward_result= list(db_con.inward.find({},{"_id":0,'pk_id':1,'sk_timeStamp':1,"all_attributes.parts":1,'gsipk_id':1,"all_attributes.batchId":1,"all_attributes.inwardId":1,
    #             "all_attributes.bom_id":1,"all_attributes.po_id":1,"all_attributes.invoice_num":1}))
    #         # return inward_result
    #         for k in inward_result:
    #             for part in k['all_attributes']['parts'].values():
    #                 if part['cmpt_id']==cmpt_id:
    #                     damage_batch_ids.append({"batchId":part['batchId'],"qty":cpmt_qty})

    #         return {'statusCode':200,'body':damage_batch_ids}
    #     except  Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400,'body': 'Internal server error'}
    def CmsInventoryGetInwardIdsForDamaged(request_body):
        try:
            data = request_body
            print(data)
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now()).isoformat()
            damage_batch_ids=[]
            cmpt_id=data['cmpt_id']
            component_result = list(db_con.Inventory.find({"all_attributes.cmpt_id":cmpt_id},{"_id":0,"all_attributes.qty":1,'pk_id':1,'sk_timeStamp':1,"all_attributes.qty":1}))
            cpmt_qty=[i['all_attributes']['qty'] for i in component_result][0]
            # if int(data['damaged_qty'])>int(cpmt_qty):
            #     return {"statusCode":400,'body':"we can not give damaged quantity more than existing component quantity"}

            inward_result= list(db_con.inward.find({},{"_id":0,'pk_id':1,'sk_timeStamp':1,"all_attributes.parts":1,'gsipk_id':1,"all_attributes.batchId":1,"all_attributes.inwardId":1,
                "all_attributes.bom_id":1,"all_attributes.po_id":1,"all_attributes.invoice_num":1}))
            # return inward_result
            for k in inward_result:
                for part in k['all_attributes']['parts'].values():
                    print(part)
                    if part['cmpt_id']==cmpt_id:
                        damage_batch_ids.append({"batchId":part['batchId'],"batch_qty":part['pass_qty']})

            return {'statusCode':200,'body':damage_batch_ids}
        except  Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Internal server error'}