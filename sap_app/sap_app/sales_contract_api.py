# import frappe
# import requests
# from requests.auth import HTTPBasicAuth
# import json
# import urllib3
# import traceback

# # Disable SSL warnings for unverified HTTPS requests
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# @frappe.whitelist()
# def sync_sales_contracts_to_sap():
#     domain = "s4hana2.amitmetaliks.com"
#     port = "1043"
#     base_url = f"https://{domain}:{port}/sap/opu/odata/sap/API_SALES_CONTRACT_SRV"
#     metadata_url = f"{base_url}/$metadata"
#     post_url = f"{base_url}/A_SalesContract"
    
#     client_id = "AMLRFC"
#     client_secret = "N6@ko}>49ki6=tUYoZprlKQ[v7-43K+cDf/\\yzhg"
    
#     # Get all submitted Sales Orders where contract is neither created nor failed yet
#     sales_orders = frappe.get_all(
#         "Sales Order",
#         filters={
#             "docstatus": 1,
#             "custom_sales_contract_created": 0,
#             "custom_sales_contract_failed": 0
#         },
#         fields=["name"]
#     )
    
#     if not sales_orders:
#         return
        
#     session = requests.Session()
#     session.auth = HTTPBasicAuth(client_id, client_secret)
    
#     headers = {
#         "x-csrf-token": "fetch"
#     }
    
#     # Step 1: GET request to fetch CSRF token
#     try:
#         response = session.get(metadata_url, headers=headers, verify=False)
#         if response.status_code != 200:
#             frappe.log_error(f"Failed to fetch metadata. Status Code: {response.status_code}\nResponse: {response.text}", "SAP API CSRF Token Error")
#             return
            
#         csrf_token = response.headers.get("x-csrf-token")
#         if not csrf_token:
#             frappe.log_error("CSRF token not found in response headers.", "SAP API CSRF Token Error")
#             return
#     except Exception as e:
#         frappe.log_error(f"Error fetching CSRF token: {str(e)}\n{traceback.format_exc()}", "SAP API Fetch Token Exception")
#         return

#     post_headers = {
#         "x-csrf-token": csrf_token,
#         "Content-Type": "application/json",
#         "Accept": "application/json"
#     }

#     for so_info in sales_orders:
#         try:
#             doc = frappe.get_doc("Sales Order", so_info.name)
            
#             # Map the fields
#             customer_sap_code = doc.custom_customer_sap_code
#             if not customer_sap_code:
#                 frappe.log_error(f"No SAP code found for customer {doc.customer} in {doc.name}", f"SAP Sync Error - {doc.name}")
#                 frappe.db.set_value("Sales Order", doc.name, "custom_sales_contract_failed", 1)
#                 frappe.db.commit()
#                 continue
            
#             po_no = doc.po_no if hasattr(doc, 'po_no') and doc.po_no else (doc.custom_reference_id or doc.name)

#             items_payload = []
#             item_no = 0010
#             for item in doc.items:
#                 items_payload.append({
#                     "SalesContractItem": str(item_no).zfill(6),
#                     "Material": str(item.item_code),
#                     "ProductionPlant": str(item.cost_center),
#                     "RequestedQuantity": str(item.qty),
#                     "RequestedQuantityUnit": str(item.stock_uom or item.uom or "MT"),
#                     "to_PricingElement": [
#                         {
#                             "ConditionType": "ZCNQ",
#                             "ConditionRateValue": str(item.rate),
#                             "ConditionCurrency": str(doc.currency or "INR"),
#                             "ConditionQuantity": "1",
#                             "ConditionQuantityUnit": str(item.stock_uom or item.uom or "MT")
#                         }
#                     ]
#                 })
#                 item_no += 10
                
