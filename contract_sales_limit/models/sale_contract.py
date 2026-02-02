from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class SaleContract(models.Model):
    _name = 'sale.contract'
    _description = 'Sales Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    # Basic Info
    name = fields.Char(string='Contract Reference', required=True, copy=False, readonly=True, default='New')
    title = fields.Char(string='Contract Title', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Approval & Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('running', 'Running'),
        ('expired', 'Expired'),
        ('to_renew', 'To Renew'),
    ], string='Status', default='draft', tracking=True, copy=False)
    
    approval_team_id = fields.Many2one('contract.approval.team', string='Approval Team', tracking=True)
    rejection_reason = fields.Text(string='Rejection Reason')
    approved_date = fields.Datetime(string='Approved Date', readonly=True)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)

    # Financials & Dates
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    date_start = fields.Date(string='Start Date', default=fields.Date.context_today, tracking=True)
    date_end = fields.Date(string='End Date', tracking=True)
    amount_total = fields.Monetary(string='Contract Amount', compute='_compute_amount_total', store=True)
    amount_used = fields.Monetary(string='Used Amount', compute='_compute_amount_used', store=True)
    amount_residual = fields.Monetary(string='Remaining Balance', compute='_compute_amount_residual', store=True)
    
    # Contract Lines
    line_ids = fields.One2many('sale.contract.line', 'contract_id', string='Contract Lines')
    
    # Sales Orders
    sale_order_ids = fields.One2many('sale.order', 'contract_id', string='Sales Orders')
    order_count = fields.Integer(string='Order Count', compute='_compute_order_count')

    # Terms
    terms_condition = fields.Html(string='Terms and Conditions')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.contract') or 'New'
        return super(SaleContract, self).create(vals)

    # Compute Methods
    @api.depends('line_ids.price_subtotal')
    def _compute_amount_total(self):
        for contract in self:
            contract.amount_total = sum(line.price_subtotal for line in contract.line_ids)

    @api.depends('sale_order_ids.state', 'sale_order_ids.amount_total')
    def _compute_amount_used(self):
        for contract in self:
            # Sum confirmed and done orders
            orders = contract.sale_order_ids.filtered(lambda o: o.state in ('sale', 'done'))
            contract.amount_used = sum(order.amount_total for order in orders)

    @api.depends('amount_total', 'amount_used')
    def _compute_amount_residual(self):
        for contract in self:
            contract.amount_residual = contract.amount_total - contract.amount_used

    def _compute_order_count(self):
        for contract in self:
            contract.order_count = len(contract.sale_order_ids)

    # Actions
    def action_submit(self):
        for rec in self:
            if not rec.approval_team_id:
                raise UserError(_("Please select an Approval Team first."))
            rec.state = 'pending'

    def action_approve(self):
        self.ensure_one()
        # Check Authorization
        current_user = self.env.user
        members = self.approval_team_id.member_ids.filtered(lambda m: m.user_id.id == current_user.id)
        
        if not members:
            raise UserError(_("You are not a member of the approval team for this contract."))

        # Check Limits
        can_approve = False
        for member in members:
            if member.min_amount <= self.amount_total <= member.max_amount:
                can_approve = True
                break
        
        if not can_approve:
            # Logic: If limit is 0 (from screenshot), assume unlimited or check if specific limit exists.
            # Based on screenshot "0.00 LE", it might mean specific limit not set.
            # Let's assume if limit is 0, they can approve anything up to the next tier, or simply allow it.
            # For strictness, let's enforce the limit.
             raise UserError(_("You are not authorized to approve a contract of this amount. Your limit: %s") % 
                             (", ".join(["%s - %s" % (m.min_amount, m.max_amount) for m in members])))

        self.write({
            'state': 'approved',
            'approved_by': current_user.id,
            'approved_date': fields.Datetime.now()
        })

    def action_reject(self):
        self.ensure_one()
        return {
            'name': _('Rejection Reason'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'contract.reject.wizard',
            'target': 'new',
            'context': {'default_contract_id': self.id}
        }

    def action_start(self):
        self.write({'state': 'running'})

    def action_cancel(self):
        self.write({'state': 'draft'})

    # Cron or Scheduled Action logic could be added here to move 'running' to 'expired' based on date_end

    def action_view_sales(self):
        return {
            'name': _('Sales Orders'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id}
        }

class SaleContractLine(models.Model):
    _name = 'sale.contract.line'
    _description = 'Contract Line'

    contract_id = fields.Many2one('sale.contract', string='Contract', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    name = fields.Text(string='Description', required=True)
    product_uom_qty = fields.Float(string='Quantity', default=1.0)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    price_unit = fields.Float(string='Unit Price', required=True)
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_amount', store=True)
    currency_id = fields.Many2one('res.currency', related='contract_id.currency_id', store=True)

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.price_subtotal = line.product_uom_qty * line.price_unit