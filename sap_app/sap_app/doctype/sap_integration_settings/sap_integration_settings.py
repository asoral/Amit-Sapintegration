# Copyright (c) 2026, kanchan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
from requests.auth import HTTPBasicAuth

class SAPIntegrationSettings(Document):
	@frappe.whitelist()
	def fetch_data_from_sap(self):
		if not self.sap_get_url:
			frappe.throw("Please provide the SAP Get URL.")
		
		if not self.client_id or not self.client_secret:
			frappe.throw("Please provide both Client ID and Client Secret.")

		try:
			response = requests.get(
				self.sap_get_url,
				auth=HTTPBasicAuth(self.client_id, self.client_secret),
				verify=False,
				timeout=10
			)

			if response.status_code == 200:
				return response.json()
			else:
				# Return the error response but also log it for the user
				error_msg = f"Failed to fetch data from SAP. Status Code: {response.status_code}"
				frappe.msgprint(error_msg, indicator="red")
				return {"status": "error", "message": f"{error_msg}. Response: {response.text}"}

		except requests.exceptions.RequestException as e:
			frappe.throw(f"An error occurred while connecting to SAP: {str(e)}")