#             payload = {
#                 "SalesContractType": "ZGCQ",
#                 "SalesOrganization": "1000",
#                 "DistributionChannel": "10",
#                 "OrganizationDivision": "17",
#                 "PurchaseOrderByCustomer": str(po_no),
#                 "SoldToParty": str(customer_sap_code),
#                 "to_Item": items_payload,
#                 "to_Partner": [
#                     {
#                         "PartnerFunction": "SP",
#                         "Customer": str(customer_sap_code)
#                     },
#                     {
#                         "PartnerFunction": "SH",
#                         "Customer": str(customer_sap_code)
#                     }
#                 ]
#             }
            
#             print(f"\n--- Payload for SO: {doc.name} ---")
#             print(json.dumps(payload, indent=4))
            
#             post_response = session.post(
#                 post_url, 
#                 headers=post_headers, 
#                 data=json.dumps(payload), 
#                 verify=False
#             )
            
#             if post_response.status_code in [200, 201]:
#                 # Success
#                 frappe.db.set_value("Sales Order", doc.name, "custom_sales_contract_created", 1)
#                 frappe.db.set_value("Sales Order", doc.name, "custom_sales_contract_failed", 0)
#                 frappe.db.commit()
#             else:
#                 # Failure
#                 error_msg = f"Status: {post_response.status_code}\n"
#                 try:
#                     error_msg += json.dumps(post_response.json(), indent=4)
#                 except:
#                     error_msg += post_response.text
                
#                 print(f"--- Error Response for SO: {doc.name} ---")
#                 print(error_msg)
                
#                 frappe.log_error(f"Payload: {json.dumps(payload, indent=4)}\n\nResponse:\n{error_msg}", f"SAP Sales Contract Creation Failed - {doc.name}")
#                 frappe.db.set_value("Sales Order", doc.name, "custom_sales_contract_failed", 1)
#                 frappe.db.commit()

#         except Exception as e:
#             frappe.log_error(f"Error processing {so_info.name}: {str(e)}\n{traceback.format_exc()}", f"SAP Sync Exception - {so_info.name}")
#             frappe.db.set_value("Sales Order", so_info.name, "custom_sales_contract_failed", 1)
#             frappe.db.commit()

# import frappe
# import requests
# from requests.auth import HTTPBasicAuth
# import json
# import urllib3
# import traceback

# # Disable SSL warnings for unverified HTTPS requests
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# @frappe.whitelist()
# def sync_sales_contracts_to_sap():
#     domain = "s4hana1.amitmetaliks.com"
#     port = "1043"
#     base_url = f"https://{domain}:{port}/sap/opu/odata/sap/API_SALES_CONTRACT_SRV"
#     metadata_url = f"{base_url}/$metadata"
#     post_url = f"{base_url}/A_SalesContract"
    
#     client_id = "AMLRFC"
#     client_secret = "N6@ko}>49ki6=tUYoZprlKQ[v7-43K+cDf/\\yzhg"
    
#     # Get all submitted Sales Orders where contract is neither created nor failed yet
#     sales_orders = frappe.get_all(
#         "Sales Order",
#         filters={
#             "docstatus": 1,
#             "custom_sales_contract_created": 0,
#             "custom_sales_contract_failed": 0
#         },
#         fields=["name"]
#     )
    
#     if not sales_orders:
#         return
        
#     session = requests.Session()
#     session.auth = HTTPBasicAuth(client_id, client_secret)
    
#     headers = {
#         "x-csrf-token": "fetch"
#     }
    
#     # Step 1: GET request to fetch CSRF token
#     try:
#         response = session.get(metadata_url, headers=headers, verify=False)
#         if response.status_code != 200:
#             frappe.log_error(f"Failed to fetch metadata. Status Code: {response.status_code}\nResponse: {response.text}", "SAP API CSRF Token Error")
#             return
            
#         csrf_token = response.headers.get("x-csrf-token")
#         if not csrf_token:
#             frappe.log_error("CSRF token not found in response headers.", "SAP API CSRF Token Error")
#             return
#     except Exception as e:
#         frappe.log_error(f"Error fetching CSRF token: {str(e)}\n{traceback.format_exc()}", "SAP API Fetch Token Exception")
#         return

