from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals


class CustomTaxesAndTotals(calculate_taxes_and_totals):
	def apply_discount_amount(self):
		super().apply_discount_amount()
		self.remove_adv_discount_distribution()

	def remove_adv_discount_distribution(self):
		for item in self.doc.items:
			if item.item_code != "ADV":
				continue

			if item.amount >= 0:
				continue

			distributed = item.distributed_discount_amount or 0

			if not distributed:
				continue

			item.distributed_discount_amount = 0

			item.net_amount -= distributed
			item.base_net_amount -= distributed

			if item.qty:
				item.net_rate = item.net_amount / item.qty
				item.base_net_rate = item.base_net_amount / item.qty
