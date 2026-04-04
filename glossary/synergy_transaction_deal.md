# Transaction & Deal

**Bounded Context:** Transaction & Deal  
**Domain:** Social Synergy (Социальная Синергия)  
**Status:** Core Subdomain

This context manages the formation, execution, and closure of deals between participants. Deals are the fundamental unit of economic exchange in Synergy4all, protected by guarantee deposits and recorded on the blockchain.

---

### Deal

**Russian:** Сделка  
**Definition:** A formalized agreement between two participants, signed by both parties. A deal contains: parties, date, subject, sum, deadline, success criteria, and guarantor information. Deals are the primary mechanism for value exchange in the network.

**Context:** A deal is created when two participants agree on terms. It goes through a lifecycle: open (signed by receiver) → active (signed by obligor) → closed (confirmed by receiver). During the open phase, the deal reserves guarantee capacity from both parties.

**Code mapping:**
```python
# contexts/transaction_deal/domain/
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

@dataclass
class Deal:
    deal_id: str
    party_a_id: str          # Obligor (performer/service provider)
    party_b_id: str          # Obligation receiver (customer)
    subject: str
    amount: float
    currency: str           # Money, goods, services, or equivalent
    deadline: datetime
    success_criteria: str
    guarantor_a_id: str     # Party A's guarantor
    guarantor_b_id: str      # Party B's guarantor
    status: DealStatus
    technical_block: TechnicalBlock
    created_at: datetime
    closed_at: Optional[datetime]
    
    def can_escalate_to_claim(self) -> bool:
        """Check if deal can be escalated to reclamation."""
        return self.status == DealStatus.CLOSED and not self._claim_filed

class DealStatus:
    DRAFT = "draft"
    SIGNED_BY_RECEIVER = "signed_by_receiver"  # Open
    SIGNED_BY_OBLIGOR = "signed_by_obligor"   # Active
    CLOSED = "closed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"

@dataclass
class TechnicalBlock:
    """Immutable technical data of the deal, signed by parties."""
    deal_id: str
    parties: tuple[str, str]
    amount: float
    created_at: datetime
    receiver_signature: Optional[bytes]
    obligor_signature: Optional[bytes]
    
    def is_fully_signed(self) -> bool:
        return self.receiver_signature and self.obligor_signature
```

