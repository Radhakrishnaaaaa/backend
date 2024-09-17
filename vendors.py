import json
from datetime import datetime,timedelta
import base64
from db_connection import db_connection_manage
import sys
import os
from bson import ObjectId
from cms_utils import file_uploads
 
# print('all_qqwjhyqgrqjhekf')
conct = db_connection_manage()
 
class Vendors():
    def CmsVendorCreate(request_body):
    # try:
        data = request_body
        #print(data)
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        null_entries = ['-','','na','n/a','nill','null','nul',"nil"]
        env_type = data.get("env_type","")
        databaseTableName = f"PtgCms{env_type}"
        s3_bucket_name = "cms-image-data"
        table_type = 'Vendor' if data['type']!='Partners' else data['type']
        sk_timeStamp = (datetime.now() + timedelta(hours=5, minutes=30)).isoformat()
        if  data['vendor_type']=="Partners":
            collection = db_con["Partners"]
        else:
            collection = db_con["Vendor"]
        # statement = f"""select * from {databaseTableName} where gsipk_table='{table_type}' """
        # result = execute_statement_with_pagination(statement)
        result = list(collection.find({"gsipk_table": table_type}))
        id_key = 'vendor_id' if table_type=='Vendor' else 'partner_id'
        vp_id = "01"
        if result:
            vp_ids = sorted([res["all_attributes"][id_key][6:] for res in result],reverse=True)
            vp_id = (str(((2 - len(str(int(vp_ids[0]) + 1)))) * "0") + str(int(vp_ids[0]) + 1) if len(str(int(vp_ids[0]))) == 1 else str(int(vp_ids[0]) + 1))
        all_attributes = {}
        all_attributes[id_key] = "PTG" +id_key[0:3].upper() + vp_id
        documents =  data["documents"]
        all_attributes["documents"] = {}
        for inx,docs in enumerate(documents):
            document_body = docs['content']
            extra_type = ''
            document_name = ("".join(letter for letter in docs['document_name'] if letter.isalnum()) + ".pdf")
            file_up = file_uploads.upload_file("Vendors","PtgCms"+env_type, extra_type,str(vp_id) ,document_name,document_body)
 
            if not file_up:
                return {"statusCode": 500, "body": "Failed while uploading documents"}
            all_attributes["documents"][f'document{inx+1}'] = file_up
        all_attributes["contact_number"] = data["contact_number"]
        all_attributes["email"] = data["email"]
        all_attributes["address1"] = data["address1"]
        all_attributes["address2"] = data["address2"]
        all_attributes["landmark"] = data["landmark"]
        all_attributes["city_name"] = data["city_name"]
        all_attributes["pin_code"] = data["pin_code"]
        all_attributes["country"] = data["country"]
        all_attributes["partner_type"] = (data["partner_type"])
        all_attributes["gst_number"] = data["gst_number"]
        all_attributes['state'] = data.get("state","")
        all_attributes["pan_number"] = data["pan_number"]
        all_attributes["ptg_poc_name"] = data["ptg_poc_name"]
        all_attributes["ptg_poc_contact_num"] = data["ptg_poc_contact_num"]
        all_attributes["holder_name"] = data['bank_info']['holder_name']
        all_attributes["bank_name"]=data['bank_info']['bank_name']
        all_attributes["account_number"]=data['bank_info']['account_number']
        all_attributes["ifsc_code"]=data['bank_info']['ifsc_code']
        all_attributes['payments'] = data['payments']
        all_attributes["branch_name"]=data['bank_info']['branch_name']
        all_attributes["terms_and_conditions"] = data["terms_and_conditions"]
        if data["gst_number"] and (data['gst_number'] not in null_entries and len(data['gst_number']) < 15):
            return {"statusCode": 400, "body": f"Either give a valid GST number or one from among {null_entries}"}
        if data["pan_number"] and (data['pan_number'] not in null_entries and len(data['pan_number']) < 10):
            return {"statusCode": 400, "body": f"Either give a valid PAN number or one from among {null_entries}"}
        # if data["gst_number"] and data['gst_number'] not in null_entries:
        #     return {"statusCode": 400, "body": f"Either give a valid GST number or one from among {null_entries}"}
        # if data["pan_number"] data['pan_number'] not in null_entries:
        #     return {"statusCode": 400, "body": f"Either give a valid PAN number or one from among {null_entries}"}
        if table_type=='Vendor':
            all_attributes["vendor_poc_name"] = data["vendor_poc_name"]
            all_attributes["vendor_poc_contact_num"] = data["vendor_poc_contact_num"]
            if any(dictionary.get("all_attributes")["vendor_name"].lower() == data['name'].lower() for dictionary in result):
                return {"statusCode": 400, "body": "Vendor name exists already"}
            if data["gst_number"] and any(dictionary.get("all_attributes")["gst_number"] == data["gst_number"] for dictionary in result if dictionary.get("all_attributes")["gst_number"].lower() not in null_entries):
                return {"statusCode": 400, "body": "gst number exists already"}
            if data["pan_number"] and any(dictionary.get("all_attributes")["pan_number"] == data["pan_number"] for dictionary in result if dictionary.get("all_attributes")["pan_number"].lower() not in null_entries):
                return {"statusCode": 400, "body": "pan_number exists already"}
            all_attributes['vendor_type'] = data['type']
            all_attributes['vendor_name'] = data['name']
            all_attributes["vendor_status"] = "Active"
            all_attributes['parts'] = {}
            all_attributes['vendor_rating'] = '0'
            m_part_number,e_part_number = 0,0
            elec_categories,mech_categories = 0,0
            if 'parts' in data:
                elec_categories = len(set([part['ctgr_id'] for part in data['parts'] if part['department'] == 'Electronic']))
                mech_categories = len(set([part['ctgr_id'] for part in data['parts'] if part['department'] == 'Electronic']))
                for part in data['parts']:
                    if part['department'] == 'Electronic':
                        if "E-parts" not in all_attributes:
                            all_attributes['E-parts'] = {}
                        all_attributes['E-parts'][f"part{e_part_number+1}"] = part
                        e_part_number+=1
                    else:
                        if "M-parts" not in all_attributes:
                            all_attributes['M-parts'] = {}
                        all_attributes['M-parts'][f"part{m_part_number+1}"] = part
                        m_part_number+=1 
            all_attributes['product_types'] = str(m_part_number+e_part_number) 
            all_attributes['categories'] = str(mech_categories+elec_categories)
            # gsipk_id = data['partner_type']
        else:
            all_attributes["partner_poc_name"] = data["partner_poc_name"]
            all_attributes["partner_poc_contact_num"] = data["partner_poc_contact"]
            if any(dictionary.get("all_attributes")["partner_name"].lower() == data['name'].lower() for dictionary in result):
                return {"statusCode": 400, "body": "partner name exists already"}
            if data["gst_number"] and any(dictionary.get("all_attributes")["gst_number"] == data["gst_number"] for dictionary in result if dictionary.get("all_attributes")["gst_number"].lower() not in null_entries):
                return {"statusCode": 400, "body": "gst number exists already"}
            if data["pan_number"] and any(dictionary.get("all_attributes")["pan_number"] == data["pan_number"] for dictionary in result if dictionary.get("all_attributes")["pan_number"].lower() not in null_entries):
                return {"statusCode": 400, "body": "pan_number exists already"}
            all_attributes['partner_name'] = data['name']
            all_attributes['partner_status'] = 'Active'
            all_attributes['vendor_type'] = 'Partners'
            gsipk_id = ' & '.join(data["partner_type"]) 
        item = {
            "pk_id": "PTG" +id_key[0:3].upper() + vp_id,
            "sk_timeStamp": sk_timeStamp,
            "all_attributes": all_attributes,
            "gsipk_table": table_type,
            "gsipk_id":' & '.join(data["partner_type"]),
            "lsi_key": "Active",
        }
        item['gsipk_id'] == data['partner_type']
        # #print(item)
        try:
            collection.insert_one(item)
            message = f"{data['type']} Vendor created successfully" if table_type=='Vendor' else "New partner created successfully"
            return {"statusCode": 200, "body": message}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Category deletion failed'}
 
        # if  data['vendor_type']=="Partners":
        #     collection = db_con["Partners"]
        # else:
        #     collection = db_con["Vendor"]
 
        # # Logic to generate vendor/partner ID
        # table_type = 'Vendor' if data['type'] != 'Partners' else data['type']
        # sk_timeStamp = (datetime.now()).isoformat()
        # result = list(collection.find({"gsipk_table": table_type}))
        # id_key = 'vendor_id' if table_type == 'Vendor' else 'partner_id'
        # vp_id = "01"
        # if result:
        #     # #print(result)
        #     vp_ids = sorted([int(res["all_attributes"][id_key][6:]) for res in result], reverse=True)
        #     vp_id = (str(((2 - len(str(int(vp_ids[0]) + 1)))) * "0") + str(int(vp_ids[0]) + 1) if len(
        #         str(int(vp_ids[0]))) == 1 else str(int(vp_ids[0]) + 1))
 
        # # Prepare attributes for insertion
        # all_attributes = {}
        # all_attributes[id_key] = "PTG" + id_key[0:3].upper() + vp_id
        # documents = data["documents"]
        # all_attributes["documents"] = {}
        # doc = {}
        # for inx,docs in enumerate(documents):
        #     document_body = docs['content']
        #     extra_type = ''
        #     document_name = ("".join(letter for letter in docs['document_name'] if letter.isalnum()) + ".pdf")
        #     file_up = file_uploads.upload_file("Vendors","PtgCms"+env_type, extra_type,str(vp_id) ,document_name,document_body)
 
        #     if not file_up:
        #         return {"statusCode": 500, "body": "Failed while uploading documents"}
        #     all_attributes["documents"][f'document{inx+1}'] = file_up
 
 
 
        # # Prepare other attributes
        # all_attributes.update({
        #     "contact_number": data["contact_number"],
        #     "email": data["email"],
        #     "address1": data["address1"],
        #     "address2": data["address2"],
        #     "landmark": data["landmark"],
        #     "city_name": data["city_name"],
        #     "pin_code": data["pin_code"],
        #     "country": data["country"],
        #     "partner_type": data["partner_type"],
        #     "gst_number": data["gst_number"],
        #     'state': data.get("state", ""),
        #     "pan_number": data["pan_number"],
        #     "ptg_poc_name": data["ptg_poc_name"],
        #     "ptg_poc_contact_num": data["ptg_poc_contact_num"],
        #     "holder_name": data['bank_info']['holder_name'],
        #     "bank_name": data['bank_info']['bank_name'],
        #     "account_number": data['bank_info']['account_number'],
        #     "ifsc_code": data['bank_info']['ifsc_code'],
        #     'payments': data['payments'],
        #     "branch_name": data['bank_info']['branch_name'],
        #     "terms_and_conditions": data["terms_and_conditions"]
        # })
 
        # # Additional attributes for Vendor or Partner
        # if table_type == 'Vendor':
        #     all_attributes.update({
        #         "vendor_poc_name": data["vendor_poc_name"],
        #         "vendor_poc_contact_num": data["vendor_poc_contact_num"],
        #         "vendor_type": data['type'],
        #         "vendor_name": data['name'],
        #         "vendor_status": "Active",
        #         "vendor_rating": '0',
        #         "parts": {}
        #     })
 
        #     # Handle part categories
        #     if 'parts' in data:
        #         for part in data['parts']:
        #             department_key = "E-parts" if part['department'] == 'Electronic' else "M-parts"
        #             if department_key not in all_attributes:
        #                 all_attributes[department_key] = {}
        #             all_attributes[department_key][f"part{len(all_attributes[department_key]) + 1}"] = part
        # else:
        #     all_attributes.update({
        #         "partner_poc_name": data["partner_poc_name"],
        #         "partner_poc_contact_num": data["partner_poc_contact"],
        #         "partner_name": data['name'],
        #         "partner_status": 'Active',
        #         "vendor_type": 'Partners',
        #         # "gsipk_id": ' & '.join(data["partner_type"])
        #     })
 
        # # Check for existing records
        # if collection.find_one({"all_attributes.vendor_name": data['name'].lower()}):
        #     return {"statusCode": 200, "body": "Vendor name exists already"}
 
        # # Insert the document into MongoDB
        # item = {
        #     "pk_id": "PTG" + id_key[0:3].upper() + vp_id,
        #     "sk_timeStamp": sk_timeStamp,
        #     "all_attributes": all_attributes,
        #     "gsipk_table": table_type,
        #     "gsipk_id": ' & '.join(data["partner_type"]),
        #     "lsi_key": "Active"
        # }
        # collection.insert_one(item)
        # conct.close_connection(client)
        # # Success message
        # message = f"{data['type']} Vendor created successfully" if table_type == 'Vendor' else "New partner created successfully"
        # return {"statusCode": 200, "body": message}
 
    def cmsEditVendorDetails(request_body):   
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            # #print(data)
            null_entries = ['-','','na','n/a','nill','null','nul',"nil"]
            if data["vendor_type"]=="Partners":
                # dynamodb = boto3.client("dynamodb")
                gsipk_table = "Partners"
                databaseTableName = "PtgCms"+data["env_type"]
                ptnr_id=data["partner_id"]
                dep_type=data["vendor_type"]
                ptnr = list(db_con.Partners.find({"pk_id":ptnr_id}))
                # return {'statusCode':34,'body':ptnr[0]['all_attributes']}
                partners = list(db_con.Partners.find({"pk_id":{ "$ne": ptnr_id }},{"all_attributes.partner_name":1,"all_attributes.gst_number":1,"all_attributes.pan_number":1}))
                if data['gst_number'] and data['gst_number'].lower()not in null_entries and any(1 for item in partners if item['all_attributes']['gst_number'].lower()==data['gst_number'].lower() if item['all_attributes']['gst_number'].lower()not in null_entries):
                    return {'statusCode': 404,'body': 'GST number already exists for another user'}
                if data['pan_number'] and data['pan_number'].lower()not in null_entries and any(1 for item in partners if item['all_attributes']['pan_number'].lower()==data['pan_number'].lower() if item['all_attributes']['pan_number'].lower()not in null_entries):
                    return {'statusCode': 404,'body': 'PAN number already exists for another user'}
                if data['partner_name'] and any(1 for item in partners if item['all_attributes']['partner_name'].lower().strip()==data['partner_name'].lower().strip()):
                    return {'statusCode': 404,'body': 'Name already exists for another partner'}
                # feature_name, environ ,type, id, filename, document_content
                # lt={f"document{inx+1}":({"S":i["document"]} if "http" in i['document'] else {"S":file_uploads.upload_file(i["document"], databaseTableName, ptnr_id,i["name"],"partnerdata")}) for inx,i in enumerate(data["documents"])}
                lt={f"document{inx+1}":file_uploads.upload_file('partnerdata',databaseTableName,'',ptnr_id,i["document_name"],i["content"]) for inx,i in enumerate(data["documents"])}
                main_dict = data
                main_dict.pop("env_type")
                main_dict.pop("documents")
 
                # main_dict.pop("documents")
                if "parts" in data.keys():
                    main_dict.pop("parts")
                ptnr_db = ptnr[0]['all_attributes']
                ptnr_db.pop("documents")
                key_value_pairs = {**{key: value for key, value in data.items()}, **ptnr_db}
                key_value_pairs.pop("partner_type")
 
                update_data = {}
                for key, value in key_value_pairs.items():
                    update_data[f"all_attributes.{key}"] = main_dict.get(key, value)  # Use main_dict value if exists, otherwise use data value
 
                # Special handling for 'partner_type'
                if "partner_type" in data:
                    update_data["all_attributes.partner_type"] = data['partner_type']
 
                # Handling 'documents' separately
                update_data["all_attributes.documents"] = lt
 
                # Constructing the filter
                query_filter = {
                    "pk_id": ptnr_id,
                    "sk_timeStamp": ptnr[0]["sk_timeStamp"]
                }
 
                # Constructing the update query
                update_query = {"$set": update_data}
 
                # Perform the update operation
                db_con.Partners.update_one(query_filter, update_query)
 
                # Return a success response
                return {"statusCode": 200, "body": json.dumps("Partners details changed successfully")}
            else:
                #
                # dynamodb = boto3.client("dynamodb")
                # #print(data)
                gsipk_table = "Vendor"
                databaseTableName = "PtgCms"+data["env_type"]
                vndr_id=data["vendor_id"]
                dep_type=data["vendor_type"]
                vndr = list(db_con.Vendor.find({"pk_id":vndr_id,"all_attributes":1,"all_attributes.vendor_type":dep_type}))
                vendors = list(db_con.Vendor.find({"pk_id":{"$ne": vndr_id}},{"all_attributes.vendor_name":1,"all_attributes.gst_number":1,"all_attributes.pan_number":1}))
                if data['gst_number'] and data['gst_number'].lower()not in null_entries and any(1 for item in vendors if item['all_attributes']['gst_number'].lower()==data['gst_number'].lower() if item['all_attributes']['gst_number'].lower()not in null_entries):
                    return {'statusCode': 404,'body': 'GST number already exists for another user'}
                if data['pan_number'] and data['pan_number'].lower()not in null_entries and any(1 for item in vendors if item['all_attributes']['pan_number'].lower()==data['pan_number'].lower() if item['all_attributes']['pan_number'].lower()not in null_entries):
                    return {'statusCode': 404,'body': 'PAN number already exists for another user'}
               
                if data.get('vendor_name') and any(1 for item in vendors if item['all_attributes']['vendor_name'].lower().strip()==data['vendor_name'].lower().strip()):
                    return {'statusCode': 404,'body': 'Name already exists for another vendor'}
                # for item in vendors:
                #     #print(item)
                if "partner_type" in data:
                    data.pop("partner_type")
                if "partner_type" in data:
                    data.pop("partner_type")
                main_dict = data
                lt={f"document{inx+1}":file_uploads.upload_file('vendordata',databaseTableName,'',vndr_id,i["document_name"],i["content"]) for inx,i in enumerate(data["documents"])}
 
                # lt = {f"document{inx + 1}": (i["document"] if "http" in i['document'] else file_uploads.upload_file(i["document"], databaseTableName, vndr_id, i["name"], "vendordata")) for inx, i in enumerate(data["documents"])}
                main_dict.pop("env_type")
                main_dict.pop("documents")
                # vndr_db = vndr[0]['all_attributes']
                key_value_pairs = {**{key: value for key, value in data.items()}, **main_dict}
                key_value_pairs['documents'] = lt
 
                res = db_con.Vendor.update_one({"pk_id": vndr_id
                                                  },
                    {"$set": {"all_attributes":key_value_pairs}})
 
                #print(res)
                return {"statusCode": 200, "body": json.dumps("Vendor details changed successfully")}
 
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Category deletion failed'}

    # def cmsEditVendorDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         #print(data)
    #         null_entries = ['-','','na','n/a','nill','null','nul',"nil"]
    #         if data["vendor_type"]=="Partners":
    #             # dynamodb = boto3.client("dynamodb")
    #             gsipk_table = "Partners"
    #             databaseTableName = "PtgCms"+data["env_type"]
    #             ptnr_id=data["partner_id"]
    #             dep_type=data["vendor_type"]
    #             # statement = f"""select * from {databaseTableName} where gsipk_table = '{gsipk_table}' and pk_id='{ptnr_id}' """
    #             # ptnr = execute_statement_with_pagination(statement)
    #             ptnr = list(db_con.Partners.find({"pk_id":ptnr_id}))
    #             # partners = f"""select all_attributes.partner_name,all_attributes.gst_number,all_attributes.pan_number from {databaseTableName} where gsipk_table = '{gsipk_table}' and pk_id!='{ptnr_id}' """
    #             # partners = execute_statement_with_pagination(partners)
    #             partners = list(db_con.Partners.find({"pk_id":{ "$ne": ptnr_id }},{"all_attributes.partner_name":1,"all_attributes.gst_number":1,"all_attributes.pan_number":1}))
    #             if data['gst_number'] and data['gst_number'].lower()not in null_entries and any(1 for item in partners if item['all_attributes']['gst_number'].lower()==data['gst_number'].lower() if item['all_attributes']['gst_number'].lower()not in null_entries):
    #                 return {'statusCode': 404,'body': 'GST number already exists for another user'}
    #             if data['pan_number'] and data['pan_number'].lower()not in null_entries and any(1 for item in partners if item['all_attributes']['pan_number'].lower()==data['pan_number'].lower() if item['all_attributes']['pan_number'].lower()not in null_entries):
    #                 return {'statusCode': 404,'body': 'PAN number already exists for another user'}
    #             if data['partner_name'] and any(1 for item in partners if item['all_attributes']['partner_name'].lower().strip()==data['partner_name'].lower().strip()):
    #                 return {'statusCode': 404,'body': 'Name already exists for another partner'}
    #             # feature_name, environ ,type, id, filename, document_content
    #             # lt={f"document{inx+1}":({"S":i["document"]} if "http" in i['document'] else {"S":file_uploads.upload_file(i["document"], databaseTableName, ptnr_id,i["name"],"partnerdata")}) for inx,i in enumerate(data["documents"])}
    #             lt={f"document{inx+1}":file_uploads.upload_file('partnerdata',databaseTableName,'',ptnr_id,i["document_name"],i["content"]) for inx,i in enumerate(data["documents"])}
    #             main_dict=data
    #             main_dict.pop("env_type")
    #             # main_dict.pop("documents")
    #             if "parts" in data.keys():
    #                 main_dict.pop("parts")
    #             # ptnr_db = extract_items_from_nested_dict(ptnr[0])['all_attributes']
    #             ptnr_db = ptnr[0]['all_attributes']
    #             # ptnr_db.pop("documents")
    #             key_value_pairs = {**{key: value for key, value in data.items()}, **ptnr_db}
    #             key_value_pairs['documents'] = lt

    #             res = db_con.Partners.update_one({"pk_id": ptnr_id},
    #                 {"$set": {"all_attributes":key_value_pairs}})
    #             return {"statusCode": 200, "body": json.dumps("Partners details changed successfully")}
    #         else:
    #             # 
    #             # dynamodb = boto3.client("dynamodb")
    #             #print(data)
    #             gsipk_table = "Vendor"
    #             databaseTableName = "PtgCms"+data["env_type"]
    #             vndr_id=data["vendor_id"] 
    #             dep_type=data["vendor_type"]
    #             # statement = f"""select * from {databaseTableName} where gsipk_table = '{gsipk_table}' and pk_id='{vndr_id}'and all_attributes."vendor_type"='{dep_type}' """
    #             # vndr = execute_statement_with_pagination(statement)
    #             vndr = list(db_con.Vendor.find({"pk_id":vndr_id,"all_attributes.vendor_type":dep_type}))
    #             # vendors = f"""select all_attributes.vendor_name,all_attributes.gst_number,all_attributes.pan_number from {databaseTableName} where gsipk_table = '{gsipk_table}' and pk_id!='{vndr_id}' """
    #             # vendors = execute_statement_with_pagination(vendors)
    #             vendors = list(db_con.Vendor.find({"pk_id":{"$ne": vndr_id}},{"all_attributes.vendor_name":1,"all_attributes.gst_number":1,"all_attributes.pan_number":1}))
    #             if data['gst_number'] and data['gst_number'].lower()not in null_entries and any(1 for item in vendors if item['all_attributes']['gst_number'].lower()==data['gst_number'].lower() if item['all_attributes']['gst_number'].lower()not in null_entries):
    #                 return {'statusCode': 404,'body': 'GST number already exists for another user'}
    #             if data['pan_number'] and data['pan_number'].lower()not in null_entries and any(1 for item in vendors if item['all_attributes']['pan_number'].lower()==data['pan_number'].lower() if item['all_attributes']['pan_number'].lower()not in null_entries):
    #                 return {'statusCode': 404,'body': 'PAN number already exists for another user'}
    #             if data['vendor_name'] and any(1 for item in vendors if item['all_attributes']['vendor_name'].lower().strip()==data['vendor_name'].lower().strip()):
    #                 return {'statusCode': 404,'body': 'Name already exists for another vendor'}
    #             if "partner_type" in data:
    #                 data.pop("partner_type")
    #             main_dict=data
    #             # lt={f"document{inx+1}":(i["document"] if "http" in i['document'] else upload_file(i["document"], databaseTableName, vndr_id,i["name"],"vendordata")) for inx,i in enumerate(data["documents"])}
    #             lt={f"document{inx+1}":file_uploads.upload_file('vendordata',databaseTableName,'',vndr_id,i["document_name"],i["content"]) for inx,i in enumerate(data["documents"])}
    #             main_dict.pop("env_type")
    #             # main_dict.pop("documents")
    #             # vndr_db = extract_items_from_nested_dict(vndr[0])['all_attributes']
    #             # vndr_db = vndr[0]['all_attributes']
    #             key_value_pairs = {**{key: value for key, value in data.items() }, **main_dict}
    #             key_value_pairs['documents'] = lt
    #             res = db_con.Vendor.update_one({"pk_id": vndr_id
    #                                               },
    #                 {"$set": {"all_attributes":key_value_pairs}})

    #             #print(res)
    #             return {"statusCode": 200, "body": json.dumps("vendor details changed successfully")}
 
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400,'body': 'Category deletion failed'}
 
 
    def cmsgetAllVendors(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            search_status=data["status"]
            # Build the match stage of the aggregation pipeline
            match_stage = {
                "$match": {
                    "gsipk_table": "Vendor",
                    "lsi_key": search_status
                }
            }
            # Execute aggregation pipeline
            pipeline = [
                match_stage
            ]
            vendors = list(db_con.Vendors.aggregate(pipeline))
            lst = sorted([
                {
                    'vendor_id': item.get('vendorId', ""),
                    'vendor_type': item["all_attributes"].get('type', ""),
                    'vendor_name': item["all_attributes"].get('name', ""),
                    'categories': item["all_attributes"].get('categories', "0"),
                    'product_types': item["all_attributes"].get('product_types', ""),
                    'contact_details': item["all_attributes"].get('contact_number', ""),
                    'email': item["all_attributes"].get('email', "")
                }
                for item in vendors
            ], key=lambda x: int(x['vendor_id'].replace("PTGVEN", "")), reverse=False)
            # #print(lst)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': lst}
 
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Category deletion failed'}
 
    def CmsVendorUpdateStatus(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            #print(data)

            status = data['status']

            if data.get('vendor_id'):
                gsipk_table = 'Vendor'
                Id = data['vendor_id']
                query = {
                    "all_attributes.vendor_id": Id,
                    "gsipk_table": gsipk_table
                }
            elif data.get('partner_id'):
                gsipk_table = 'Partners'
                Id = data['partner_id']
                query = {
                    "all_attributes.partner_id": Id,
                    "gsipk_table": gsipk_table
                }
            collection = db_con[gsipk_table]
            # #print("tablestatus",gsipk_table)
            result = collection.find_one(query)
            #print(result)
            if result:
                update_result = collection.update_one(
                    {"_id": result["_id"]},
                    {"$set": {"all_attributes.vendor_status": status, "lsi_key": status}}
                )

                if update_result.modified_count > 0:
                    return {
                        'statusCode': 200,
                        'body': "Status updated successfully"
                    }
                else:
                    return {
                        'statusCode': 404,
                        'body': "Failed to update status"
                    }
            else:
                return {
                    'statusCode': 404,
                    'body': "Kindly check the data is present in vendors or partners"
                }
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'error': 'There is an AWS Lambda Data Capturing Error'}


    def CmsVendorAddRating(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            vendor_id = data["vendor_id"] #"PTGVEN01"
            # Define the filter
            filter = {"pk_id": vendor_id}
            # Perform the query
            result = (db_con.Vendor.find_one(filter))
            # #print(result)
            filter = {
                "_id": result["_id"]}
            # #print(filter)
            # # Define the update operation
            update = {
                "$set": {
                    "all_attributes.vendor_rating": data["rating"],
                }
            }
            # # Perform the update operation
            result = db_con.Vendor.update_one(filter, update)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': f' Vendor rating updated successfully'}
 
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'failed to upload rating'}
        

    def CmsVendorGetAllDataDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            search_status = data['status']
            lst = []
           
            if data['type'] == 'Partners':
                partners = list(db_con.Partners.find({"lsi_key": search_status}))
                lst = sorted([{
                    'partner_id': item.get('pk_id', ""),
                    'partner_name': item.get('all_attributes', {}).get('partner_name', ""),
                    'partner_type': ["".join([value for value in item.get('all_attributes', {}).get('partner_type', [])])],
                    'contact_details': item.get('all_attributes', {}).get('contact_number', ""),
                    'email': item.get('all_attributes', {}).get('email', "")
                } for item in partners], key=lambda x: x['partner_id'], reverse=False)
            else:
                query = {"all_attributes.vendor_status": search_status}
                extra_attribute = {} if data['type'] == 'all_vendors' else {"all_attributes.vendor_type": data['type']}
                query.update(extra_attribute)
                vendors = list(db_con.Vendor.find(query))
                lst = sorted([{
                    'vendor_id': item.get('pk_id', ""),
                    'vendor_type': item.get('all_attributes', {}).get('vendor_type', ""),
                    'vendor_name': item.get('all_attributes', {}).get('vendor_name', ""),
                    'categories': item.get('all_attributes', {}).get('categories', "0"),
                    'product_types': item.get('all_attributes', {}).get('product_types', ""),
                    'contact_details': item.get('all_attributes', {}).get('contact_number', ""),
                    'email': item.get('all_attributes', {}).get('email', "")
                } for item in vendors], key=lambda x: int(x['vendor_id'].replace("PTGVEN", "")), reverse=False)
               
            # Close the database connection
            conct.close_connection(client)
            return {'statusCode': 200, 'body': lst}
       
        except Exception as err:
            exc_type, _, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check data)'}

    def CmsVendorGetDetailsByName(request_body):
        try:
            print(request_body)
            data = request_body
            #dependent on Bom
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            vendor_id = data["vendor_id"]  # "PTGVEN01"
            if data["type"] == "Vendor":
                env_type = data.get("env_type", "")
                databaseTableName = f"PtgCms{env_type}"
                vendor_name = data.get("vendor_name", "")
                vendor_id = data["vendor_id"]
                db_response = list(db_con.Vendor.find({
                    '$and':[
                    {'pk_id':vendor_id},
                    {'all_attributes.vendor_name':vendor_name}
                    ]
                },{'_id':0,'all_attributes':1,'sk_timeStamp':1}))
                if db_response:    
                    category=list(db_con.Metadata.find({},{'_id':0,'pk_id':1,'sub_categories':1,'gsisk_id':1,'gsipk_id':1}))
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
                    inventory=list(db_con.Inventory.find({},{'_id':0,'all_attributes.description':1,'all_attributes.package':1,'all_attributes.manufacturer':1,'all_attributes.cmpt_id':1,'all_attributes.prdt_name':1,'all_attributes.sub_ctgr':1}))
                    inventory = {item['all_attributes']['cmpt_id']: item for item in inventory}
                    # return inventory
                    db=db_response[0]['all_attributes']
                    boms=list(db_con.BOM.find({},{'_id':0,'all_attributes.bom_id':1,'all_attributes.bom_name':1}))
                    #print("bomdata",boms)
                    boms = {item['all_attributes']['bom_id']: item['all_attributes']['bom_name'] for item in boms}
                    # unique_part_ids = set()
                    unique_parts = {}
                    for key in db['parts'].keys():
                        part = db['parts'][key]
                        #print("partkey",part)
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
                                "part_name": category[part['ctgr_id']]['sub_categories'][inventory[part['cmpt_id']]["all_attributes"]['sub_ctgr']]
                            }
                            corrected_dict = {**modified_key, **{sub_key: value for sub_key, value in part.items() if sub_key not in modified_key}}
                            unique_parts[key] = corrected_dict
                        else:
                            #print("inventory_product",inventory)
                            part['bom_name'] = boms[part['bom_id']]
                            part['prdt_name'] = inventory[part['cmpt_id']]["all_attributes"]['prdt_name']
                            part['part_name'] = inventory[part['cmpt_id']]["all_attributes"]['prdt_name']
                            part['ctgr_name'] = category[part['ctgr_id']]['ctgr_name']
                            unique_parts[key] = part
                    db['parts'] = unique_parts
                    db['vendor_date'] = db_response[0]['sk_timeStamp'][:10]
                    docs = [{"content": value, 'document_name': value.split("/")[-1]} for key, value in db['documents'].items()]
                    docs = file_uploads.get_file(docs)
                    db['documents']=docs
                    return {'statusCode': 200, 'body': db}
                else:
                    return {'statusCode': 404, 'body': "could not find data for the given Vendor name"}
            else:
                env_type = data.get("env_type", "")
                databaseTableName = f"PtgCms{env_type}"
                vendor_name = data.get("vendor_name", "")
                vendor_id = data["vendor_id"]
                db_response= db_response = list(db_con.Partners.find({
                    '$and':[
                    {'pk_id':vendor_id},
                    {'all_attributes.partner_name':vendor_name}
                    ]
                },{'_id':0,'all_attributes':1,'sk_timeStamp':1}))
                if db_response:
                    category= list(db_con.Metadata.find({},{'_id':0,'all_attributes':1,'pk_id':1,'sk_timeStamp':1,'gsisk_id':1,'gsipk_id':1,'sub_categories':1}))
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
                    # return {'statusCode':33,'body':db_response}
             
                    # inventory = f"select all_attributes.description,all_attributes.package,all_attributes.manufacturer,all_attributes.cmpt_id,all_attributes.prdt_name from {databaseTableName} where gsipk_table='Inventory'"
                    # inventory = extract_items_from_array_of_nested_dict(execute_statement_with_pagination(inventory))
                    inventory=list(db_con.Inventory.find({},{'_id':0,'all_attributes.description':1,'all_attributes.package':1,'all_attributes.manufacturer':1,'all_attributes.cmpt_id':1,'all_attributes.prdt_name':1}))
                    inventory = {item['all_attributes']['cmpt_id']: item for item in inventory}

                    db=db_response[0]['all_attributes']

                    db['vendor_date'] = db_response[0]['sk_timeStamp'][:10]
                    docs = [{"content": value, 'document_name': value.split("/")[-1]} for key, value in db['documents'].items()]
                    docs = file_uploads.get_file(docs)
                    db['documents']=docs
                    return {'statusCode':33,'body':db}
                
                else:
                    return {'statusCode': 404, 'body': "could not find data for the given Vendor name"}
                    
                # Calculate overall status based on the status of individual parts
                # overall_status = all(part_info.get("status", False) for part_info in db.get("parts", {}).values())
            
                # Add overall status to the response  
                # db["overall_parts_status"] = overall_status
    
                # return {'statusCode': 200, 'body': db}
       
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename   
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Bad Request(check data)'}
        
        
    def cmsVendorsGetNamesAndIds(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            #print(data)
 
            env_type = data['env_type']
            databaseTableName = f"PtgCms{env_type}"
 
            # Assuming data['department'] is present in the request body
            department = data.get('department', '')
            # MongoDB query to fetch vendor IDs and names based on the department
            if department:
                result = list(db_con.Vendor.find({
                        "$or": [
                            {"all_attributes.vendor_type": data['department']},
                            {"all_attributes.vendor_type": "Mec&Ele"}
                        ]
                    },
                        {"all_attributes.vendor_id": 1, "all_attributes.vendor_name": 1,
                        "_id": 0}))
 
               
            else:      
                result = list(
                    db_con.Vendor.find({}, {"all_attributes.vendor_id": 1, "all_attributes.vendor_name": 1, "_id": 0}))
 
            formatted_result = [{"vendor_id": entry["all_attributes"]["vendor_id"],
                                 "vendor_name": entry["all_attributes"]["vendor_name"]} for entry in result]
            if formatted_result:    
                return {'statusCode': 200, 'body': formatted_result}
            else:
                return {'statusCode': 400, 'body': "Vendors not found"}
 
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}
 
 
 
