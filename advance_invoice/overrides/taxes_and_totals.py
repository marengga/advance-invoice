from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
from frappe.utils import flt


class CustomTaxesAndTotals(calculate_taxes_and_totals):
	def apply_discount_amount(self):
		if not self.doc.discount_amount:
			return super().apply_discount_amount()

		positive_items = [item for item in self.doc.items if flt(item.amount) > 0]

		negative_items = [item for item in self.doc.items if flt(item.amount) <= 0]

		if not negative_items:
			return super().apply_discount_amount()

		positive_total = sum(flt(item.amount) for item in positive_items)

		if not positive_total:
			return super().apply_discount_amount()

		remaining_discount = flt(self.doc.discount_amount)

		for idx, item in enumerate(positive_items):
			if idx == len(positive_items) - 1:
				distributed = remaining_discount
			else:
				distributed = round(
					flt(self.doc.discount_amount) * flt(item.amount) / positive_total,
					self.doc.precision("discount_amount"),
				)

				remaining_discount -= distributed

			item.distributed_discount_amount = distributed

		for item in negative_items:
			item.distributed_discount_amount = 0

		self._calculate()
