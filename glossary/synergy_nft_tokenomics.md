# NFT Contracts & Tokenomics

**Bounded Context:** NFT Contracts & Tokenomics  
**Domain:** Social Synergy (Социальная Синергия)  
**Status:** Supporting/Generic Subdomain

This context manages the blockchain-based infrastructure for Synergy4all: NFT contracts, various token types, and the tokenomics system. While important, this is a technical/infrastructure context that supports the core business domains.

---

### NFT Token

**Russian:** NFT-токен  
**Definition:** A unique, unforgeable digital token stored on blockchain. NFT tokens can represent many things in Synergy4all: deal contracts, share ownership, voting rights, authorship proof, or logistics data.

**Context:** NFT tokens are the technical foundation for trustless operations. Once created, they cannot be modified or deleted. All data is permanently recorded. Any participant can verify all transactions, fund movements, and token histories.

**Code mapping:**
```python
# contexts/nft_tokenomics/domain/
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

@dataclass
class NFTToken:
    token_id: str
    token_type: TokenType
    owner_participant_id: str
    metadata: dict
    created_at: datetime
    blockchain_tx_hash: str
    status: TokenStatus
    
    def transfer(self, to_participant_id: str) -> TokenTransfer:
        """Transfer ownership to another participant."""
        return TokenTransfer(
            token_id=self.token_id,
            from_id=self.owner_participant_id,
            to_id=to_participant_id,
            transferred_at=datetime.now(),
        )
    
    def get_history(self) -> list[TokenEvent]:
        """Get full history of this token."""
        pass

class TokenType:
    DEAL_CONTRACT = "deal_contract"
    CROWDFUNDING = "crowdfunding"
    EQUITY = "equity"
    LOGISTICS = "logistics"
    SMART_CONTRACT = "smart_contract"
    AUTHORSHIP = "authorship"
    VOTING = "voting"

class TokenStatus:
    ACTIVE = "active"
    FROZEN = "frozen"       # During dispute/resolution
    TRANSFERRED = "transferred"
    BURNED = "burned"       # Destroyed

@dataclass
class TokenEvent:
    event_type: str
    token_id: str
    timestamp: datetime
    participant_id: str
    details: dict
```

