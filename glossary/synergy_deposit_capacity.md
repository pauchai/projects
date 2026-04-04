# Deposit & Guarantee Capacity

**Bounded Context:** Deposit & Guarantee Capacity  
**Domain:** Social Synergy (Социальная Синергия)  
**Status:** Core Subdomain

This context manages the insurance deposits that back participant transactions and the derived guarantee capacity that determines how much a participant can transact. The deposit is an accounting unit, not a settlement unit — it only moves on claim/insurance events.

---

### Guarantee Deposit

**Russian:** Страховой депозит / Гарантийный депозит  
**Definition:** A monetary amount (or liquid resources) held by guarantors as collateral for a participant's transactions. The deposit is NOT an entry fee — it remains the participant's property and is used only for force-majeure compensation when claims are paid out.

**Context:** The deposit is the "quantum of action" — the maximum single-transaction value that is insured. The deposit is split across two guarantors (each holds half). It is an accounting unit, not a transactional one — during normal transactions, the deposit does not move. It is held physically (cash, bank account, or cooperative share) by the guarantors.

**Code mapping:**
```python
# contexts/deposit_capacity/domain/
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

@dataclass
class GuaranteeDeposit:
    deposit_id: str
    participant_id: str
    guarantor_1_id: str
    guarantor_2_id: str
    amount: float
    status: DepositStatus
    created_at: datetime
    last_updated_at: datetime
    
    def is_active(self) -> bool:
        return self.status == DepositStatus.ACTIVE
    
    def split_across_guarantors(self) -> tuple[float, float]:
        """Deposit is split equally between two guarantors."""
        return (self.amount / 2, self.amount / 2)

class DepositStatus:
    ACTIVE = "active"
    FROZEN = "frozen"        # During claim resolution
    PARTIALLY_USED = "partially_used"
    REPLENISHING = "replenishing"
    RELEASED = "released"     # Participant exited
```