# import json
# from datetime import datetime,timedelta
# import base64
# from db_connection import db_connection_manage
# import sys
# import os
# from bson import ObjectId


# conct = db_connection_manage()

# class Vendors():
#     def CmsVendorCreate(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             collection = db_con["Vendor"]

#             # Logic to generate vendor/partner ID
#             table_type = 'Vendor' if data['type'] != 'Partners' else data['type']
#             sk_timeStamp = (datetime.now()).isoformat()
#             result = list(collection.find({"gsipk_table": table_type}))
#             id_key = 'vendor_id' if table_type == 'Vendor' else 'partner_id'
#             vp_id = "01"
#             if result:
#                 # #print(result)
#                 vp_ids = sorted([int(res["all_attributes"][id_key][6:]) for res in result], reverse=True)
#                 vp_id = (str(((2 - len(str(int(vp_ids[0]) + 1)))) * "0") + str(int(vp_ids[0]) + 1) if len(
#                     str(int(vp_ids[0]))) == 1 else str(int(vp_ids[0]) + 1))

#             # Prepare attributes for insertion
#             all_attributes = {}
#             all_attributes[id_key] = "PTG" + id_key[0:3].upper() + vp_id
#             documents = data["documents"]
#             doc = {}
#             for inx, docs in enumerate(documents):
#                 img = docs['content']
#                 image_type = docs["document_name"]
#                 if img:
#                     image_64_decode = base64.b64decode(img)
#                     directory = f"../../../cms-images/vendor/{data['type']}/{vp_id}/"
#                     image_path = os.path.join(directory, image_type)
#                     # Create directory if it doesn't exist
#                     os.makedirs(directory, exist_ok=True)
#                     with open(image_path, 'wb') as image_result:
#                         image_result.write(image_64_decode)
#                     doc[image_type] = image_path
#             all_attributes["documents"]=doc