**Related terms:** [Technical Block](#technical-block), [Deal Closure](#deal-closure), [Recall Period](#recall-period), [Obligor](#obligor), [Obligation Receiver](#obligation-receiver)

---

### Technical Block

**Russian:** Технический блок  
**Definition:** The immutable core data of a deal: parties, date, and sum. The technical block is signed first by the obligation receiver, then by the obligor. It serves as the reference point for any claims or disputes.

**Context:** The technical block is the "receipt" that proves the deal exists. When filing a reclamation, the claimant includes the technical block plus a claim code. The block is stored immutably and serves as evidence in dispute resolution.

**Code mapping:**
```python
# contexts/transaction_deal/domain/
@dataclass
class TechnicalBlock:
    block_id: str
    deal_id: str
    party_a_id: str
    party_b_id: str
    amount: float
    created_at: datetime
    receiver_signature: Optional[bytes] = None
    obligor_signature: Optional[bytes] = None
    claim_code: Optional[str] = None  # Added when reclamation filed
    
    def sign_by_receiver(self, signature: bytes) -> "TechnicalBlock":
        """Receiver (customer) signs first."""
        return TechnicalBlock(
            block_id=self.block_id,
            deal_id=self.deal_id,
            party_a_id=self.party_a_id,
            party_b_id=self.party_b_id,
            amount=self.amount,
            created_at=self.created_at,
            receiver_signature=signature,
            obligor_signature=self.obligor_signature,
        )
    
    def sign_by_obligor(self, signature: bytes) -> "TechnicalBlock":
        """Obligor (performer) signs and returns."""
        return TechnicalBlock(
            receiver_signature=self.receiver_signature,
            obligor_signature=signature,
            claim_code=self.claim_code,
            **self.__dict__,
        )
    
    def attach_claim_code(self, code: str) -> "TechnicalBlock":
        """Attach claim code for reclamation."""
        return TechnicalBlock(claim_code=code, **self.__dict__)
```

**Related terms:** [Deal](#deal), [Reclamation](#reclamation), [Deal Signing](#deal-signing)

---

### Deal Signing

**Russian:** Подписание сделки  
**Definition:** The process of creating a legally binding deal. The obligation receiver signs first (initiating the deal), then the obligor signs and returns (accepting the obligation).

**Context:** Deal signing is a two-step process: (1) receiver creates the technical block and signs it, (2) obligor reviews and signs, returning the completed block. The deal becomes "open" once both signatures are present.

**Code mapping:**
```python
# contexts/transaction_deal/application/
class DealSigningService:
    def __init__(
        self,
        deal_repository: DealRepository,
        capacity_service: GuaranteeCapacityService,
        signature_service: SignatureService,
    ):
        self._deals = deal_repository
        self._capacity = capacity_service
        self._signatures = signature_service
    
    def create_and_sign_by_receiver(
        self,
        receiver_id: str,
        obligor_id: str,
        deal_data: DealData,
    ) -> TechnicalBlock:
        # Check receiver has capacity
        capacity = self._capacity.calculate(receiver_id)
        if not capacity.can_open_transaction(deal_data.amount):
            raise InsufficientCapacityError()
        
        # Create technical block
        block = TechnicalBlock(
            block_id=uuid4(),
            deal_id=uuid4(),
            party_a_id=obligor_id,
            party_b_id=receiver_id,
            amount=deal_data.amount,
            created_at=datetime.now(),
        )
        
        # Receiver signs
        signed_block = block.sign_by_receiver(
            self._signatures.sign(block, receiver_id)
        )
        
        return signed_block
    
    def sign_by_obligor(self, block: TechnicalBlock, obligor_id: str) -> Deal:
        # Check obligor capacity
        capacity = self._capacity.calculate(obligor_id)
        if not capacity.can_open_transaction(block.amount):
            raise InsufficientCapacityError()
        
        # Obligor signs
        signed_block = block.sign_by_obligor(
            self._signatures.sign(block, obligor_id)
        )
        
        # Create and open the deal
        deal = self._open_deal(signed_block)
        
        # Reserve capacity for both parties
        self._capacity.reserve(block.party_a_id, block.amount)
        self._capacity.reserve(block.party_b_id, block.amount)
        
        return deal
```

**Related terms:** [Technical Block](#technical-block), [Deal](#deal), [Guarantee Capacity](#guarantee-capacity), [Electronic Digital Signature (EDS)](#electronic-digital-signature-eds)

---

### Deal Closure

**Russian:** Закрытие сделки  
**Definition:** The process of completing a transaction. The obligation receiver signs a closing block with a closure code and returns it to the obligor. Once closed, the deal is final and guarantee capacity is restored.

**Context:** Deal closure is initiated by the obligation receiver (the customer). They sign a closing block indicating the service/goods were received satisfactorily. The closure code proves the receiver confirmed. If the receiver doesn't close within the recall period, the deal may be disputed.

**Code mapping:**
```python
# contexts/transaction_deal/domain/
@dataclass
class ClosingBlock:
    deal_id: str
    closure_code: str       # Unique code generated for this closure
    receiver_signature: bytes
    closed_at: datetime
    comments: Optional[str]
    
    def verify(self, deal: Deal, receiver_signature_service: SignatureService) -> bool:
        """Verify the closing block is valid."""
        return receiver_signature_service.verify(
            self.closure_code,
            deal.party_b_id,
            self.receiver_signature,
        )

# contexts/transaction_deal/application/
class DealClosureService:
    def close_deal(
        self,
        deal_id: str,
        receiver_id: str,
        closure_code: str,
    ) -> ClosedDeal:
        deal = self._deals.get(deal_id)
        
        if deal.party_b_id != receiver_id:
            raise NotReceiverError("Only receiver can close the deal")
        
        if deal.status != DealStatus.SIGNED_BY_OBLIGOR:
            raise InvalidStatusError("Deal must be active to close")
        
        # Create closing block
        closing = ClosingBlock(
            deal_id=deal_id,
            closure_code=closure_code,
            receiver_signature=self._signatures.sign(closure_code, receiver_id),
            closed_at=datetime.now(),
        )
        
        # Update deal status
        deal.status = DealStatus.CLOSED
        deal.closed_at = datetime.now()
        deal.closing_block = closing
        self._deals.save(deal)
        
        # Restore guarantee capacity to both parties
        self._capacity.release(deal.party_a_id, deal.amount)
        self._capacity.release(deal.party_b_id, deal.amount)
        
        return deal
```

**Related terms:** [Deal](#deal), [Recall Period](#recall-period), [Guarantee Capacity](#guarantee-capacity), [Reclamation](#reclamation)

---

### Recall Period

**Russian:** Период отзыва  
**Definition:** A time window after deal closure during which the deal can be disputed or recalled. The period varies by transaction amount: 30 minutes for small amounts (100 units), up to 1 year for large amounts.

**Context:** The recall period protects both parties. If the receiver realizes the goods/services were unsatisfactory, they can file a reclamation during this period. After the recall period expires, the deal is considered final.

**Code mapping:**
```python
# contexts/transaction_deal/domain/
class RecallPeriodCalculator:
    """Calculates recall period based on transaction amount."""
    
    # Historical tiers from Almaty experiment
    SMALL_AMOUNT = 100.0      # 30 minutes
    MEDIUM_AMOUNT = 1000.0    # 24 hours
    LARGE_AMOUNT = 10000.0    # 7 days
    MAX_AMOUNT = 100000.0     # 1 year
    
    @classmethod
    def get_recall_period(cls, amount: float) -> timedelta:
        if amount <= cls.SMALL_AMOUNT:
            return timedelta(minutes=30)
        elif amount <= cls.MEDIUM_AMOUNT:
            return timedelta(hours=24)
        elif amount <= cls.LARGE_AMOUNT:
            return timedelta(days=7)
        else:
            return timedelta(days=365)
    
    @classmethod
    def get_dispute_window(cls, closed_at: datetime, amount: float) -> datetime:
        """Returns the deadline for filing reclamation."""
        period = cls.get_recall_period(amount)
        return closed_at + period

@dataclass
class RecallDeadline:
    deal_id: str
    recall_expires_at: datetime
    can_file_reclamation: bool
    
    def is_expired(self) -> bool:
        return datetime.now() > self.recall_expires_at
```

**Related terms:** [Deal Closure](#deal-closure), [Reclamation](#reclamation), [Claim](#claim)

---

### NFT-Contract

**Russian:** NFT-договор  
**Definition:** A blockchain-recorded digital contract representing a deal. NFT-contracts are unique, immutable, and timestamped. They prevent retroactive modification and serve as proof of agreement.

**Context:** NFT-contracts differ from smart contracts. Smart contracts require centralized enforcement; NFT-contracts rely on collective verification by interested parties (self-governance). The NFT contains: who, when, for what, through whom.

**Code mapping:**
```python
# contexts/transaction_deal/domain/
@dataclass
class NFTContract:
    token_id: str            # Blockchain token ID
    deal_id: str            # Reference to the deal
    creator_participant_id: str
    contract_type: str       # deal, crowdfunding, equity, etc.
    metadata: dict          # Who, when, for what, through whom
    created_at: datetime
    blockchain_tx_hash: str
    status: NFTContractStatus
    
    def get_parties(self) -> tuple[str, str]:
        return (self.metadata["party_a"], self.metadata["party_b"])
    
    def is_verified(self) -> bool:
        """Check if contract has been verified by parties."""
        return all(self.metadata.get(f"signature_{p}") for p in self.get_parties())

class NFTContractStatus:
    CREATED = "created"
    SIGNED = "signed"
    FULFILLED = "fulfilled"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"

# contexts/transaction_deal/infrastructure/
class NFTContractStorage(Protocol):
    """Port: blockchain storage for NFT contracts."""
    def mint(self, contract: NFTContract) -> str: ...  # Returns token_id
    def transfer(self, token_id: str, from_id: str, to_id: str) -> None: ...
    def get_metadata(self, token_id: str) -> dict: ...
```

**Related terms:** [Deal](#deal), [Smart Contract](#smart-contract), [Blockchain](#blockchain), [Collective Verification](#collective-verification)

---

### Deal Template

**Russian:** Шаблон сделки  
**Definition:** A standardized form for creating deals. Templates ensure all required fields are present and provide consistency across the network.

**Context:** The mandatory fields for a deal template are: Parties, Subject, Deadline, Success criteria, Value/equivalent, Deposit amounts, Guarantors per side, Reclamation channel. Templates can be simple (micro-deals) or complex (crowdfunding, trust management).

**Code mapping:**
```python
# contexts/transaction_deal/domain/
@dataclass
class DealTemplate:
    template_id: str
    name: str
    category: str            # micro, standard, complex, crowdfunding
    required_fields: list[str]
    optional_fields: list[str]
    default_recall_period: timedelta
    requires_guarantors: bool
    
    # Required fields per Synergy4all rules
    REQUIRED = [
        "parties",
        "subject",
        "deadline",
        "success_criteria",
        "value",
        "deposit_amounts",
        "guarantors_per_side",
        "reclamation_channel",
    ]

@dataclass
class DealData:
    """Data to create a deal from template."""
    template_id: str
    party_a_id: str
    party_b_id: str
    subject: str
    amount: float
    deadline: datetime
    success_criteria: str
    value_type: str          # money, goods, services, equivalent
    
    def validate(self, template: DealTemplate) -> ValidationResult:
        """Validate data against template requirements."""
        pass
```

**Related terms:** [Deal](#deal), [Reclamation Channel](#reclamation-channel), [Guarantor](#guarantor)

---

### Obligor

**Russian:** Обязанная сторона  
**Definition:** The participant who has the obligation to deliver goods or services. Also called "performer" or "service provider." They sign the deal second, accepting the obligation.

**Context:** The obligor is the party who will perform the service or provide the goods. They must have sufficient guarantee capacity to enter the deal. Once the deal is closed by the receiver, their guarantee capacity is restored.

**Code mapping:**
```python
# contexts/transaction_deal/domain/
@dataclass
class DealParty:
    participant_id: str
    role: str  # OBLIGOR or RECEIVER
    
    def is_obligor(self) -> bool:
        return self.role == "obligor"
    
    def is_receiver(self) -> bool:
        return self.role == "receiver"

class PartyRole:
    OBLIGOR = "obligor"      # Performer / service provider
    RECEIVER = "receiver"    # Customer / buyer
```

**Related terms:** [Deal](#deal), [Obligation Receiver](#obligation-receiver), [Guarantee Capacity](#guarantee-capacity)

---

### Obligation Receiver

**Russian:** Получатель обязательства  
**Definition:** The participant who receives the goods or services. Also called "customer" or "buyer." They sign the deal first, initiating the transaction.

**Context:** The obligation receiver is the customer in the transaction. They initiate the deal by signing the technical block first. Upon receiving satisfactory goods/services, they close the deal with a closure code.

**Code mapping:**
```python
# contexts/transaction_deal/domain/
# See Obligor — PartyRole.RECEIVER

@dataclass
class ObligationReceiver:
    participant_id: str
    role: str = "receiver"
    
    def initiate_deal(self, obligor_id: str, deal_data: DealData) -> TechnicalBlock:
        """Receiver initiates by creating and signing technical block."""
        pass
    
    def close_deal(self, deal_id: str, closure_code: str) -> ClosingBlock:
        """Receiver confirms satisfaction and closes the deal."""
        pass
```

**Related terms:** [Deal](#deal), [Obligor](#obligor), [Deal Closure](#deal-closure)

---

### Multi-Link Exchange Chain

**Russian:** Многосвязная цепочка обмена  
**Definition:** A transaction involving more than two participants, where value flows through a chain. Example: A fixes B's car → B (farmer) gives milk to C's child → C fixes A's computer. Differences in value are recorded as accounting units.

**Context:** The Almaty experiment used multi-link exchanges to enable participants without direct matching to still transact. The system finds chains of complementary needs. Value differences are tracked as internal credits (accounting units/bonuses) that can be spent later.

**Code mapping:**
```python
# contexts/transaction_deal/domain/
@dataclass
class ExchangeChain:
    chain_id: str
    participants: list[str]  # [A, B, C, ...]
    exchanges: list[Exchange]  # Each leg of the chain
    total_value: float
    accounting_units_settled: float  # Difference carryover
    
@dataclass
class Exchange:
    from_participant_id: str
    to_participant_id: str
    goods_or_service: str
    value: float

@dataclass
class AccountingUnit:
    """Internal credit for value differences."""
    unit_id: str
    holder_id: str
    amount: float
    earned_from: str  # Which exchange created the difference
    can_spend_on: list[str]  # Categories of acceptable use
```

**Related terms:** [Account Unit](#account-unit), [Marketplace](#marketplace), [Equivalent Exchange](#equivalent-exchange)

---

### Equivalent Exchange

**Russian:** Эквивалентный обмен  
**Definition:** Transactions settled in equivalent value, not necessarily money. Services, goods, or accounting units can all serve as payment. The key principle is equivalence of value, not medium of exchange.

**Context:** Synergy4all supports multiple value types: money, goods, services, and accounting units. Equivalence is determined by agreement between parties or by market price of equivalent. This enables bartering and service exchanges.

**Code mapping:**
```python
# contexts/transaction_deal/domain/
class EquivalentType:
    MONEY = "money"
    GOODS = "goods"
    SERVICES = "services"
    ACCOUNTING_UNIT = "accounting_unit"
    MIXED = "mixed"  # Combination of above

@dataclass
class EquivalentValue:
    """Represents value regardless of medium."""
    amount: float
    equivalent_type: str
    conversion_rate: float  # To base unit (e.g., money)
    
    def convert_to(self, target_type: str) -> float:
        """Convert to another equivalent type."""
        # Use conversion rates
        pass
    
    @classmethod
    def from_goods(cls, goods_value: float) -> "EquivalentValue":
        return cls(goods_value, EquivalentType.GOODS, conversion_rate=1.0)
    
    @classmethod
    def from_services(cls, service_value: float) -> "EquivalentValue":
        return cls(service_value, EquivalentType.SERVICES, conversion_rate=1.0)
```

**Related terms:** [Account Unit](#account-unit), [Multi-Link Exchange Chain](#multi-link-exchange-chain), [Transaction](#transaction)

---

### Reclamation Channel

**Russian:** Канал рекламации  
**Definition:** The designated path for filing claims/disputes related to a specific deal. Each deal specifies which guarantors or arbitration mechanism handles disputes.

**Context:** When creating a deal, parties must specify the reclamation channel — typically their mutual guarantors. For more complex deals, the channel might include additional arbitrators or specific dispute resolution rules.

**Code mapping:**
```python
# contexts/transaction_deal/domain/
@dataclass
class ReclamationChannel:
    channel_id: str
    deal_id: str
    primary_arbiters: list[str]  # guarantor IDs
    escalation_path: list[str]   # higher-level arbitrators
    rules: dict                  # Custom rules for this deal type
    
    def file_claim(self, claim_data: ClaimData) -> Claim:
        """File a claim through this channel."""
        # Route to primary arbitrators first
        pass
    
    def escalate(self, claim_id: str) -> None:
        """If primary fails, escalate to next level."""
        pass

class DefaultReclamationChannel:
    """Standard channel using mutual guarantors."""
    @staticmethod
    def for_deal(deal: Deal) -> ReclamationChannel:
        return ReclamationChannel(
            channel_id=f"default_{deal.deal_id}",
            deal_id=deal.deal_id,
            primary_arbiters=[deal.guarantor_a_id, deal.guarantor_b_id],
            escalation_path=[],  # Goes to guarantors' guarantors
            rules={},
        )
```

**Related terms:** [Deal](#deal), [Guarantor](#guarantor), [Reclamation](#reclamation), [Claim](#claim)

---

## Cross-Context Boundary Notes

| Term | Used by Context | Relationship |
|------|-----------------|--------------|
| Deal | [Dispute Resolution](synergy_dispute_resolution.md), [Synergy Cycle](synergy_cycle.md) | Primary entity for claims; forms cycle links |
| Technical Block | [Dispute Resolution](synergy_dispute_resolution.md) | Evidence in claim filing |
| Guarantee Capacity | [Deposit & Capacity](synergy_deposit_capacity.md) | Consumed by deals |
| NFT-Contract | [NFT/Tokenomics](synergy_nft_tokenomics.md) | Deal recorded as token |
| Deal Template | [Marketplace](synergy_marketplace.md), [NFT/Tokenomics](synergy_nft_tokenomics.md) | Used in cycle formation |
| Accounting Unit | [Deposit & Capacity](synergy_deposit_capacity.md), [Contribution Evaluation](synergy_contribution_evaluation.md) | Value difference tracking |
| Obligor / Receiver | [Dispute Resolution](synergy_dispute_resolution.md) | Parties to claim |