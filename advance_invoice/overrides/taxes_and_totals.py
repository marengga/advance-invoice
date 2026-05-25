import frappe
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
from frappe.utils import flt


class CustomTaxesAndTotals(calculate_taxes_and_totals):
	def apply_discount_amount(self):
		if not self.doc.discount_amount:
			self.doc.base_discount_amount = 0
			return

		if not self.doc.apply_discount_on:
			frappe.throw("Please select Apply Discount On")

		self.doc.base_discount_amount = flt(
			self.doc.discount_amount * self.doc.conversion_rate,
			self.doc.precision("base_discount_amount"),
		)

		if self.doc.apply_discount_on == "Grand Total" and self.doc.get("is_cash_or_non_trade_discount"):
			self.discount_amount_applied = True
			return

		negative_items = [item for item in self._items if flt(item.amount) <= 0]
		for item in negative_items:
			item.distributed_discount_amount = 0

		positive_items = [item for item in self._items if flt(item.amount) > 0]

		if not positive_items:
			self.discount_amount_applied = True
			self._calculate()
			return

		positive_total = sum(flt(item.net_amount) for item in positive_items)
		if not positive_total:
			self.discount_amount_applied = True
			self._calculate()
			return

		net_total = 0
		expected_net_total = 0
		remaining_discount = flt(self.doc.discount_amount)

		precision = self.doc.precision("distributed_discount_amount")

		for idx, item in enumerate(positive_items):
			if idx == len(positive_items) - 1:
				distributed_amount = remaining_discount
			else:
				distributed_amount = flt(
					self.doc.discount_amount * flt(item.net_amount) / positive_total,
					precision,
				)

				remaining_discount -= distributed_amount

			adjusted_net_amount = item.net_amount - distributed_amount
			expected_net_total += adjusted_net_amount
			item.net_amount = flt(adjusted_net_amount, item.precision("net_amount"))
			item.distributed_discount_amount = flt(
				distributed_amount, item.precision("distributed_discount_amount")
			)
			net_total += item.net_amount

			rounding_difference = flt(expected_net_total - net_total, self.doc.precision("net_total"))
			if rounding_difference:
				item.net_amount = flt(item.net_amount + rounding_difference, item.precision("net_amount"))
				item.distributed_discount_amount = flt(
					distributed_amount + rounding_difference,
					item.precision("distributed_discount_amount"),
				)
				net_total += rounding_difference

			item.net_rate = flt(item.net_amount / item.qty, item.precision("net_rate")) if item.qty else 0
			self._set_in_company_currency(item, ["net_rate", "net_amount"])

		self.discount_amount_applied = True
		self._calculate()