#             # Prepare other attributes
#             all_attributes.update({
#                 "contact_number": data["contact_number"],
#                 "email": data["email"],
#                 "address1": data["address1"],
#                 "address2": data["address2"],
#                 "landmark": data["landmark"],
#                 "city_name": data["city_name"],
#                 "pin_code": data["pin_code"],
#                 "country": data["country"],
#                 "partner_type": data["partner_type"],
#                 "gst_number": data["gst_number"],
#                 'state': data.get("state", ""),
#                 "pan_number": data["pan_number"],
#                 "ptg_poc_name": data["ptg_poc_name"],
#                 "ptg_poc_contact_num": data["ptg_poc_contact_num"],
#                 "holder_name": data['bank_info']['holder_name'],
#                 "bank_name": data['bank_info']['bank_name'],
#                 "account_number": data['bank_info']['account_number'],
#                 "ifsc_code": data['bank_info']['ifsc_code'],
#                 'payments': data['payments'],
#                 "branch_name": data['bank_info']['branch_name'],
#                 "terms_and_conditions": data["terms_and_conditions"]
#             })

#             # Additional attributes for Vendor or Partner
#             if table_type == 'Vendor':
#                 all_attributes.update({
#                     "vendor_poc_name": data["vendor_poc_name"],
#                     "vendor_poc_contact_num": data["vendor_poc_contact_num"],
#                     "vendor_type": data['type'],
#                     "vendor_name": data['name'],
#                     "vendor_status": "Active",
#                     "vendor_rating": '0',
#                     "parts": {}
#                 })

