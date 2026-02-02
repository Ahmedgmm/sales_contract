from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_contract_required = fields.Boolean(string='Require Contract for Sales', 
                                            help="If checked, users cannot confirm a Sale Order without linking it to an approved/running contract.",
                                            config_parameter='sale_contract_approval.required_contract')