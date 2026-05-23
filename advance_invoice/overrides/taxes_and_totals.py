from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
from frappe.utils import flt


class CustomTaxesAndTotals(calculate_taxes_and_totals):
	def apply_discount_amount(self):
		super().apply_discount_amount()

		if not self.doc.discount_amount:
			return

		negative_items = [item for item in self.doc.items if flt(item.amount) <= 0]

		if not negative_items:
			return

		positive_items = [item for item in self.doc.items if flt(item.amount) > 0]

		removed_discount = 0

		for item in negative_items:
			removed_discount += flt(item.distributed_discount_amount)

			item.distributed_discount_amount = 0

		if not removed_discount:
			return

		positive_total = sum(flt(item.amount) for item in positive_items)

		remaining = removed_discount

		precision = self.doc.precision("distributed_discount_amount")

		for idx, item in enumerate(positive_items):
			if idx == len(positive_items) - 1:
				additional = remaining
			else:
				additional = round(
					removed_discount * flt(item.amount) / positive_total,
					precision,
				)

				remaining -= additional

			item.distributed_discount_amount += additional