#                 # Handle part categories
#                 if 'parts' in data:
#                     for part in data['parts']:
#                         department_key = "E-parts" if part['department'] == 'Electronic' else "M-parts"
#                         if department_key not in all_attributes:
#                             all_attributes[department_key] = {}
#                         all_attributes[department_key][f"part{len(all_attributes[department_key]) + 1}"] = part
#             else:
#                 all_attributes.update({
#                     "partner_poc_name": data["partner_poc_name"],
#                     "partner_poc_contact_num": data["partner_poc_contact"],
#                     "partner_name": data['name'],
#                     "partner_status": 'Active',
#                     "vendor_type": 'Partners',
#                     "gsipk_id": ' & '.join(data["partner_type"])
#                 })

#             # Check for existing records
#             if collection.find_one({"all_attributes.vendor_name": data['name'].lower()}):
#                 return {"statusCode": 400, "body": "Vendor name exists already"}

#             # Insert the document into MongoDB
#             item = {
#                 "pk_id": "PTG" + id_key[0:3].upper() + vp_id,
#                 "sk_timeStamp": sk_timeStamp,
#                 "all_attributes": all_attributes,
#                 "gsipk_table": table_type,
#                 "gsipk_id": data['type'],
#                 "lsi_key": "Active"
#             }
#             collection.insert_one(item)
#             conct.close_connection(client)
#             # Success message
#             message = f"{data['type']} Vendor created successfully" if table_type == 'Vendor' else "New partner created successfully"
#             return {"statusCode": 200, "body": message}