**Related terms:** [NFT-Contract](synergy_transaction_deal.md#nft-contract), [Blockchain](#blockchain), [Share Token](synergy_marketplace.md#share-token)

---

### Crowdfunding Token

**Russian:** Краудфандинговый токен  
**Definition:** A token representing a financial contribution to a project. Crowdfunding tokens are tied to the contribution amount and can be tradeable or usable within the project.

**Context:** Crowdfunding tokens enable project funding without traditional intermediaries. Participants buy tokens to fund projects. The tokens represent their contribution and may provide benefits (discounts, priority access, voting rights) depending on project terms.

**Code mapping:**
```python
# contexts/nft_tokenomics/domain/
@dataclass
class CrowdfundingToken(NFTToken):
    def __init__(self, *args, **kwargs):
        kwargs["token_type"] = TokenType.CROWDFUNDING
        super().__init__(*args, **kwargs)
    
    project_id: str
    contribution_amount: float
    contribution_currency: str  # money, goods, services
    token_price: float         # Price per token
    tradeable: bool            # Can be sold on secondary market
    benefits: list[str]       # Discounts, priority, etc.

@dataclass
class CrowdfundingCampaign:
    campaign_id: str
    project_id: str
    goal_amount: float
    raised_amount: float
    token_price: float
    start_date: datetime
    end_date: datetime
    status: CampaignStatus
    token_contract_address: str
    
    def is_successful(self) -> bool:
        return self.raised_amount >= self.goal_amount
    
    def get_contribution_summary(
        self,
        participant_id: str,
    ) -> ContributionSummary:
        tokens = self._token_repo.get_by_owner(participant_id)
        return ContributionSummary(
            participant_id=participant_id,
            tokens_held=len(tokens),
            total_value=tokens.total_value(),
        )

class CampaignStatus:
    FUNDING = "funding"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ACTIVE = "active"  # Project running
    COMPLETED = "completed"
```

**Related terms:** [Project](#project), [Crowdfunding](#crowdfunding), [Tokenomics](#tokenomics)

---

### Equity Token

**Russian:** Токен акций  
**Definition:** A token representing digital ownership shares in a project, virtual corporation, or shared asset. Equity tokens represent co-ownership and may include voting rights and profit-sharing.

**Context:** Equity tokens are the digital equivalent of shares. Purchasing an equity token makes the holder a co-owner. These tokens are typically not tradeable (or have trade restrictions) to maintain ownership integrity.

**Code mapping:**
```python
# contexts/nft_tokenomics/domain/
@dataclass
class EquityToken(NFTToken):
    def __init__(self, *args, **kwargs):
        kwargs["token_type"] = TokenType.EQUITY
        super().__init__(*args, **kwargs)
    
    entity_id: str          # Project or Virtual Corporation ID
    share_percentage: float
    voting_weight: float    # May differ from ownership %
    profit_share: float    # Percentage of profits
    transfer_restricted: bool
    lock_period_days: int   # If restricted

@dataclass
class EquityDistribution:
    entity_id: str
    total_shares: float
    tokenized_shares: float  # Portion tokenized
    holders: list[EquityHolder]
    
    def calculate_votes(
        self,
        token_id: str,
        proposal_id: str,
    ) -> float:
        """Calculate voting power for a proposal."""
        token = self._tokens.get(token_id)
        return token.voting_weight * token.share_percentage
    
    def calculate_dividend(
        self,
        total_profit: float,
    ) -> dict[str, float]:
        """Distribute profit to holders."""
        distribution = {}
        for holder in self.holders:
            tokens = self._tokens.get_by_owner(holder.participant_id)
            total_share = sum(t.share_percentage for t in tokens)
            distribution[holder.participant_id] = total_profit * (total_share / 100)
        return distribution

@dataclass
class EquityHolder:
    participant_id: str
    total_shares: float
    voting_power: float
```

**Related terms:** [Virtual Corporation](synergy_cycle.md#virtual-corporation), [Share](synergy_contribution_evaluation.md#share), [Voting Token](#voting-token)

---

### Logistics Token

**Russian:** Токен логистики и учета  
**Definition:** A token containing data about work performed, expenses, income, and project status. Logistics tokens track the "logistics and accounting" of operations.

**Context:** Logistics tokens are used for operational tracking. They contain proof of work, expense records, delivery confirmations, and status updates. These tokens provide transparency and auditability for project operations.

**Code mapping:**
```python
# contexts/nft_tokenomics/domain/
@dataclass
class LogisticsToken(NFTToken):
    def __init__(self, *args, **kwargs):
        kwargs["token_type"] = TokenType.LOGISTICS
        super().__init__(*args, **kwargs)
    
    operation_type: str     # delivery, work_completed, expense, income
    related_deal_id: Optional[str]
    data: dict              # Specific data (photos, geolocation, documents)
    timestamp: datetime
    verified_by: Optional[str]  # Who verified the data

@dataclass
class WorkProof:
    """Token for proof of work completion."""
    token_id: str
    executor_id: str
    deal_id: str
    work_description: str
    evidence_attachments: list[str]  # URLs to photos, docs
    location: Optional[GeoLocation]
    completed_at: datetime
    verified: bool
    verified_by: Optional[str]

@dataclass
class ExpenseRecord:
    """Token for expense tracking."""
    token_id: str
    project_id: str
    amount: float
    category: str
    description: str
    receipts: list[str]
    approved: bool

@dataclass
class DeliveryConfirmation:
    """Token for delivery verification."""
    token_id: str
    from_participant_id: str
    to_participant_id: str
    deal_id: str
    delivered_at: datetime
    condition: str  # good, damaged, etc.
```

**Related terms:** [Deal](synergy_transaction_deal.md#deal), [Proof of Work](#proof-of-work), [Project](#project)

---

### Smart Contract Token

**Russian:** Токен смарт-контрактов  
**Definition:** A token representing an automated digital contract that executes when conditions are met. Unlike NFT-contracts which rely on social verification, smart contract tokens use code-based enforcement.

**Context:** Smart contract tokens automate conditional payments and obligations. However, Synergy4all explicitly distinguishes between smart contracts (automated) and NFT-contracts (socially verified). Smart contracts are appropriate for simple conditional logic; complex social situations require the reclamation system.

**Code mapping:**
```python
# contexts/nft_tokenomics/domain/
@dataclass
class SmartContractToken(NFTToken):
    def __init__(self, *args, **kwargs):
        kwargs["token_type"] = TokenType.SMART_CONTRACT
        super().__init__(*args, **kwargs)
    
    contract_code: str      # Smart contract logic
    conditions: dict        # Trigger conditions
    executed_at: Optional[datetime]
    execution_result: Optional[dict]

@dataclass
class SmartContract:
    contract_id: str
    creator_id: str
    contract_type: str      # escrow, payment, conditional
    trigger_conditions: list[Trigger]
    actions: list[ContractAction]
    status: ContractStatus
    
    def evaluate(self, event: dict) -> list[ContractAction]:
        """Check if conditions met and return actions."""
        for trigger in self.trigger_conditions:
            if trigger.matches(event):
                return self._execute_actions(trigger.actions)
        return []

class Trigger:
    condition_type: str
    parameters: dict
    
    def matches(self, event: dict) -> bool:
        # Check if event satisfies condition
        pass

@dataclass
class ContractAction:
    action_type: str  # transfer, notify, update
    parameters: dict

class ContractStatus:
    ACTIVE = "active"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
```

**Related terms:** [NFT-Contract](synergy_transaction_deal.md#nft-contract), [Collective Verification](#collective-verification), [Reclamation](synergy_dispute_resolution.md#reclamation)

---

### Authorship Token

**Russian:** Токен авторства  
**Definition:** A token that proves authorship of content, protecting against deepfakes and falsification. Authorship tokens establish provenance and ownership of intellectual work.

**Context:** Authorship tokens address the challenge of verifying who created what in a digital network. Creators mint authorship tokens when producing original work. The token serves as proof against plagiarism and deepfake fabrication.

**Code mapping:**
```python
# contexts/nft_tokenomics/domain/
@dataclass
class AuthorshipToken(NFTToken):
    def __init__(self, *args, **kwargs):
        kwargs["token_type"] = TokenType.AUTHORSHIP
        super().__init__(*args, **kwargs)
    
    content_hash: str       # Hash of the content
    content_type: str       # text, image, video, audio, code
    title: str
    description: str
    original_creator_id: str
    
    def verify_ authorship(self, content: str) -> bool:
        """Verify content matches the token's hash."""
        return hashlib.sha256(content.encode()).hexdigest() == self.content_hash
    
    def transfer(self, new_owner_id: str) -> None:
        """Transfer — but original creator always tracked."""
        # Authorship can transfer but original creator remains in metadata
        self.metadata["original_creator"] = self.original_creator_id
        super().transfer(new_owner_id)

@dataclass
class ContentRegistry:
    """Registry of all authorship tokens."""
    def register(
        self,
        creator_id: str,
        content: str,
        content_type: str,
    ) -> AuthorshipToken:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        token = AuthorshipToken(
            token_id=uuid4(),
            owner_participant_id=creator_id,
            metadata={},
            created_at=datetime.now(),
            blockchain_tx_hash=self._mint_to_blockchain(),
            status=TokenStatus.ACTIVE,
            content_hash=content_hash,
            content_type=content_type,
            title="",
            description="",
            original_creator_id=creator_id,
        )
        
        return token
    
    def verify(self, token_id: str, content: str) -> bool:
        token = self._tokens.get(token_id)
        return token.verify_authorship(content)
```

**Related terms:** [Content](#content), [Intellectual Property](#intellectual-property), [Proof of Authorship](#proof-of-authorship)

---

### Voting Token

**Russian:** Токен голосования  
**Definition:** A token used for governance decisions within projects, virtual corporations, or the network. Voting tokens represent decision-making power.

**Context:** Voting tokens enable decentralized governance. Unlike equity tokens which represent ownership, voting tokens specifically represent the right to participate in decisions. One participant may have both equity and voting tokens.

**Code mapping:**
```python
# contexts/nft_tokenomics/domain/
@dataclass
class VotingToken(NFTToken):
    def __init__(self, *args, **kwargs):
        kwargs["token_type"] = TokenType.VOTING
        super().__init__(*args, **kwargs)
    
    entity_id: str          # Project, VC, or network
    voting_power: float     # Weight of this vote
    token_type: str         # equity_based, reputation_based, one_per_person
    
@dataclass
class Proposal:
    proposal_id: str
    entity_id: str
    title: str
    description: str
    proposed_by: str
    votes_for: float
    votes_against: float
    status: ProposalStatus
    voting_ends_at: datetime
    
    def tally_votes(
        self,
        votes: list[VotingToken],
    ) -> VoteResult:
        total_for = sum(v.voting_power for v in votes if v.vote == "for")
        total_against = sum(v.voting_power for v in votes if v.vote == "against")
        
        return VoteResult(
            proposal_id=self.proposal_id,
            passed=total_for > total_against,
            votes_for=total_for,
            votes_against=total_against,
        )

class ProposalStatus:
    DRAFT = "draft"
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXPIRED = "expired"

@dataclass
class Vote:
    token_id: str
    proposal_id: str
    vote: str  # "for", "against", "abstain"
    voted_at: datetime
```

**Related terms:** [Virtual Corporation](synergy_cycle.md#virtual-corporation), [Equity Token](#equity-token), [Governance](#governance)

---

### Collective Verification

**Russian:** Коллективная верификация  
**Definition:** The verification method for NFT-contracts where interested parties (not centralized authorities) validate transactions. This is the self-governance mechanism that replaces centralized verification.

**Context:** Unlike traditional systems with banks or state verification, Synergy4all relies on collective verification by personally interested parties. The guaranty chain ensures verification happens — parties with skin in the game (guarantors, participants in the cycle) verify transactions.

**Code mapping:**
```python
# contexts/nft_tokenomics/domain/
class CollectiveVerification:
    """Verification by interested parties, not central authority."""
    
    @staticmethod
    def get_verifiers(
        transaction: NFTContract,
    ) -> list[str]:
        """Get list of parties who should verify this contract."""
        verifiers = []
        
        # Parties to the deal
        verifiers.extend(transaction.get_parties())
        
        # Their guarantors
        for party in transaction.get_parties():
            guarantors = self._guaranty_repo.get_guarantors(party)
            verifiers.extend([g.guarantor_id for g in guarantors])
        
        return verifiers
    
    @staticmethod
    def verify(
        contract: NFTContract,
        verifying_participant_id: str,
    ) -> VerificationResult:
        """A participant verifies the contract."""
        if verifying_participant_id not in CollectiveVerification.get_verifiers(contract):
            raise NotAuthorizedError("Not an interested party")
        
        # Verification logic: check signatures, data integrity
        return VerificationResult(
            verified=True,
            verifier_id=verifying_participant_id,
            verified_at=datetime.now(),
        )

@dataclass
class VerificationResult:
    verified: bool
    verifier_id: str
    verified_at: datetime
    verification_data: dict

@dataclass
class VerificationThreshold:
    """Minimum verifications required."""
    min_party_verifications: int = 1
    min_guarantor_verifications: int = 1
    
    def is_satisfied(
        self,
        verifications: list[VerificationResult],
    ) -> bool:
        party_count = sum(1 for v in verifications if self._is_party(v.verifier_id))
        guarantor_count = sum(1 for v in verifications if self._is_guarantor(v.verifier_id))
        
        return (
            party_count >= self.min_party_verifications
            and guarantor_count >= self.min_guarantor_verifications
        )
```

**Related terms:** [NFT-Contract](synergy_transaction_deal.md#nft-contract), [Guaranty Chain](synergy_participant_identity.md#guaranty-chain), [Blockchain](#blockchain)

---

### Personal Money

**Russian:** Личные деньги  
**Definition:** The concept that each participant can issue their own NFT-contracts representing their personal services or assets. Personal money transforms each participant into a potential "bank" — their contracts become a form of personal currency.

**Context:** "Personal money" is the ultimate expression of the NFT-contract system. Each participant can create contracts representing what they offer. These contracts can be exchanged directly without converting to fiat currency. This is a fundamental shift from centralized货币 to distributed value representation.

**Code mapping:**
```python
# contexts/nft_tokenomics/domain/
@dataclass
class PersonalMoneyContract:
    """NFT-contract representing personal services/assets."""
    contract_id: str
    issuer_id: str
    value_type: str          # service, goods, skill
    value_description: str
    redemption_conditions: str
    transferable: bool
    
    def get_issuer_profile(self) -> Storefront:
        """Get the issuer's storefront for credibility."""
        return self._storefront_repo.get(self.issuer_id)
    
    def accept_as_payment(
        self,
        recipient_id: str,
        amount: float,
    ) -> ContractExchange:
        """Exchange this personal money for other value."""
        return ContractExchange(
            from_contract_id=self.contract_id,
            to_participant_id=recipient_id,
            amount=amount,
            exchange_rate=1.0,  # Direct exchange
        )

@dataclass
class PersonalMoneyWallet:
    """Wallet containing various personal money contracts."""
    def __init__(self, participant_id: str):
        self.participant_id = participant_id
        self._contracts: list[PersonalMoneyContract] = []
    
    def add_contract(self, contract: PersonalMoneyContract) -> None:
        self._contracts.append(contract)
    
    def get_total_value(self) -> float:
        """Total value of all personal money contracts."""
        return sum(c.amount for c in self._contracts)
    
    def find_compatible_contracts(
        self,
        need: Need,
    ) -> list[PersonalMoneyContract]:
        """Find contracts that could fulfill a need."""
        return [
            c for c in self._contracts
            if c.value_type == need.category
        ]
```

**Related terms:** [NFT-Contract](synergy_transaction_deal.md#nft-contract), [Storefront](synergy_marketplace.md#storefront), [Equivalent Exchange](synergy_transaction_deal.md#equivalent-exchange)

---

### Conversion Gateway

**Russian:** Шлюз конвертации  
**Definition:** An exchange/bridge between NFT-contracts/crypto and fiat currency. The gateway is identified as a vulnerability point where authorities can block operations.

**Context:** Conversion gateways are the bridge between the Synergy4all internal economy and the external financial system. The transition path is: Money → Cryptocurrency → NFT-contracts denominated in currency → Direct NFT-to-NFT exchange (no currency needed). Gateways are the weakest point in this chain.

**Code mapping:**
```python
# contexts/nft_tokenomics/infrastructure/
class ConversionGateway:
    """Bridge between crypto/NFT and fiat."""
    
    def __init__(
        self,
        bank_api: BankAPI,
        crypto_exchange: CryptoExchange,
        gateway_status: GatewayStatus,
    ):
        self._bank = bank_api
        self._crypto = crypto_exchange
        self._status = gateway_status
    
    def nft_to_fiat(
        self,
        nft_contract: NFTContract,
        target_currency: str,
    ) -> ConversionResult:
        # Check gateway status (can be blocked by authorities)
        if self._status == GatewayStatus.BLOCKED:
            raise GatewayBlockedError("Gateway blocked by authorities")
        
        # Convert NFT value to fiat
        return ConversionResult(
            from_token_id=nft_contract.token_id,
            to_currency=target_currency,
            amount=self._calculate_value(nft_contract),
            gateway_fee=self._get_fee(),
        )
    
    def fiat_to_nft(
        self,
        amount: float,
        currency: str,
        target_participant_id: str,
    ) -> NFTContract:
        # Create NFT representing fiat value
        pass

class GatewayStatus:
    ACTIVE = "active"
    LIMITED = "limited"    # Some restrictions
    BLOCKED = "blocked"    # Full block by authorities

@dataclass
class ConversionResult:
    from_token_id: str
    to_currency: str
    amount: float
    fee: float
    gateway_id: str
```

**Related terms:** [Fiat Money](#fiat-money), [Cryptocurrency](#cryptocurrency), [NFT-Contract](#nft-contract), [Personal Money](#personal-money)

---

### Proof of Work Token

**Russian:** Доказательство выполнения работ  
**Definition:** A token that proves work was completed, with evidence (photos, geolocation, documents) attached. Proof of work tokens are created by executors and confirmed by clients.

**Context:** The proof of work flow: Executor performs work → creates token with evidence (photos, geolocation, documents) → Client verifies and confirms → immutable record is created. This is distinct from the smart contract token — it's about evidence, not automation.

**Code mapping:**
```python
# contexts/nft_tokenomics/domain/
@dataclass
class ProofOfWorkToken(NFTToken):
    def __init__(self, *args, **kwargs):
        kwargs["token_type"] = TokenType.LOGISTICS
        super().__init__(*args, **kwargs)
    
    executor_id: str
    deal_id: str
    work_description: str
    evidence_attachments: list[str]  # URLs to photos, docs
    geolocation: Optional[GeoLocation]
    timestamp: datetime
    client_confirmation: Optional[ClientConfirmation]

@dataclass
class WorkSubmission:
    """Executor submits work with evidence."""
    token_id: str
    executor_id: str
    deal_id: str
    work_performed: str
    evidence: list[WorkEvidence]
    submitted_at: datetime
    
    def to_proof_of_work_token(self) -> ProofOfWorkToken:
        return ProofOfWorkToken(
            token_id=uuid4(),
            owner_participant_id=self.executor_id,
            token_type=TokenType.LOGISTICS,
            metadata={},
            created_at=datetime.now(),
            blockchain_tx_hash="",
            status=TokenStatus.ACTIVE,
            executor_id=self.executor_id,
            deal_id=self.deal_id,
            work_description=self.work_performed,
            evidence_attachments=[e.url for e in self.evidence],
            geolocation=self.evidence[0].geolocation if self.evidence else None,
            timestamp=self.submitted_at,
            client_confirmation=None,
        )

@dataclass
class WorkEvidence:
    evidence_type: str  # photo, video, document
    url: str
    geolocation: Optional[GeoLocation]
    timestamp: datetime

@dataclass
class ClientConfirmation:
    client_id: str
    confirmed_at: datetime
    payment_released: bool
```

**Related terms:** [Deal](synergy_transaction_deal.md#deal), [Logistics Token](#logistics-token), [Payment](#payment)

---

## Cross-Context Boundary Notes

| Term | Used by Context | Relationship |
|------|-----------------|--------------|
| NFT Token | [Transaction & Deal](synergy_transaction_deal.md), [Marketplace](synergy_marketplace.md) | Represents deals, shares, votes |
| Deal/NFT-Contract | [Transaction & Deal](synergy_transaction_deal.md) | Deal recorded as NFT |
| Share Token | [Marketplace](synergy_marketplace.md), [Contribution Evaluation](synergy_contribution_evaluation.md) | Share represented as token |
| Equity Token | [Contribution Evaluation](synergy_contribution_evaluation.md) | Ownership in VC/project |
| Voting Token | [Synergy Cycle](synergy_cycle.md) | Governance in VC |
| Proof of Work | [Transaction & Deal](synergy_transaction_deal.md) | Work verification in deals |
| Collective Verification | [Transaction & Deal](synergy_transaction_deal.md), [Participant Identity](synergy_participant_identity.md) | Verification via guaranty chain |