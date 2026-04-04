# Dispute Resolution / Reclamation

**Bounded Context:** Dispute Resolution  
**Domain:** Social Synergy (Социальная Синергия)  
**Status:** Core Subdomain

This context manages the reclamation system — the primary mechanism for conflict resolution and social immune system of Synergy4all. Any participant can file a reclamation against any other without explaining reasons. The system escalates through guarantor chains until resolution.

---

### Reclamation

**Russian:** Рекламация  
**Definition:** A formal complaint filed by one participant against another. The claimant files by sending the deal's technical block plus a claim code to the Registration Automaton. The reclamation blocks the target's deals and triggers escalation.

**Context:** Reclamations are the core of the "social immune system." Any participant can file against any other — without explaining why. This removes the burden of proof and enables quick response to perceived problems. The target's deals are immediately blocked.

**Code mapping:**
```python
# contexts/dispute_resolution/domain/
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

@dataclass
class Reclamation:
    reclamation_id: str
    claim_id: str           # Unique claim code
    claimant_id: str        # Who files
    target_id: str          # Against whom
    deal_id: str           # Associated deal (if any)
    technical_block: TechnicalBlock
    filed_at: datetime
    status: ReclamationStatus
    escalation_level: int   # 0 = local, 1 = first guarantor level, etc.
    current_arbiters: list[str]  # IDs of current decision-makers
    
    def block_target_deals(self) -> None:
        """All open deals of target are blocked."""
        pass

class ReclamationStatus:
    FILED = "filed"
    BLOCKED = "blocked"           # Target's deals blocked
    ESCALATED = "escalated"       # Escalating to guarantors
    RESOLVED = "resolved"         # Decision made
    DISMISSED = "dismissed"       # Claimant's claim rejected
    EXPIRED = "expired"           # No response, auto-resolve

@dataclass
class ClaimCode:
    """Unique code generated when reclamation is filed."""
    code: str
    reclamation_id: str
    generated_at: datetime
```