#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400,'body': 'Vendor deletion failed'}

#     def cmsEditVendorDetails(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             vendor_id=data["vendor_id"]
#             filter = {"pk_id": vendor_id}
#             # Perform the query
#             result = (db_con.Vendor.find_one(filter))
#             documents = data['documents']
#             doc = {}
#             for inx, docs in enumerate(documents):
#                 img = docs['document']
#                 image_type = docs["name"]
#                 if img:
#                     image_64_decode = base64.b64decode(img)
#                     directory = f"../../../cms-images/vendor/{data['vendor_type']}/{vendor_id}/"
#                     image_path = os.path.join(directory, image_type)
#                     # Create directory if it doesn't exist
#                     os.makedirs(directory, exist_ok=True)
#                     with open(image_path, 'wb') as image_result:
#                         image_result.write(image_64_decode)
#                     doc[image_type] = image_path
#             del data["documents"]
#             for key, value in data.items():
#                 # Check if the key exists in the nested dictionary 'all_attributes'
#                 if key in result['all_attributes']:
#                     # If the key exists and the value is a dictionary, update its contents
#                     if isinstance(value, dict):
#                         for nested_key, nested_value in value.items():
#                             # #print(nested_key)
#                             result['all_attributes'][key][nested_key] = nested_value
#                     else:
#                         # If the key exists but the value is not a dictionary, update the value directly
#                         result['all_attributes'][key] = value
#             result["all_attributes"]["documents"].append(doc)
#             # Update the database
#             db_con.Vendor.update_one({"_id": result["_id"]}, {"$set": result})
#             conct.close_connection(client)
#             return {'statusCode': 200, 'body': f' Vendor Edited successfully'}

