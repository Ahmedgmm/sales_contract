from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ContractApprovalTeam(models.Model):
    _name = 'contract.approval.team'
    _description = 'Contract Approval Team'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Team Name', required=True, tracking=True)
    member_ids = fields.One2many('contract.approver.member', 'team_id', string='Members')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

class ContractApproverMember(models.Model):
    _name = 'contract.approver.member'
    _description = 'Contract Approver Member'

    team_id = fields.Many2one('contract.approval.team', string='Team', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Approver', required=True, ondelete='cascade')
    role = fields.Char(string='Role/Position', default='Approver')
    min_amount = fields.Float(string='Min Approval Amount', default=0.0, help='Minimum amount this user can approve')
    max_amount = fields.Float(string='Max Approval Amount', required=True, help='Maximum amount this user can approve')

    _sql_constraints = [
        ('unique_user_per_team', 'UNIQUE(team_id, user_id)', 'A user can only be once in a team.'),
    ]