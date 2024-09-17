import json
from datetime import datetime, timedelta
import base64
from db_connection import db_connection_manage
import sys
import os
from cms_utils import file_uploads
from base64 import b64decode, b64encode
import shutil

conct = db_connection_manage()
class Categories():
    def CmsCategoryAddMetadata(request_body):
        # try:
        #print('entered')
        print(request_body)
        data = request_body
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        sk_timeStamp = datetime.now().isoformat()
        categoryName = data['categoryName'].strip()
        basic_categories = ["Crystals", "Mosfet", "Inductor", "Switch", "Resistor", "Transistor", "Ferrite Bead",
                            "Diode", "Led", "Fuse", "Ic", "Connector", "Capacitor"]
        lsi_key = "Static" if categoryName in basic_categories else "Dynamic"
        image_type = data['image_type']
        img = data['category_image']
        dep_type = data['ct_type']
        attr_list = [value.strip().lower() for value in data['product_attributes'].values()]
        subcat_list = [value.strip().lower() for value in data['sub_categories'].values()]
        if len(data['product_attributes']) == 0:
            return {"statusCode": 400, "body": "No attributes added"}
        if (len(attr_list) > len(set(attr_list))):
            return {"statusCode": 400, "body": "Duplicate Attributes cannot be created"}
        if data['ct_type'] == 'Electronic':
            if len(data['sub_categories']) == 0:
                return {"statusCode": 400, "body": "No sub categories added"}
            if (len(subcat_list) > len(set(subcat_list))):
                return {"statusCode": 400, "body": "Duplicate Sub_categories cannot be created"}
        ctgr_details = {key: data['product_attributes'][key] for inx, key in
                        enumerate(data['product_attributes'].keys())}
        sub_categories = {key: data['sub_categories'][key] for inx, key in enumerate(data['sub_categories'].keys())} if \
        data['ct_type'] == 'Electronic' else ""
        categories = list(db_con.Category.find({}))
        metadata = list(db_con.Metadata.find({}))
        # if any(dictionary['all_attributes']['ctgr_name'].lower() == categoryName.lower() and dictionary['gsipk_id'] == data['ct_type'] for dictionary in categories):
        #     return {"statusCode" : 400, "body" : "Category name already exists"}
        category_id = "00001"
        metadataId = "00001"
        if categories:
            category_ids = [i['all_attributes']["ctgr_id"].replace("CTID_", "") for i in categories]
            category_ids.sort(reverse=True)
            category_id = str(((5 - len(str(int(category_ids[0]) + 1)))) * "0") + str(int(category_ids[0]) + 1)
        if metadata:
            metadataIds = [i["pk_id"].replace("MDID_", "") for i in metadata]
            metadataIds.sort(reverse=True)
            metadataId = str(((5 - len(str(int(metadataIds[0]) + 1)))) * "0") + str(int(metadataIds[0]) + 1)
        category_id = max(metadataId, category_id)

        upload_image = ''
        if img:
            destination_filename = f"{category_id}.{image_type}"#file_uploads
            upload_image = file_uploads.upload_file("categoryimage", "PtgCms" + env_type, dep_type, category_id,
                                                  destination_filename, img) if img else ""
            # upload_image = Categories.upload_file("categoryimage", "PtgCms" + env_type, dep_type, category_id,
            #                                       destination_filename, img) if img else ""

        categoryDetails = {}
        categoryDetails['ctgr_id'] = "CTID_" + category_id
        categoryDetails['mtdt_id'] = "MDID_" + category_id
        categoryDetails["ctgr_image"] = upload_image
        categoryDetails["sk_timeStamp"] = sk_timeStamp
        categoryDetails["ctgr_name"] = categoryName
        category_data = {
            "pk_id": "CTID_" + category_id,
            "sk_timeStamp": sk_timeStamp,
            "all_attributes": categoryDetails,
            "gsipk_id": data['ct_type'],
            "gsipk_table":"Category"
        }
        category_metadata = {
            "pk_id": "MDID_" + category_id,
            "sk_timeStamp": str(sk_timeStamp),
            "all_attributes": ctgr_details,
            "gsisk_id": categoryName,
            "lsi_key": lsi_key,
            "gsipk_id": data['ct_type'],
            "gsipk_table":"Metadata"
        }
        if data['ct_type'] == 'Electronic' and sub_categories:
            category_metadata['sub_categories'] = sub_categories
        print(category_data)
        db_con.Category.insert_one(category_data)
        db_con.Metadata.insert_one(category_metadata)
        conct.close_connection(client)
        return {'statusCode': 200, 'body': f'New category {categoryName} created successfully'}
        # except Exception as err:
        #     exc_type, exc_obj, tb = sys.exc_info()
        #     f_name = tb.tb_frame.f_code.co_filename
        #     line_no = tb.tb_lineno
        #     #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
        #     return {'statusCode': 400,'body': 'Internal server error'}

    def upload_file(feature_name, type, dep_type, id, filename, document_content):
        data_folder = "cms-image-data"
        document_content = base64.b64decode(document_content)  # Correct variable name
        file_path = "/".join([data_folder, type,feature_name,dep_type, str(id), filename])  # Ensure id is converted to string
        #print(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        # Open the file in binary write mode
        with open(file_path, 'wb') as filewr:
            filewr.write(document_content)
            #print(file_path)
        return file_path

    def cmsCategoryDelete(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            category = data['ctgr_id']
            ct_type = data['type']
            category_data = list(db_con.Category.find({"pk_id": category}))
            category_metaData = list(db_con.Metadata.find({"pk_id": category.replace("CTID", "MDID")}))
            print(category_metaData)
            #print(category_data[0], category_metaData[0])
            category_inventory = list(db_con.Inventory.find({"all_attributes.ctgr_id": category}))
            print(category_inventory)
            if (len(category_metaData) and category_metaData[0]['lsi_key'] == "Static"):
                conct.close_connection(client)
                return {'statusCode': 404, 'body': 'You cannot delete this category '}
            if len(category_inventory):
                conct.close_connection(client)
                return {'statusCode': 404, 'body': 'This Category cannot be deleted with components'}
            if category_metaData and category_data:
                filename = category_data[0]['all_attributes']["ctgr_image"]
                print(filename)
                db_con.Category.delete_one({"pk_id": category})
                db_con.Metadata.delete_one({"pk_id": category.replace("CTID", "MDID")})
                # if filename:
                #     os.remove(filename)
                response = {'statusCode': 200, 'body': "Category Deleted Successfully"}
            else:
                response = {'statusCode': 400, 'body': "metadata or category data not found"}
            conct.close_connection(client)
            return response
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Category deletion failed'}

    def CmsCategoryEditMetadata(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            if data["dep_type"] == "Electronic":
                if data["sub_categories"]:
                    # new_category_name =  data['ctgr_name']
                    new_category_name = data['new_category']
                    attr_list = [value.strip().lower() for value in data['product_attributes'].values()]
                    subcat_list = [value.strip().lower() for value in data['sub_categories'].values()]
                    if len(data['product_attributes']) == 0:
                        conct.close_connection(client)
                        return {"statusCode": 404, "body": "No attributes added"}
                    if (len(attr_list) > len(set(attr_list))):
                        conct.close_connection(client)
                        return {"statusCode": 404, "body": "Duplicate Attributes cannot be created"}
                    if data['dep_type'] == 'Electronic':
                        if len(data['sub_categories']) == 0:
                            conct.close_connection(client)
                            return {"statusCode": 404, "body": "No sub categories added"}
                        if (len(subcat_list) > len(set(subcat_list))):
                            conct.close_connection(client)
                            return {"statusCode": 409, "body": "Duplicate Sub_categories cannot be created"}
                    ctgry_lst = list(db_con.Category.find({}))
                    categoryId = data['ctgr_id']
                    ctgr_name_lst = [i["all_attributes"]["ctgr_name"].lower() for i in ctgry_lst if
                                     i["all_attributes"]["ctgr_id"] != data['ctgr_id'] and i["gsipk_id"] == data[
                                         'dep_type']]
                    if data["new_category"].lower().strip() in ctgr_name_lst:
                        conct.close_connection(client)
                        return {"statusCode": 200, "body": "Category name already exists"}
                    _subcategories = data['sub_categories'].keys()
                    inventory = list(db_con.Inventory.find({"gsipk_id":"Electronic","all_attributes.ctgr_id":categoryId}))
                    if any(1 for item in inventory if item['all_attributes']['sub_ctgr'] not in _subcategories):
                        conct.close_connection(client)
                        return {"statusCode": 404,
                                "body": "You cannot delete a subcategory for which inventory is present"}
                    #print(new_category_name)
                    result = db_con.Category.update_one(
                        {"pk_id": categoryId},
                        {"$set": {"all_attributes.ctgr_name": new_category_name}}
                    )
                    result = db_con.Metadata.update_one(
                        {"pk_id": categoryId.replace("CTID", "MDID")},
                        {"$set": {
                            "all_attributes": {key: value.strip() for key, value in data["product_attributes"].items()},
                            "sub_categories": {key: value.strip() for key, value in data["sub_categories"].items()},
                            "gsisk_id": new_category_name
                            }
                         }
                    )
                    conct.close_connection(client)
                    return {"statusCode": 200, "body": "Electric category details changed successfully"}
                else:
                    conct.close_connection(client)
                    return {'statusCode': 400, 'body': 'Please add SubCategory'}
            elif data["dep_type"] == "Mechanic":
                #print(data)
                attr_list = [value.strip().lower() for value in data['product_attributes'].values()]
                if len(data['product_attributes']) == 0:
                    conct.close_connection(client)
                    return {"statusCode": 404, "body": "Please add attributes"}
                if (len(attr_list) > len(set(attr_list))):
                    conct.close_connection(client)
                    return {"statusCode": 404, "body": "Duplicate Attributes cannot be created"}
                # new_category_name =  data['ctgr_name']
                new_category_name = data['new_category']
                ctgry_lst = list(db_con.Category.find({}))
                ctgr_name_lst = [i["all_attributes"]["ctgr_name"].lower().strip() for i in ctgry_lst if
                                 i["all_attributes"]["ctgr_id"] != data['ctgr_id'] and i["gsipk_id"] == data[
                                     'dep_type']]
                if data["new_category"].lower().strip() in ctgr_name_lst:
                    conct.close_connection(client)
                    return {"statusCode": 404, "body": "Category name already exists"}
                categoryId = data['ctgr_id']
                ctgry = [ctgr for ctgr in ctgry_lst if ctgr['pk_id'] == categoryId]
                metadataId = ctgry[0]["all_attributes"]["mtdt_id"]
                metadataId = ctgry[0]["all_attributes"]["mtdt_id"]
                result = db_con.Category.update_one(
                    {"pk_id": categoryId},  # filter
                    {"$set": {"all_attributes.ctgr_name": new_category_name}}  # update
                )
                result = db_con.Metadata.update_one(
                    {
                        "pk_id": categoryId.replace("CTID", "MDID")},  # filter
                    {
                        "$set":
                            {
                                "all_attributes": {key: value.strip() for key, value in
                                                   data["product_attributes"].items()},
                                "gsisk_id": new_category_name
                            }
                    }
                )
                conct.close_connection(client)
                return {"statusCode": 200, "body": "Mechanic category details changed successfully"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Internal server error'}

    def CmsCategoryGetMetadata(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            category = data['ctgr_name']
            ctgr_id = data['ctgr_id']
            category_info = list(
                db_con.Category.find({"all_attributes.ctgr_name": category, "all_attributes.ctgr_id": ctgr_id}))
            if category_info:
                category_info = category_info[0]
                metadataId = category_info['all_attributes']['mtdt_id']
                metadata_info = db_con.Metadata.find({"pk_id": metadataId})
                category_data = {}
                if metadata_info:
                    result = metadata_info[0]
                    category_data['ctgr_name'] = category
                    category_data['product_attributes'] = result['all_attributes']
                    category_data['department'] = result['gsipk_id']
                    if category_info['gsipk_id'] == 'Electronic':
                        category_data['sub_categories'] = result['sub_categories']
                        category_data['department'] = result['gsipk_id']
                    category_data["new_category"] = category
                    conct.close_connection(client)
                    return {'statusCode': 200, 'body': category_data}
                conct.close_connection(client)
                return {'statusCode': 404, 'body': 'No data found in Metadata'}
            else:
                conct.close_connection(client)
                return {"statusCode": 404, "body": "category data is no there"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'There is an AWS Lambda Data Capturing Error'}
    def cmsCategoriesGetAllCategoresByDepartment(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            department = data['ct_type']
            db = list(db_con.Category.find({"gsipk_id": department}))
            lst = []
            db = [i["all_attributes"] for i in db]
            for item in db:
                dic = {}
                for k, v in item.items():
                    # if isinstance(v, dict):
                    if k == 'ctgr_image':
                        path = item['ctgr_image']
                        if path:
                            v = path
                            print(v)
                        else:
                            v = ''
                        #print(v)
                    #     dic[k] = v
                    # else:
                    dic[k] = v
                lst.append(dic)
                lst = sorted(lst, key=lambda x: x['ctgr_name'], reverse=False)
            #print(len(lst))
            conct.close_connection(client)
            return {'statusCode': 200, 'body': lst}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': []}
        

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
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}

    def CmsCategoryReplaceImage(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            category = data["category_name"]
            img = data["img"]
            dep_type = data['dep_type']
            image_type = data["image_type"]
            result = list(db_con.Category.find({"all_attributes.ctgr_name": category, "gsipk_id": data["dep_type"]}))
            categoryId = result[0]["all_attributes"]["ctgr_id"]
            destination_filename = f"{categoryId}.{image_type}"
            add_img = file_uploads.upload_file("categoryimage", "PtgCms" + env_type, dep_type,
                                             categoryId.replace("CTID_", ''),
                                             destination_filename, img)
            # add_img = Categories.upload_file("categoryimage", "PtgCms" + env_type, dep_type, categoryId.replace("CTID_",''),
            #                                  destination_filename, img)
            if result:
                #print(result)
                category_id = result[0]['pk_id']
                db_con.Category.update_one(
                    {"pk_id": result[0]["pk_id"], "sk_timeStamp": result[0]["sk_timeStamp"]},
                    {"$set": {"all_attributes.ctgr_image": add_img}}

                )
                return {'statusCode': 200, 'body': json.dumps('Replaced Category image successfully')}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
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
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request(check data)'}
        
