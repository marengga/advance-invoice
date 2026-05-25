__version__ = "0.3.7"

import erpnext.controllers.taxes_and_totals as tt

from advance_invoice.overrides.taxes_and_totals import CustomTaxesAndTotals

tt.calculate_taxes_and_totals = CustomTaxesAndTotals