#     post_headers = {
#         "x-csrf-token": csrf_token,
#         "Content-Type": "application/json",
#         "Accept": "application/json"
#     }

#     for so_info in sales_orders:
#         try:
#             doc = frappe.get_doc("Sales Order", so_info.name)
            
#             # Map the fields
#             customer_sap_code = doc.custom_customer_sap_code
#             if not customer_sap_code:
#                 frappe.log_error(f"No SAP code found for customer {doc.customer} in {doc.name}", f"SAP Sync Error - {doc.name}")
#                 frappe.db.set_value("Sales Order", doc.name, "custom_sales_contract_failed", 1)
#                 frappe.db.commit()
#                 continue
            
#             po_no = doc.po_no if hasattr(doc, 'po_no') and doc.po_no else (doc.custom_reference_id or doc.name)

#             items_payload = []
#             item_no = 10
#             for item in doc.items:
#                 items_payload.append({
#                     "SalesContractItem": str(item_no).zfill(6),
#                     "Material": str(frappe.get_value("Item", {"item_code": item.item_code}, "name")),
#                     "ProductionPlant": str(frappe.get_value("Cost Center", {"name": item.cost_center}, "parent_cost_center")),
#                     "RequestedQuantity": str(item.qty),
#                     "RequestedQuantityUnit": str(item.stock_uom or item.uom or "MT"),
#                     "to_PricingElement": [
#                         {
#                             "ConditionType": "ZPR0",
#                             "ConditionRateValue": str(item.rate),
#                             "ConditionCurrency": str(doc.currency or "INR"),
#                             "ConditionQuantity": "1",
#                             "ConditionQuantityUnit": str(item.stock_uom or item.uom or "MT")
#                         }
#                     ]
#                 })
#                 item_no += 10
                
#             payload = {
#                 "SalesContractType": "ZGCQ",
#                 "SalesOrganization": "1000",
#                 "DistributionChannel": "10",
#                 "OrganizationDivision": "17",
#                 "PurchaseOrderByCustomer": str(po_no),
#                 "SoldToParty": str(customer_sap_code),
#                 "to_Item": items_payload,
#                 "to_Partner": [
#                     {
#                         "PartnerFunction": "SP",
#                         "Customer": str(customer_sap_code)
#                     },
#                     {
#                         "PartnerFunction": "SH",
#                         "Customer": str(customer_sap_code)
#                     }
#                 ]
#             }
            
#             print(f"\n--- Payload for SO: {doc.name} ---")
#             print(json.dumps(payload, indent=4))
            
#             post_response = session.post(
#                 post_url, 
#                 headers=post_headers, 
#                 data=json.dumps(payload), 
#                 verify=False
#             )
            
#             if post_response.status_code in [200, 201]:
#                 # Success
#                 frappe.db.set_value("Sales Order", doc.name, "custom_sales_contract_created", 1)
#                 frappe.db.set_value("Sales Order", doc.name, "custom_sales_contract_failed", 0)
#                 frappe.db.commit()
#             else:
#                 # Failure
#                 error_msg = f"Status: {post_response.status_code}\n"
#                 try:
#                     error_msg += json.dumps(post_response.json(), indent=4)
#                 except:
#                     error_msg += post_response.text
                
#                 print(f"--- Error Response for SO: {doc.name} ---")
#                 print(error_msg)
                
#                 frappe.log_error(f"Payload: {json.dumps(payload, indent=4)}\n\nResponse:\n{error_msg}", f"SAP Sales Contract Creation Failed - {doc.name}")
#                 frappe.db.set_value("Sales Order", doc.name, "custom_sales_contract_failed", 1)
#                 frappe.db.commit()