#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400,'body': 'Category deletion failed'}
    
#     def CmsVendorGetAllDataDetails(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             search_status = data['status']
#             lst = []
           
#             if data['type'] == 'Partners':
#                 partners = list(db_con.Partners.find({"lsi_key": search_status}))
#                 lst = sorted([{
#                     'partner_id': item.get('pk_id', ""),
#                     'partner_name': item.get('all_attributes', {}).get('partner_name', ""),
#                     'partner_type': [value for value in item.get('all_attributes', {}).get('partner_type', {"L": []})['L']],
#                     'contact_details': item.get('all_attributes', {}).get('contact_number', ""),
#                     'email': item.get('all_attributes', {}).get('email', "")
#                 } for item in partners], key=lambda x: x['partner_id'], reverse=False)
                   
#             else:
#                 query = {"all_attributes.vendor_status": search_status}
#                 extra_attribute = {} if data['type'] == 'all_vendors' else {"all_attributes.vendor_type": data['type']}
#                 query.update(extra_attribute)
#                 vendors = list(db_con.Vendor.find(query))
#                 lst = sorted([{
#                     'vendor_id': item.get('pk_id', ""),
#                     'vendor_type': item.get('all_attributes', {}).get('vendor_type', ""),
#                     'vendor_name': item.get('all_attributes', {}).get('vendor_name', ""),
#                     'categories': item.get('all_attributes', {}).get('categories', ""),
#                     'product_types': item.get('all_attributes', {}).get('product_types', ""),
#                     'contact_details': item.get('all_attributes', {}).get('contact_number', ""),
#                     'email': item.get('all_attributes', {}).get('email', "")
#                 } for item in vendors], key=lambda x: int(x['vendor_id'].replace("PTGVEN", "")), reverse=False)
               
