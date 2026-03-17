

import frappe
from frappe.model.document import Document
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta


class SAPIntegrationSettings(Document):

	
	def get_sap_data(self):
		"""Fetch data from SAP and return it for preview."""
		records = self._fetch_records_from_sap()
		return records


	
	def process_sap_data(self):
		"""Fetch and insert/update records in SAP Sales Register."""
		records = self._fetch_records_from_sap()

		count_created = 0
		count_updated = 0

		meta = frappe.get_meta("SAP Sales Register")
		valid_fields = [df.fieldname for df in meta.fields]

		for record in records:
			vbeln = record.get("vbeln")
			posnr = record.get("posnr", "")

			doc_name = None
			if vbeln:
				existing = frappe.db.get_value(
					"SAP Sales Register",
					{"vbeln": vbeln, "posnr": posnr},
					"name"
				)
				if existing:
					doc_name = existing

			doc_dict = {"doctype": "SAP Sales Register"}

			for key, value in record.items():
				lower_key = key.lower()
				if lower_key in valid_fields:
					doc_dict[lower_key] = value

			if doc_name:
				doc = frappe.get_doc("SAP Sales Register", doc_name)
				doc.update(doc_dict)
				doc.save()
				count_updated += 1
			else:
				doc = frappe.get_doc(doc_dict)
				doc.insert()
				count_created += 1

		frappe.db.commit()

		return {
			"status": "success",
			"message": f"Successfully processed {len(records)} records.",
			"created": count_created,
			"updated": count_updated
		}


	def _fetch_records_from_sap(self):
		"""Fetch records from SAP using dynamic date range"""

		# Yesterday date
		yesterday = datetime.today() - timedelta(days=1)
		date_str = yesterday.strftime("%Y%m%d")

		base_url = "https://s4hana2.amitmetaliks.com:1043/sap/opu/odata/sap/ZMIS_DO_SRV/ES_SALREG001Set"

		url = (
			f"{base_url}?"
			f"$filter=SVkorg eq '1000' and "
			f"(SFkdat ge '{date_str}' and SFkdat le '{date_str}')"
			f"&$format=json"
		)

		frappe.logger().info(f"SAP API URL: {url}")

		response = requests.get(
			url,
			auth=HTTPBasicAuth(self.client_id, self.client_secret),
			verify=False
		)

		if response.status_code != 200:
			frappe.throw(f"Failed to fetch data from SAP. Status Code: {response.status_code}. Response: {response.text}")

		data = response.json()

		records = data.get("d", {}).get("results", [])

		return records

	def run_sap_sync():
		doc = frappe.get_single("SAP Integration Settings")
		doc.process_sap_data()
