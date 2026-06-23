import frappe
from frappe.model.document import Document
from frappe.utils import getdate
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import urllib3

# Disable SSL warnings for unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def parse_sap_amount(val):
	"""Parse SAP currency/numeric fields, handling trailing minus signs for credits."""
	if not val:
		return 0.0
	val_str = str(val).strip()
	is_negative = False
	if val_str.endswith('-'):
		is_negative = True
		val_str = val_str[:-1].strip()
	elif val_str.startswith('-'):
		is_negative = True
		val_str = val_str[1:].strip()
	try:
		amount = float(val_str)
		return -amount if is_negative else amount
	except ValueError:
		return 0.0


def parse_sap_date(val):
	"""Parse YYYYMMDD string format from SAP to YYYY-MM-DD format."""
	if not val:
		return None
	val_str = str(val).strip()
	if len(val_str) == 8 and val_str.isdigit():
		return f"{val_str[:4]}-{val_str[4:6]}-{val_str[6:]}"
	return val_str


class SAPIntegrationSettings(Document):

	def get_client_credentials(self):
		"""Retrieve client ID and client secret, with decryption error fallback."""
		client_id = self.client_id or "AMLRFC"
		client_secret = None
		try:
			client_secret = self.get_password("client_secret")
		except Exception:
			pass
		if not client_secret:
			client_secret = "N6@ko}>49ki6=tUYoZprlKQ[v7-43K+cDf/\\yzhg"
		return client_id, client_secret

	@frappe.whitelist()
	def get_sap_data(self):
		"""Fetch data from SAP and return it for preview."""
		records = self.fetch_records_from_sap()
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
				doc.save(ignore_permissions=True)
				count_updated += 1
			else:
				doc = frappe.get_doc(doc_dict)
				doc.insert(ignore_permissions=True)
				count_created += 1

		frappe.db.commit()

		return {
			"status": "success",
			"message": f"Successfully processed {len(records)} records.",
			"created": count_created,
			"updated": count_updated
		}

	@frappe.whitelist()
	def insert_process_sap_data(self):
		"""Fetch and insert/update records in SAP Sales Register."""
		records = self.fetch_records_from_sap()

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
				doc.save(ignore_permissions=True)
				count_updated += 1
			else:
				doc = frappe.get_doc(doc_dict)
				doc.insert(ignore_permissions=True)
				count_created += 1

		frappe.db.commit()

		return {
			"status": "success",
			"message": f"Successfully processed {len(records)} records.",
			"created": count_created,
			"updated": count_updated
		}

	def fetch_records_from_sap(self):
		"""Fetch records from SAP using dynamic date range"""
		from_date = getdate(self.from_date)
		to_date = getdate(self.to_date)

		date_str1 = from_date.strftime("%Y%m%d")
		date_str2 = to_date.strftime("%Y%m%d")

		frappe.logger().info(f"From: {date_str1}, To: {date_str2}")

		base_url = "https://s4hana1.amitmetaliks.com:1043/sap/opu/odata/sap/ZMIS_DO_SRV/ES_SALREG001Set"

		url = (
			f"{base_url}?"
			f"$filter=SVkorg eq '1000' and "
			f"(SFkdat ge '{date_str1}' and SFkdat le '{date_str2}')"
			f"&$format=json"
		)

		frappe.logger().info(f"SAP API URL: {url}")

		client_id, client_secret = self.get_client_credentials()
		response = requests.get(
			url,
			auth=HTTPBasicAuth(client_id, client_secret),
			verify=False
		)

		if response.status_code != 200:
			frappe.throw(f"Failed to fetch data from SAP. Status Code: {response.status_code}. Response: {response.text}")

		data = response.json()
		records = data.get("d", {}).get("results", [])

		return records

	def _fetch_records_from_sap(self):
		"""Fetch records from SAP using dynamic date range"""
		yesterday = datetime.today() - timedelta(days=1)
		date_str = yesterday.strftime("%Y%m%d")

		base_url = "https://s4hana1.amitmetaliks.com:1043/sap/opu/odata/sap/ZMIS_DO_SRV/ES_SALREG001Set"

		url = (
			f"{base_url}?"
			f"$filter=SVkorg eq '1000' and "
			f"(SFkdat ge '{date_str}' and SFkdat le '{date_str}')"
			f"&$format=json"
		)

		frappe.logger().info(f"SAP API URL: {url}")

		client_id, client_secret = self.get_client_credentials()
		response = requests.get(
			url,
			auth=HTTPBasicAuth(client_id, client_secret),
			verify=False
		)

		if response.status_code != 200:
			frappe.throw(f"Failed to fetch data from SAP. Status Code: {response.status_code}. Response: {response.text}")

		data = response.json()
		records = data.get("d", {}).get("results", [])

		return records

	# ==================== SAP Payment Integration Methods ====================

	def get_sap_payment_oauth_token(self):
		"""Fetch OAuth2 token for ZPAYMENT_API_SRV"""
		token_url = "https://s4hana1.amitmetaliks.com:1043/sap/bc/sec/oauth2/token"
		client_id, client_secret = self.get_client_credentials()
		payload = {
			"grant_type": "client_credentials",
			"client_id": client_id,
			"client_secret": client_secret,
			"scope": "ZPAYMENT_API_SRV_0001",
			"state": "12345"
		}
		headers = {"Content-Type": "application/x-www-form-urlencoded"}
		response = requests.post(token_url, data=payload, headers=headers, verify=False, timeout=30)
		response.raise_for_status()
		return response.json().get("access_token")

	def fetch_payments_from_sap(self, from_date=None, to_date=None):
		"""Fetch payment records from SAP using optional date filters"""
		base_url = "https://s4hana1.amitmetaliks.com:1043/sap/opu/odata/sap/ZPAYMENT_API_SRV/ZES_PaymentSet"
		params = {"$format": "json"}

		filters = ["BUKRS eq '1000'"]
		if from_date and to_date:
			date_str1 = getdate(from_date).strftime("%Y%m%d")
			date_str2 = getdate(to_date).strftime("%Y%m%d")
			filters.append(f"(BUDAT ge '{date_str1}' and BUDAT le '{date_str2}')")

		params["$filter"] = " and ".join(filters)

		token = None
		try:
			token = self.get_sap_payment_oauth_token()
		except Exception as e:
			frappe.logger().warn(f"OAuth2 fetch failed for SAP Payments: {str(e)}. Using Basic Auth.")

		headers = {}
		auth = None
		client_id, client_secret = self.get_client_credentials()
		if token:
			headers["Authorization"] = f"Bearer {token}"
		else:
			auth = HTTPBasicAuth(client_id, client_secret)

		# Try with filters, fall back to unfiltered if SAP throws an error
		try:
			response = requests.get(
				base_url,
				params=params,
				headers=headers,
				auth=auth,
				verify=False,
				timeout=60
			)
			response.raise_for_status()
		except Exception as e:
			if "$filter" in params:
				frappe.logger().warn(f"SAP Payment fetch with filter failed: {str(e)}. Retrying without filter.")
				params.pop("$filter", None)
				response = requests.get(
					base_url,
					params=params,
					headers=headers,
					auth=auth,
					verify=False,
					timeout=60
				)
				response.raise_for_status()
			else:
				raise e

		data = response.json()
		return data.get("d", {}).get("results", [])

	@frappe.whitelist()
	def get_sap_payment_data(self):
		"""Fetch payment records from SAP and return them for preview."""
		return self.fetch_payments_from_sap(self.from_date, self.to_date)

	@frappe.whitelist()
	def process_sap_payment_data_manual(self):
		"""Fetch and sync payment records manually based on settings dates."""
		return self.process_sap_payment_data(self.from_date, self.to_date)

	def process_sap_payment_data(self, from_date=None, to_date=None):
		"""Map SAP payment records and insert/update them in SAP Payment DocType."""
		records = self.fetch_payments_from_sap(from_date, to_date)

		count_created = 0
		count_updated = 0

		for record in records:
			bukrs = record.get("BUKRS")
			belnr = record.get("BELNR")
			gjahr = record.get("GJAHR")
			buzei = record.get("BUZEI")

			if not (bukrs and belnr and gjahr and buzei):
				continue

			payment_id = f"{bukrs}-{belnr}-{gjahr}-{buzei}"

			doc_dict = {
				"doctype": "SAP Payment",
				"payment_id": payment_id,
				"bukrs": bukrs,
				"belnr": belnr,
				"gjahr": gjahr,
				"buzei": buzei,
				"kunnr": record.get("KUNNR"),
				"name1": record.get("NAME1"),
				"vbel2": record.get("VBEL2"),
				"vertn": record.get("VERTN"),
				"prctr": record.get("PRCTR"),
				"blart": record.get("BLART"),
				"vorgn": record.get("VORGN"),
				"koart": record.get("KOART"),
				"shkzg": record.get("SHKZG"),
				"bldat": parse_sap_date(record.get("BLDAT")),
				"budat": parse_sap_date(record.get("BUDAT")),
				"dmbtr": parse_sap_amount(record.get("DMBTR")),
				"cust_bal": parse_sap_amount(record.get("CUST_BAL")),
				"waers": record.get("WAERS"),
			}

			existing = frappe.db.exists("SAP Payment", payment_id)
			if existing:
				doc = frappe.get_doc("SAP Payment", payment_id)
				doc.update(doc_dict)
				doc.save(ignore_permissions=True)
				count_updated += 1
			else:
				doc = frappe.get_doc(doc_dict)
				doc.insert(ignore_permissions=True)
				count_created += 1

		frappe.db.commit()

		return {
			"status": "success",
			"message": f"Successfully processed {len(records)} payment records.",
			"created": count_created,
			"updated": count_updated
		}


# ==================== Scheduler Task Functions ====================

def run_sap_sync():
	doc = frappe.get_single("SAP Integration Settings")
	if not doc.enable:
		frappe.logger().info("SAP Sync skipped: Enable is OFF")
		return
	doc.process_sap_data()


def run_sap_payment_sync():
	doc = frappe.get_single("SAP Integration Settings")
	if not doc.enable:
		frappe.logger().info("SAP Payment Sync skipped: Enable is OFF")
		return

	# Fetch payments from yesterday and today to cover any time-zone / cutoff differences
	yesterday = datetime.today() - timedelta(days=1)
	today = datetime.today()
	doc.process_sap_payment_data(from_date=yesterday, to_date=today)