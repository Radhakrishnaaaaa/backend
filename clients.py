import json
from datetime import datetime,timedelta
import base64
from db_connection import db_connection_manage
import sys
import binascii

import os

from cms_utils import file_uploads
 
upl = file_uploads()
 
conct = db_connection_manage()

class Clients():
    def CmsClientCreate(request_body):
        try:
            data = request_body
            # #print(data)
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp = (datetime.now() + timedelta(hours=5, minutes=30)).isoformat()
            result = list(db_con.Clients.find({}))
            all_bom_ids = []
            for item in result:
                all_attributes = item.get("all_attributes",{})
                boms = all_attributes.get("boms",{})
                # #print(boms)  
               
                bom1 = boms.get("bom1", {})
               
                # #print(bom1)
                bom_id = bom1.get("bom_id",{})
                # #print(bom_id)
                if bom_id:
                    all_bom_ids.append(bom_id)
            data_bom_ids = [bom.get("bom_id", "")for bom in data.get("boms",[])]
            if any(bom_id in all_bom_ids for bom_id in data_bom_ids):
                conct.close_connection(client)
                return {"statusCode": 400, "body": "BOM ID(s) already added for this client"}
            if result and any(1 for item in result if item["all_attributes"]["client_name"].lower()==data['client_name'].lower()):
                conct.close_connection(client)
                return{"statusCode":400, "body":"Client Already exists"}
            client_name = data["client_name"].strip().title()
            id_key = 'client_id'
            vp_id = "01"
            if result:
                vp_ids = sorted([res["all_attributes"][id_key][6:] for res in result], reverse=True)
                vp_id = (str(((2 - len(str(int(vp_ids[0]) + 1)))) * "0") + str(int(vp_ids[0]) + 1) if len(str(int(vp_ids[0]))) == 1 else str(int(vp_ids[0]) + 1))
            all_attributes = {}
            all_attributes[id_key] = "PTG" +id_key[0:3].upper() + vp_id
            documents =  data["documents"]
            all_attributes["documents"] = {}
            all_attributes["orders"] = {}
            boms = {
                f"bom{inx+1}": {
                    "bom_id": i['bom_id'],
                    "moq": i['moq'],
                    "lead_time": i["lead_time"],
                    "warranty": i["warranty"],
                    "price": i["price"],
                    "gst": i["gst"]
                }
                for inx, i in enumerate(data["boms"])
                }
                # #print(data['documents'])
            if any(document['content']=='' for document in data['documents']):
                conct.close_connection(client)
                return {"statusCode": 400, "body": "Please Upload Valid Document"}
           
            for inx, docs in enumerate(documents):
                # #print(docs)
                # #print(inx)
               
                document_body = docs['content']
                #print(document_body)   
                document_name = ("".join(letter if letter.isalnum() or letter == '.' else '' for letter in docs['document_name']))
                document_name = document_name + (".pdf" if not document_name.endswith(".pdf") else "")
                destination_filename = f"{document_name}"
                extra_type=''
                # #print(destination_filename)      
                upload_image = file_uploads.upload_file("Clients","PtgCms"+env_type,extra_type, str(vp_id) ,destination_filename,document_body)
                # a.append(upload_image)     
                # #print(upload_image)
           
                if not upload_image:
                    conct.close_connection(client)
                    return {"statusCode": 500, "body": "Failed while uploading documents"}
 
                all_attributes["documents"][f'document{inx+1}'] = upload_image        
            all_attributes["client_name"] = client_name
            all_attributes["client_location"] = data["client_location"]
            all_attributes["email"] = data["email"]
            all_attributes["contact_number"] = data["contact_number"]
            all_attributes["terms_and_conditions"] = data["terms_and_conditions"]
            all_attributes["payment_terms"] = data["payment_terms"]
            all_attributes["client_status"] = "Active"
            all_attributes["types_of_boms"] = str(len(boms))
            all_attributes['boms'] = boms
            for bom in data["boms"]:
                bom_id = bom.get("bom_id", "")
           
            item = {
                "pk_id": "PTG" +id_key[0:3].upper() + vp_id,
                "sk_timeStamp": sk_timeStamp,
                "all_attributes": all_attributes,
                "gsipk_table": "Clients",
                "gsipk_id":"--",
                "lsi_key": "Active",
            }
       
 
            db_con.Clients.insert_one(item)
            conct.close_connection(client)
            return {"statusCode": 200, "body": "Client Created Successfully"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Internal server error'}
       
    def cmsClientEditDetails(request_body):
        # try:
        data = request_body
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        result = list(db_con.Clients.find({},{'_id':0,'all_attributes.client_name':1,'all_attributes.client_status':1,'all_attributes.documents':1,'all_attributes.client_id':1,'all_attributes.orders':1,'pk_id':1,'sk_timeStamp':1}))
        client_data = [item for item in result if item['pk_id']==data['client_id']]
        boms = []
        if any(document['content']=='' for document in data['documents']):
            conct.close_connection(client)
            return {"statusCode": 400, "body": "Please Upload Valid Document"}
        if len(data['boms']):
            boms = sorted(data['boms'], key=lambda x : int(x['bom_id'].replace("PTGBOM","")))
        if any(1 for item in result if item['all_attributes']["client_id"]!=data['client_id'] and item['all_attributes']["client_name"]==data['client_name']):
            conct.close_connection(client)
            return {'statusCode': 400,'body':f"Client name {data['client_name']} already exists in database"}
 
        if result and any(1 for item in result if item['all_attributes']["client_id"]==data['client_id']):
            # return result[0]['all_attributes']['documents']
            all_attributes = {key:data[key] for key in data.keys() if key not in ["env_type","documents"]}
            all_attributes['documents'] = {}
            for inx, docs in enumerate(data['documents']):
                key = f"document{inx+1}"
                document_body = docs['content']
                if not document_body.endswith(".pdf"):
                    document_64_decode = base64.b64decode(document_body)
                    document_name = ("".join(letter if letter.isalnum() or letter == '.' else '' for letter in docs['document_name']))
                    document_name = document_name + (".pdf" if not document_name.endswith(".pdf") else "")
                    extra_type=''
                    upload_image = file_uploads.upload_file("Clients","PtgCms"+env_type, extra_type,str(data['client_id']) ,document_name,document_body)
 
                    all_attributes['documents'][key] = upload_image
                else:
                    all_attributes['documents'][key]=document_body
            all_attributes['boms'] = {f"bom{inx+1}":item for inx,item in enumerate(boms)}
            all_attributes['types_of_boms'] = str(len(boms))
            # all_attributes['created_date'] = client[0]['sk_timeStamp'][:10]
            all_attributes['client_status'] = client_data[0]['all_attributes']['client_status']
            if 'orders' in data:
                all_attributes['orders'] = data['orders']
            # all_attributes = create_nested_dicts(all_attributes)
            if not 'orders' in all_attributes:
                all_attributes['orders'] = client_data[0]['all_attributes']['orders']
 
            key = {"pk_id": client_data[0]['pk_id'],"sk_timeStamp": client_data[0]['sk_timeStamp']}
            update_query={"$set":{"all_attributes":all_attributes}}
            result=db_con.Clients.update_one(key,update_query)
            conct.close_connection(client)
 
            if result:
                conct.close_connection(client)
                return {'statusCode':200,'body':"client details updated successfully"}
            else:
                conct.close_connection(client)
                return {'statusCode':400,'body':"Failed while updating client"}
        else:
            conct.close_connection(client)
            return {'statusCode': 400,'body':"Failed to fetch record for given client_id"}
        # except Exception as err:
        #     exc_type, exc_obj, tb = sys.exc_info()
            # f_name = tb.tb_frame.f_code.co_filename
            # line_no = tb.tb_lineno
            # #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            # return {'statusCode': 400,'body': 'Bad Request(check data)'}
       
    def CmsClientSearchAddBom(request_body):
        data = request_body
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        search_query = data['bom_name']
        if not search_query:
            conct.close_connection(client)
            return {'statusCode': 404, 'body': "No search parameters passed"}
 
        env_type = data["env_type"]
        bom_result = list(db_con.BOM.find(
                {
                    '$or': [
                        {'pk_id': search_query},
                        {'all_attributes.bom_name': search_query}
                    ]
                },
                {'_id':0,'all_attributes': 1, 'pk_id': 1}
            ))
        client_result=list(db_con.Clients.find({},{'_id':0,'all_attributes.boms':1}))
        bom_ids=[k['bom_id']  for i in client_result for j,k in i['all_attributes']['boms'].items()]
        if data['bom_name'] in bom_ids:
            conct.close_connection(client)
            return {'statusCode':400,'body':'this bom_id is alreday added' }    
        if bom_result:
           
            response_dict = {key: value for key, value in bom_result[0]['all_attributes'].items()}
            conct.close_connection(client)
 
            return {
                "statusCode": 200,
                "body": [{
                    "bom_id": response_dict['bom_id'],
                    "total_categories": response_dict['total_categories'],
                    "created_time": response_dict['created_time'],
                    "total_components": response_dict['total_components'],
                    "description": response_dict['description'],
                    "bom_name": response_dict['bom_name']
                }]
                }
 
        else:
            conct.close_connection(client)
            return {
                'statusCode':400,
                'body':"No data"
            }
        
    def CmsClientsUploadPo(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            data_po_information = data["po_information"]
            client_id = data['client_id']

            # Extract all bom_ids from Clients collection excluding the given client_id
            all_clients = list(db_con.Clients.find(
                # {'all_attributes.client_id': {'$ne': client_id}}
                {'all_attributes.client_id': {'$ne': client_id}},
                {'all_attributes.orders': 1, '_id': 0}
            ))
            existing_bom_ids = {order['bom_id'] for client in all_clients for order in
                                client['all_attributes'].get('orders',{}).values()}

            # Check for any existing bom_id in the new data
            bom_data = [i['bom_id'] for i in data['po_information']]
            if any(bom_id in existing_bom_ids for bom_id in bom_data):
                conct.close_connection(client)
                return {'statusCode': 400, 'body': "BOM_ID already exists in other clients"}

            # Check for duplicates in po_id and bom_id in the new data
            po_ids = [i['po_id'] for i in data['po_information']]
            duplicates_po = ', '.join(po_id for po_id in set(po_ids) if po_ids.count(po_id) > 1)
            if duplicates_po:
                conct.close_connection(client)
                return {'statusCode': 400, 'body': 'Duplicates found for po_id ' + duplicates_po}

            bom_ids = [i['bom_id'] for i in data['po_information']]
            duplicates_bom = ', '.join(bom_id for bom_id in set(bom_ids) if bom_ids.count(bom_id) > 1)
            if duplicates_bom:
                conct.close_connection(client)
                return {'statusCode': 400, 'body': 'Duplicates found for bom_id ' + duplicates_bom}

            # Fetch the client details
            result_client = list(db_con.Clients.find(
                {'all_attributes.client_id': client_id},
                {'_id': 0, 'all_attributes': 1, 'sk_timeStamp': 1}
            ))

            if result_client:
                client_details = result_client[0]

                # Check for duplicates in the existing client data
                existing_po_ids = [j['po_id'] for j in client_details['all_attributes']['orders'].values()]
                existing_bom_ids = [j['bom_id'] for j in client_details['all_attributes']['orders'].values()]

                combined_po_ids = existing_po_ids + po_ids
                duplicates_po_id = ', '.join(
                    po_id for po_id in set(combined_po_ids) if combined_po_ids.count(po_id) > 1)
                if duplicates_po_id:
                    conct.close_connection(client)
                    return {'statusCode': 400, 'body': 'Duplicates found for po_id ' + duplicates_po_id}

                combined_bom_ids = existing_bom_ids + bom_ids
                duplicates_bom_id = ', '.join(
                    bom_id for bom_id in set(combined_bom_ids) if combined_bom_ids.count(bom_id) > 1)
                if duplicates_bom_id:
                    conct.close_connection(client)
                    return {'statusCode': 400, 'body': 'Duplicates found for bom_id ' + duplicates_bom_id}

                sk_timeStamp = client_details["sk_timeStamp"]

                if "orders" in client_details["all_attributes"]:
                    po_information = client_details["all_attributes"]["orders"]
                    max_order_key = max(po_information.keys(), default="po0", key=lambda x: int(x.replace("po", "")))
                    starting_index = int(max_order_key.replace("po", "")) + 1 if max_order_key != "po0" else 1
                    new_po_information = {
                        f"po{starting_index + i}": po for i, po in enumerate(data["po_information"])
                    }
                    po_information.update(new_po_information)
                else:
                    client_details["all_attributes"]["orders"] = po_information

                key = {
                    "pk_id": client_details["all_attributes"]["client_id"],
                    "sk_timeStamp": sk_timeStamp
                }

                update_query = {"$set": {"all_attributes.orders": client_details["all_attributes"]["orders"]}}
                result = db_con.Clients.update_one(key, update_query)
                conct.close_connection(client)

                return {"statusCode": 200, "body": f"Successfully uploaded PO for {data['client_id']}"}
            else:
                conct.close_connection(client)
                return {"statusCode": 400, "body": "Client not found"}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return {'statusCode': 400, 'body': f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}"}

    # def CmsClientsUploadPo(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         data_po_information = data["po_information"]
    #         client_id=data['client_id']
    #         po_information = {f"po{inx+1}": value for inx,value in enumerate(data["po_information"])}
    #         # result_client=list(db_con.Clients.find({},{'_id':0,'all_attributes.boms':1}))
    #         result_client = list(db_con.Clients.find(
    #             {
    #                     'all_attributes.client_id': client_id
    #             },
    #             {'_id':0,'all_attributes': 1, 'sk_timeStamp': 1}
    #         ))
    #         result_bom=list(db_con.BOM.find({},{'_id':0,'pk_id':1}))
    #         bom_data = [i['bom_id'] for i in data['po_information']]
    #         pk_ids = [i["pk_id"] for i in result_bom]
    #         mismatched_bom_ids = [bom_id for bom_id in bom_data if bom_id not in pk_ids]
    #         # Display pop-up if mismatches found
    #         if mismatched_bom_ids:
    #             conct.close_connection(client)
    #             return {'statusCode':400,'body':"Please give existing BOM_ID"}
    #         a = [i['po_id'] for i in data['po_information']]  
    #         duplicates = ', '.join(po_id for po_id in set(a) if a.count(po_id) > 1)
    #         if duplicates:
    #             conct.close_connection(client)
    #             return {'statusCode':400,'body':'Duplicates found for po_id ' + duplicates}
    #         b = [i['bom_id'] for i in data['po_information']]
    #         duplicates1 = ', '.join(po_id for po_id in set(b) if b.count(po_id) > 1)
    #         if duplicates1:
    #             conct.close_connection(client)
    #             return {'statusCode':400,'body':'Duplicates found for bom_id' + duplicates1}
    #         if result_client:
    #             client_details = result_client[0]
    #             # orders=client_details["all_attributes"]["M"]["orders"]
    #             e = [j['po_id'] for i, j in client_details['all_attributes']['orders'].items()] + [i['po_id'] for i in data['po_information']]
    #             duplicates_po_id=', '.join(po_id for po_id in set(e) if e.count(po_id) > 1)
    #             if duplicates_po_id:
    #                 conct.close_connection(client)
    #                 return {'statusCode':400,'body':'Duplicates found for po_id' + duplicates_po_id}
    #             e1 = [j['bom_id'] for i, j in client_details['all_attributes']['orders'].items()] + [i['bom_id'] for i in data['po_information']]
    #             duplicates_bom_id=', '.join(bom_id for bom_id in set(e1) if e1.count(bom_id) > 1)
    #             if duplicates_bom_id:
    #                 conct.close_connection(client)
    #                 return {'statusCode':400,'body':'Duplicates found for bom_id' + duplicates_bom_id}
               
    #             sk_timeStamp = client_details["sk_timeStamp"]
    #             if "orders" in client_details["all_attributes"]:
    #                 # Assuming you have existing data in client_details["all_attributes"]["M"]["orders"]["M"]
    #                 po_information = client_details["all_attributes"]["orders"]
    #                 max_order_key = max(po_information.keys(), default="po0", key=lambda x: int(x.replace("po", "")))
    #                 starting_index = int(max_order_key.replace("po", "")) + 1 if max_order_key != "po0" else 1
    #                 new_po_information = {
    #                     f"po{starting_index + i}":  {key:  po[key] for key in po} for i, po in enumerate(data["po_information"])
    #                 }
    #                 po_information.update(new_po_information)
                   
    #             else:
    #                 # If "orders" does not exist, set it to the new items
    #                 client_details["all_attributes"]["orders"] = po_information
    #             key = {
    #                     "pk_id": client_details["all_attributes"]["client_id"],
    #                     "sk_timeStamp":sk_timeStamp
    #                 }
    #             # key = {"pk_id": client[0]['pk_id'],"sk_timeStamp": client[0]['sk_timeStamp']}
               
    #             update_query={"$set":{"all_attributes.orders":po_information}}
    #             result=db_con.Clients.update_one(key,update_query)
    #             conct.close_connection(client)
 
           
    #             return {"statusCode": 200,"body": f"Successfully uploaded PO for {data['client_id']}"}
    #         else:
    #             conct.close_connection(client)
    #             return {"statusCode": 400,"body": "Client not found"}
       
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400,'body': []}
    def cmsClientsGetAll(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            query={'all_attributes.client_status':data['status']}        
            req_attributes={'_id':0,'all_attributes.client_id':1,'all_attributes.client_name':1,'all_attributes.contact_number':1,'all_attributes.types_of_boms':1,'all_attributes.email':1}
            result=list(db_con.Clients.find(query,req_attributes))
            modified_result =sorted([{'client_id':x['all_attributes']['client_id'],'client_name':x['all_attributes']['client_name'],'contact_number':x['all_attributes']['contact_number'],'types_of_boms':x['all_attributes']['types_of_boms'],'email':x['all_attributes']['email']} for x in result],key=lambda x: int(x['client_id'].replace("PTGCLI","")), reverse=False)
            conct.close_connection(client)
 
            return {'statusCode':200,'body':modified_result}
 
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': []}
    def CmsClientBomSearchSuggestion(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            bom_search = data['bom_search']
                   
            results = list(db_con.BOM.find({
                "$or" :[
                {"all_attributes.bom_name": {"$regex": bom_search, "$options": "i"}},
                {"all_attributes.bom_id": {"$regex": bom_search, "$options": "i"}},
                ] },  
            {"_id":0,"pk_id": 1, "all_attributes.bom_name": 1,"all_attributes.bom_id":1}))
            if results:
                formatted_results = [[doc['pk_id'], doc['all_attributes']['bom_name']] for doc in results]
                conct.close_connection(client)
 
                return {"statusCode": 200, "body": formatted_results}
            else:
                conct.close_connection(client)
                return {"statusCode":400,'body':"BOM not found"}
        except Exception as err:
            exc_type, _, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'error': 'Bad Request (check data)'}
        
    def get_bom_details(data, bom_id):
        env_type = data['env_type']
        db_conct = conct.get_conn(env_type)
        db_con = db_conct['db']
        client = db_conct['client']
        bom_result = list(db_con.BOM.find({"pk_id": bom_id},{"_id":0,"all_attributes":1}))
        if bom_result:
            conct.close_connection(client)
            return bom_result[0]['all_attributes']
        else:
            conct.close_connection(client)
            return {}
 
    def cmsClientGetInnerDetailsById(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            client_id = data["client_id"]
            result = list(db_con.Clients.find({"pk_id": client_id},{"_id":0,"all_attributes":1,"sk_timeStamp":1}))
            if result:
                part_info = result[0]['all_attributes']
                part_info["created_date"] = result[0]['sk_timeStamp'][:10]
                docs = [{"content":value,'document_name':value.split("/")[-1]} for key,value in part_info['documents'].items()]
                # base_url="http://localhost:8000"  
                part_info['documents'] = file_uploads.get_file(docs)
                if "orders" in part_info:  
                    part_info["orders"] = dict(sorted(part_info["orders"].items(), key=lambda x: x[1]["bom_id"]))
                boms = part_info["boms"]
                bom_details = {bom_key: Clients.get_bom_details(data,bom_value['bom_id']) for bom_key, bom_value in boms.items()}
                # return bom_details
                bom_details = {}    
                for bom_key, bom_value in boms.items():
                    bom_id = bom_value['bom_id']
                    bom_details = Clients.get_bom_details(data,bom_id)
                    bom_value["bom_name"] = bom_details["bom_name"]
                    bom_value["created_date"]=bom_details["created_time"]
                   
                    bom_value["total_categories"] = bom_details["total_categories"]
                    bom_value["total_components"] = bom_details["total_components"]
                conct.close_connection(client)
 
                return {"statusCode": 200, "body": part_info}
            else:
                conct.close_connection(client)
                return {"statusCode": 400, "body": "something went wrong, please try agian"}
        except Exception as err:
            exc_type, _, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'error': 'Bad Request (check data)'}
        
    def cmsAssignClientInBom(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            gsipk_table = 'ClientAssign'
            outward_id = data['outward_id']
            client_id = data['client_id']
            client_name = data['client_name']
            result = list(db_con.ClientAssign.find({
                "gsisk_id": outward_id,
                "all_attributes.client_id": client_id,
                "all_attributes.client_name": client_name
            }))
            result1 = list(db_con.FinalProduct.find({"gsisk_id": outward_id}))
            documents = data.get('documents', [])
            doc = {}
            for idx, docs in enumerate(documents):
                image_path = file_uploads.upload_file("ClientAssign", "PtgCms" + env_type, "",
                                                      "delivery_challan" + str(idx + 1),
                                                      docs["doc_name"], docs['doc_body'])
                doc[docs["doc_name"]] = image_path
            kits_data = data.get('kits', {})
            common_batches2 = {}
            for batch_key, batch_values in kits_data.items():
                common_batches2[batch_key] = {}
                for idx, kit_data in enumerate(batch_values):
                    product_key = f"product{idx + 1}"
                    common_batches2[batch_key][product_key] = {
                        "final_product_kit_id": kit_data["final_product_kit_id"],
                        "pcba_id": kit_data["pcba_id"],
                        "e_sim_id": kit_data["e_sim_id"],
                        "som_id_imei_id": kit_data["som_id_imei_id"],
                        # "unit_no": kit_data["unit_no"],
                        "product_id": kit_data["product_id"],
                        "display_number": kit_data["display_number"],
                        "e_sim_no": kit_data["e_sim_no"],
                        "als_id": kit_data["als_id"],
                        "date_of_ems": kit_data['date_of_ems'],
                        "ict": kit_data['ict'],
                        "fct": kit_data['fct'],
                        "eol": kit_data['eol'],
                        "date_of_eol": kit_data['date_of_eol'],
                        "eol_document": kit_data['eol_document'],
                        "status": "Dispatched"
                    }
            if result:
                sk_timeStamp = datetime.now().isoformat()
                existing_record = result[0]
                all_attributes = existing_record['all_attributes']
                existing_kits = all_attributes.get('kits', {})
                for batch_key in common_batches2:
                    if batch_key in existing_kits:
                        for idx, (product_key, kit_data) in enumerate(common_batches2[batch_key].items()):
                            if not any(
                                    kit['pcba_id'] == kit_data['pcba_id'] for kit in existing_kits[batch_key].values()):
                                next_product_num = len(existing_kits[batch_key]) + 1
                                enumerated_product_key = f"product{next_product_num}"
                                existing_kits[batch_key][enumerated_product_key] = kit_data
                    else:
                        existing_kits[batch_key] = common_batches2[batch_key]
                if 'delivery_challan' in all_attributes:
                    all_attributes['delivery_challan'].update(doc)
                else:
                    all_attributes['delivery_challan'] = doc
                all_attributes.update({
                    'kits': existing_kits,
                    'sender_name': data['sender_name'],
                    'receiver_name': data['receiver_name'],
                    'receiver_contact': data['receiver_contact_num'],
                    'contact_details': data['contact_details'],
                    'ship_to': data['ship_to'],
                    'qty': data['qty']
                })
                resp = db_con.ClientAssign.update_one(
                    {"pk_id": existing_record['pk_id']},
                    {"$set": {"all_attributes": all_attributes}}
                )
                if result1:
                    resp = db_con.FinalProduct.update_one(
                        {"pk_id": existing_record['pk_id']},
                        {"$set": {"all_attributes": all_attributes}}
                    )
                fp = db_con.FinalProduct.find_one({'all_attributes.outward_id': data['outward_id']})
                if fp:
                    for batch_key, batch_value in fp['all_attributes']['kits'].items():
                        if batch_key.startswith('Final_product_batch'):
                            for product_key, product_value in batch_value.items():
                                if product_key.startswith('product'):
                                    # for kit_data in data['kits'][batch_key]:
                                    for kit_data in data['kits'].get(batch_key, []):
                                        if kit_data['pcba_id'] == product_value['pcba_id']:
                                            product_value['product_status'] = 'Dispatched'
                    resp = db_con.FinalProduct.update_one(
                        {"pk_id": fp['pk_id']},
                        {"$set": {"all_attributes.kits": fp['all_attributes']['kits']}}
                    )
                return {'statusCode': 200, 'body': 'Record updated successfully'}
            else:
                sk_timeStamp = datetime.now().isoformat()
                all_attributes = {
                    'bom_id': result1[0]['all_attributes']['bom_id'] if result1 else None,
                    'outward_id': outward_id,
                    'client_id': client_id,
                    'client_name': client_name,
                    'sender_name': data['sender_name'],
                    'receiver_name': data['receiver_name'],
                    'receiver_contact': data['receiver_contact_num'],
                    'contact_details': data['contact_details'],
                    'ship_to': data['ship_to'],
                    'orderId': result1[0]['all_attributes']['orderId'] if result1 else None,
                    'order_date': '',
                    'status': '',
                    'quantity': result1[0]['all_attributes']['quantity'] if result1 else None,
                    'qty': result1[0]['all_attributes'].get('qty', ''),
                    'against_po': data.get('against_po', ''),
                    'delivery_end_date': data.get('ded', ''),
                    'delivery_challan': doc,
                    'kits': common_batches2
                }
                for batch_key in common_batches2:
                    for idx, (product_key, kit_data) in enumerate(common_batches2[batch_key].items()):
                        enumerated_product_key = f"product{idx + 1}"
                        all_attributes['kits'][batch_key][enumerated_product_key] = kit_data
                item = {
                    "pk_id": outward_id + "_AC",
                    "sk_timeStamp": sk_timeStamp,
                    "all_attributes": all_attributes,
                    "gsipk_table": gsipk_table,
                    "gsisk_id": outward_id
                }
                response = db_con.ClientAssign.insert_one(item)
                fp = db_con.FinalProduct.find_one({'all_attributes.outward_id': data['outward_id']})
                if fp:
                    for batch_key, batch_value in fp['all_attributes']['kits'].items():
                        if batch_key.startswith('Final_product_batch'):
                            for product_key, product_value in batch_value.items():
                                if product_key.startswith('product'):
                                    # for kit_data in data['kits'][batch_key]:
                                    for kit_data in data['kits'].get(batch_key, []):
                                        if kit_data['pcba_id'] == product_value['pcba_id']:
                                            product_value['product_status'] = 'Dispatched'
                    resp = db_con.FinalProduct.update_one(
                        {"pk_id": fp['pk_id']},
                        {"$set": {"all_attributes.kits": fp['all_attributes']['kits']}}
                    )
                return {'statusCode': 200, 'body': "Assigned to Client Successfully"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check data)'}
        
    def cmsClientAssignDoc(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            fp = db_con.ClientAssign.find_one({'all_attributes.outward_id': data['outward_id']})
            delivery_challan = fp['all_attributes'].get('delivery_challan',{})
            if delivery_challan:
                delivery_challan_urls = []
                for doc_name, url in delivery_challan.items():
                    delivery_challan_urls.append({'doc_name': doc_name, 'doc_url': url})
                return {'statusCode': 200, 'body': delivery_challan_urls}
            else:
                return {'statusCode': 200, 'body': 'Delivery challan not available'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'Bad Request (check data)'}

    # def cmsAssignClientInBom(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
    #         gsipk_table = 'ClientAssign'
    #         outward_id = data['outward_id']
    #         client_id = data['client_id']
    #         client_name = data['client_name']
    #         result = list(db_con.ClientAssign.find({"gsisk_id": outward_id, "all_attributes.client_id": client_id,
    #                                                 "all_attributes.client_name": client_name}))
    #         result1 = list(db_con.FinalProduct.find({"gsisk_id": outward_id, "all_attributes.client_id": client_id,
    #                                                  "all_attributes.client_name": client_name}))
    #         documents = data.get('documents', [])
    #         doc = {}
    #         for idx, docs in enumerate(documents):
    #             image_path = file_uploads.upload_file("ClientAssign", "PtgCms" + env_type, "",
    #                                                   "delivery_challan" + str(idx + 1),
    #                                                   docs["doc_name"], docs['doc_body'])
    #             doc[docs["doc_name"]] = image_path

    #         # Initialize kits structure
    #         kits_data = data.get('kits', {})
    #         common_batches2 = {}
    #         for batch_key, batch_values in kits_data.items():
    #             common_batches2[batch_key] = {}
    #             for idx, kit_data in enumerate(batch_values):
    #                 product_key = f"product{idx + 1}"
    #                 common_batches2[batch_key][product_key] = {
    #                     "final_product_kit_id": kit_data["final_product_kit_id"],
    #                     "pcba_id": kit_data["svic_pcba"],
    #                     "e_sim_id": kit_data["E_sim_id"],
    #                     "som_id&imei_id": kit_data["som_id"],
    #                     "unit_no": kit_data["unit_no"],
    #                     "display_number": kit_data["display_num"],
    #                     "e_sim_no": kit_data["E_sim_no"],
    #                     "als_id": kit_data["alis_pcba"],
    #                     "date_of_ems": kit_data['date_of_ems'],
    #                     "ict": kit_data['ict'],
    #                     "fct": kit_data['fct'],
    #                     "eol": kit_data['eol'],
    #                     "date_of_eol": kit_data['date_of_eol'],
    #                     "eol_document": kit_data['eol_document'],
    #                     "status": kit_data['status']
    #                 }

    #         all_attributes1 = result1[0]['all_attributes'] if result1 else None

    #         if result:
    #             sk_timeStamp = (datetime.now()).isoformat()
    #             existing_record = result[0]
    #             all_attributes = existing_record['all_attributes']
    #             existing_kits = all_attributes.get('kits', {})

    #             # Update existing kits with new kits data
    #             for batch_key in common_batches2:
    #                 if batch_key in existing_kits:
    #                     next_product_num = len(existing_kits[batch_key]) + 1
    #                     for idx, kit_data in enumerate(common_batches2[batch_key].values()):
    #                         product_key = f"product{next_product_num + idx}"
    #                         existing_kits[batch_key][product_key] = kit_data
    #                 else:
    #                     existing_kits[batch_key] = common_batches2[batch_key]

    #             # Update delivery challan documents
    #             if 'delivery_challan' in all_attributes:
    #                 all_attributes['delivery_challan'].update(doc)
    #             else:
    #                 all_attributes['delivery_challan'] = doc

    #             # Update other attributes
    #             all_attributes['kits'] = existing_kits
    #             all_attributes['sender_name'] = data['sender_name']
    #             all_attributes['receiver_name'] = data['receiver_name']
    #             all_attributes['receiver_contact'] = data['receiver_contact_num']
    #             all_attributes['contact_details'] = data['contact_details']
    #             all_attributes['ship_to'] = data['ship_to']

    #             resp = db_con.ClientAssign.update_one(
    #                 {"pk_id": existing_record['pk_id']},
    #                 {"$set": {"all_attributes": all_attributes}}
    #             )
    #             if result1:
    #                 resp = db_con.FinalProduct.update_one(
    #                     {"pk_id": existing_record['pk_id']},
    #                     {"$set": {"all_attributes": all_attributes}}
    #                 )
    #             return {'statusCode': 200, 'body': 'Record updated successfully'}
    #         else:
    #             sk_timeStamp = (datetime.now()).isoformat()
    #             all_attributes = {
    #                 'bom_id': result1[0]['all_attributes']['bom_id'] if result1 else None,
    #                 'outward_id': outward_id,
    #                 'client_id': client_id,
    #                 'client_name': client_name,
    #                 'sender_name': data['sender_name'],
    #                 'receiver_name': data['receiver_name'],
    #                 'receiver_contact': data['receiver_contact_num'],
    #                 'contact_details': data['contact_details'],
    #                 'ship_to': data['ship_to'],
    #                 'orderId': result1[0]['all_attributes']['orderId'] if result1 else None,
    #                 'order_date': '',
    #                 'status': '',
    #                 'quantity': result1[0]['all_attributes']['quantity'] if result1 else None,
    #                 'qty': result1[0]['all_attributes']['qty'] if result1 else None,
    #                 'against_po': data.get('against_po', ''),
    #                 'delivery_end_date': data.get('ded', ''),
    #                 'delivery_challan': doc,
    #                 'kits': common_batches2
    #             }
    #             item = {
    #                 "pk_id": outward_id + "_AC",
    #                 "sk_timeStamp": sk_timeStamp,
    #                 "all_attributes": all_attributes,
    #                 "gsipk_table": gsipk_table,
    #                 "gsisk_id": outward_id
    #             }
    #             response = db_con.ClientAssign.insert_one(item)
    #             return {'statusCode': 200, 'body': "Assigned to Client Successfully"}
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'Bad Request (check data)'}
# import json

# from datetime import datetime, timedelta
# import base64
# from db_connection import db_connection_manage
# import sys
# import binascii

# import os
# from utils import file_uploads

# upl = file_uploads()

# conct = db_connection_manage()


# # #print(conct)
# class Clients():
#     def CmsClientCreate(request_body):
#         try:
#             data = request_body
#             # #print(data)
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             sk_timeStamp = (datetime.now() + timedelta(hours=5, minutes=30)).isoformat()
#             result = list(db_con.Clients.find({}))
#             all_bom_ids = []
#             for item in result:
#                 all_attributes = item.get("all_attributes", {})
#                 boms = all_attributes.get("boms", {})
#                 # #print(boms)

#                 bom1 = boms.get("bom1", {})

#                 # #print(bom1)
#                 bom_id = bom1.get("bom_id", {})
#                 # #print(bom_id)
#                 if bom_id:
#                     all_bom_ids.append(bom_id)
#             data_bom_ids = [bom.get("bom_id", "") for bom in data.get("boms", [])]
#             if any(bom_id in all_bom_ids for bom_id in data_bom_ids):
#                 conct.close_connection(client)
#                 return {"statusCode": 400, "body": "BOM ID(s) already added for this client"}
#             if result and any(1 for item in result if
#                               item["all_attributes"]["client_name"].lower() == data['client_name'].lower()):
#                 conct.close_connection(client)
#                 return {"statusCode": 400, "body": "Client Already exists"}
#             client_name = data["client_name"].strip().title()
#             id_key = 'client_id'
#             vp_id = "01"
#             if result:
#                 vp_ids = sorted([res["all_attributes"][id_key][6:] for res in result], reverse=True)
#                 vp_id = (str(((2 - len(str(int(vp_ids[0]) + 1)))) * "0") + str(int(vp_ids[0]) + 1) if len(
#                     str(int(vp_ids[0]))) == 1 else str(int(vp_ids[0]) + 1))
#             all_attributes = {}
#             all_attributes[id_key] = "PTG" + id_key[0:3].upper() + vp_id
#             documents = data["documents"]
#             all_attributes["documents"] = {}
#             all_attributes["orders"] = {}
#             boms = {
#                 f"bom{inx + 1}": {
#                     "bom_id": i['bom_id'],
#                     "moq": i['moq'],
#                     "lead_time": i["lead_time"],
#                     "warranty": i["warranty"],
#                     "price": i["price"],
#                     "gst": i["gst"]
#                 }
#                 for inx, i in enumerate(data["boms"])
#             }
#             # #print(data['documents'])
#             if any(document['content'] == '' for document in data['documents']):
#                 conct.close_connection(client)
#                 return {"statusCode": 400, "body": "Please Upload Valid Document"}

#             for inx, docs in enumerate(documents):
#                 # #print(docs)
#                 # #print(inx)

#                 document_body = docs['content']
#                 document_name = (
#                     "".join(letter if letter.isalnum() or letter == '.' else '' for letter in docs['document_name']))
#                 document_name = document_name + (".pdf" if not document_name.endswith(".pdf") else "")
#                 destination_filename = f"{document_name}"
#                 # #print(destination_filename)
#                 upload_image = file_uploads.upload_file("Clients", "PtgCms" + env_type, str(vp_id),
#                                                         destination_filename, document_body)
#                 # a.append(upload_image)
#                 # #print(upload_image)

#                 if not upload_image:
#                     conct.close_connection(client)
#                     return {"statusCode": 500, "body": "Failed while uploading documents"}

#                 all_attributes["documents"][f'document{inx + 1}'] = upload_image
#             all_attributes["client_name"] = client_name
#             all_attributes["client_location"] = data["client_location"]
#             all_attributes["email"] = data["email"]
#             all_attributes["contact_number"] = data["contact_number"]
#             all_attributes["terms_and_conditions"] = data["terms_and_conditions"]
#             all_attributes["payment_terms"] = data["payment_terms"]
#             all_attributes["client_status"] = "Active"
#             all_attributes["types_of_boms"] = str(len(boms))
#             all_attributes['boms'] = boms
#             for bom in data["boms"]:
#                 bom_id = bom.get("bom_id", "")

#             item = {
#                 "pk_id": "PTG" + id_key[0:3].upper() + vp_id,
#                 "sk_timeStamp": sk_timeStamp,
#                 "all_attributes": all_attributes,
#                 "gsipk_table": "Clients",
#                 "gsipk_id": "--",
#                 "lsi_key": "Active",
#             }

#             db_con.Clients.insert_one(item)
#             conct.close_connection(client)
#             return {"statusCode": 200, "body": "Client Created Successfully"}
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'body': 'Internal server error'}

#     def cmsClientEditDetails(request_body):
#         # try:
#         data = request_body
#         env_type = data['env_type']
#         db_conct = conct.get_conn(env_type)
#         db_con = db_conct['db']
#         client = db_conct['client']
#         result = list(db_con.Clients.find({},
#                                           {'_id': 0, 'all_attributes.client_name': 1, 'all_attributes.client_status': 1,
#                                            'all_attributes.documents': 1, 'all_attributes.client_id': 1,
#                                            'all_attributes.orders': 1, 'pk_id': 1, 'sk_timeStamp': 1}))
#         client_data = [item for item in result if item['pk_id'] == data['client_id']]
#         boms = []
#         if any(document['content'] == '' for document in data['documents']):
#             conct.close_connection(client)
#             return {"statusCode": 400, "body": "Please Upload Valid Document"}
#         if len(data['boms']):
#             boms = sorted(data['boms'], key=lambda x: int(x['bom_id'].replace("PTGBOM", "")))
#         if any(1 for item in result if
#                item['all_attributes']["client_id"] != data['client_id'] and item['all_attributes']["client_name"] ==
#                data['client_name']):
#             conct.close_connection(client)
#             return {'statusCode': 400, 'body': f"Client name {data['client_name']} already exists in database"}

#         if result and any(1 for item in result if item['all_attributes']["client_id"] == data['client_id']):
#             # return result[0]['all_attributes']['documents']
#             all_attributes = {key: data[key] for key in data.keys() if key not in ["env_type", "documents"]}
#             all_attributes['documents'] = {}
#             for inx, docs in enumerate(data['documents']):
#                 key = f"document{inx + 1}"
#                 document_body = docs['content']
#                 if not document_body.endswith(".pdf"):
#                     document_64_decode = base64.b64decode(document_body)
#                     document_name = ("".join(
#                         letter if letter.isalnum() or letter == '.' else '' for letter in docs['document_name']))
#                     document_name = document_name + (".pdf" if not document_name.endswith(".pdf") else "")
#                     file_path = os.path.join("cms-images", "client_edit", data['client_id'], document_name)
#                     # Create directories if they don't exist
#                     os.makedirs(os.path.dirname(file_path), exist_ok=True)
#                     # Open the file in binary write mode
#                     with open(file_path, 'wb') as filewr:
#                         filewr.write(document_64_decode)
#                     all_attributes['documents'][key] = f"cms-images/client_data/{data['client_id']}/{document_name}"
#                 else:
#                     all_attributes['documents'][key] = document_body
#             all_attributes['boms'] = {f"bom{inx + 1}": item for inx, item in enumerate(boms)}
#             all_attributes['types_of_boms'] = str(len(boms))
#             # all_attributes['created_date'] = client[0]['sk_timeStamp'][:10]
#             all_attributes['client_status'] = client_data[0]['all_attributes']['client_status']
#             if 'orders' in data:
#                 all_attributes['orders'] = data['orders']
#             # all_attributes = create_nested_dicts(all_attributes)
#             if not 'orders' in all_attributes:
#                 all_attributes['orders'] = client_data[0]['all_attributes']['orders']

#             key = {"pk_id": client_data[0]['pk_id'], "sk_timeStamp": client_data[0]['sk_timeStamp']}
#             update_query = {"$set": {"all_attributes": all_attributes}}
#             result = db_con.Clients.update_one(key, update_query)
#             conct.close_connection(client)

#             if result:
#                 conct.close_connection(client)
#                 return {'statuscode': 200, 'body': "client details updated successfully"}
#             else:
#                 conct.close_connection(client)
#                 return {'statuscode': 400, 'body': "Failed while updating client"}
#         else:
#             conct.close_connection(client)
#             return {'statusCode': 400, 'body': "Failed to fetch record for given client_id"}
#         # except Exception as err:
#         #     exc_type, exc_obj, tb = sys.exc_info()
#         # f_name = tb.tb_frame.f_code.co_filename
#         # line_no = tb.tb_lineno
#         # #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#         # return {'statusCode': 400,'body': 'Bad Request(check data)'}

#     def CmsClientSearchAddBom(request_body):
#         data = request_body
#         env_type = data['env_type']
#         db_conct = conct.get_conn(env_type)
#         db_con = db_conct['db']
#         client = db_conct['client']
#         search_query = data['bom_name']
#         if not search_query:
#             conct.close_connection(client)
#             return {'statusCode': 404, 'body': "No search parameters passed"}

#         env_type = data["env_type"]
#         bom_result = list(db_con.BOM.find(
#             {
#                 '$or': [
#                     {'pk_id': search_query},
#                     {'all_attributes.bom_name': search_query}
#                 ]
#             },
#             {'_id': 0, 'all_attributes': 1, 'pk_id': 1}
#         ))
#         client_result = list(db_con.Clients.find({}, {'_id': 0, 'all_attributes.boms': 1}))
#         bom_ids = [k['bom_id'] for i in client_result for j, k in i['all_attributes']['boms'].items()]
#         if data['bom_name'] in bom_ids:
#             conct.close_connection(client)
#             return {'statusCode': 400, 'body': 'this bom_id is alreday added'}
#         if bom_result:

#             response_dict = {key: value for key, value in bom_result[0]['all_attributes'].items()}
#             conct.close_connection(client)

#             return {
#                 "statusCode": 200,
#                 "body": {
#                     "bom_id": response_dict['bom_id'],
#                     "total_categories": response_dict['total_categories'],
#                     "created_time": response_dict['created_time'],
#                     "total_components": response_dict['total_components'],
#                     "description": response_dict['description'],
#                     "bom_name": response_dict['bom_name']
#                 }
#             }

#         else:
#             conct.close_connection(client)
#             return {
#                 'statuscode': 404,
#                 'body': "No data"
#             }

#     def CmsClientsUploadPo(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             data_po_information = data["po_information"]
#             client_id = data['client_id']
#             po_information = {f"po{inx + 1}": value for inx, value in enumerate(data["po_information"])}
#             # result_client=list(db_con.Clients.find({},{'_id':0,'all_attributes.boms':1}))
#             result_client = list(db_con.Clients.find(
#                 {
#                     'all_attributes.client_id': client_id
#                 },
#                 {'_id': 0, 'all_attributes': 1, 'sk_timeStamp': 1}
#             ))
#             result_bom = list(db_con.BOM.find({}, {'_id': 0, 'pk_id': 1}))
#             bom_data = [i['bom_id'] for i in data['po_information']]
#             pk_ids = [i["pk_id"] for i in result_bom]
#             mismatched_bom_ids = [bom_id for bom_id in bom_data if bom_id not in pk_ids]
#             # Display pop-up if mismatches found
#             if mismatched_bom_ids:
#                 conct.close_connection(client)
#                 return {'statusCode': 400, 'body': "Please give existing BOM_ID"}
#             a = [i['po_id'] for i in data['po_information']]
#             duplicates = ', '.join(po_id for po_id in set(a) if a.count(po_id) > 1)
#             if duplicates:
#                 conct.close_connection(client)
#                 return {'statusCode': 400, 'body': 'Duplicates found for po_id ' + duplicates}
#             b = [i['bom_id'] for i in data['po_information']]
#             duplicates1 = ', '.join(po_id for po_id in set(b) if b.count(po_id) > 1)
#             if duplicates1:
#                 conct.close_connection(client)
#                 return {'statusCode': 400, 'body': 'Duplicates found for bom_id' + duplicates1}
#             if result_client:
#                 client_details = result_client[0]
#                 # orders=client_details["all_attributes"]["M"]["orders"]
#                 e = [j['po_id'] for i, j in client_details['all_attributes']['orders'].items()] + [i['po_id'] for i in
#                                                                                                    data[
#                                                                                                        'po_information']]
#                 duplicates_po_id = ', '.join(po_id for po_id in set(e) if e.count(po_id) > 1)
#                 if duplicates_po_id:
#                     conct.close_connection(client)
#                     return {'statusCode': 400, 'body': 'Duplicates found for po_id' + duplicates_po_id}
#                 e1 = [j['bom_id'] for i, j in client_details['all_attributes']['orders'].items()] + [i['bom_id'] for i
#                                                                                                      in data[
#                                                                                                          'po_information']]
#                 duplicates_bom_id = ', '.join(bom_id for bom_id in set(e1) if e1.count(bom_id) > 1)
#                 if duplicates_bom_id:
#                     conct.close_connection(client)
#                     return {'statusCode': 400, 'body': 'Duplicates found for bom_id' + duplicates_bom_id}

#                 sk_timeStamp = client_details["sk_timeStamp"]
#                 if "orders" in client_details["all_attributes"]:
#                     # Assuming you have existing data in client_details["all_attributes"]["M"]["orders"]["M"]
#                     po_information = client_details["all_attributes"]["orders"]
#                     max_order_key = max(po_information.keys(), default="po0", key=lambda x: int(x.replace("po", "")))
#                     starting_index = int(max_order_key.replace("po", "")) + 1 if max_order_key != "po0" else 1
#                     new_po_information = {
#                         f"po{starting_index + i}": {key: po[key] for key in po} for i, po in
#                         enumerate(data["po_information"])
#                     }
#                     po_information.update(new_po_information)

#                 else:
#                     # If "orders" does not exist, set it to the new items
#                     client_details["all_attributes"]["orders"] = po_information
#                 key = {
#                     "pk_id": client_details["all_attributes"]["client_id"],
#                     "sk_timeStamp": sk_timeStamp
#                 }
#                 # key = {"pk_id": client[0]['pk_id'],"sk_timeStamp": client[0]['sk_timeStamp']}

#                 update_query = {"$set": {"all_attributes.orders": po_information}}
#                 result = db_con.Clients.update_one(key, update_query)
#                 conct.close_connection(client)

#                 return {"statusCode": 200, "body": f"Successfully uploaded PO for {data['client_id']}"}
#             else:
#                 conct.close_connection(client)
#                 return {"statusCode": 400, "body": "Client not found"}

#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'body': []}

#     def cmsClientsGetAll(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             query = {'all_attributes.client_status': data['status']}
#             req_attributes = {'_id': 0, 'all_attributes.client_id': 1, 'all_attributes.client_name': 1,
#                               'all_attributes.contact_number': 1, 'all_attributes.types_of_boms': 1,
#                               'all_attributes.email': 1}
#             result = list(db_con.Clients.find(query, req_attributes))
#             modified_result = sorted([{'client_id': x['all_attributes']['client_id'],
#                                        'client_name': x['all_attributes']['client_name'],
#                                        'contact_number': x['all_attributes']['contact_number'],
#                                        'types_of_boms': x['all_attributes']['types_of_boms'],
#                                        'email': x['all_attributes']['email']} for x in result],
#                                      key=lambda x: int(x['client_id'].replace("PTGCLI", "")), reverse=False)
#             conct.close_connection(client)

#             return {'statusCode': 200, 'body': modified_result}

#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'body': []}

#     def CmsClientBomSearchSuggestion(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             bom_search = data['bom_search']

#             results = list(db_con.BOM.find({
#                 "$or": [
#                     {"all_attributes.bom_name": {"$regex": bom_search, "$options": "i"}},
#                     {"all_attributes.bom_id": {"$regex": bom_search, "$options": "i"}},
#                 ]},
#                 {"_id": 0, "pk_id": 1, "all_attributes.bom_name": 1, "all_attributes.bom_id": 1}))
#             if results:
#                 formatted_results = [[doc['pk_id'], doc['all_attributes']['bom_name']] for doc in results]
#                 conct.close_connection(client)

#                 return {"statusCode": 200, "body": formatted_results}
#             else:
#                 conct.close_connection(client)
#                 return {"statuscode": 400, 'body': "BOM not found"}
#         except Exception as err:
#             exc_type, _, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'error': 'Bad Request (check data)'}

#     def get_bom_details(data, bom_id):
#         env_type = data['env_type']
#         db_conct = conct.get_conn(env_type)
#         db_con = db_conct['db']
#         client = db_conct['client']
#         bom_result = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "all_attributes": 1}))
#         if bom_result:
#             conct.close_connection(client)
#             return bom_result[0]['all_attributes']
#         else:
#             conct.close_connection(client)
#             return {}

#     def cmsClientGetInnerDetailsById(request_body):
#         # try:
#         data = request_body
#         env_type = data['env_type']
#         db_conct = conct.get_conn(env_type)
#         db_con = db_conct['db']
#         client = db_conct['client']
#         client_id = data["client_id"]
#         result = list(db_con.Clients.find({"pk_id": client_id}, {"_id": 0, "all_attributes": 1, "sk_timeStamp": 1}))
#         if result:
#             part_info = result[0]['all_attributes']
#             part_info["created_date"] = result[0]['sk_timeStamp'][:10]
#             docs = [{"content": value, 'document_name': value.split("/")[-1]} for key, value in
#                     part_info['documents'].items()]
#             # base_url="http://localhost:8000"
#             part_info['documents'] = file_uploads.get_file(docs)
#             if "orders" in part_info:
#                 part_info["orders"] = dict(sorted(part_info["orders"].items(), key=lambda x: x[1]["bom_id"]))
#             boms = part_info["boms"]
#             bom_details = {bom_key: Clients.get_bom_details(data, bom_value['bom_id']) for bom_key, bom_value in
#                            boms.items()}
#             # return bom_details
#             bom_details = {}
#             for bom_key, bom_value in boms.items():
#                 bom_id = bom_value['bom_id']
#                 bom_details = Clients.get_bom_details(data, bom_id)
#                 bom_value["bom_name"] = bom_details["bom_name"]
#                 bom_value["created_date"] = bom_details["created_time"]

#                 bom_value["total_categories"] = bom_details["total_categories"]
#                 bom_value["total_components"] = bom_details["total_components"]
#             conct.close_connection(client)

#             return {"statusCode": 200, "body": part_info}
#         else:
#             conct.close_connection(client)
#             return {"statusCode": 400, "body": "something went wrong, please try agian"}
    # except Exception as err:
    #     exc_type, _, tb = sys.exc_info()
    #     f_name = tb.tb_frame.f_code.co_filename
    #     line_no = tb.tb_lineno
    #     #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #     return {'statusCode': 400, 'error': 'Bad Request (check data)'}
# import json
# from datetime import datetime, timedelta
# import base64
# from db_connection import db_connection_manage
# import sys
# import binascii
# import os
# from utils import file_uploads
#
# upl = file_uploads()
#
# conct = db_connection_manage()
#
#
# # #print(conct)
# class Clients():
#     def CmsClientCreate(request_body):
#         try:
#             data = request_body
#             # #print(data)
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             sk_timeStamp = (datetime.now() + timedelta(hours=5, minutes=30)).isoformat()
#             result = list(db_con.Clients.find({}))
#             all_bom_ids = []
#             for item in result:
#                 all_attributes = item.get("all_attributes", {})
#                 boms = all_attributes.get("boms", {})
#                 # #print(boms)
#
#                 bom1 = boms.get("bom1", {})
#
#                 # #print(bom1)
#                 bom_id = bom1.get("bom_id", {})
#                 # #print(bom_id)
#                 if bom_id:
#                     all_bom_ids.append(bom_id)
#             data_bom_ids = [bom.get("bom_id", "") for bom in data.get("boms", [])]
#             if any(bom_id in all_bom_ids for bom_id in data_bom_ids):
#                 conct.close_connection(client)
#                 return {"statusCode": 400, "body": "BOM ID(s) already added for this client"}
#             if result and any(1 for item in result if
#                               item["all_attributes"]["client_name"].lower() == data['client_name'].lower()):
#                 conct.close_connection(client)
#                 return {"statusCode": 400, "body": "Client Already exists"}
#             client_name = data["client_name"].strip().title()
#             id_key = 'client_id'
#             vp_id = "01"
#             if result:
#                 vp_ids = sorted([res["all_attributes"][id_key][6:] for res in result], reverse=True)
#                 vp_id = (str(((2 - len(str(int(vp_ids[0]) + 1)))) * "0") + str(int(vp_ids[0]) + 1) if len(
#                     str(int(vp_ids[0]))) == 1 else str(int(vp_ids[0]) + 1))
#             all_attributes = {}
#             all_attributes[id_key] = "PTG" + id_key[0:3].upper() + vp_id
#             documents = data["documents"]
#             all_attributes["documents"] = {}
#             all_attributes["orders"] = {}
#             boms = {
#                 f"bom{inx + 1}": {
#                     "bom_id": i['bom_id'],
#                     "moq": i['moq'],
#                     "lead_time": i["lead_time"],
#                     "warranty": i["warranty"],
#                     "price": i["price"],
#                     "gst": i["gst"]
#                 }
#                 for inx, i in enumerate(data["boms"])
#             }
#             # #print(data['documents'])
#             if any(document['content'] == '' for document in data['documents']):
#                 conct.close_connection(client)
#                 return {"statusCode": 400, "body": "Please Upload Valid Document"}
#
#             for inx, docs in enumerate(documents):
#                 # #print(docs)
#                 # #print(inx)
#
#                 document_body = docs['content']
#                 document_name = (
#                     "".join(letter if letter.isalnum() or letter == '.' else '' for letter in docs['document_name']))
#                 document_name = document_name + (".pdf" if not document_name.endswith(".pdf") else "")
#                 destination_filename = f"{document_name}"
#                 # #print(destination_filename)
#                 upload_image = file_uploads.upload_file("Clients", "PtgCms" + env_type, str(vp_id),
#                                                         destination_filename, document_body)
#                 # a.append(upload_image)
#                 # #print(upload_image)
#
#                 if not upload_image:
#                     conct.close_connection(client)
#                     return {"statusCode": 500, "body": "Failed while uploading documents"}
#
#                 all_attributes["documents"][f'document{inx + 1}'] = upload_image
#             all_attributes["client_name"] = client_name
#             all_attributes["client_location"] = data["client_location"]
#             all_attributes["email"] = data["email"]
#             all_attributes["contact_number"] = data["contact_number"]
#             all_attributes["terms_and_conditions"] = data["terms_and_conditions"]
#             all_attributes["payment_terms"] = data["payment_terms"]
#             all_attributes["client_status"] = "Active"
#             all_attributes["types_of_boms"] = str(len(boms))
#             all_attributes['boms'] = boms
#             for bom in data["boms"]:
#                 bom_id = bom.get("bom_id", "")
#
#             item = {
#                 "pk_id": "PTG" + id_key[0:3].upper() + vp_id,
#                 "sk_timeStamp": sk_timeStamp,
#                 "all_attributes": all_attributes,
#                 "gsipk_table": "Clients",
#                 "gsipk_id": "--",
#                 "lsi_key": "Active",
#             }
#
#             db_con.Clients.insert_one(item)
#             conct.close_connection(client)
#             return {"statusCode": 200, "body": "Client Created Successfully"}
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'body': 'Internal server error'}
#
#     def cmsClientEditDetails(request_body):
#         # try:
#         data = request_body
#         env_type = data['env_type']
#         db_conct = conct.get_conn(env_type)
#         db_con = db_conct['db']
#         client = db_conct['client']
#         result = list(db_con.Clients.find({},
#                                           {'_id': 0, 'all_attributes.client_name': 1, 'all_attributes.client_status': 1,
#                                            'all_attributes.documents': 1, 'all_attributes.client_id': 1,
#                                            'all_attributes.orders': 1, 'pk_id': 1, 'sk_timeStamp': 1}))
#         client_data = [item for item in result if item['pk_id'] == data['client_id']]
#         boms = []
#         if any(document['content'] == '' for document in data['documents']):
#             conct.close_connection(client)
#             return {"statusCode": 400, "body": "Please Upload Valid Document"}
#         if len(data['boms']):
#             boms = sorted(data['boms'], key=lambda x: int(x['bom_id'].replace("PTGBOM", "")))
#         if any(1 for item in result if
#                item['all_attributes']["client_id"] != data['client_id'] and item['all_attributes']["client_name"] ==
#                data['client_name']):
#             conct.close_connection(client)
#             return {'statusCode': 400, 'body': f"Client name {data['client_name']} already exists in database"}
#
#         if result and any(1 for item in result if item['all_attributes']["client_id"] == data['client_id']):
#             # return result[0]['all_attributes']['documents']
#             all_attributes = {key: data[key] for key in data.keys() if key not in ["env_type", "documents"]}
#             all_attributes['documents'] = {}
#             for inx, docs in enumerate(data['documents']):
#                 key = f"document{inx + 1}"
#                 document_body = docs['content']
#                 if not document_body.endswith(".pdf"):
#                     document_64_decode = base64.b64decode(document_body)
#                     document_name = ("".join(
#                         letter if letter.isalnum() or letter == '.' else '' for letter in docs['document_name']))
#                     document_name = document_name + (".pdf" if not document_name.endswith(".pdf") else "")
#                     file_path = os.path.join("cms-images", "client_edit", data['client_id'], document_name)
#                     # Create directories if they don't exist
#                     os.makedirs(os.path.dirname(file_path), exist_ok=True)
#                     # Open the file in binary write mode
#                     with open(file_path, 'wb') as filewr:
#                         filewr.write(document_64_decode)
#                     all_attributes['documents'][key] = f"cms-images/client_data/{data['client_id']}/{document_name}"
#                 else:
#                     all_attributes['documents'][key] = document_body
#             all_attributes['boms'] = {f"bom{inx + 1}": item for inx, item in enumerate(boms)}
#             all_attributes['types_of_boms'] = str(len(boms))
#             # all_attributes['created_date'] = client[0]['sk_timeStamp'][:10]
#             all_attributes['client_status'] = client_data[0]['all_attributes']['client_status']
#             if 'orders' in data:
#                 all_attributes['orders'] = data['orders']
#             # all_attributes = create_nested_dicts(all_attributes)
#             if not 'orders' in all_attributes:
#                 all_attributes['orders'] = client_data[0]['all_attributes']['orders']
#
#             key = {"pk_id": client_data[0]['pk_id'], "sk_timeStamp": client_data[0]['sk_timeStamp']}
#             update_query = {"$set": {"all_attributes": all_attributes}}
#             result = db_con.Clients.update_one(key, update_query)
#             conct.close_connection(client)
#
#             if result:
#                 conct.close_connection(client)
#                 return {'statuscode': 200, 'body': "client details updated successfully"}
#             else:
#                 conct.close_connection(client)
#                 return {'statuscode': 400, 'body': "Failed while updating client"}
#         else:
#             conct.close_connection(client)
#             return {'statusCode': 400, 'body': "Failed to fetch record for given client_id"}
#         # except Exception as err:
#         #     exc_type, exc_obj, tb = sys.exc_info()
#         # f_name = tb.tb_frame.f_code.co_filename
#         # line_no = tb.tb_lineno
#         # #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#         # return {'statusCode': 400,'body': 'Bad Request(check data)'}
#
#     def CmsClientSearchAddBom(request_body):
#         data = request_body
#         env_type = data['env_type']
#         db_conct = conct.get_conn(env_type)
#         db_con = db_conct['db']
#         client = db_conct['client']
#         search_query = data['bom_name']
#         if not search_query:
#             conct.close_connection(client)
#             return {'statusCode': 404, 'body': "No search parameters passed"}
#
#         env_type = data["env_type"]
#         bom_result = list(db_con.BOM.find(
#             {
#                 '$or': [
#                     {'pk_id': search_query},
#                     {'all_attributes.bom_name': search_query}
#                 ]
#             },
#             {'_id': 0, 'all_attributes': 1, 'pk_id': 1}
#         ))
#         client_result = list(db_con.Clients.find({}, {'_id': 0, 'all_attributes.boms': 1}))
#         bom_ids = [k['bom_id'] for i in client_result for j, k in i['all_attributes']['boms'].items()]
#         if data['bom_name'] in bom_ids:
#             conct.close_connection(client)
#             return {'statusCode': 400, 'body': 'this bom_id is alreday added'}
#         if bom_result:
#
#             response_dict = {key: value for key, value in bom_result[0]['all_attributes'].items()}
#             conct.close_connection(client)
#
#             return {
#                 "statusCode": 200,
#                 "body": {
#                     "bom_id": response_dict['bom_id'],
#                     "total_categories": response_dict['total_categories'],
#                     "created_time": response_dict['created_time'],
#                     "total_components": response_dict['total_components'],
#                     "description": response_dict['description'],
#                     "bom_name": response_dict['bom_name']
#                 }
#             }
#
#         else:
#             conct.close_connection(client)
#             return {
#                 'statuscode': 404,
#                 'body': "No data"
#             }
#
#     def CmsClientsUploadPo(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             data_po_information = data["po_information"]
#             client_id = data['client_id']
#             po_information = {f"po{inx + 1}": value for inx, value in enumerate(data["po_information"])}
#             # result_client=list(db_con.Clients.find({},{'_id':0,'all_attributes.boms':1}))
#             result_client = list(db_con.Clients.find(
#                 {
#                     'all_attributes.client_id': client_id
#                 },
#                 {'_id': 0, 'all_attributes': 1, 'sk_timeStamp': 1}
#             ))
#             result_bom = list(db_con.BOM.find({}, {'_id': 0, 'pk_id': 1}))
#             bom_data = [i['bom_id'] for i in data['po_information']]
#             pk_ids = [i["pk_id"] for i in result_bom]
#             mismatched_bom_ids = [bom_id for bom_id in bom_data if bom_id not in pk_ids]
#             # Display pop-up if mismatches found
#             if mismatched_bom_ids:
#                 conct.close_connection(client)
#                 return {'statusCode': 400, 'body': "Please give existing BOM_ID"}
#             a = [i['po_id'] for i in data['po_information']]
#             duplicates = ', '.join(po_id for po_id in set(a) if a.count(po_id) > 1)
#             if duplicates:
#                 conct.close_connection(client)
#                 return {'statusCode': 400, 'body': 'Duplicates found for po_id ' + duplicates}
#             b = [i['bom_id'] for i in data['po_information']]
#             duplicates1 = ', '.join(po_id for po_id in set(b) if b.count(po_id) > 1)
#             if duplicates1:
#                 conct.close_connection(client)
#                 return {'statusCode': 400, 'body': 'Duplicates found for bom_id' + duplicates1}
#             if result_client:
#                 client_details = result_client[0]
#                 # orders=client_details["all_attributes"]["M"]["orders"]
#                 e = [j['po_id'] for i, j in client_details['all_attributes']['orders'].items()] + [i['po_id'] for i in
#                                                                                                    data[
#                                                                                                        'po_information']]
#                 duplicates_po_id = ', '.join(po_id for po_id in set(e) if e.count(po_id) > 1)
#                 if duplicates_po_id:
#                     conct.close_connection(client)
#                     return {'statusCode': 400, 'body': 'Duplicates found for po_id' + duplicates_po_id}
#                 e1 = [j['bom_id'] for i, j in client_details['all_attributes']['orders'].items()] + [i['bom_id'] for i
#                                                                                                      in data[
#                                                                                                          'po_information']]
#                 duplicates_bom_id = ', '.join(bom_id for bom_id in set(e1) if e1.count(bom_id) > 1)
#                 if duplicates_bom_id:
#                     conct.close_connection(client)
#                     return {'statusCode': 400, 'body': 'Duplicates found for bom_id' + duplicates_bom_id}
#
#                 sk_timeStamp = client_details["sk_timeStamp"]
#                 if "orders" in client_details["all_attributes"]:
#                     # Assuming you have existing data in client_details["all_attributes"]["M"]["orders"]["M"]
#                     po_information = client_details["all_attributes"]["orders"]
#                     max_order_key = max(po_information.keys(), default="po0", key=lambda x: int(x.replace("po", "")))
#                     starting_index = int(max_order_key.replace("po", "")) + 1 if max_order_key != "po0" else 1
#                     new_po_information = {
#                         f"po{starting_index + i}": {key: po[key] for key in po} for i, po in
#                         enumerate(data["po_information"])
#                     }
#                     po_information.update(new_po_information)
#
#                 else:
#                     # If "orders" does not exist, set it to the new items
#                     client_details["all_attributes"]["orders"] = po_information
#                 key = {
#                     "pk_id": client_details["all_attributes"]["client_id"],
#                     "sk_timeStamp": sk_timeStamp
#                 }
#                 # key = {"pk_id": client[0]['pk_id'],"sk_timeStamp": client[0]['sk_timeStamp']}
#
#                 update_query = {"$set": {"all_attributes.orders": po_information}}
#                 result = db_con.Clients.update_one(key, update_query)
#                 conct.close_connection(client)
#
#                 return {"statusCode": 200, "body": f"Successfully uploaded PO for {data['client_id']}"}
#             else:
#                 conct.close_connection(client)
#                 return {"statusCode": 400, "body": "Client not found"}
#
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'body': []}
#
#     def cmsClientsGetAll(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             query = {'all_attributes.client_status': data['status']}
#             req_attributes = {'_id': 0, 'all_attributes.client_id': 1, 'all_attributes.client_name': 1,
#                               'all_attributes.contact_number': 1, 'all_attributes.types_of_boms': 1,
#                               'all_attributes.email': 1}
#             result = list(db_con.Clients.find(query, req_attributes))
#             modified_result = sorted([{'client_id': x['all_attributes']['client_id'],
#                                        'client_name': x['all_attributes']['client_name'],
#                                        'contact_number': x['all_attributes']['contact_number'],
#                                        'types_of_boms': x['all_attributes']['types_of_boms'],
#                                        'email': x['all_attributes']['email']} for x in result],
#                                      key=lambda x: int(x['client_id'].replace("PTGCLI", "")), reverse=False)
#             conct.close_connection(client)
#
#             return {'statusCode': 200, 'body': modified_result}
#
#         except Exception as err:
#             exc_type, exc_obj, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'body': []}
#
#     def CmsClientBomSearchSuggestion(request_body):
#         try:
#             data = request_body
#             env_type = data['env_type']
#             db_conct = conct.get_conn(env_type)
#             db_con = db_conct['db']
#             client = db_conct['client']
#             bom_search = data['bom_search']
#
#             results = list(db_con.BOM.find({
#                 "$or": [
#                     {"all_attributes.bom_name": {"$regex": bom_search, "$options": "i"}},
#                     {"all_attributes.bom_id": {"$regex": bom_search, "$options": "i"}},
#                 ]},
#                 {"_id": 0, "pk_id": 1, "all_attributes.bom_name": 1, "all_attributes.bom_id": 1}))
#             if results:
#                 formatted_results = [[doc['pk_id'], doc['all_attributes']['bom_name']] for doc in results]
#                 conct.close_connection(client)
#
#                 return {"statusCode": 200, "body": formatted_results}
#             else:
#                 conct.close_connection(client)
#                 return {"statuscode": 400, 'body': "BOM not found"}
#         except Exception as err:
#             exc_type, _, tb = sys.exc_info()
#             f_name = tb.tb_frame.f_code.co_filename
#             line_no = tb.tb_lineno
#             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#             return {'statusCode': 400, 'error': 'Bad Request (check data)'}
#
#     def get_bom_details(data, bom_id):
#         env_type = data['env_type']
#         db_conct = conct.get_conn(env_type)
#         db_con = db_conct['db']
#         client = db_conct['client']
#         bom_result = list(db_con.BOM.find({"pk_id": bom_id}, {"_id": 0, "all_attributes": 1}))
#         if bom_result:
#             conct.close_connection(client)
#             return bom_result[0]['all_attributes']
#         else:
#             conct.close_connection(client)
#             return {}
#
#     def cmsClientGetInnerDetailsById(request_body):
#         # try:
#         data = request_body
#         env_type = data['env_type']
#         db_conct = conct.get_conn(env_type)
#         db_con = db_conct['db']
#         client = db_conct['client']
#         client_id = data["client_id"]
#         result = list(db_con.Clients.find({"pk_id": client_id}, {"_id": 0, "all_attributes": 1, "sk_timeStamp": 1}))
#         if result:
#             part_info = result[0]['all_attributes']
#             part_info["created_date"] = result[0]['sk_timeStamp'][:10]
#             docs = [{"content": value, 'document_name': value.split("/")[-1]} for key, value in
#                     part_info['documents'].items()]
#             # base_url="http://localhost:8000"
#             part_info['documents'] = file_uploads.get_file(docs)
#             if "orders" in part_info:
#                 part_info["orders"] = dict(sorted(part_info["orders"].items(), key=lambda x: x[1]["bom_id"]))
#             boms = part_info["boms"]
#             bom_details = {bom_key: Clients.get_bom_details(data, bom_value['bom_id']) for bom_key, bom_value in
#                            boms.items()}
#             # return bom_details
#             bom_details = {}
#             for bom_key, bom_value in boms.items():
#                 bom_id = bom_value['bom_id']
#                 bom_details = Clients.get_bom_details(data, bom_id)
#                 bom_value["bom_name"] = bom_details["bom_name"]
#                 bom_value["created_date"] = bom_details["created_time"]
#
#                 bom_value["total_categories"] = bom_details["total_categories"]
#                 bom_value["total_components"] = bom_details["total_components"]
#             conct.close_connection(client)
#
#             return {"statusCode": 200, "body": part_info}
#         else:
#             conct.close_connection(client)
#             return {"statusCode": 400, "body": "something went wrong, please try agian"}
#     # except Exception as err:
#     #     exc_type, _, tb = sys.exc_info()
#     #     f_name = tb.tb_frame.f_code.co_filename
#     #     line_no = tb.tb_lineno
#     #     #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
#     #     return {'statusCode': 400, 'error': 'Bad Request (check data)'}
#
# # import json
# # from datetime import datetime,timedelta
# # import base64
# # from db_connection import db_connection_manage
# # import sys
# # import binascii
# # import os
# #
# # conct = db_connection_manage()
# # # #print(conct)
# # class Clients():
# #     def CmsClientCreate(request_body):
# #         try:
# #             data = request_body
# #             # #print(data)
# #             env_type = data['env_type']
# #             db_conct = conct.get_conn(env_type)
# #             db_con = db_conct['db']
# #             client = db_conct['client']
# #             sk_timeStamp = (datetime.now() + timedelta(hours=5, minutes=30)).isoformat()
# #             result = list(db_con.Clients.find({}))
# #             all_bom_ids = []
# #             for item in result:
# #                 all_attributes = item.get("all_attributes",{})
# #                 boms = all_attributes.get("boms",{})
# #                 # #print(boms)
# #
# #                 bom1 = boms.get("bom1", {})
# #
# #                 # #print(bom1)
# #                 bom_id = bom1.get("bom_id",{})
# #                 # #print(bom_id)
# #                 if bom_id:
# #                     all_bom_ids.append(bom_id)
# #             data_bom_ids = [bom.get("bom_id", "")for bom in data.get("boms",[])]
# #             if any(bom_id in all_bom_ids for bom_id in data_bom_ids):
# #                 conct.close_connection(client)
# #                 return {"statusCode": 400, "body": "BOM ID(s) already added for this client"}
# #             if result and any(1 for item in result if item["all_attributes"]["client_name"].lower()==data['client_name'].lower()):
# #                 conct.close_connection(client)
# #                 return{"statusCode":400, "body":"Client Already exists"}
# #             client_name = data["client_name"].strip().title()
# #             id_key = 'client_id'
# #             vp_id = "01"
# #             if result:
# #                 vp_ids = sorted([res["all_attributes"][id_key][6:] for res in result], reverse=True)
# #                 vp_id = (str(((2 - len(str(int(vp_ids[0]) + 1)))) * "0") + str(int(vp_ids[0]) + 1) if len(str(int(vp_ids[0]))) == 1 else str(int(vp_ids[0]) + 1))
# #             all_attributes = {}
# #             all_attributes[id_key] = "PTG" +id_key[0:3].upper() + vp_id
# #             documents =  data["documents"]
# #             all_attributes["documents"] = {}
# #             all_attributes["orders"] = {}
# #             boms = {
# #                 f"bom{inx+1}": {
# #                     "bom_id": i['bom_id'],
# #                     "moq": i['moq'],
# #                     "lead_time": i["lead_time"],
# #                     "warranty": i["warranty"],
# #                     "price": i["price"],
# #                     "gst": i["gst"]
# #                 }
# #                 for inx, i in enumerate(data["boms"])
# #                 }
# #             if data['documents']:
# #                 # #print(data['documents'])
# #                 if any(document['content']=='' for document in data['documents']):
# #                     conct.close_connection(client)
# #                     return {"statusCode": 400, "body": "Please Upload Valid Document"}
# #                 for inx, docs in enumerate(documents):
# #                     document_body = docs['content']
# #                     document_64_decode = base64.b64decode(document_body)
# #                     document_name = ("".join(letter if letter.isalnum() or letter == '.' else '' for letter in docs['document_name']))
# #                     document_name = document_name + (".pdf" if not document_name.endswith(".pdf") else "")
# #                     file_path = os.path.join("cms-images", "client", str(vp_id), document_name)
# #                     # Create directories if they don't exist
# #                     os.makedirs(os.path.dirname(file_path), exist_ok=True)
# #                     # Open the file in binary write mode
# #                     with open(file_path, 'wb') as filewr:
# #                         filewr.write(document_64_decode)
# #                     file_up = f"cms-images/client/{vp_id}/{document_name}"
# #                     # # document_result = open(f"cms-images/client/{vp_id}/document.'pdf'", 'wb')
# #                     # document_result.write(document_64_decode)
# #                     # file_up = f"cms-images/client/{vp_id}/document.'pdf'"
# #
# #                 if not file_up:
# #                     conct.close_connection(client)
# #                     return {"statusCode": 500, "body": "Failed while uploading documents"}
# #                 all_attributes["documents"][f'document{inx+1}'] = file_up
# #             all_attributes["client_name"] = client_name
# #             all_attributes["client_location"] = data["client_location"]
# #             all_attributes["email"] = data["email"]
# #             all_attributes["contact_number"] = data["contact_number"]
# #             all_attributes["terms_and_conditions"] = data["terms_and_conditions"]
# #             all_attributes["payment_terms"] = data["payment_terms"]
# #             all_attributes["client_status"] = "Active"
# #             all_attributes["types_of_boms"] = str(len(boms))
# #             all_attributes['boms'] = boms
# #             # #print(all_attributes['boms'])
# #             for bom in data["boms"]:
# #                 bom_id = bom.get("bom_id", "")
# #
# #             item = {
# #                 "pk_id": "PTG" +id_key[0:3].upper() + vp_id,
# #                 "sk_timeStamp": sk_timeStamp,
# #                 "all_attributes": all_attributes,
# #                 "gsipk_table": "Clients",
# #                 "gsipk_id":"--",
# #                 "lsi_key": "Active",
# #             }
# #
# #
# #             db_con.Clients.insert_one(item)
# #             conct.close_connection(client)
# #             return {"statusCode": 200, "body": "Client Created Successfully"}
# #         except Exception as err:
# #             exc_type, exc_obj, tb = sys.exc_info()
# #             f_name = tb.tb_frame.f_code.co_filename
# #             line_no = tb.tb_lineno
# #             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
# #             return {'statusCode': 400,'body': 'Internal server error'}
# #
# #     def cmsClientEditDetails(request_body):
# #         # try:
# #         data = request_body
# #         env_type = data['env_type']
# #         db_conct = conct.get_conn(env_type)
# #         db_con = db_conct['db']
# #         client = db_conct['client']
# #         result = list(db_con.Clients.find({},{'_id':0,'all_attributes.client_name':1,'all_attributes.client_status':1,'all_attributes.documents':1,'all_attributes.client_id':1,'all_attributes.orders':1,'pk_id':1,'sk_timeStamp':1}))
# #         client_data = [item for item in result if item['pk_id']==data['client_id']]
# #         boms = []
# #         if any(document['content']=='' for document in data['documents']):
# #             conct.close_connection(client)
# #             return {"statusCode": 400, "body": "Please Upload Valid Document"}
# #         if len(data['boms']):
# #             boms = sorted(data['boms'], key=lambda x : int(x['bom_id'].replace("PTGBOM","")))
# #         if any(1 for item in result if item['all_attributes']["client_id"]!=data['client_id'] and item['all_attributes']["client_name"]==data['client_name']):
# #             conct.close_connection(client)
# #             return {'statusCode': 400,'body':f"Client name {data['client_name']} already exists in database"}
# #
# #         if result and any(1 for item in result if item['all_attributes']["client_id"]==data['client_id']):
# #             # return result[0]['all_attributes']['documents']
# #             all_attributes = {key:data[key] for key in data.keys() if key not in ["env_type","documents"]}
# #             all_attributes['documents'] = {}
# #             for inx, docs in enumerate(data['documents']):
# #                 key = f"document{inx+1}"
# #                 document_body = docs['content']
# #                 if not document_body.endswith(".pdf"):
# #                     document_64_decode = base64.b64decode(document_body)
# #                     document_name = ("".join(letter if letter.isalnum() or letter == '.' else '' for letter in docs['document_name']))
# #                     document_name = document_name + (".pdf" if not document_name.endswith(".pdf") else "")
# #                     file_path = os.path.join("cms-images", "client_edit", data['client_id'], document_name)
# #                     # Create directories if they don't exist
# #                     os.makedirs(os.path.dirname(file_path), exist_ok=True)
# #                     # Open the file in binary write mode
# #                     with open(file_path, 'wb') as filewr:
# #                         filewr.write(document_64_decode)
# #                     all_attributes['documents'][key] = f"cms-images/client_data/{data['client_id']}/{document_name}"
# #                 else:
# #                     all_attributes['documents'][key]=document_body
# #             all_attributes['boms'] = {f"bom{inx+1}":item for inx,item in enumerate(boms)}
# #             all_attributes['types_of_boms'] = str(len(boms))
# #             # all_attributes['created_date'] = client[0]['sk_timeStamp'][:10]
# #             all_attributes['client_status'] = client_data[0]['all_attributes']['client_status']
# #             if 'orders' in data:
# #                 all_attributes['orders'] = data['orders']
# #             # all_attributes = create_nested_dicts(all_attributes)
# #             if not 'orders' in all_attributes:
# #                 all_attributes['orders'] = client_data[0]['all_attributes']['orders']
# #
# #             key = {"pk_id": client_data[0]['pk_id'],"sk_timeStamp": client_data[0]['sk_timeStamp']}
# #             update_query={"$set":{"all_attributes":all_attributes}}
# #             result=db_con.Clients.update_one(key,update_query)
# #             conct.close_connection(client)
# #
# #             if result:
# #                 conct.close_connection(client)
# #                 return {'statuscode':200,'body':"client details updated successfully"}
# #             else:
# #                 conct.close_connection(client)
# #                 return {'statuscode':400,'body':"Failed while updating client"}
# #         else:
# #             conct.close_connection(client)
# #             return {'statusCode': 400,'body':"Failed to fetch record for given client_id"}
# #         # except Exception as err:
# #         #     exc_type, exc_obj, tb = sys.exc_info()
# #             # f_name = tb.tb_frame.f_code.co_filename
# #             # line_no = tb.tb_lineno
# #             # #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
# #             # return {'statusCode': 400,'body': 'Bad Request(check data)'}
# #
# #     def CmsClientSearchAddBom(request_body):
# #         data = request_body
# #         env_type = data['env_type']
# #         db_conct = conct.get_conn(env_type)
# #         db_con = db_conct['db']
# #         client = db_conct['client']
# #         search_query = data['bom_name']
# #         if not search_query:
# #             conct.close_connection(client)
# #             return {'statusCode': 404, 'body': "No search parameters passed"}
# #
# #         env_type = data["env_type"]
# #         bom_result = list(db_con.BOM.find(
# #                 {
# #                     '$or': [
# #                         {'pk_id': search_query},
# #                         {'all_attributes.bom_name': search_query}
# #                     ]
# #                 },
# #                 {'_id':0,'all_attributes': 1, 'pk_id': 1}
# #             ))
# #         client_result=list(db_con.Clients.find({},{'_id':0,'all_attributes.boms':1}))
# #         bom_ids=[k['bom_id']  for i in client_result for j,k in i['all_attributes']['boms'].items()]
# #         if data['bom_name'] in bom_ids:
# #             conct.close_connection(client)
# #             return {'statusCode':400,'body':'this bom_id is alreday added' }
# #         if bom_result:
# #
# #             response_dict = {key: value for key, value in bom_result[0]['all_attributes'].items()}
# #             conct.close_connection(client)
# #
# #             return {
# #                 "statusCode": 200,
# #                 "body": {
# #                     "bom_id": response_dict['bom_id'],
# #                     "total_categories": response_dict['total_categories'],
# #                     "created_time": response_dict['created_time'],
# #                     "total_components": response_dict['total_components'],
# #                     "description": response_dict['description'],
# #                     "bom_name": response_dict['bom_name']
# #                 }
# #                 }
# #
# #         else:
# #             conct.close_connection(client)
# #             return {
# #                 'statuscode':404,
# #                 'body':"No data"
# #             }
# #     def CmsClientsUploadPo(request_body):
# #         try:
# #             data = request_body
# #             env_type = data['env_type']
# #             db_conct = conct.get_conn(env_type)
# #             db_con = db_conct['db']
# #             client = db_conct['client']
# #             data_po_information = data["po_information"]
# #             client_id=data['client_id']
# #             po_information = {f"po{inx+1}": value for inx,value in enumerate(data["po_information"])}
# #             # result_client=list(db_con.Clients.find({},{'_id':0,'all_attributes.boms':1}))
# #             result_client = list(db_con.Clients.find(
# #                 {
# #                         'all_attributes.client_id': client_id
# #                 },
# #                 {'_id':0,'all_attributes': 1, 'sk_timeStamp': 1}
# #             ))
# #             result_bom=list(db_con.BOM.find({},{'_id':0,'pk_id':1}))
# #             bom_data = [i['bom_id'] for i in data['po_information']]
# #             pk_ids = [i["pk_id"] for i in result_bom]
# #             mismatched_bom_ids = [bom_id for bom_id in bom_data if bom_id not in pk_ids]
# #             # Display pop-up if mismatches found
# #             if mismatched_bom_ids:
# #                 conct.close_connection(client)
# #                 return {'statusCode':400,'body':"Please give existing BOM_ID"}
# #             a = [i['po_id'] for i in data['po_information']]
# #             duplicates = ', '.join(po_id for po_id in set(a) if a.count(po_id) > 1)
# #             if duplicates:
# #                 conct.close_connection(client)
# #                 return {'statusCode':400,'body':'Duplicates found for po_id ' + duplicates}
# #             b = [i['bom_id'] for i in data['po_information']]
# #             duplicates1 = ', '.join(po_id for po_id in set(b) if b.count(po_id) > 1)
# #             if duplicates1:
# #                 conct.close_connection(client)
# #                 return {'statusCode':400,'body':'Duplicates found for bom_id' + duplicates1}
# #             if result_client:
# #                 client_details = result_client[0]
# #                 # orders=client_details["all_attributes"]["M"]["orders"]
# #                 e = [j['po_id'] for i, j in client_details['all_attributes']['orders'].items()] + [i['po_id'] for i in data['po_information']]
# #                 duplicates_po_id=', '.join(po_id for po_id in set(e) if e.count(po_id) > 1)
# #                 if duplicates_po_id:
# #                     conct.close_connection(client)
# #                     return {'statusCode':400,'body':'Duplicates found for po_id' + duplicates_po_id}
# #                 e1 = [j['bom_id'] for i, j in client_details['all_attributes']['orders'].items()] + [i['bom_id'] for i in data['po_information']]
# #                 duplicates_bom_id=', '.join(bom_id for bom_id in set(e1) if e1.count(bom_id) > 1)
# #                 if duplicates_bom_id:
# #                     conct.close_connection(client)
# #                     return {'statusCode':400,'body':'Duplicates found for bom_id' + duplicates_bom_id}
# #
# #                 sk_timeStamp = client_details["sk_timeStamp"]
# #                 if "orders" in client_details["all_attributes"]:
# #                     # Assuming you have existing data in client_details["all_attributes"]["M"]["orders"]["M"]
# #                     po_information = client_details["all_attributes"]["orders"]
# #                     max_order_key = max(po_information.keys(), default="po0", key=lambda x: int(x.replace("po", "")))
# #                     starting_index = int(max_order_key.replace("po", "")) + 1 if max_order_key != "po0" else 1
# #                     new_po_information = {
# #                         f"po{starting_index + i}":  {key:  po[key] for key in po} for i, po in enumerate(data["po_information"])
# #                     }
# #                     po_information.update(new_po_information)
# #
# #                 else:
# #                     # If "orders" does not exist, set it to the new items
# #                     client_details["all_attributes"]["orders"] = po_information
# #                 key = {
# #                         "pk_id": client_details["all_attributes"]["client_id"],
# #                         "sk_timeStamp":sk_timeStamp
# #                     }
# #                 # key = {"pk_id": client[0]['pk_id'],"sk_timeStamp": client[0]['sk_timeStamp']}
# #
# #                 update_query={"$set":{"all_attributes.orders":po_information}}
# #                 result=db_con.Clients.update_one(key,update_query)
# #                 conct.close_connection(client)
# #
# #
# #                 return {"statusCode": 200,"body": f"Successfully uploaded PO for {data['client_id']}"}
# #             else:
# #                 conct.close_connection(client)
# #                 return {"statusCode": 400,"body": "Client not found"}
# #
# #         except Exception as err:
# #             exc_type, exc_obj, tb = sys.exc_info()
# #             f_name = tb.tb_frame.f_code.co_filename
# #             line_no = tb.tb_lineno
# #             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
# #             return {'statusCode': 400,'body': []}
# #     def cmsClientsGetAll(request_body):
# #         try:
# #             data = request_body
# #             env_type = data['env_type']
# #             db_conct = conct.get_conn(env_type)
# #             db_con = db_conct['db']
# #             client = db_conct['client']
# #             query={'all_attributes.client_status':data['status']}
# #             req_attributes={'_id':0,'all_attributes.client_id':1,'all_attributes.client_name':1,'all_attributes.contact_number':1,'all_attributes.types_of_boms':1,'all_attributes.email':1}
# #             result=list(db_con.Clients.find(query,req_attributes))
# #             modified_result =sorted([{'client_id':x['all_attributes']['client_id'],'client_name':x['all_attributes']['client_name'],'contact_number':x['all_attributes']['contact_number'],'types_of_boms':x['all_attributes']['types_of_boms'],'email':x['all_attributes']['email']} for x in result],key=lambda x: int(x['client_id'].replace("PTGCLI","")), reverse=False)
# #             conct.close_connection(client)
# #
# #             return {'statusCode':200,'body':modified_result}
# #
# #         except Exception as err:
# #             exc_type, exc_obj, tb = sys.exc_info()
# #             f_name = tb.tb_frame.f_code.co_filename
# #             line_no = tb.tb_lineno
# #             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
# #             return {'statusCode': 400,'body': []}
# #     def CmsClientBomSearchSuggestion(request_body):
# #         try:
# #             data = request_body
# #             env_type = data['env_type']
# #             db_conct = conct.get_conn(env_type)
# #             db_con = db_conct['db']
# #             client = db_conct['client']
# #             bom_search = data['bom_search']
# #
# #             results = list(db_con.BOM.find({
# #                 "$or" :[
# #                 {"all_attributes.bom_name": {"$regex": bom_search, "$options": "i"}},
# #                 {"all_attributes.bom_id": {"$regex": bom_search, "$options": "i"}},
# #                 ] },
# #             {"_id":0,"pk_id": 1, "all_attributes.bom_name": 1,"all_attributes.bom_id":1}))
# #             if results:
# #                 formatted_results = [[doc['pk_id'], doc['all_attributes']['bom_name']] for doc in results]
# #                 conct.close_connection(client)
# #
# #                 return {"statusCode": 200, "body": formatted_results}
# #             else:
# #                 conct.close_connection(client)
# #                 return {"statuscode":400,'body':"BOM not found"}
# #         except Exception as err:
# #             exc_type, _, tb = sys.exc_info()
# #             f_name = tb.tb_frame.f_code.co_filename
# #             line_no = tb.tb_lineno
# #             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
# #             return {'statusCode': 400, 'error': 'Bad Request (check data)'}
# #     def get_bom_details(data, bom_id):
# #         env_type = data['env_type']
# #         db_conct = conct.get_conn(env_type)
# #         db_con = db_conct['db']
# #         client = db_conct['client']
# #         bom_result = list(db_con.BOM.find({"pk_id": bom_id},{"_id":0,"all_attributes":1}))
# #         if bom_result:
# #             conct.close_connection(client)
# #             return bom_result[0]['all_attributes']
# #         else:
# #             conct.close_connection(client)
# #             return {}
# #
# #     def cmsClientGetInnerDetailsById(request_body):
# #         try:
# #             data = request_body
# #             env_type = data['env_type']
# #             db_conct = conct.get_conn(env_type)
# #             db_con = db_conct['db']
# #             client = db_conct['client']
# #             client_id = data["client_id"]
# #             result = list(db_con.Clients.find({"pk_id": client_id},{"_id":0,"all_attributes":1,"sk_timeStamp":1}))
# #             if result:
# #                 part_info = result[0]['all_attributes']
# #                 part_info["created_date"] = result[0]['sk_timeStamp'][:10]
# #                 docs = [{"content":value,'document_name':value.split("/")[-1]} for key,value in part_info['documents'].items()]
# #                 part_info['documents'] = docs
# #                 if "orders" in part_info:
# #                     part_info["orders"] = dict(sorted(part_info["orders"].items(), key=lambda x: x[1]["bom_id"]))
# #                 boms = part_info["boms"]
# #                 bom_details = {bom_key: Clients.get_bom_details(data,bom_value['bom_id']) for bom_key, bom_value in boms.items()}
# #                 # return bom_details
# #                 bom_details = {}
# #                 for bom_key, bom_value in boms.items():
# #                     bom_id = bom_value['bom_id']
# #                     bom_details = Clients.get_bom_details(data,bom_id)
# #                     bom_value["bom_name"] = bom_details["bom_name"]
# #                     bom_value["created_date"]=bom_details["created_time"]
# #
# #                     bom_value["total_categories"] = bom_details["total_categories"]
# #                     bom_value["total_components"] = bom_details["total_components"]
# #                 conct.close_connection(client)
# #
# #                 return {"statusCode": 200, "body": part_info}
# #             else:
# #                 conct.close_connection(client)
# #                 return {"statusCode": 400, "body": "something went wrong, please try agian"}
# #         except Exception as err:
# #             exc_type, _, tb = sys.exc_info()
# #             f_name = tb.tb_frame.f_code.co_filename
# #             line_no = tb.tb_lineno
# #             #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
# #             return {'statusCode': 400, 'error': 'Bad Request (check data)'}



    # def cmsGetClientAssignPoDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
           
    #         po_id = data['po_id']
    #         bom_id = data['bom_id']
           
    #         query = list(db_con.ClientAssign.find({'all_attributes.against_po': po_id, 'all_attributes.bom_id': bom_id}, {'_id': 0, 'all_attributes': 1}))
           
    #         if not query:
    #             return {'statusCode': 404, 'body': 'No client assignment found for the given PO and BOM'}
           
    #         return_list = query[0]['all_attributes']
    #         sorted_batches = dict(sorted(return_list['kits'].items()))
    #         for batch_key, products in sorted_batches.items():
    #             sorted_batches[batch_key] = dict(sorted(products.items()))
           
    #         return_list['kits'] = sorted_batches
           
    #         return {'statusCode': 200, 'body': return_list}
 
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': []}



    # def cmsGetClientAssignPoDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         client = db_conct['client']
           
    #         po_id = data['po_id']
    #         bom_id = data['bom_id']
           
    #         query = list(db_con.ClientAssign.find({'all_attributes.against_po': po_id, 'all_attributes.bom_id': bom_id}, {'_id': 0, 'all_attributes': 1}))
           
    #         if not query:
    #             return {'statusCode': 404, 'body': 'No client assignment found for the given PO and BOM'}
           
    #         return_list = query[0]['all_attributes']
    #         sorted_batches = dict(sorted(return_list['kits'].items()))
    #         for batch_key, products in sorted_batches.items():
    #             sorted_batches[batch_key] = dict(sorted(products.items()))
           
    #         return_list['kits'] = sorted_batches
    #         for batch_key, batch in return_list['kits'].items():
    #             for product_key, product in batch.items():
    #                 if product_key.startswith('product'):
    #                     if product['status'] == 'Dispatched':
    #                         product['status_checked'] = 'false'
    #                     else:
    #                         product['status_checked'] = 'true'
    #                     product['status_checked'] = True if product['status_checked'].lower() == 'true' else False
    #         return {'statusCode': 200, 'body': return_list}
 
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': []}

    def cmsGetClientAssignPoDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']

            po_id = data['po_id']
            bom_id = data['bom_id']

            query = list(db_con.ClientAssign.find({'all_attributes.against_po': po_id},
                                                  {'_id': 0, 'all_attributes': 1}))
            if not query:
                return {'statusCode': 404, 'body': 'No client assignment found for the given PO and BOM'}

            final_product_batches = {}
            for item in query:
                for key, value in item['all_attributes'].items():
                    if key == 'kits':
                        for batch_key, batch_value in value.items():
                            if batch_key not in final_product_batches:
                                final_product_batches[batch_key] = {}
                            for product_key, product_value in batch_value.items():
                                product_num = len(final_product_batches[batch_key]) + 1
                                final_product_batches[batch_key][f'product{product_num}'] = product_value

            return_list = query[0]['all_attributes']
            return_list['kits'] = final_product_batches
            for batch_key, batch in return_list['kits'].items():
                for product_key, product in batch.items():
                    if product_key.startswith('product'):
                        if product['status'] == 'Dispatched':
                            product['status_checked'] = 'false'
                        else:
                            product['status_checked'] = 'true'
                        product['status_checked'] = True if product['status_checked'].lower() == 'true' else False
            return {'statusCode': 200, 'body': return_list}

        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': []}
       
 
       
 
    # def cmsStatusClientAssignPoDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         status = data['status']
    #         new_status = "Delivered" if status == 'Received' else "Product Rejected"
    #         kits = data['kits']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
 
    #         for kit_item in kits:
    #             final_product_kit_id = kit_item['final_product_kit_id']
    #             pcba_id = kit_item['pcba_id']
    #             client_id = kit_item['client_id']
    #             final_product_batch_id = f"final_product_batch{final_product_kit_id.replace('final_product_kit', '')}"
    #             query_client = {
    #                 'all_attributes.kits.' + final_product_batch_id: {'$exists': True},
    #                 'all_attributes.client_id': client_id
    #             }
    #             document_client = db_con.ClientAssign.find_one(query_client)
 
    #             if document_client:
    #                 for key, product in document_client['all_attributes']['kits'][final_product_batch_id].items():
    #                     if key.startswith('product'):
    #                         if product['pcba_id'] == pcba_id:
    #                             update_client = {
    #                                 '$set': {
    #                                     f'all_attributes.kits.{final_product_batch_id}.{key}.status': new_status
    #                                 }
    #                             }
    #                             db_con.ClientAssign.update_one(query_client, update_client)
    #                             break  
 
    #             query_final = {
    #                 'all_attributes.kits.' + final_product_batch_id: {'$exists': True}
    #             }
    #             document_final = db_con.FinalProduct.find_one(query_final)
 
    #             if document_final:
    #                 for key, product in document_final['all_attributes']['kits'][final_product_batch_id].items():
    #                     if key.startswith('product'):
    #                         if product['pcba_id'] == pcba_id:
    #                             update_final = {
    #                                 '$set': {
    #                                     f'all_attributes.kits.{final_product_batch_id}.{key}.Product_Status': new_status
    #                                 }
    #                             }
    #                             db_con.FinalProduct.update_one(query_final, update_final)
    #                             break
 
    #         return {'statusCode': 200, 'body': 'Status updated successfully'}
 
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'An error occurred while updating status'}
 
 
 
 
    # def cmsStatusClientAssignPoDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         status = data['status']
    #         new_status = "Delivered" if status == 'Received' else "Product Rejected"
    #         kits = data['kits']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
 
    #         for kit_item in kits:
    #             final_product_kit_id = kit_item['final_product_kit_id']
    #             pcba_id = kit_item['pcba_id']
    #             client_id = kit_item['client_id']
    #             final_product_batch_id = f"final_product_batch{final_product_kit_id.replace('final_product_kit', '')}"
 
    #             query_client = {
    #                 f'all_attributes.kits.{final_product_batch_id}': {'$exists': True},
    #                 'all_attributes.client_id': client_id
    #             }
    #             document_client = db_con.ClientAssign.find_one(query_client)
 
    #             if document_client:
    #                 for key, product in document_client['all_attributes']['kits'][final_product_batch_id].items():
    #                     if key.startswith('product'):
    #                         if product['pcba_id'] == pcba_id:
    #                             update_client = {
    #                                 '$set': {
    #                                     f'all_attributes.kits.{final_product_batch_id}.{key}.status': new_status
    #                                 }
    #                             }
    #                             db_con.ClientAssign.update_one(query_client, update_client)
    #                             break
 
    #             query_final = {
    #                 f'all_attributes.kits.{final_product_batch_id}': {'$exists': True}
    #             }
    #             document_final = db_con.FinalProduct.find_one(query_final)
 
    #             if document_final:
    #                 for key, product in document_final['all_attributes']['kits'][final_product_batch_id].items():
    #                     if key.startswith('product'):
    #                         if product['pcba_id'] == pcba_id:
    #                             update_final = {
    #                                 '$set': {
    #                                     f'all_attributes.kits.{final_product_batch_id}.{key}.Product_Status': new_status
    #                                 }
    #                             }
    #                             db_con.FinalProduct.update_one(query_final, update_final)
    #                             break
 
    #         return {'statusCode': 200, 'body': 'Status updated successfully'}
 
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'An error occurred while updating status'}
 
 
    # def cmsStatusClientAssignPoDetails(request_body):
    #     try:
    #         data = request_body
    #         env_type = data['env_type']
    #         status = data['status']
    #         new_status = "Received" if status == 'Received' else "Product Rejected"
    #         new_status1 = "Delivered" if status == 'Received' else "Product Rejected"
    #         kits = data['kits']
    #         db_conct = conct.get_conn(env_type)
    #         db_con = db_conct['db']
    #         for batch_key, products in kits.items():
    #             for product_key, product in products.items():
    #                 if product_key.startswith('product'):
    #                     final_product_kit_id = product['final_product_kit_id']
    #                     pcba_id = product['pcba_id']
    #                     final_product_batch_id = f"Final_product_batch{final_product_kit_id.replace('final_product_kit', '')}"
    #                     query_client = {
    #                         f'all_attributes.kits.{final_product_batch_id}': {'$exists': True},
    #                         f'all_attributes.kits.{final_product_batch_id}.{product_key}.pcba_id': pcba_id
    #                     }
 
    #                     document_client = db_con.ClientAssign.find_one(query_client)
 
    #                     if document_client:
    #                         update_client = {
    #                             '$set': {
    #                                 f'all_attributes.kits.{final_product_batch_id}.{product_key}.status': new_status
    #                             }
    #                         }
    #                         db_con.ClientAssign.update_one(query_client, update_client)
    #                     query_final = {
    #                         f'all_attributes.kits.{final_product_batch_id}': {'$exists': True},
    #                         f'all_attributes.kits.{final_product_batch_id}.{product_key}.pcba_id': pcba_id
    #                     }
    #                     document_final = db_con.FinalProduct.find_one(query_final)
 
    #                     if document_final:
    #                         update_final = {
    #                             '$set': {
    #                                 f'all_attributes.kits.{final_product_batch_id}.{product_key}.product_status': new_status1
    #                             }
    #                         }
    #                         db_con.FinalProduct.update_one(query_final, update_final)
 
    #         return {'statusCode': 200, 'body': 'Status updated successfully'}
 
    #     except Exception as err:
    #         exc_type, exc_obj, tb = sys.exc_info()
    #         f_name = tb.tb_frame.f_code.co_filename
    #         line_no = tb.tb_lineno
    #         print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
    #         return {'statusCode': 400, 'body': 'An error occurred while updating status'}

    def cmsStatusClientAssignPoDetails(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            status = data['status']
            new_status = "Received" if status == 'Received' else "Product Rejected"
            new_status1 = "Delivered" if status == 'Received' else "Product Rejected"
            kits = data['kits']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            for batch_key, products in kits.items():
                for product_key, product in products.items():
                    if product_key.startswith('product'):
                        final_product_kit_id = product['final_product_kit_id']
                        pcba_id = product['pcba_id']
                        final_product_batch_id = f"Final_product_batch{final_product_kit_id.replace('final_product_kit', '')}"
                        query_client = {
                            f'all_attributes.kits.{final_product_batch_id}': {'$exists': True},
                            f'all_attributes.kits.{final_product_batch_id}.{product_key}.pcba_id': pcba_id
                        }
                        document_client = db_con.ClientAssign.find_one(query_client)
                        if document_client:
                            update_client = {
                                '$set': {
                                    f'all_attributes.kits.{final_product_batch_id}.{product_key}.status': new_status
                                }
                            }
                            db_con.ClientAssign.update_one(query_client, update_client)
                        final = db_con.FinalProduct.find()
                        for item in final:
                            for final_product_batch_id, products in item['all_attributes']['kits'].items():
                                for product_key, product_info in products.items():
                                    if product_key != 'status':
                                        if product_info.get('pcba_id') == pcba_id:
                                            query_final = {
                                                f'all_attributes.kits.{final_product_batch_id}': {'$exists': True},
                                                f'all_attributes.kits.{final_product_batch_id}.{product_key}.pcba_id': pcba_id
                                            }
                                            update_final = {
                                                '$set': {
                                                    f'all_attributes.kits.{final_product_batch_id}.{product_key}.product_status': new_status1
                                                }
                                            }
                                            db_con.FinalProduct.update_one(query_final, update_final) 
            return {'statusCode': 200, 'body': 'Status updated successfully'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400, 'body': 'An error occurred while updating status'}