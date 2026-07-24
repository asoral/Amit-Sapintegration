# Copyright (c) 2026, kanchan and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SAPSalesRegister(Document):
	def validate(self):
		self.sanitize_sap_numeric_fields()

	def sanitize_sap_numeric_fields(self):
		"""
		SAP formats negative numbers with a trailing minus sign (e.g. '4.820-' or '242445.32-').
		Convert trailing minus values into proper Python leading minus format (e.g. '-4.820').
		"""
		numeric_fields = [
			"fkimg", "tcs_base_amt", "tcsbaseamt", "inv_amt", "invamt", "base_amt", "baseamt",
			"tax_amt", "taxamt", "sgst", "cgst", "igst", "jtc1_amt", "jtc1amt",
			"jtc2_amt", "jtc2amt", "tcs", "round", "dis_amt", "disamt",
			"rate", "con_qty", "conqty", "so_qty", "soqty"
		]

		for fieldname in numeric_fields:
			val = getattr(self, fieldname, None)
			if val is not None and isinstance(val, str):
				val_str = val.strip()
				if val_str.endswith("-"):
					setattr(self, fieldname, "-" + val_str[:-1].strip())

