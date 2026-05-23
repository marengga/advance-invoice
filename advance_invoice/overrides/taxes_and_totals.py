from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
from frappe.utils import flt


class CustomTaxesAndTotals(calculate_taxes_and_totals):
	def apply_discount_amount(self):
		if not self.doc.discount_amount:
			return super().apply_discount_amount()

		adv_rows = [d for d in self.doc.items if d.item_code == "ADV"]

		if not adv_rows:
			return super().apply_discount_amount()

		positive_items = [d for d in self.doc.items if d.amount > 0]

		positive_total = sum(flt(d.amount) for d in positive_items)

		if not positive_total:
			return

		discount = flt(self.doc.discount_amount)

		remaining = discount

		for idx, item in enumerate(positive_items):
			share = round(
				discount * item.amount / positive_total,
				2,
			)

			if idx == len(positive_items) - 1:
				share = remaining

			remaining -= share

			item.distributed_discount_amount = share

		for item in adv_rows:
			item.distributed_discount_amount = 0

		self._calculate()
