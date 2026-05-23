import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from frappe.utils import flt


class CustomSalesInvoice(SalesInvoice):
	def get_gl_entries(self, warehouse_account=None):
		self.normalize_advance_item()
		gl_entries = super().get_gl_entries(warehouse_account)

		company = frappe.get_doc("Company", self.company)
		advance_account = company.default_advance_received_account

		if self.custom_is_advance:
			if not advance_account:
				frappe.throw(f"Default Advance Received Account has not been set for {company.name}")

			self.replace_income_account(gl_entries, advance_account)

		if advance_account:
			self.replace_advance_settlement(gl_entries, advance_account)

		self.rebalance_gl(gl_entries)

		return gl_entries

	def normalize_advance_item(self):
		for item in self.items:
			if item.item_code != "ADV":
				continue

			if item.amount >= 0:
				continue

			item.distributed_discount_amount = 0
			item.net_amount = item.amount
			item.net_rate = item.rate

	def replace_income_account(self, gl_entries, advance_account):
		item_accounts = {d.income_account for d in self.items if d.income_account}

		for gle in gl_entries:
			if gle.account in item_accounts and gle.credit > 0:
				gle.account = advance_account

	def replace_advance_settlement(self, gl_entries, advance_account):
		settlement_rows = [d for d in self.items if d.item_code == "ADV" and d.amount < 0]

		settlement_accounts = {d.income_account for d in settlement_rows}

		settlement_amount = abs(sum(d.amount for d in settlement_rows))

		for gle in gl_entries:
			if gle.account not in settlement_accounts:
				continue

			if gle.credit >= 0:
				continue

			gle.account = advance_account
			gle.debit = settlement_amount
			gle.credit = 0

	def rebalance_gl(self, gl_entries):
		total_debit = sum(flt(d.debit) for d in gl_entries)
		total_credit = sum(flt(d.credit) for d in gl_entries)

		difference = round(total_debit - total_credit, 2)

		if abs(difference) < 0.01:
			return

		roundoff = self.get_roundoff_account()

		existing = next(
			(d for d in gl_entries if d.account == roundoff),
			None,
		)

		if existing:
			if difference > 0:
				existing.credit += difference
			else:
				existing.debit += abs(difference)

			return

		gl_entries.append(
			self.get_gl_dict(
				{
					"account": roundoff,
					"credit": max(difference, 0),
					"debit": abs(min(difference, 0)),
				}
			)
		)

	def get_roundoff_account(self):
		company = frappe.get_cached_doc("Company", self.company)

		if company.round_off_account:
			return company.round_off_account

		frappe.throw(f"Default Round Off Account has not been set for {company.name}")
