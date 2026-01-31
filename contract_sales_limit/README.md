# Contract-Based Sales Limitation Module for Odoo 19

## Overview
This module restricts sales order confirmations based on approved contracts with configurable approval teams and amount limits.

## Features

### 1. Contract Approval Teams
- Create multiple approval teams with designated team leaders
- Define multiple approvers per team with:
  - Role/Position information
  - Minimum and maximum approval amounts
  - Edit permissions
  - Custom condition codes for advanced rules

### 2. Enhanced Contract Management
- **Approval Workflow**: Draft → Pending → Approved/Rejected
- **Financial Tracking**:
  - Contract Amount (total approved)
  - Used Amount (sum of confirmed sales)
  - Remaining Amount (available balance)
- **Approval Controls**:
  - Team-based approval with amount limits
  - Track approver and approval date
  - Rejection reasons
- **Integration**: Direct links to related sale orders

### 3. Sales Order Restrictions
- Link sale orders to approved contracts
- Prevent confirmation without valid contract (optional)
- Real-time validation of contract limits
- Visual alerts for missing or unapproved contracts
- Automatic remaining amount calculations

### 4. Configuration Options
- Company-wide setting to require contracts for all sales
- Per-order toggle to require contracts
- Multi-company support

## Installation

1. Copy the `contract_sales_limit` folder to your Odoo addons directory
2. Update the apps list: `Settings > Apps > Update Apps List`
3. Search for "Contract-Based Sales Limitation"
4. Click Install

**Dependencies**: This module requires the `contract` module to be installed first.

## Configuration

### Step 1: Create Approval Teams
1. Navigate to: `Sales > Contract Approval > Approval Teams`
2. Click "New"
3. Fill in:
   - Team Name (e.g., "Management Team")
   - Team Leader
4. Add Approvers:
   - User
   - Role/Position
   - Minimum/Maximum approval amounts
   - Can Edit permission

### Step 2: Configure Contracts
1. Go to: `Sales > Contract Approval > Contracts`
2. Create or edit a contract
3. Set:
   - Approval Team
   - Contract Amount (total limit)
   - Partner
4. Click "Submit for Approval"
5. Authorized approvers can then approve or reject

### Step 3: Link Sales Orders
1. Create a sale order
2. Select an approved contract from the dropdown
3. System validates:
   - Contract is approved
   - Contract is in running state
   - Order amount doesn't exceed remaining balance

### Step 4: Global Settings (Optional)
1. Go to: `Sales > Configuration > Settings`
2. Find "Require Approved Contract for Sales"
3. Enable to make contracts mandatory for all orders

## Usage Examples

### Example 1: Basic Setup
```
Approval Team: "Management"
- Team Leader: John Doe
- Approvers:
  * Alice (Manager): Min: 0, Max: 50,000
  * Bob (Director): Min: 50,000, Max: 200,000
  * Carol (CEO): Min: 200,000, Max: Unlimited (0)

Contract: "Annual Supply Agreement"
- Partner: ABC Corp
- Approval Team: Management
- Contract Amount: 100,000
- Status: Approved by Alice

Sale Orders:
- SO001: 30,000 (Confirmed) ✓
- SO002: 40,000 (Confirmed) ✓
- SO003: 35,000 (Cannot confirm - exceeds remaining 30,000) ✗
```

### Example 2: Approval Workflow
```
1. Sales team creates contract (Draft)
2. Submit for Approval (Pending)
3. Manager reviews:
   - If amount within limit → Approve → Contract Active
   - If amount exceeds limit → Escalate to Director
4. Once approved, sales team can create orders
```

## Technical Details

### Models Created
- `contract.approval.team`: Approval team configuration
- `contract.approval.team.approver`: Team member details with limits

### Models Extended
- `contract.contract`: Added approval workflow and financial tracking
- `sale.order`: Added contract linking and validation
- `res.company`: Added global contract requirement setting
- `res.config.settings`: Added configuration option

### Key Methods
- `contract.action_submit_for_approval()`: Submit contract for review
- `contract.action_approve_contract()`: Approve with limit validation
- `contract.action_reject_contract()`: Reject contract
- `sale_order.action_confirm()`: Override with contract validation

### Validation Rules
1. Contract must be approved before use
2. Contract must be in "Running" state
3. Sale order amount cannot exceed remaining contract balance
4. Approver must have sufficient approval limits
5. At least one approver required per team

## Security

### Access Rights
- **Sales Users**: Read contracts and approval teams
- **Sales Managers**: Full access to create/modify teams and contracts
- **Approvers**: Can approve/reject based on assigned team

### Approval Authorization
- Only team members can approve contracts
- Team leader has override authority
- Amount limits enforced per approver

## Customization

### Custom Approval Conditions
Use the "Custom Condition Code" field in approvers to add Python logic:
```python
# Example: Approve only for specific partners
result = contract.partner_id.id in [1, 2, 3]

# Example: Approve based on contract type
result = contract.type_id.name == 'Annual'

# Example: Time-based approval
from datetime import datetime
result = datetime.now().month in [1, 2, 3]  # Q1 only
```

## Troubleshooting

### Issue: "Cannot confirm sale order without an approved contract"
**Solution**: Link an approved contract or disable "Require Contract" on the order

### Issue: "Contract amount exceeds your approval limit"
**Solution**: Request approval from someone with higher limits

### Issue: "Sale order amount exceeds contract remaining amount"
**Solution**: 
- Request contract amount increase
- Split order into multiple smaller orders
- Create new contract

## Support & Maintenance

### Logging
Enable developer mode to see detailed validation messages

### Data Integrity
- Contract amounts auto-calculate from confirmed orders
- Constraints prevent negative amounts
- Unique approver per team enforced

## Future Enhancements (Roadmap)
- Multi-level approval workflow
- Email notifications for approval requests
- Contract renewal automation
- Dashboard with approval metrics
- Mobile app support
- API endpoints for external integrations

## Version History
- **1.0.0** (2026-01-31): Initial release for Odoo 19

## License
LGPL-3

## Credits
Developed for Odoo 19 Community and Enterprise editions.
