from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_id = fields.Many2one('sale.contract', string='Contract', domain="[('state', 'in', ['approved', 'running'])]", tracking=True)

    @api.constrains('contract_id', 'amount_total')
    def _check_contract_limit(self):
        for order in self:
            if order.contract_id:
                # Real-time Validation
                if order.contract_id.amount_residual < order.amount_total:
                    raise ValidationError(
                        _("You cannot confirm this Sales Order. It exceeds the remaining balance of the contract. "
                          "Remaining: %s, Order Total: %s") % 
                        (order.contract_id.amount_residual, order.amount_total)
                    )

    def action_confirm(self):
        # Company Settings Check
        if self.env.company.sale_contract_required:
            for order in self:
                if not order.contract_id:
                    raise ValidationError(_("Company policy requires a valid contract for all Sales Orders."))
        
        # Check Limits again before final confirmation
        # (Because amount might have changed after the constraint check if lines were modified)
        for order in self:
            if order.contract_id:
                # Recalculate used amount including THIS order if we are simulating
                # Or simply check the constraint again
                if order.contract_id.amount_residual < order.amount_total:
                     raise ValidationError(_("Contract limit exceeded for Order %s.") % order.name)
        
        return super(SaleOrder, self).action_confirm()

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        # Optional: auto-fill lines from contract? Or just notify
        if self.contract_id:
            return {
                'warning': {
                    'title': _("Contract Loaded"),
                    'message': _("Ensure the order total stays within the contract limit: %s") % self.contract_id.amount_residual
                }
            }