**Related terms:** [Technical Block](#technical-block), [Blocking](#blocking), [Escalation](#escalation), [Collegium](#collegium)

---

### Claim

**Russian:** Претензия  
**Definition:** A general term for a dispute. In practice, "claim" and "reclamation" are often used interchangeably. A claim can be filed with or without an associated deal. Claims can be: transaction claims (related to a deal) or exclusion claims (to remove a participant).

**Context:** There are two main claim types: (1) Transaction claims — related to specific deals, requiring the technical block as evidence. (2) Exclusion claims — to exclude a participant for bad faith, where deposit is blocked during dispute but no financial obligation arises.

**Code mapping:**
```python
# contexts/dispute_resolution/domain/
class ClaimType:
    TRANSACTION = "transaction"      # Related to specific deal
    EXCLUSION = "exclusion"          # Remove participant from network
    MUTUAL = "mutual"                # Counter-claim from respondent

@dataclass
class Claim:
    claim_id: str
    claim_type: str
    claimant_id: str
    target_id: str
    deal_id: Optional[str]
    amount: Optional[float]         # For transaction claims
    basis: str                      # Reason (can be empty for reclamation)
    filed_at: datetime
    status: ClaimStatus
    
    def is_transaction_claim(self) -> bool:
        return self.claim_type == ClaimType.TRANSACTION
    
    def is_exclusion_claim(self) -> bool:
        return self.claim_type == ClaimType.EXCLUSION
    
    def get_limit(self, claimant_deposit: float, transaction_amount: float) -> float:
        """Claim total limited to min(deposit, transaction_amount)."""
        return min(claimant_deposit, transaction_amount)

class ClaimStatus:
    FILED = "filed"
    UNDER_REVIEW = "under_review"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    COUNTERFILED = "counterfiled"
    EXPIRED = "expired"
```

**Related terms:** [Reclamation](#reclamation), [Technical Block](#technical-block), [Exclusion Claim](#exclusion-claim), [Counter-Claim](#counter-claim)

---

### Blocking

**Russian:** Блокировка  
**Definition:** The immediate effect of filing a reclamation — the target participant's all open deals are frozen. No new deals can be opened. The blocking persists until the reclamation is resolved.

**Context:** Blocking is the enforcement mechanism that makes reclamations serious. When a reclamation is filed, the target cannot continue transacting. This creates pressure for quick resolution. The blocking is automatic and immediate upon filing.

**Code mapping:**
```python
# contexts/dispute_resolution/domain/
@dataclass
class Block:
    block_id: str
    target_participant_id: str
    reclamation_id: str
    blocked_at: datetime
    reason: str
    affects_new_deals: bool = True
    affects_existing_deals: bool = True
    
    def is_active(self) -> bool:
        return self.status == BlockStatus.ACTIVE
    
    def lift(self, resolution: str) -> None:
        """Lift block after reclamation is resolved."""
        pass

class BlockStatus:
    ACTIVE = "active"
    PARTIAL = "partial"      # Only existing deals blocked
    LIFTED = "lifted"

# contexts/dispute_resolution/application/
class BlockingService:
    def file_reclamation(self, reclamation: Reclamation) -> Block:
        # Create block for target
        block = Block(
            block_id=uuid4(),
            target_participant_id=reclamation.target_id,
            reclamation_id=reclamation.reclamation_id,
            blocked_at=datetime.now(),
            reason=f"Reclamation {reclamation.claim_id} filed",
        )
        
        # Freeze all target's open deals
        open_deals = self._deal_repo.get_open_by_participant(reclamation.target_id)
        for deal in open_deals:
            deal.status = DealStatus.BLOCKED
            self._deal_repo.save(deal)
        
        return block
```

**Related terms:** [Reclamation](#reclamation), [Deal](#deal), [Participant](#participant)

---

### Escalation

**Russian:** Эскалация  
**Definition:** The process where a reclamation moves from local resolution to higher levels of the guaranty chain. If local guarantors cannot resolve within 24 hours, the claim escalates to the next level.

**Context:** Escalation is automatic after the grace period (24 hours by default). Each escalation level adds more arbiters (guarantors of guarantors). The escalation creates increasing pressure and involves more decision-makers. "Dead" branches (non-responsive guarantors) are eventually cut off.

**Code mapping:**
```python
# contexts/dispute_resolution/domain/
class EscalationRules:
    GRACE_PERIOD_HOURS = 24
    ESCALATION_INTERVAL_HOURS = 24
    MAX_ESCALATION_LEVELS = 10
    
    @classmethod
    def should_escalate(cls, reclamation: Reclamation) -> bool:
        """Check if escalation conditions are met."""
        time_passed = datetime.now() - reclamation.filed_at
        return time_passed > timedelta(hours=cls.GRACE_PERIOD_HOURS)

@dataclass
class EscalationEvent:
    escalation_id: str
    reclamation_id: str
    from_level: int
    to_level: int
    triggered_at: datetime
    new_arbiters: list[str]  # New guarantor IDs added
    notification_sent: bool
    
    def get_new_arbiters(
        self,
        claim: Claim,
        guaranty_chain: list[str],
    ) -> list[str]:
        """Get arbitrators at the new level."""
        if self.to_level >= len(guaranty_chain):
            return []  # Reached root
        # Get guarantors at the target's level
        target_guarantors = self._get_guarantors_at_level(
            claim.target_id, self.to_level
        )
        claimant_guarantors = self._get_guarantors_at_level(
            claim.claimant_id, self.to_level
        )
        return target_guarantors + claimant_guarantors

# contexts/dispute_resolution/application/
class EscalationService:
    def escalate(self, reclamation: Reclamation) -> EscalationEvent:
        if not EscalationRules.should_escalate(reclamation):
            raise CannotEscalateError()
        
        new_level = reclamation.escalation_level + 1
        if new_level > EscalationRules.MAX_ESCALATION_LEVELS:
            raise MaxEscalationReachedError()
        
        # Create escalation event
        event = EscalationEvent(
            escalation_id=uuid4(),
            reclamation_id=reclamation.reclamation_id,
            from_level=reclamation.escalation_level,
            to_level=new_level,
            triggered_at=datetime.now(),
            new_arbiters=[],
            notification_sent=False,
        )
        
        # Update reclamation
        reclamation.escalation_level = new_level
        reclamation.status = ReclamationStatus.ESCALATED
        self._reclamations.save(reclamation)
        
        return event
```

**Related terms:** [Reclamation](#reclamation), [Guaranty Chain](#guaranty-chain), [Grace Period](#grace-period), [Branch Cutting](#branch-cutting)

---

### Daily Doubling

**Russian:** Суточное удвоение  
**Definition:** The escalation rule that claim amounts double every 24 hours during escalation. This creates exponential pressure to resolve quickly and prevents stalling.

**Context:** Each day the claim is escalated without resolution, the claimed amount doubles. Day 1: 100%, Day 2: 200%, Day 3: 400%, etc. This incentivizes quick resolution and makes it increasingly expensive to ignore.

**Code mapping:**
```python
# contexts/dispute_resolution/domain/
class DailyDoubling:
    BASE_AMOUNT_MULTIPLIER = 1.0
    DOUBLING_INTERVAL_HOURS = 24
    
    @classmethod
    def calculate_current_amount(
        cls,
        original_amount: float,
        filed_at: datetime,
    ) -> float:
        """Calculate doubled amount based on time passed."""
        days_elapsed = (datetime.now() - filed_at).total_seconds() / 86400
        doubling_count = int(days_elapsed)
        
        return original_amount * (2 ** doubling_count)
    
    @classmethod
    def get_escalation_cost(
        cls,
        original_amount: float,
        escalation_level: int,
    ) -> float:
        """Cost to escalate at each level (for arbitration)."""
        # At higher levels, more guarantors share the cost
        return original_amount * (2 ** escalation_level) / (escalation_level + 1)

@dataclass
class DoublingSchedule:
    """Tracks current amount over time."""
    original_amount: float
    current_amount: float
    filed_at: datetime
    last_calculated_at: datetime
    
    def update(self) -> float:
        """Recalculate current amount."""
        self.current_amount = self.calculate_current_amount(
            self.original_amount,
            self.filed_at,
        )
        self.last_calculated_at = datetime.now()
        return self.current_amount
```

**Related terms:** [Escalation](#escalation), [Claim](#claim), [Collegium](#collegium)

---

### Grace Period

**Russian:** Льготный период  
**Definition:** The initial 24-hour window after a reclamation is filed where the parties can resolve directly without escalation. If resolved, no escalation occurs.

**Context:** The grace period gives parties a chance to settle privately. During this window, the target is blocked but no escalation to guarantors happens. If parties reach agreement within 24 hours, the reclamation is dismissed without involving guarantors.

**Code mapping:**
```python
# contexts/dispute_resolution/domain/
class GracePeriod:
    DEFAULT_HOURS = 24
    
    @classmethod
    def is_within_grace_period(cls, reclamation: Reclamation) -> bool:
        elapsed = datetime.now() - reclamation.filed_at
        return elapsed < timedelta(hours=cls.DEFAULT_HOURS)
    
    @classmethod
    def get_remaining_time(cls, reclamation: Reclamation) -> timedelta:
        elapsed = datetime.now() - reclamation.filed_at
        remaining = timedelta(hours=cls.DEFAULT_HOURS) - elapsed
        return max(timedelta(0), remaining)

@dataclass
class GracePeriodStatus:
    reclamation_id: str
    expires_at: datetime
    is_within_period: bool
    direct_resolution_achieved: bool

# contexts/dispute_resolution/application/
class GracePeriodService:
    def check_resolution(self, reclamation: Reclamation) -> ResolutionResult:
        if self._direct_resolution_filed(reclamation.reclamation_id):
            return ResolutionResult(
                status="resolved_directly",
                reclamation_id=reclamation.reclamation_id,
                resolved_at=datetime.now(),
            )
        
        if not GracePeriod.is_within_grace_period(reclamation):
            # Trigger automatic escalation
            self._escalation_service.escalate(reclamation)
            return ResolutionResult(
                status="escalated",
                reclamation_id=reclamation.reclamation_id,
            )
        
        return ResolutionResult(
            status="in_grace_period",
            remaining=GracePeriod.get_remaining_time(reclamation),
        )
```

**Related terms:** [Reclamation](#reclamation), [Escalation](#escalation), [Counter-Claim](#counter-claim)

---

### Collegium

**Russian:** Коллегиум  
**Definition:** A panel of 4 guarantors who decide on escalated claims — 2 from the target's side and 2 from the claimant's side. The collegium is the decision-making body for dispute resolution.

**Context:** At escalation level 1+, the reclamation is decided by a collegium: target's guarantor + target's guarantor's guarantor vs. claimant's guarantor + claimant's guarantor's guarantor. If they cannot agree, it escalates further. The collegium decides fault and compensation.

**Code mapping:**
```python
# contexts/dispute_resolution/domain/
@dataclass
class Collegium:
    collegium_id: str
    reclamation_id: str
    level: int
    members: list[CollegiumMember]
    scheduled_at: datetime
    decision: Optional[CollegiumDecision]
    
    def has_quorum(self) -> bool:
        """Need at least 3 of 4 members to decide."""
        return sum(1 for m in self.members if m.status == "present") >= 3
    
    def can_decide(self) -> bool:
        """Check if collegium can make a decision."""
        return self.has_quorum() and self.decision is None

@dataclass
class CollegiumMember:
    member_id: str           # Guarantor ID
    role: str               # "claimant_side" or "target_side"
    present: bool
    vote: Optional[str]      # "guilty", "innocent", "abstain"

@dataclass
class CollegiumDecision:
    decision_id: str
    collegium_id: str
    fault_allocation: float  # 0.0 = claimant, 1.0 = target, split for partial
    compensation_amount: float
    reasoning: str
    voted_at: datetime
    votes: dict[str, str]

# contexts/dispute_resolution/application/
class CollegiumFormationService:
    def form_collegium(
        self,
        claim: Claim,
        escalation_level: int,
        target_guaranty_chain: list[str],
        claimant_guaranty_chain: list[str],
    ) -> Collegium:
        """Form 4-person collegium at escalation level."""
        # Get 2 guarantors from each side at this level
        target_side = [
            target_guaranty_chain[escalation_level],
            target_guaranty_chain[escalation_level + 1] if len(target_guaranty_chain) > escalation_level + 1 else None,
        ]
        claimant_side = [
            claimant_guaranty_chain[escalation_level],
            claimant_guaranty_chain[escalation_level + 1] if len(claimant_guaranty_chain) > escalation_level + 1 else None,
        ]
        
        members = [
            CollegiumMember(id=t, role="target_side", present=False)
            for t in target_side if t
        ] + [
            CollegiumMember(id=c, role="claimant_side", present=False)
            for c in claimant_side if c
        ]
        
        return Collegium(
            collegium_id=uuid4(),
            reclamation_id=claim.claim_id,
            level=escalation_level,
            members=members,
            scheduled_at=datetime.now(),
            decision=None,
        )
```

**Related terms:** [Escalation](#escalation), [Guarantor](#guarantor), [Claim](#claim), [Decision](#decision)

---

### Counter-Claim

**Russian:** Встречная претензия  
**Definition:** A claim filed by the respondent (target of the original claim) against the original claimant. The respondent has a time window (default 14 days or 24 hours in fast-track) to file a counter-claim.

**Context:** Counter-claims enable mutual resolution. If the original claim is frivolous, the respondent can file a counter-claim. Both claims are then resolved together. The respondent's counter-claim has equal standing to the original.

**Code mapping:**
```python
# contexts/dispute_resolution/domain/
class CounterClaimWindow:
    DEFAULT_DAYS = 14
    FAST_TRACK_HOURS = 24
    
    @classmethod
    def can_file_counter_claim(
        cls,
        original_claim: Claim,
        filed_at: datetime,
    ) -> bool:
        elapsed = datetime.now() - filed_at
        return elapsed < timedelta(days=cls.DEFAULT_DAYS)
    
    @classmethod
    def get_remaining_time(cls, original_claim: Claim) -> timedelta:
        elapsed = datetime.now() - original_claim.filed_at
        remaining = timedelta(days=cls.DEFAULT_DAYS) - elapsed
        return max(timedelta(0), remaining)

@dataclass
class CounterClaim:
    counter_claim_id: str
    original_claim_id: str
    respondent_id: str       # Who was originally targeted
    claimant_id: str         # Original claimant becomes respondent
    amount: float
    basis: str
    filed_at: datetime
    status: str
    
    def link_to_original(self, original_claim: Claim) -> LinkedClaims:
        """Return both claims as linked for joint resolution."""
        return LinkedClaims(
            primary_claim_id=original_claim.claim_id,
            counter_claim_id=self.counter_claim_id,
            resolution_type="mutual",
        )

@dataclass
class LinkedClaims:
    primary_claim_id: str
    counter_claim_id: str
    resolution_type: str
```

**Related terms:** [Claim](#reclamation), [Grace Period](#grace-period), [Collegium](#collegium), [Resolution](#resolution)

---

### Exclusion Claim

**Russian:** Исключение  
**Definition:** A special type of claim to exclude a participant from the network for bad faith. Unlike transaction claims, exclusion claims do not create financial obligation — they only block the deposit during the dispute.

**Context:** Exclusion claims are used to remove "destructors" — participants who consistently act dishonestly. The deposit is frozen during the dispute but no money changes hands from this claim alone. If successful, the participant is expelled.

**Code mapping:**
```python
# contexts/dispute_resolution/domain/
class ExclusionClaim(Claim):
    def __init__(self, *args, **kwargs):
        kwargs["claim_type"] = ClaimType.EXCLUSION
        kwargs["amount"] = 0  # No financial amount
        super().__init__(*args, **kwargs)
    
    def freeze_deposit(self) -> None:
        """Freeze target's deposit during dispute."""
        pass
    
    def release_if_dismissed(self) -> bool:
        """If claim dismissed, release deposit."""
        pass
    
    def execute_if_successful(self) -> ExcludedParticipant:
        """If successful, exclude the participant."""
        pass

@dataclass
class ExclusionResult:
    success: bool
    excluded_participant_id: str
    effective_at: datetime
    re_entry_possible: bool
    re_entry_conditions: str
```

**Related terms:** [Claim](#claim), [Deposit](#deposit), [Destructor](#destructor), [Re-entry](#re-entry)

---

### Branch Cutting

**Russian:** Обрезка ветви  
**Definition:** The process of cutting off non-responsive guarantor chains. When a branch (sub-tree) of guarantors fails to respond to escalations, higher-level participants can "cut" that branch, removing it from the network.

**Context:** If a guarantor chain reaches a point where no one responds (guarantor of guarantor is non-responsive), active participants can cut that branch. The "dead" branch is disconnected, and participants below it must find new guarantors to reconnect.

**Code mapping:**
```python
# contexts/dispute_resolution/domain/
class BranchCuttingRules:
    MAX_DAYS_NON_RESPONSIVE = 72  # 3 days
    MIN_PARTICIPANTS_TO_CUT = 3
    
    @classmethod
    def can_cut_branch(
        cls,
        chain_segment: list[str],
        non_responsive_days: int,
        active_participants_requesting: int,
    ) -> bool:
        return (
            non_responsive_days >= cls.MAX_DAYS_NON_RESPONSIVE
            and active_participants_requesting >= cls.MIN_PARTICIPANTS_TO_CUT
        )

@dataclass
class BranchCutEvent:
    cut_id: str
    branch_root_id: str      # Top of the dead branch
    cut_at_level: int
    affected_participants: list[str]
    requested_by: list[str]  # Active participants requesting cut
    executed_at: datetime
    
    def notify_affected(self) -> None:
        """Notify all affected participants they must find new guarantors."""
        pass

# contexts/dispute_resolution/application/
class BranchCuttingService:
    def request_cut(
        self,
        branch_root_id: str,
        requesting_participant_ids: list[str],
    ) -> BranchCutEvent:
        # Verify non-responsiveness
        # Check requesting participants have standing
        # Execute cut
        pass
    
    def reconnect_affected(self, participant_id: str, new_guarantors: list[str]) -> None:
        """Help affected participants find new guarantors."""
        pass
```

**Related terms:** [Escalation](#escalation), [Guaranty Chain](#guaranty-chain), [Guarantor](#guarantor)

---

### Claim Limit

**Russian:** Лимит претензии  
**Definition:** The rule that total claims filed by a participant cannot exceed their deposit sum or the relevant transaction sum — whichever is smaller.

**Context:** This prevents malicious claimants from making unlimited claims. A participant's claim exposure is limited by their deposit. If they file claims exceeding their deposit, additional claims are rejected.

**Code mapping:**
```python
# contexts/dispute_resolution/domain/
class ClaimLimit:
    @staticmethod
    def get_limit(claimant_deposit: float, transaction_amount: float) -> float:
        """Claim cannot exceed min(deposit, transaction_amount)."""
        return min(claimant_deposit, transaction_amount)
    
    @staticmethod
    def can_file_claim(
        claimant_id: str,
        proposed_amount: float,
        claimant_deposit: float,
        existing_claims_total: float,
    ) -> bool:
        available = claimant_deposit - existing_claims_total
        return proposed_amount <= available
    
    @staticmethod
    def get_remaining_capacity(claimant_deposit: float, existing_claims_total: float) -> float:
        """Remaining claim capacity."""
        return max(0, claimant_deposit - existing_claims_total)
```

**Related terms:** [Claim](#claim), [Guarantee Deposit](#guarantee-deposit), [Participant](#participant)

---

## Cross-Context Boundary Notes

| Term | Used by Context | Relationship |
|------|-----------------|--------------|
| Reclamation | [Transaction & Deal](synergy_transaction_deal.md) | References technical block from deal |
| Technical Block | [Transaction & Deal](synergy_transaction_deal.md) | Evidence in claim |
| Claim | [Deposit & Capacity](synergy_deposit_capacity.md) | Triggers deposit transfer/replenishment |
| Participant | [Participant Identity](synergy_participant_identity.md) | Parties to claim |
| Guarantor | [Participant Identity](synergy_participant_identity.md), [Deposit & Capacity](synergy_deposit_capacity.md) | Arbiters, hold deposits |
| Deposit | [Deposit & Capacity](synergy_deposit_capacity.md) | Source of compensation |
| Blocked Deal | [Transaction & Deal](synergy_transaction_deal.md) | Effect of reclamation |