#             # Close the database connection
#             conct.close_connection(client)
#             return {'statusCode': 200, 'body': lst}
       
#         except Exception as err:
#             exc_type, _, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'body': 'Bad Request (check data)'}

#     def CmsVendorGetDetailsById(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             #print(data)

#             vendor_id = data["vendor_id"]
#             vendor_name = data["vendor_name"]
#             gsipk_table = "Vendor"
#             status = "Active"

#             result = db_con[gsipk_table].find_one({
#                 "lsi_key": status,
#                 "all_attributes.vendor_id": vendor_id,
#                 "all_attributes.vendor_name": vendor_name
#             })

#             if result:
#                 if 'all_attributes' in result and 'parts' in result['all_attributes']:
#                     part_info = list(result['all_attributes']['parts'].values())
#                     if part_info:
#                         return {"statusCode": 200, "body": part_info}
#                 return {"statusCode": 400, "body": []}  # If parts info is empty or not found
#             else:
#                 return {"statusCode": 400, "body": "No data found for the given vendor ID and name"}
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'body': 'Bad Request (check data)'}

#     def CmsVendorUpdateStatus(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             #print(data)

#             status = data['status']

#             if data.get('vendor_id'):
#                 gsipk_table = 'Vendor'
#                 Id = data['vendor_id']
#                 query = {
#                     "all_attributes.vendor_id": Id,
#                     "gsipk_table": gsipk_table
#                 }
#             elif data.get('partner_id'):
#                 gsipk_table = 'Partners'
#                 Id = data['partner_id']
#                 query = {
#                     "all_attributes.partner_id": Id,
#                     "gsipk_table": gsipk_table
#                 }
#             collection = db_con[gsipk_table]
#             result = collection.find_one(query)