#         except Exception as e:
#             frappe.log_error(f"Error processing {so_info.name}: {str(e)}\n{traceback.format_exc()}", f"SAP Sync Exception - {so_info.name}")
#             frappe.db.set_value("Sales Order", so_info.name, "custom_sales_contract_failed", 1)
#             frappe.db.commit()




import frappe
import requests
from requests.auth import HTTPBasicAuth
import json
import urllib3
import traceback

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@frappe.whitelist()
def sync_sales_contracts_to_sap():
    domain = "s4hana1.amitmetaliks.com"
    port = "1043"
    base_url = f"https://{domain}:{port}/sap/opu/odata/sap/API_SALES_CONTRACT_SRV"
    metadata_url = f"{base_url}/$metadata"
    post_url = f"{base_url}/A_SalesContract"
    
    client_id = "AMLRFC"
    client_secret = "N6@ko}>49ki6=tUYoZprlKQ[v7-43K+cDf/\\yzhg"
    
    sales_orders = frappe.get_all(
        "Sales Order",
        filters={
            "docstatus": 1,
            "custom_sales_contract_created": 0,
            "custom_sales_contract_failed": 0
        },
        fields=["name"]
    )
    
    if not sales_orders:
        return
        
    session = requests.Session()
    session.auth = HTTPBasicAuth(client_id, client_secret)
    
    headers = {"x-csrf-token": "fetch"}
    
    try:
        response = session.get(metadata_url, headers=headers, verify=False)
        if response.status_code != 200:
            frappe.log_error(
                f"Failed to fetch metadata. Status Code: {response.status_code}\nResponse: {response.text}",
                "SAP API CSRF Token Error"
            )
            return
            
        csrf_token = response.headers.get("x-csrf-token")
        if not csrf_token:
            frappe.log_error("CSRF token not found in response headers.", "SAP API CSRF Token Error")
            return
    except Exception as e:
        frappe.log_error(
            f"Error fetching CSRF token: {str(e)}\n{traceback.format_exc()}",
            "SAP API Fetch Token Exception"
        )
        return

    post_headers = {
        "x-csrf-token": csrf_token,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    for so_info in sales_orders:
        try:
            doc = frappe.get_doc("Sales Order", so_info.name)
            
            customer_sap_code = doc.custom_customer_sap_code
            if not customer_sap_code:
                error_msg = f"SAP Sync Failed: No SAP customer code found for customer '{doc.customer}'."
                frappe.log_error(error_msg, f"SAP Sync Error - {doc.name}")
                
                # Add comment on Sales Order document
                doc.add_comment("Comment", text=f"❌ SAP Contract Creation Failed:\n{error_msg}")
                
                frappe.db.set_value("Sales Order", doc.name, "custom_sales_contract_failed", 1)
                frappe.db.commit()
                continue
            
            po_no = doc.po_no if hasattr(doc, 'po_no') and doc.po_no else (doc.custom_reference_id or doc.name)

            # Find TR_TMT_16MM_BEND item rate from the order
            bend_item_rate = 0
            for item in doc.items:
                if item.item_code == "TR_TMT_16MM_BEND":
                    bend_item_rate = item.rate
                    break

            # If TR_TMT_16MM_BEND not found in items, log warning and add comment
            if not bend_item_rate:
                warning_msg = f"SAP Sync Warning: TR_TMT_16MM_BEND not found in order items. Rate defaulting to 0."
                frappe.log_error(warning_msg, f"SAP Sync Warning - {doc.name}")
                doc.add_comment("Comment", text=f"⚠️ SAP Contract Warning:\n{warning_msg}")

            # Sum all item quantities
            total_qty = sum(item.qty for item in doc.items)

            # UOM from first item
            uom = (doc.items[0].stock_uom or doc.items[0].uom or "MT") if doc.items else "MT"

            # ProductionPlant from doc.custom_branch
            production_plant = str(doc.branch) if doc.branch else ""

            items_payload = [
                {
                    "SalesContractItem": "000010",
                    "Material": "TR_TMT_16MM_BEND",
                    "ProductionPlant": production_plant,
                    "RequestedQuantity": str(total_qty),
                    "RequestedQuantityUnit": uom,
                    "to_PricingElement": [
                        {
                            "ConditionType": "ZPR0",
                            "ConditionRateValue": str(bend_item_rate),
                            "ConditionCurrency": str(doc.currency or "INR"),
                            "ConditionQuantity": "1",
                            "ConditionQuantityUnit": uom
                        }
                    ]
                }
            ]
                
            payload = {
                "SalesContractType": "ZGCQ",
                "SalesOrganization": "1000",
                "DistributionChannel": "10",
                "OrganizationDivision": "17",
                "PurchaseOrderByCustomer": str(po_no),
                "SoldToParty": str(customer_sap_code),
                "to_Item": items_payload,
                "to_Partner": [
                    {"PartnerFunction": "SP", "Customer": str(customer_sap_code)},
                    {"PartnerFunction": "SH", "Customer": str(customer_sap_code)}
                ]
            }
            
            print(f"\n--- Payload for SO: {doc.name} ---")
            print(json.dumps(payload, indent=4))
            
            post_response = session.post(
                post_url,
                headers=post_headers,
                data=json.dumps(payload),
                verify=False
            )
            print("post response----------", post_response.text)
            
            if post_response.status_code in [200, 201]:
                # Extract SAP Contract Number from response
                try:
                    response_data = post_response.json()
                    sap_contract_number = response_data.get("d", {}).get("SalesContract", "")
                except Exception:
                    sap_contract_number = ""

                # Save contract number + mark success
                frappe.db.set_value("Sales Order", doc.name, {
                    "custom_sales_contract_created": 1,
                    "custom_sales_contract_failed": 0,
                    "custom_sap_contract_number": sap_contract_number
                })

                # Add success comment on Sales Order document
                doc.add_comment("Comment", text=f"✅ SAP Contract Created Successfully.\nSAP Contract Number: {sap_contract_number}")

                frappe.db.commit()
                print(f"--- SAP Contract Number saved: {sap_contract_number} for SO: {doc.name} ---")

            else:
                # Parse SAP error message from response
                try:
                    error_response = post_response.json()
                    sap_error = error_response.get("error", {}).get("message", {}).get("value", post_response.text)
                except Exception:
                    sap_error = post_response.text

                error_msg = f"SAP Contract Creation Failed.\nStatus Code: {post_response.status_code}\nSAP Error: {sap_error}"

                print(f"--- Error Response for SO: {doc.name} ---")
                print(error_msg)
                
                frappe.log_error(
                    f"Payload: {json.dumps(payload, indent=4)}\n\nResponse:\n{error_msg}",
                    f"SAP Sales Contract Creation Failed - {doc.name}"
                )

                # Add failure comment on Sales Order document
                doc.add_comment("Comment", text=f"❌ SAP Contract Creation Failed:\nStatus Code: {post_response.status_code}\nSAP Error: {sap_error}")

                frappe.db.set_value("Sales Order", doc.name, "custom_sales_contract_failed", 1)
                frappe.db.commit()

        except Exception as e:
            error_detail = f"Exception: {str(e)}\n{traceback.format_exc()}"
            frappe.log_error(
                f"Error processing {so_info.name}: {error_detail}",
                f"SAP Sync Exception - {so_info.name}"
            )

            # Add exception comment on Sales Order document
            try:
                so_doc = frappe.get_doc("Sales Order", so_info.name)
                so_doc.add_comment("Comment", text=f"❌ SAP Contract Sync Exception:\n{str(e)}")
            except Exception:
                pass

            frappe.db.set_value("Sales Order", so_info.name, "custom_sales_contract_failed", 1)
            frappe.db.commit()