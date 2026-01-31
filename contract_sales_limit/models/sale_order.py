# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_id = fields.Many2one('contract.contract', string='Contract', 
                                  domain="[('partner_id', '=', partner_id), ('approval_state', '=', 'approved'), ('state', '=', 'open')]",
                                  tracking=True)
    contract_approval_state = fields.Selection(related='contract_id.approval_state', 
                                               string='Contract Approval', readonly=True)
    contract_remaining_amount = fields.Monetary(related='contract_id.remaining_amount',
                                                string='Contract Remaining', readonly=True)
    require_contract = fields.Boolean(string='Require Contract', 
                                      default=lambda self: self.env.company.sale_require_contract,
                                      help='If checked, this sale order requires an approved contract')
    
    @api.onchange('partner_id')
    def _onchange_partner_contract(self):
        """Reset contract when partner changes"""
        if self.partner_id:
            self.contract_id = False
    
    @api.constrains('contract_id', 'amount_total')
    def _check_contract_limit(self):
        """Check if sale order amount exceeds contract remaining amount"""
        for order in self:
            if order.contract_id and order.state in ['sale', 'done']:
                if order.amount_total > order.contract_id.remaining_amount + order.amount_total:
                    # Allow current order but check total doesn't exceed
                    other_orders_amount = sum(
                        order.contract_id.sale_order_ids.filtered(
                            lambda o: o.id != order.id and o.state in ['sale', 'done']
                        ).mapped('amount_total')
                    )
                    if order.amount_total + other_orders_amount > order.contract_id.contract_amount:
                        raise ValidationError(_(
                            'This sale order amount (%(amount)s) would exceed the contract limit. '
                            'Contract Amount: %(contract)s, Already Used: %(used)s, Available: %(available)s',
                            amount=order.amount_total,
                            contract=order.contract_id.contract_amount,
                            used=other_orders_amount,
                            available=order.contract_id.contract_amount - other_orders_amount
                        ))
    
    def action_confirm(self):
        """Override to check contract approval before confirmation"""
        for order in self:
            # Check if contract is required
            if order.require_contract or self.env.company.sale_require_contract:
                if not order.contract_id:
                    raise UserError(_(
                        'Cannot confirm sale order without an approved contract. '
                        'Please link an approved contract to this order.'
                    ))
                
                if order.contract_id.approval_state != 'approved':
                    raise UserError(_(
                        'The linked contract is not approved yet. '
                        'Contract Status: %(status)s',
                        status=dict(order.contract_id._fields['approval_state'].selection).get(
                            order.contract_id.approval_state
                        )
                    ))
                
                if order.contract_id.state != 'open':
                    raise UserError(_(
                        'The linked contract is not in running state. '
                        'Please ensure the contract is active.'
                    ))
                
                # Check remaining amount
                if order.amount_total > order.contract_id.remaining_amount:
                    raise UserError(_(
                        'This sale order amount (%(amount)s) exceeds the contract remaining amount (%(remaining)s). '
                        'Contract Total: %(contract)s, Used: %(used)s',
                        amount=order.amount_total,
                        remaining=order.contract_id.remaining_amount,
                        contract=order.contract_id.contract_amount,
                        used=order.contract_id.used_amount
                    ))
        
        return super(SaleOrder, self).action_confirm()
    
    def _prepare_invoice(self):
        """Add contract reference to invoice"""
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.contract_id:
            invoice_vals['ref'] = _('Contract: %s') % self.contract_id.name
        return invoice_vals


class ResCompany(models.Model):
    _inherit = 'res.company'

    sale_require_contract = fields.Boolean(
        string='Require Approved Contract for Sales',
        default=False,
        help='If checked, all sale orders will require an approved contract before confirmation'
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_require_contract = fields.Boolean(
        related='company_id.sale_require_contract',
        readonly=False,
        string='Require Approved Contract for Sales'
    )
