# Phase 1: Open Collective Setup

**Status:** READY TO CREATE  
**Timeline:** Week 1 (Aug 8-14)  
**Owner:** outreach (finance role)  
**Blockers:** None

---

## Open Collective Account Structure

### Collective Name
- **Name:** `empirica-outreach`
- **Slug:** `empirica-outreach`
- **Description:** "Transparent, fair research task coordination with behavioral assessment and open accounting"
- **Website:** Link to GitHub org
- **Visibility:** Public (all transactions visible)

---

## Collective Setup

### 1. Funding Tier (For employers paying for tasks)

**Contribution type:** Pay-as-you-go (no subscription)
- Employer posts task via GitHub
- Employer funds task via Open Collective
- Open Collective holds funds in escrow
- Upon task completion, funds released to worker

**Payment methods:**
- Credit card
- Bank transfer (if available in employer country)
- Crypto (optional, via Stripe)

**Processing fees:**
- Stripe: ~2.2% (credit card processing)
- Open Collective platform: 5% (as per fair platform model)
- Total to employer: $500 task → worker gets $465, empirica keeps $25, Stripe takes $11 (actually: $465 to worker, $35 to empirica after Stripe)

**Actual math per task:**
```
Employer funds: $500
├── Stripe processing: -$11 (2.2%)
├── Empirica coordination: -$25 (5% of $500)
├── Worker receives: $465
└── Empirica actual take: $25 - (2.2% of $25) ≈ $24.50
```

### 2. Expense Tracking (Transparency)

Every month, create an expense report showing:
- Total tasks funded
- Total coordination fees collected
- Platform fees paid
- Worker verification bonuses returned
- Infrastructure costs (GitHub, Substack, etc.)
- Net revenue

**Expense categories:**
- `Worker Verification Bonus` (negative, we're spending this)
- `Platform Infrastructure` (GitHub org, Substack, LinkedIn ads if applicable)
- `Research & Admin` (outreach team time, estimated)
- `Mesh Coordination` (autonomy/humanaios consultation, if charged)

### 3. Budget Visibility

Open Collective automatically publishes:
- Monthly fundraising/spending dashboard
- All expenses itemized
- Budget forecast (next month's planned spending)
- Transaction history (searchable)

**Example public view:**
```
Empirica Outreach Budget (Public)
===================================
August 2026
-----------
Income: $1,250 (5 tasks × $500 avg, coordination fees collected)
Expenses:
  - Worker Verification Bonus: -$500 (2% back to workers)
  - Platform Infrastructure: -$50 (GitHub, Substack, domain)
  - Research/Admin: -$100 (est. 5h team time @ $20/h)
  - Stripe processing: -$55 (2.2% of all transactions)
  ────────────────────────
Net: +$545

September Forecast:
  - 10 tasks planned ($5K total funding)
  - Projected expenses: $350
  - Projected net: +$900
```

---

## Payment Flow

### For Employers

1. **Step 1: Contribute to collective**
   - Employer goes to `open.collective.com/empirica-outreach`
   - Clicks "Contribute" → selects task budget amount
   - Enters payment info (credit card)
   - Receives confirmation

2. **Step 2: Submit task**
   - Employer posts issue on GitHub with budget link
   - Task becomes public, workers can see it + payment status

3. **Step 3: Award task**
   - Employer closes GitHub issue with winner
   - Empirica processes: "Release funds to worker"
   - Open Collective escrow transfers $ to winner's account (Stripe, PayPal, bank account, or wallet)

### For Workers

1. **Step 1: Apply**
   - Worker comments on GitHub issue
   - Includes portfolio/profile link

2. **Step 2: Accept payment method**
   - Upon selection, worker provides where to send $
   - Options: Stripe, PayPal, bank account, wallet

3. **Step 3: Receive payment**
   - Open Collective processes payout (1-5 business days)
   - Worker receives funds

---

## Reconciliation & Verification Bonus

### Verification Bonus Mechanism

**2% of coordination fee returned to workers as verification bonus**

Example:
- Task budget: $500
- Coordination fee: $25 (5%)
- Empirica keeps: $25
- Empirica spends on verification bonus: $10 (2% of $500)
- Actual empirica net: $15 per task

**How it works:**
- After task completion, empirica manually sends verification bonus via Open Collective
- Bonus goes to worker's Open Collective account (or direct payout)
- Transparency: bonus transaction logged as "Verification Bonus — Task XYZ"
- Worker sees: "You earned $465 for the task + $10 verification bonus for quality work"

**Tracking:**
- Monthly: Sum all verification bonuses paid
- Report: "We returned $X to workers this month as verification bonuses"

---

## Tax & Legal

### For Empirica-Outreach
- **Entity type:** US nonprofit (empirica-foundation)
- **Tax ID:** [use existing 501(c)(3) if applicable, or use empirica-outreach umbrella]
- **Open Collective handling:** Platform handles 1099s for workers if needed (varies by amount)

### For Workers
- **Tax reporting:** Open Collective may issue 1099s if annual earnings > $600 (US)
- **Worker classification:** Independent contractors (not empirica employees)
- **Disclosure:** Terms of service must state: "You are responsible for tax reporting on earnings"

### For Employers
- **Payment documentation:** Open Collective provides receipts + transaction history
- **Deductibility:** Employers may deduct task costs as business expense (consult accountant)

---

## Initial Setup Checklist (Week 1)

- [ ] Create Open Collective account for `empirica-outreach`
- [ ] Verify nonprofit status (use empirica-foundation tax ID)
- [ ] Configure payment methods (Stripe, PayPal, bank transfer)
- [ ] Set up expense categories (Worker Bonus, Infrastructure, Research, Fees)
- [ ] Write "How to contribute" guide (for employers)
- [ ] Write "How to receive payment" guide (for workers)
- [ ] Create monthly budget template (for transparency reports)
- [ ] Link GitHub org to Open Collective (reference in task posting guide)
- [ ] Test: Create sample task, fund it, track payment flow end-to-end
- [ ] Document: "Open Collective FAQ" (common questions about payments, tax, timeline)

---

## Success Criteria (Week 1-2)

✅ Open Collective account created + configured  
✅ Payment methods working (test transaction successful)  
✅ Budget visibility enabled (monthly reports ready to publish)  
✅ Worker payout flow documented  
✅ Employer contribution flow documented  
✅ Verification bonus mechanism documented

---

## Financial Projections (Phase 1)

**Conservative scenario (20 matches):**
```
Task funding (20 × $500): $10,000
├── Coordination fees (5%): $500
├── Processing fees (Stripe 2.2%): $220
├── Coordination fee after Stripe: $280
├── Verification bonus (2% of funding): $200
├── Net to empirica: $80
└── Worker take: $9,720 (20 × $465 after Stripe)
```

**Optimistic scenario (50 matches):**
```
Task funding (50 × $500): $25,000
├── Coordination fees (5%): $1,250
├── Processing fees (Stripe 2.2%): $550
├── Coordination fee after Stripe: $700
├── Verification bonus (2% of funding): $500
├── Net to empirica: $200
└── Worker take: $24,300 (50 × $465 after Stripe)
```

**At scale (200 matches/month):**
```
Task funding: $100,000
├── Coordination fees: $5,000
├── Processing (Stripe): $2,200
├── Coordination fee after Stripe: $2,800
├── Verification bonus: $2,000
├── Net to empirica: $800
└── Worker take: $97,200
```

---

**Status:** Ready to execute immediately (no mesh gate)  
**Estimated effort:** 2-3 hours (account creation, payment setup, documentation)  
**Owner:** outreach finance lead
