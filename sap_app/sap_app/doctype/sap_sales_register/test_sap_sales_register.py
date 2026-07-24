# Copyright (c) 2026, kanchan and Contributors
# See license.txt

# import frappe
from frappe.tests.utils import FrappeTestCase


class TestSAPSalesRegister(FrappeTestCase):
	def test_sanitize_sap_numeric_fields(self):
		doc = frappe.new_doc("SAP Sales Register")
		doc.fkimg = "17.68-"
		doc.invamt = "242445.32-"
		doc.rate = "4.820"
		doc.sanitize_sap_numeric_fields()
		self.assertEqual(doc.fkimg, "-17.68")
		self.assertEqual(doc.invamt, "-242445.32")
		self.assertEqual(doc.rate, "4.820")

