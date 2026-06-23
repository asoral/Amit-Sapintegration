import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch

class TestSAPPayment(FrappeTestCase):
	def test_payment_id_generation(self):
		"""Test that validate() formats the payment_id field correctly."""
		doc = frappe.get_doc({
			"doctype": "SAP Payment",
			"bukrs": "1000",
			"belnr": "3000002438",
			"gjahr": "2026",
			"buzei": "002"
		})
		doc.validate()
		self.assertEqual(doc.payment_id, "1000-3000002438-2026-002")

	@patch('frappe.db.get_value')
	def test_link_sales_order_by_contract_number(self, mock_get_value):
		"""Test that validate() automatically finds and links Sales Order based on VBEL2 matching contract number."""
		# Simulate finding a Sales Order ID "SAL-ORD-2026-00044" when looking up by contract
		mock_get_value.side_effect = lambda doctype, filters, fieldname=None: (
			"SAL-ORD-2026-00044" if doctype == "Sales Order" and filters.get("custom_sap_contract_number") == "0200031543" else None
		)
		
		doc = frappe.get_doc({
			"doctype": "SAP Payment",
			"bukrs": "1000",
			"belnr": "3000002438",
			"gjahr": "2026",
			"buzei": "002",
			"vbel2": "0200031543"
		})
		doc.validate()
		self.assertEqual(doc.sales_order, "SAL-ORD-2026-00044")

	@patch('frappe.db.get_value')
	def test_link_sales_order_by_stripped_contract_number(self, mock_get_value):
		"""Test that validate() finds Sales Order by contract number stripped of leading zeros."""
		# Simulate finding nothing on exact match, but finding on stripped match
		def db_get_value_mock(doctype, filters, fieldname=None):
			if doctype == "Sales Order":
				if filters.get("custom_sap_contract_number") == "0200031543":
					return None
				elif filters.get("custom_sap_contract_number") == ["like", "%200031543"]:
					return "SAL-ORD-2026-00044"
			return None
			
		mock_get_value.side_effect = db_get_value_mock
		
		doc = frappe.get_doc({
			"doctype": "SAP Payment",
			"bukrs": "1000",
			"belnr": "3000002438",
			"gjahr": "2026",
			"buzei": "002",
			"vbel2": "0200031543"
		})
		doc.validate()
		self.assertEqual(doc.sales_order, "SAL-ORD-2026-00044")
