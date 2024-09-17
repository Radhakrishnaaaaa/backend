import json
from datetime import datetime, timedelta
import base64
from db_connection import db_connection_manage
import sys
import os
import re

conct = db_connection_manage()

class UserRoles:
    
    def createUserRole(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type )
            db_con = db_conct['db']
            sk_timeStamp = (datetime.now()).isoformat()
            
            get_roles = list(db_con.UserRoles.find({}, {"_id": 0}))
            print(get_roles)
            for role_name in get_roles:
                print(role_name['all_attributes']['role_name'], data['role_name'])
                if data['role_name'].capitalize() == role_name['all_attributes']['role_name'].capitalize():
                    return {'status': 400, 'body': 'Role Name Already Existed'}
            role_name_data = {
                'role_name': data['role_name'].capitalize(),
                'role_id': f'PTGROLE_{len(get_roles) + 1}'
            }
            roleData = {
                'pk_id': f'PTGROLE_{len(get_roles) + 1}',
                'created_on': sk_timeStamp,
                'all_attributes': role_name_data,
                'gsipk_table': 'Roles',
                'gsipk_id': '',
                'lsi_key': '',
                'role_permissions_assigned': False
            }
            db_con.UserRoles.insert_one(roleData)
            return {'statusCode': 200, 'body': 'Role Created Successfully'}
            
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Role Creation Failed'}
        
    def getUserRoles(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            
            get_roles = list(db_con.UserRoles.find({}, {"_id": 0}))
            return {'statusCode': 200, 'body': get_roles}
            
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Role Creation Failed'}
        
    def assignPermissionsToRole(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            sk_timeStamp = (datetime.now()).isoformat()
            inventory_permissions = {}
            components_permissions = {}
            dashboard_permissions = {}
            vendors_permissions = {}
            clients_permissions = {}
            boms_permissions = {}
            purchase_order_permissions = {}
            if "screen_permissions" in data and "Inventory" in data["screen_permissions"]:
                inventory_data = data['screen_permissions']['Inventory']
                inventory_permissions = {
                    'Read': True if inventory_data["read"] == True else False,
                    'Write': True if inventory_data["write"] == True else False,
                    'Delete': True if inventory_data["delete"] == True else False
                }
            if "screen_permissions" in data and "Components" in data["screen_permissions"]:
                components_data = data['screen_permissions']['Components']
                components_permissions = {
                    'Read': True if components_data["read"] == True else False,
                    'Write': True if components_data["write"] == True else False,
                    'Delete': True if components_data["delete"] == True else False
                }
            if "screen_permissions" in data and "Dashboard" in data["screen_permissions"]:
                dashboard_data = data['screen_permissions']['Dashboard']
                dashboard_permissions = {
                    'Read': True if dashboard_data["read"] == True else False,
                    'Write': True if dashboard_data["write"] == True else False,
                    'Delete': True if dashboard_data["delete"] == True else False
                }
            if "screen_permissions" in data and "Vendors" in data["screen_permissions"]:
                vendors_data = data['screen_permissions']['Vendors']
                vendors_permissions = {
                    'Read': True if vendors_data["read"] == True else False,
                    'Write': True if vendors_data["write"] == True else False,
                    'Delete': True if vendors_data["delete"] == True else False
                }
            if "screen_permissions" in data and "Clients" in data["screen_permissions"]:
                clients_data = data['screen_permissions']['Clients']
                clients_permissions = {
                    'Read': True if clients_data["read"] == True else False,
                    'Write': True if clients_data["write"] == True else False,
                    'Delete': True if clients_data["delete"] == True else False
                }
            if "screen_permissions" in data and "Boms" in data["screen_permissions"]:
                boms_data = data['screen_permissions']['Boms']
                boms_permissions = {
                    'Read': True if boms_data["read"] == True else False,
                    'Write': True if boms_data["write"] == True else False,
                    'Delete': True if boms_data["delete"] == True else False
                }
            if "screen_permissions" in data and "PurchaseOrders" in data["screen_permissions"]:
                purchase_orders_data = data['screen_permissions']['PurchaseOrders']
                components_permissions = {
                    'Read': True if purchase_orders_data["read"] == True else False,
                    'Write': True if purchase_orders_data["write"] == True else False,
                    'Delete': True if purchase_orders_data["delete"] == True else False
                }
            screen_data = {
                'Inventory': inventory_permissions,
                'Components': components_permissions,
                'Dashboard': dashboard_permissions,
                'Clients': clients_permissions,
                'Vendors': vendors_permissions,
                'Boms': boms_permissions,
                'Purchase_orders': purchase_order_permissions,
            }
            role_data = {
                'role_id': data['role_id'],
                'role_name': data['role_name'].capitalize(),
                'screen_permissions': screen_data
            }
            permissions_data = {
                'pk_id': data['role_id'],
                'assigned_on': sk_timeStamp,
                'all_attributes': role_data,
                'gsipk_table': 'Permissions',
                'gsipk_id': '',
                'lsi_key': ''
            }
            print(data['is_update'])
            if data['is_update'] is False:
                assign_permissions_role = db_con.RolePermissions.insert_one(permissions_data)
                if assign_permissions_role:
                    get_roles = list(db_con.UserRoles.find({}, {"_id": 0}))
                    print("a", get_roles)
                    for role in get_roles:
                        print(role['pk_id'] == data['role_id'], role['pk_id'], data['role_id'])
                        if role['pk_id'] == data['role_id']:
                            db_con.UserRoles.update_one(
                                {'pk_id': data['role_id']},
                                {"$set": {
                                    "role_permissions_assigned": True,
                                }}
                            )
            else:
                 get_roles_permissions = list(db_con.RolePermissions.find({}, {"_id": 0}))
                 for role in get_roles_permissions:
                    if role['all_attributes']['role_id'] == data['role_id']:
                        print('kalyan', data['role_id'])
                        db_con.RolePermissions.update_one(
                            {'pk_id': data['role_id']},
                            {"$set": {
                                'all_attributes.screen_permissions': screen_data
                            }}
                        )
            return {'statusCode': 200, 'body': f"Permissions Successfully assigned to {data['role_name'].capitalize()} role"}
            
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Permission assigning failed'}
        
    def getRolePermissions(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            
            get_roles_permissions = list(db_con.RolePermissions.find({}, {"_id": 0}))
            for role_permission in get_roles_permissions:
                if role_permission["pk_id"] == data["role_id"]:
                    role_permission_data = role_permission["all_attributes"]
            print(role_permission_data)
            return {'statusCode': 200, 'body': role_permission_data}
            
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            #print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Role Creation Failed'}
        
    