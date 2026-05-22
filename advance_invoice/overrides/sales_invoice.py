import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from frappe.utils import flt


class CustomSalesInvoice(SalesInvoice):
	def get_gl_entries(self, warehouse_account=None):
		gl_entries = super().get_gl_entries(warehouse_account)

		company = frappe.get_doc("Company", self.company)
		advance_account = company.default_advance_received_account

		if self.custom_is_advance:
			if not advance_account:
				frappe.throw(f"Default Advance Received Account has not been set for {company.name}")

			self.replace_income_account(gl_entries, advance_account)

		if advance_account:
			self.replace_advance_settlement(gl_entries, advance_account)

		return gl_entries

	def replace_income_account(self, gl_entries, advance_account):
		item_accounts = {d.income_account for d in self.items if d.income_account}

		for gle in gl_entries:
			if gle.account in item_accounts and gle.credit > 0:
				gle.account = advance_account

	def replace_advance_settlement(self, gl_entries, advance_account):
		settlement_amount = abs(
			sum(d.net_amount for d in self.items if d.item_code == "ADV" and d.amount < 0)
		)

		settlement_accounts = {d.income_account for d in self.items if d.item_code == "ADV"}

		for gle in gl_entries:
			if gle.account not in settlement_accounts:
				continue

			if abs(flt(gle.credit)) != settlement_amount:
				continue

			gle.account = advance_account

			if gle.credit < 0:
				gle.debit = abs(gle.credit)
				gle.credit = 0