**Related terms:** [Guarantor](#guarantor), [Participant](#participant), [Action Quantum](#action-quantum), [Deposit Custody](#deposit-custody), [Deposit Status Level](#deposit-status-level)

---

### Action Quantum

**Russian:** Квант действия  
**Definition:** The minimum unit of guaranteed transactional activity, determined by the deposit amount. It represents the maximum value of a single transaction that is fully insured by the deposit.

**Context:** The action quantum is the "quantum of action" — the maximum single-transaction value that is insured by the guarantee deposit. Transactions up to this amount are guaranteed; larger transactions may be partially guaranteed or unguaranteed.

**Code mapping:**
```python
# contexts/deposit_capacity/domain/
@dataclass
class ActionQuantum:
    deposit_amount: float
    
    def get_max_guaranteed_transaction(self) -> float:
        """The quantum equals the deposit amount."""
        return self.amount
    
    def is_within_quantum(self, transaction_amount: float) -> bool:
        """Check if transaction is fully within the quantum."""
        return transaction_amount <= self.amount
    
    def get_coverage_ratio(self, transaction_amount: float) -> float:
        """Returns 1.0 for full coverage, <1.0 for partial."""
        if transaction_amount <= self.amount:
            return 1.0
        return self.amount / transaction_amount
```

**Related terms:** [Guarantee Deposit](#guarantee-deposit), [Transaction](#transaction), [Guarantee Capacity](#guarantee-capacity)

---

### Guarantee Capacity

**Russian:** Гарантийные возможности  
**Definition:** The remaining amount a participant can guarantee — calculated as the deposit minus the sum of all open (unclosed) transactions. This is a dynamic value that changes as deals open and close.

**Context:** Guarantee capacity determines how much a participant can transact at any given time. When a deal opens, both parties' capacity is reduced by the deal amount. When the deal closes, capacity is restored. If capacity is exhausted, participants can still transact but explicitly as "unguaranteed" — the counterparty accepts the risk.

**Code mapping:**
```python
# contexts/deposit_capacity/domain/
@dataclass
class GuaranteeCapacity:
    participant_id: str
    total_deposit: float
    open_transaction_sum: float
    
    def get_available_capacity(self) -> float:
        """Available = deposit - open transactions."""
        return max(0, self.total_deposit - self.open_transaction_sum)
    
    def can_open_transaction(self, amount: float) -> bool:
        """Check if participant has capacity for new transaction."""
        return self.get_available_capacity() >= amount
    
    def reserve_for_transaction(self, amount: float) -> "GuaranteeCapacity":
        """Create new capacity with amount reserved (for opening deal)."""
        return GuaranteeCapacity(
            participant_id=self.participant_id,
            total_deposit=self.total_deposit,
            open_transaction_sum=self.open_transaction_sum + amount,
        )
    
    def release_from_transaction(self, amount: float) -> "GuaranteeCapacity":
        """Create new capacity with amount released (for closing deal)."""
        return GuaranteeCapacity(
            participant_id=self.participant_id,
            total_deposit=self.total_deposit,
            open_transaction_sum=max(0, self.open_transaction_sum - amount),
        )

# contexts/deposit_capacity/application/
class GuaranteeCapacityService:
    def calculate(self, participant_id: str) -> GuaranteeCapacity:
        deposit = self._deposit_repo.get_total(participant_id)
        open_sum = self._transaction_repo.get_open_sum(participant_id)
        return GuaranteeCapacity(participant_id, deposit, open_sum)
```

**Related terms:** [Guarantee Deposit](#guarantee-deposit), [Open Transaction](#open-transaction), [Closed Transaction](#closed-transaction), [Unguaranteed Transaction](#unguaranteed-transaction)

---

### Deposit Status Level

**Russian:** Уровень статуса депозита  
**Definition:** The tier/level of a participant's deposit, which determines their transaction limits and privileges. Historically: top tier ~$2100, middle tier ~$100, pensioners ~$10.

**Context:** Deposit status levels are derived from the deposit amount. Higher deposits provide higher guarantee capacity. The status can be upgraded (deposit increased) or downgraded (deposit decreased) — both require guarantor confirmation. After a claim pays out, the deposit must be replenished or the status is downgraded.

**Code mapping:**
```python
# contexts/deposit_capacity/domain/
class DepositTier:
    """Historical tiers from Almaty experiment."""
    PENSIONER = 10.0
    STANDARD = 100.0
    PREMIUM = 2100.0
    
    @classmethod
    def from_amount(cls, amount: float) -> str:
        if amount >= cls.PREMIUM:
            return "premium"
        elif amount >= cls.STANDARD:
            return "standard"
        else:
            return "pensioner"

@dataclass
class DepositStatusLevel:
    participant_id: str
    current_tier: str
    deposit_amount: float
    can_upgrade: bool
    can_downgrade: bool
    
    def request_upgrade(self, new_amount: float, guarantor_approval: bool) -> None:
        """Request to increase deposit and tier."""
        if not guarantor_approval:
            raise ApprovalRequiredError("Guarantor approval required for upgrade")
        # Process upgrade
        pass
    
    def request_downgrade(self, new_amount: float) -> None:
        """Request to decrease deposit and tier."""
        # Process downgrade, return difference to participant
        pass
    
    def enforce_replenishment_after_claim(self, claim_amount: float) -> None:
        """After claim payout, enforce deposit replenishment or downgrade."""
        if self.deposit_amount - claim_amount < 0:
            self._downgrade()
        else:
            self._require_replenishment(claim_amount)
```

**Related terms:** [Guarantee Deposit](#guarantee-deposit), [Claim](#claim), [Deposit Replenishment](#deposit-replenishment)

---

### Deposit Custody

**Russian:** Хранение депозита  
**Definition:** The physical storage mechanism for guarantee deposits. Deposits can be held as cash, in a bank account, or as cooperative shares — as long as the guarantor has access for force-majeure compensation.

**Context:** The deposit is held by the participant's two guarantors jointly. The original Almaty experiment used bank accounts with power-of-attorney for guarantors. Other options include: cash held by guarantors, cooperative shares, or escrowed crypto. The key requirement: guarantors must be able to access the funds to pay claims.

**Code mapping:**
```python
# contexts/deposit_capacity/domain/
from typing import Protocol

class DepositCustody(Protocol):
    """Port: deposit custody mechanisms."""
    def hold(self, deposit: GuaranteeDeposit) -> CustodyReceipt: ...
    def release(self, deposit_id: str, amount: float, recipient_id: str) -> None: ...
    def claim(self, deposit_id: str, claimant_id: str, amount: float) -> ClaimResult: ...

class BankAccountCustody:
    """Bank account with guarantor power-of-attorney."""
    def __init__(self, bank_api: BankAPI):
        self._bank = bank_api
    
    def hold(self, deposit: GuaranteeDeposit) -> CustodyReceipt:
        account = self._bank.create_joint_account(
            owner=deposit.participant_id,
            joint_holder=deposit.guarantor_1_id,
            second_joint_holder=deposit.guarantor_2_id,
        )
        return CustodyReceipt(
            deposit_id=deposit.deposit_id,
            account_number=account.number,
            custody_type="bank_joint",
        )

class CashCustody:
    """Physical cash held by guarantors."""
    def hold(self, deposit: GuaranteeDeposit) -> CustodyReceipt:
        return CustodyReceipt(
            deposit_id=deposit.deposit_id,
            guarantor_1_receipt=self._create_receipt(deposit.guarantor_1_id, deposit.amount / 2),
            guarantor_2_receipt=self._create_receipt(deposit.guarantor_2_id, deposit.amount / 2),
            custody_type="cash",
        )

class CooperativeShareCustody:
    """Cooperate shares as deposit."""
    def hold(self, deposit: GuaranteeDeposit) -> CustodyReceipt:
        # Create cooperative membership with guarantor as delegate
        pass
```

**Related terms:** [Guarantee Deposit](#guarantee-deposit), [Guarantor](#guarantor), [Receipt](#receipt), [Bank Account](#bank-account)

---

### Receipt

**Russian:** Расписка  
**Definition:** A document issued by a guarantor to acknowledge receipt of a participant's deposit funds. Two receipts are exchanged: guarantor gives ward a storage-obligation receipt; ward gives guarantor a usage-authorization receipt.

**Context:** The receipt is the physical/documentation proof of deposit custody. When a participant exits, the guarantor provides receipts showing any claim deductions. Third parties give guarantors a funds-received receipt upon claim settlement.

**Code mapping:**
```python
# contexts/deposit_capacity/domain/
@dataclass
class StorageObligationReceipt:
    """Guarantor gives ward: I hold your deposit."""
    receipt_id: str
    guarantor_id: str
    ward_id: str
    amount: float
    issued_at: datetime
    conditions: str  # Terms of storage and withdrawal

@dataclass
class UsageAuthorizationReceipt:
    """Ward gives guarantor: You may use for claims."""
    receipt_id: str
    ward_id: str
    guarantor_id: str
    amount: float
    issued_at: datetime

@dataclass
class FundsReceivedReceipt:
    """Third party gives guarantor: I received claim payment."""
    receipt_id: str
    from_guarantor_id: str
    to_participant_id: str  # Original claimant
    amount: float
    settlement_date: datetime

@dataclass
class ExitReceipt:
    """Guarantor gives exiting participant: Your deposit after claims."""
    receipt_id: str
    participant_id: str
    original_deposit: float
    claims_paid: float
    returned_amount: float
    guarantor_signatures: list[bytes]
```

**Related terms:** [Guarantee Deposit](#guarantee-deposit), [Guarantor](#guarantor), [Claim](#claim), [Offboarding](#offboarding)

---

### Deposit Replenishment

**Russian:** Пополнение депозита  
**Definition:** The process of restoring a guarantee deposit to its original level after it has been partially used to pay out claims.

**Context:** After a claim is paid out from a participant's deposit, the deposit must be replenished to its original level. If the participant does not replenish, their status level is downgraded (e.g., from premium to standard). Replenishment requires guarantor confirmation.

**Code mapping:**
```python
# contexts/deposit_capacity/application/
class DepositReplenishmentService:
    def __init__(self, deposit_repo: DepositRepository, guarantor_service: GuarantorService):
        self._deposits = deposit_repo
        self._guarantors = guarantor_service
    
    def request_replenishment(
        self,
        participant_id: str,
        amount: float,
        payment_method: str,
    ) -> ReplenishmentRequest:
        # Validate amount covers the deficit
        current = self._deposits.get_total(participant_id)
        # Create replenishment request
        return ReplenishmentRequest(
            participant_id=participant_id,
            current_amount=current,
            requested_amount=amount,
            payment_method=payment_method,
            status="pending_guarantor_approval",
        )
    
    def process_replenishment(self, request_id: str, guarantor_approval: bool) -> None:
        if not guarantor_approval:
            raise ApprovalRejectedError("Guarantor rejected replenishment")
        # Update deposit amounts
        # Restore status level if applicable
        pass
    
    def enforce_or_downgrade(self, participant_id: str, deficit: float) -> None:
        """If participant doesn't replenish, downgrade their status level."""
        current_deposit = self._deposits.get_total(participant_id)
        new_tier = self._calculate_downgraded_tier(current_deposit)
        self._deposits.update_tier(participant_id, new_tier)
```

**Related terms:** [Guarantee Deposit](#guarantee-deposit), [Deposit Status Level](#deposit-status-level), [Claim](#claim)

---

### Zero-Guarantee Transaction

**Russian:** Сделка без гарантии  
**Definition:** A transaction where the participant's guarantee capacity is exhausted, and the counterparty explicitly accepts the risk of the other party defaulting. The transaction proceeds without deposit backing.

**Context:** If a participant's guarantee capacity is fully used (deposit minus open transactions = 0), they can still transact. However, the counterparty must explicitly accept the risk — the transaction is marked as "unguaranteed" or "zero-guarantee" and the counterparty's deposit is not affected.

**Code mapping:**
```python
# contexts/deposit_capacity/domain/
@dataclass
class TransactionGuaranteeStatus:
    FULLY_GUARANTEED = "fully_guaranteed"
    PARTIALLY_GUARANTEED = "partially_guaranteed"
    ZERO_GUARANTEE = "zero_guarantee"  # Counterparty accepts risk
    
    @classmethod
    def calculate(
        cls,
        transaction_amount: float,
        party_capacity: float,
    ) -> str:
        if party_capacity <= 0:
            return cls.ZERO_GUARANTEE
        elif party_capacity >= transaction_amount:
            return cls.FULLY_GUARANTEED
        else:
            return cls.PARTIALLY_GUARANTEE

@dataclass
class ZeroGuaranteeConsent:
    """Counterparty explicitly accepts zero-guarantee risk."""
    consenting_participant_id: str
    transaction_id: str
    accepted_at: datetime
    risk_acknowledgment: str  # "I accept full risk of counterparty default"
```

**Related terms:** [Guarantee Capacity](#guarantee-capacity), [Transaction](#transaction), [Participant](#participant)

---

### Open Transaction

**Russian:** Открытая сделка  
**Definition:** A transaction that has been signed by both parties but not yet closed. While open, it reserves guarantee capacity from both parties' deposits.

**Context:** An open transaction reduces both parties' available guarantee capacity. The transaction remains open until the receiving party signs a closure block. If the transaction is not closed within the recall period, it may be disputed.

**Code mapping:**
```python
# contexts/deposit_capacity/domain/
@dataclass
class OpenTransaction:
    transaction_id: str
    participant_a_id: str
    participant_b_id: str
    amount: float
    opened_at: datetime
    recall_deadline: datetime  # Time window before automatic dispute
    guarantee_status: str
    
    def is_within_recall_period(self) -> bool:
        return datetime.now() < self.recall_deadline
    
    def reserve_capacity(self) -> tuple[float, float]:
        """Return capacity amounts to reserve from each party."""
        return (self.amount, self.amount)
    
    def can_escalate_to_claim(self) -> bool:
        """After recall deadline passes, can escalate to reclamation."""
        return not self.is_within_recall_period()
```

**Related terms:** [Guarantee Capacity](#guarantee-capacity), [Transaction Closure](#transaction-closure), [Recall Period](#recall-period), [Reclamation](#reclamation)

---

### Closed Transaction

**Russian:** Закрытая сделка  
**Definition:** A transaction that has been completed and confirmed by the receiving party. Guarantee capacity is restored to both parties.

**Context:** A closed transaction is one where the obligation receiver has signed the closing block and returned it to the obligor. Once closed, the transaction is final (unless a reclamation is filed within the dispute window). Both parties' guarantee capacity is fully restored.

**Code mapping:**
```python
# contexts/deposit_capacity/domain/
@dataclass
class ClosedTransaction:
    transaction_id: str
    participant_a_id: str
    participant_b_id: str
    amount: float
    opened_at: datetime
    closed_at: datetime
    closure_code: str  # Signed by receiving party
    guarantee_status_at_close: str
    
    def restore_capacity(self) -> tuple[float, float]:
        """Return capacity amounts to restore to each party."""
        return (self.amount, self.amount)
    
    def is_within_dispute_window(self) -> bool:
        """Time window to file reclamation after closure."""
        from datetime import timedelta
        return datetime.now() - self.closed_at < timedelta(days=14)
```

**Related terms:** [Open Transaction](#open-transaction), [Guarantee Capacity](#guarantee-capacity), [Transaction Closure](#transaction-closure)

---

### Deposit Transfer

**Russian:** Перевод депозита  
**Definition:** The movement of deposit funds, which only occurs in specific circumstances: claim payout, participant exit, or deposit upgrade/downgrade.

**Context:** The deposit is an accounting unit — it does NOT move during normal transactions. Transfers only happen for: (1) claim payout from guarantor to claimant, (2) participant exit returning deposit minus claims, (3) upgrade/downgrade adjusting the deposit amount.

**Code mapping:**
```python
# contexts/deposit_capacity/domain/
class DepositTransferType:
    CLAIM_PAYOUT = "claim_payout"
    EXIT_RETURN = "exit_return"
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"

@dataclass
class DepositTransfer:
    transfer_id: str
    deposit_id: str
    from_participant_id: str
    to_participant_id: str
    amount: float
    transfer_type: str
    initiated_at: datetime
    confirmed_at: datetime | None
    
    def is_confirmed(self) -> bool:
        return self.confirmed_at is not None
    
    def execute(self) -> TransferResult:
        if not self.is_confirmed():
            raise TransferNotConfirmedError()
        # Execute the transfer via custody mechanism
        pass
```

**Related terms:** [Guarantee Deposit](#guarantee-deposit), [Claim](#claim), [Offboarding](#offboarding), [Deposit Status Level](#deposit-status-level)

---

## Cross-Context Boundary Notes

| Term | Used by Context | Relationship |
|------|-----------------|--------------|
| Guarantee Deposit | [Participant Identity](synergy_participant_identity.md), [Transaction & Deal](synergy_transaction_deal.md) | Backbone of trust; used in deal lifecycle |
| Guarantee Capacity | [Transaction & Deal](synergy_transaction_deal.md), [Dispute Resolution](synergy_dispute_resolution.md) | Consumed by transactions; referenced in claims |
| Open Transaction | [Transaction & Deal](synergy_transaction_deal.md) | Consumes capacity; claim reference |
| Closed Transaction | [Transaction & Deal](synergy_transaction_deal.md) | Restores capacity; historical record |
| Deposit Custody | [Participant Identity](synergy_participant_identity.md) | Guarantors hold deposits |
| Receipt | [Participant Identity](synergy_participant_identity.md), [Dispute Resolution](synergy_dispute_resolution.md) | Proof of deposit; used in claim settlement |
| Deposit Status Level | [Contribution Evaluation](synergy_contribution_evaluation.md) | A-component includes reputation/status |
| Claim Payout | [Dispute Resolution](synergy_dispute_resolution.md) | Triggers deposit transfer and replenishment |