# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ContractApprovalTeam(models.Model):
    _name = 'contract.approval.team'
    _description = 'Contract Approval Team'
    _order = 'name'

    name = fields.Char(string='Team Name', required=True)
    team_leader_id = fields.Many2one('res.users', string='Team Leader', required=True)
    approver_ids = fields.One2many('contract.approval.team.approver', 'team_id', string='Approvers')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    @api.constrains('approver_ids')
    def _check_approvers(self):
        for team in self:
            if not team.approver_ids:
                raise ValidationError('At least one approver must be defined for the approval team.')


class ContractApprovalTeamApprover(models.Model):
    _name = 'contract.approval.team.approver'
    _description = 'Contract Approval Team Approver'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    team_id = fields.Many2one('contract.approval.team', string='Approval Team', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Approver', required=True)
    role_position = fields.Char(string='Role/Position')
    can_edit = fields.Boolean(string='Can Edit', default=False)
    minimum_amount = fields.Monetary(string='Minimum Amount', default=0.0, currency_field='currency_id')
    maximum_amount = fields.Monetary(string='Maximum Amount', default=0.0, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                   default=lambda self: self.env.company.currency_id)
    custom_condition_code = fields.Text(string='Custom Condition Code',
                                        help='Python code to evaluate custom conditions. Use "result" variable to set True/False.')
    
    _sql_constraints = [
        ('unique_user_team', 'unique(team_id, user_id)', 
         'An approver can only be added once per team!')
    ]
    
    @api.constrains('minimum_amount', 'maximum_amount')
    def _check_amounts(self):
        for approver in self:
            if approver.maximum_amount > 0 and approver.minimum_amount > approver.maximum_amount:
                raise ValidationError('Minimum amount cannot be greater than maximum amount.')
