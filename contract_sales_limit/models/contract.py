# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Contract(models.Model):
    _inherit = 'contract.contract'

    approval_team_id = fields.Many2one('contract.approval.team', string='Approval Team',
                                       help='Team responsible for approving this contract')
    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Approval State', default='draft', tracking=True)
    
    approved_by_id = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Datetime(string='Approval Date', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason')
    
    # Financial limits
    contract_amount = fields.Monetary(string='Contract Amount', currency_field='currency_id',
                                      help='Total approved amount for this contract')
    used_amount = fields.Monetary(string='Used Amount', compute='_compute_used_amount', 
                                  store=True, currency_field='currency_id')
    remaining_amount = fields.Monetary(string='Remaining Amount', compute='_compute_remaining_amount',
                                       store=True, currency_field='currency_id')
    
    sale_order_ids = fields.One2many('sale.order', 'contract_id', string='Sale Orders')
    sale_order_count = fields.Integer(string='Sale Orders', compute='_compute_sale_order_count')
    
    # Override state to integrate with approval
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
    ], ondelete={'draft': 'set default'})
    
    def _compute_sale_order_count(self):
        for contract in self:
            contract.sale_order_count = len(contract.sale_order_ids)
    
    @api.depends('sale_order_ids', 'sale_order_ids.state', 'sale_order_ids.amount_total')
    def _compute_used_amount(self):
        for contract in self:
            confirmed_orders = contract.sale_order_ids.filtered(
                lambda o: o.state in ['sale', 'done']
            )
            contract.used_amount = sum(confirmed_orders.mapped('amount_total'))
    
    @api.depends('contract_amount', 'used_amount')
    def _compute_remaining_amount(self):
        for contract in self:
            contract.remaining_amount = contract.contract_amount - contract.used_amount
    
    def action_submit_for_approval(self):
        """Submit contract for approval"""
        for contract in self:
            if not contract.approval_team_id:
                raise UserError(_('Please assign an approval team before submitting for approval.'))
            if contract.contract_amount <= 0:
                raise UserError(_('Contract amount must be greater than zero.'))
            contract.approval_state = 'pending'
    
    def action_approve_contract(self):
        """Approve contract - only by authorized approvers"""
        for contract in self:
            if not contract.approval_team_id:
                raise UserError(_('No approval team assigned to this contract.'))
            
            # Check if current user is an authorized approver
            approver = contract.approval_team_id.approver_ids.filtered(
                lambda a: a.user_id == self.env.user
            )
            
            if not approver and self.env.user != contract.approval_team_id.team_leader_id:
                raise UserError(_('You are not authorized to approve this contract.'))
            
            # Check amount limits if approver found
            if approver:
                if approver.maximum_amount > 0 and contract.contract_amount > approver.maximum_amount:
                    raise UserError(_(
                        'The contract amount (%(amount)s) exceeds your approval limit (%(limit)s).',
                        amount=contract.contract_amount,
                        limit=approver.maximum_amount
                    ))
                if contract.contract_amount < approver.minimum_amount:
                    raise UserError(_(
                        'The contract amount (%(amount)s) is below your minimum approval amount (%(min)s).',
                        amount=contract.contract_amount,
                        min=approver.minimum_amount
                    ))
            
            contract.write({
                'approval_state': 'approved',
                'approved_by_id': self.env.user.id,
                'approved_date': fields.Datetime.now(),
                'state': 'open',  # Activate the contract
            })
    
    def action_reject_contract(self):
        """Reject contract"""
        for contract in self:
            if not contract.approval_team_id:
                raise UserError(_('No approval team assigned to this contract.'))
            
            # Check if current user is an authorized approver
            approver = contract.approval_team_id.approver_ids.filtered(
                lambda a: a.user_id == self.env.user
            )
            
            if not approver and self.env.user != contract.approval_team_id.team_leader_id:
                raise UserError(_('You are not authorized to reject this contract.'))
            
            contract.approval_state = 'rejected'
    
    def action_reset_to_draft(self):
        """Reset contract to draft"""
        for contract in self:
            contract.write({
                'approval_state': 'draft',
                'approved_by_id': False,
                'approved_date': False,
                'rejection_reason': False,
            })
    
    def action_view_sale_orders(self):
        """View sale orders linked to this contract"""
        self.ensure_one()
        return {
            'name': _('Sale Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id}
        }
    
    @api.constrains('contract_amount')
    def _check_contract_amount(self):
        for contract in self:
            if contract.contract_amount < 0:
                raise ValidationError(_('Contract amount cannot be negative.'))
