import frappe
from frappe.model.document import Document
from frappe.utils import nowdate
from sap_app.sap_app.api_sync import sync_sales_contracts_to_sap

class SalesContract(Document):
	def validate(self):
		# Ensure is_synced is 0 for new documents or when significant fields change
		if self.is_new():
			self.is_synced = 0
			self.sap_sync_status = "Draft"
		
		self.calculate_totals()

	def calculate_totals(self):
		total = 0.0
		if hasattr(self, "items"):
			for item in self.items:
				item.amount = (item.qty or 0) * (item.rate or 0)
				total += item.amount
			self.total_net_amount = total
