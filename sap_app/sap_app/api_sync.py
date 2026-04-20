import frappe
import requests
import json
from frappe.utils import now_datetime, flt
from requests.auth import HTTPBasicAuth

def format_sap_id(value):
	"""Pad numeric IDs with leading zeros up to 10 digits."""
	if value and str(value).isdigit():
		return str(value).zfill(10)
	return str(value or "")

def format_item_position(value):
	"""Pad item position with leading zeros up to 6 digits (e.g. 000010)."""
	if value and str(value).isdigit():
		return str(value).zfill(6)
	# If already formatted or alphanumeric, return as-is
	return str(value or "000010")

def format_quantity(value):
	"""Return quantity as a string. Use integer string if whole number (e.g. '10' not '10.0')."""
	f = flt(value)
	if f == int(f):
		return str(int(f))
	return str(f)

def clean_payload(d):
	"""Recursively remove empty strings from dictionaries to prevent SAP GETWA_NOT_ASSIGNED dumps."""
	if isinstance(d, dict):
		return {k: clean_payload(v) for k, v in d.items() if v != ""}
	elif isinstance(d, list):
		return [clean_payload(v) for v in d]
	return d

@frappe.whitelist()
def sync_sales_contracts_to_sap(docname=None):
	"""
	Scheduler job to sync Sales Contracts to SAP daily.
	Handles CSRF token fetch and PascalCase field mapping.
	Can be run manually for a specific document by passing docname.
	"""
	# 1. Fetch Sales Contracts to sync
	if docname:
		contracts = [{"name": docname}]
	else:
		contracts = frappe.get_all("Sales Contract", 
			filters={"sap_sync_status": ["!=", "Synced"]},
			fields=["name"]
		)
	
	if not contracts:
		return "No contracts to sync."

	# SAP Credentials
	settings = frappe.get_single("SAP Integration Settings")
	if not settings.enable:
		return "SAP Integration is disabled in settings."

	client_id = settings.client_id
	client_secret = settings.get_password("client_secret")
	auth = HTTPBasicAuth(client_id, client_secret)

	# SAP Endpoints
	base_url = "https://s4hana2.amitmetaliks.com:1043/sap/opu/odata/sap/API_SALES_CONTRACT_SRV"
	token_url = f"{base_url}/$metadata"
	post_url = f"{base_url}/A_SalesContract"

	# 2. Fetch CSRF Token
	try:
		token_response = requests.get(
			token_url, 
			auth=auth, 
			headers={"x-csrf-token": "fetch"},
			timeout=30,
			verify=False
		)
		token_response.raise_for_status()
		csrf_token = token_response.headers.get("x-csrf-token")
		cookies = token_response.cookies
		
		if not csrf_token:
			frappe.log_error(title="SAP Sync Error", message="Failed to fetch CSRF token from SAP")
			return "Failed to fetch CSRF token."
			
	except Exception as e:
		frappe.log_error(title="SAP Sync Error", message=f"Error fetching SAP CSRF token:\n\n{str(e)}")
		return f"Error fetching token: {str(e)}"

	success_count = 0
	synced_list = []
	errors = []

	for c in contracts:
		doc = frappe.get_doc("Sales Contract", c.get("name"))
		
		# 3. Map ERPNext Doc to SAP PascalCase JSON
		payload = {
			"SalesContractType": doc.sales_contract_type,
			"SalesOrganization": doc.sales_organization,
			"DistributionChannel": doc.distribution_channel,
			"OrganizationDivision": doc.organization_division,
			"PurchaseOrderByCustomer": doc.purchase_order_by_customer,
			"SoldToParty": format_sap_id(doc.sold_to_party),
			"to_Item": [],
			"to_Partner": []
		}

		# Map Items
		for item in (doc.to_item or []):
			item_data = {
				"SalesContractItem": format_item_position(item.sales_contract_item),
				"Material": item.item_code,
				"ProductionPlant": item.production_plant,
				"RequestedQuantity": format_quantity(item.qty),
				"RequestedQuantityUnit": item.uom,
			}
			
			# Map Pricing Elements from JSON text field
			pricing_elements = []
			if item.pricing_elements_json:
				try:
					parsed_pe = json.loads(item.pricing_elements_json)
					if isinstance(parsed_pe, list):
						for pe in parsed_pe:
							pricing_elements.append({
								"ConditionType": pe.get("ConditionType"),
								"ConditionRateValue": "{:.2f}".format(flt(pe.get("ConditionRateValue"))),
								"ConditionCurrency": pe.get("ConditionCurrency"),
								"ConditionQuantity": format_quantity(pe.get("ConditionQuantity")),
								"ConditionQuantityUnit": pe.get("ConditionQuantityUnit")
							})
					elif isinstance(parsed_pe, dict):
						pe = parsed_pe
						pricing_elements.append({
							"ConditionType": pe.get("ConditionType"),
							"ConditionRateValue": "{:.2f}".format(flt(pe.get("ConditionRateValue"))),
							"ConditionCurrency": pe.get("ConditionCurrency"),
							"ConditionQuantity": format_quantity(pe.get("ConditionQuantity")),
							"ConditionQuantityUnit": pe.get("ConditionQuantityUnit")
						})
				except Exception as e:
					frappe.log_error(title="SAP Sync JSON Parse Error", message=f"Error parsing pricing elements for item {item.name}:\n{str(e)}\nData:\n{item.pricing_elements_json}")
			
			# Only add to_PricingElement if there are pricing rows
			if pricing_elements:
				item_data["to_PricingElement"] = pricing_elements
			
			payload["to_Item"].append(item_data)  # type: ignore

		# Map Partners
		# First collect partner roles already entered by user
		entered_roles = set()
		for partner in (doc.to_partner or []):
			role = partner.partner_role or ""
			customer = format_sap_id(partner.partner_name)
			payload["to_Partner"].append({
				"PartnerFunction": role,
				"Customer": customer
			})
			entered_roles.add(role)

		# Auto-add SP (Sold-to Party) if not already present
		if "SP" not in entered_roles and doc.sold_to_party:
			payload["to_Partner"].insert(0, {  # type: ignore
				"PartnerFunction": "SP",
				"Customer": format_sap_id(doc.sold_to_party)
			})

		# Clean empty strings before sending!
		payload = clean_payload(payload)

		try:
			# 4. POST to SAP
			headers = {
				"x-csrf-token": csrf_token,
				"Content-Type": "application/json",
				"Accept": "application/json"
			}
			
			response = requests.post(
				post_url, 
				auth=auth, 
				json=payload, 
				headers=headers, 
				cookies=cookies,
				timeout=60,
				verify=False
			)
			
			if response.status_code in [200, 201]:
				try:
					resp_json = response.json()
				except Exception:
					resp_json = response.text

				doc.db_set("is_synced", 1)
				doc.db_set("sap_sync_status", "Synced")
				doc.db_set("sap_response", json.dumps({
					"request_payload": payload,
					"response": resp_json
				}, indent=2))
				success_count += 1
				synced_list.append(doc.name)
			else:
				err_msg = f"API Error {response.status_code}: {response.text}"
				errors.append(f"Contract {doc.name}: {err_msg}")
				doc.db_set("sap_sync_status", "Failed")
				doc.db_set("sap_response", json.dumps({
					"request_payload": payload,
					"error": f"FAILED: {err_msg}"
				}, indent=2))
				
		except Exception as e:
			errors.append(f"Contract {doc.name}: {str(e)}")
			doc.db_set("sap_sync_status", "Failed")
			doc.db_set("sap_response", json.dumps({
				"request_payload": payload,
				"exception": str(e)
			}, indent=2))

	return {
		"status": "Success" if success_count > 0 and not errors else ("Partial" if success_count > 0 else "Failed"),
		"total_synced": success_count,
		"synced": synced_list,
		"errors": errors
	}