#             if result:
#                 update_result = collection.update_one(
#                     {"_id": result["_id"]},
#                     {"$set": {"all_attributes.vendor_status": status, "lsi_key": status}}
#                 )

#                 if update_result.modified_count > 0:
#                     return {
#                         'statusCode': 200,
#                         'body': "Status updated successfully"
#                     }
#                 else:
#                     return {
#                         'statusCode': 404,
#                         'body': "Failed to update status"
#                     }
#             else:
#                 return {
#                     'statusCode': 404,
#                     'body': "Kindly check the data is present in vendors or partners"
#                 }
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'error': 'There is an AWS Lambda Data Capturing Error'}

#     def cmsVendorsGetNamesAndIds(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             #print(data)

#             env_type = data['env_type']
#             databaseTableName = f"PtgCms{env_type}"

#             # Assuming data['department'] is present in the request body
#             department = data.get('department', '')

#             # MongoDB query to fetch vendor IDs and names based on the department
#             if department:
#                 result = list(db_con.Vendor.find({"all_attributes.vendor_type": {"$in": [department, "Mec&Ele"]}},
#                                                  {"all_attributes.vendor_id": 1, "all_attributes.vendor_name": 1,
#                                                   "_id": 0}))
#             else:
#                 result = list(
#                     db_con.Vendor.find({}, {"all_attributes.vendor_id": 1, "all_attributes.vendor_name": 1, "_id": 0}))

#             formatted_result = [{"vendor_id": entry["all_attributes"]["vendor_id"],
#                                  "vendor_name": entry["all_attributes"]["vendor_name"]} for entry in result]
#             if formatted_result:
#                 return {'statusCode': 200, 'body': formatted_result}
#             else:
#                 return {'statusCode': 400, 'body': "Vendors not found"}

#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'body': 'Bad Request(check data)'}


#     def CmsVendorGetAllData(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             search_status = data['status']
#             lst = []
#             if data['type'] == 'Partners':
#                 partners = list(db_con.Partners.find({"lsi_key": search_status}))
#                 # statement = f"""select * from {databaseTableName} where gsipk_table = '{gsipk_table}' and lsi_key='{search_status}' """
#                 # partners = execute_statement_with_pagination(statement=statement)
#                 # return partners
#                 #
#                 lst = sorted([{
#                     'partner_id': item["all_attributes"].get('partner_id', ""),
#                     'partner_name': item["all_attributes"].get('partner_name', ""),
#                     'partner_type': [value for value in item["all_attributes"].get('partner_type', {"L": []})['L']],
#                     'contact_details': item["all_attributes"].get('contact_number', ""),
#                     'email': item["all_attributes"].get('email', "")
#                 }
#                     for item in partners], key=lambda x: x['partner_id'], reverse=False)

#             else:
#                 query = {"all_attributes.vendor_status": search_status}
#                 extra_attribute = {} if data['type'] == 'all_vendors' else {"all_attributes.vendor_type": data['type']}
#                 query.update(extra_attribute)
#                 # extra_attribute = '' if data['type']=='all_vendors' else f" and all_attributes.vendor_type='{data['type']}'"
#                 vendors = list(db_con.Vendor.find(query))
#                 # return {"statusCode":256500,"body":vendors}
#                 # statement = f"""select * from {databaseTableName} where gsipk_table = 'Vendor' and all_attributes.vendor_status='{search_status}'{extra_attribute} """
#                 # vendors = execute_statement_with_pagination(statement=statement)
#                 lst = sorted([{
#                     'vendor_id': item["all_attributes"].get('vendor_id', ""),
#                     'vendor_type': item["all_attributes"].get('vendor_type', ""),
#                     'vendor_name': item["all_attributes"].get('vendor_name', ""),
#                     'categories': item["all_attributes"].get('categories', ""),
#                     'product_types': item["all_attributes"].get('product_types', ""),
#                     'contact_details': item["all_attributes"].get('contact_number', ""),
#                     'email': item["all_attributes"].get('email', "")
#                 }
#                     for item in vendors], key=lambda x: int(x['vendor_id'].replace("PTGVEN", "")), reverse=False)
#             conct.close_connection(client)
#             return {'statusCode': 200, 'body': lst}
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'body': 'Bad Request(check data)'}
#     def cmsgetAllVendors(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             search_status=data["status"]
#             # Build the match stage of the aggregation pipeline
#             match_stage = {
#                 "$match": {
#                     "gsipk_table": "Vendor",
#                     "lsi_key": search_status
#                 }
#             }
#             # Execute aggregation pipeline
#             pipeline = [
#                 match_stage
#             ]
#             vendors = list(db_con.Vendor.aggregate(pipeline))
#             lst = sorted([
#                 {
#                     'vendor_id': item.get('vendorId', ""),
#                     'vendor_type': item["all_attributes"].get('type', ""),
#                     'vendor_name': item["all_attributes"].get('name', ""),
#                     'categories': item["all_attributes"].get('categories', ""),
#                     'product_types': item["all_attributes"].get('product_types', ""),
#                     'contact_details': item["all_attributes"].get('contact_number', ""),
#                     'email': item["all_attributes"].get('email', "")
#                 }
#                 for item in vendors
#             ], key=lambda x: int(x['vendor_id'].replace("PTGVEN", "")), reverse=False)
#             # #print(lst)
#             conct.close_connection(client)
#             return {'statusCode': 200, 'body': lst}

#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400,'body': 'Category deletion failed'}



#     def CmsVendorAddRating(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             vendor_id = data["vendor_id"] #"PTGVEN01"
#             # Define the filter
#             filter = {"pk_id": vendor_id}
#             # Perform the query
#             result = (db_con.Vendor.find_one(filter))
#             # #print(result)
#             filter = {
#                 "_id": result["_id"]}
#             # #print(filter)
#             # # Define the update operation
#             update = {
#                 "$set": {
#                     "all_attributes.vendor_rating": data["rating"],
#                 }
#             }
#             # # Perform the update operation
#             result = db_con.Vendor.update_one(filter, update)
#             conct.close_connection(client)
#             return {'statusCode': 200, 'body': f' Vendor rating updated successfully'}

#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400,'body': 'failed to upload rating'}




