import frappe
from frappe.model.document import Document

class SAPPayment(Document):
	def validate(self):
		self.ensure_custom_fields()
		self.set_payment_id()
		self.link_sales_order()

	def ensure_custom_fields(self):
		"""Programmatically create custom_sap_contract_number custom field if it does not exist in database."""
		if not frappe.db.exists("Custom Field", "Sales Order-custom_sap_contract_number"):
			try:
				frappe.get_doc({
					"doctype": "Custom Field",
					"dt": "Sales Order",
					"fieldname": "custom_sap_contract_number",
					"label": "SAP Contract Number",
					"fieldtype": "Data",
					"insert_after": "custom_sales_contract_failed",
					"read_only": 1,
					"module": "SAP App"
				}).insert(ignore_permissions=True)
				frappe.clear_cache(doctype="Sales Order")
				frappe.logger().info("Created missing Custom Field: Sales Order-custom_sap_contract_number")
			except Exception as e:
				frappe.logger().error(f"Failed to dynamically create custom_sap_contract_number custom field: {str(e)}")

	def set_payment_id(self):
		if self.bukrs and self.belnr and self.gjahr and self.buzei:
			self.payment_id = f"{self.bukrs}-{self.belnr}-{self.gjahr}-{self.buzei}"

	def link_sales_order(self):
		if self.vbel2 and not self.sales_order:
			so = None
			
			# 1. Try matching VBEL2 to custom_sap_contract_number
			try:
				so = frappe.db.get_value("Sales Order", {"custom_sap_contract_number": self.vbel2}, "name")
			except Exception as e:
				frappe.logger().warn(f"Failed to query Sales Order by custom_sap_contract_number: {str(e)}")
			
			# 2. Try matching after stripping leading zeros from VBEL2
			if not so:
				stripped_vbel = self.vbel2.lstrip('0')
				if stripped_vbel:
					try:
						so = frappe.db.get_value("Sales Order", {"custom_sap_contract_number": ["like", f"%{stripped_vbel}"]})
					except Exception as e:
						pass
			
			# 3. Try matching directly by Sales Order ID
			if not so:
				try:
					so = frappe.db.get_value("Sales Order", {"name": self.vbel2}, "name")
				except Exception as e:
					pass
				
			if so:
				self.sales_order = so
