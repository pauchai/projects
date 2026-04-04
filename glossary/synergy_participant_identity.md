# Participant Identity & Guarantorship

**Bounded Context:** Participant Identity & Guarantorship  
**Domain:** Social Synergy (Социальная Синергия)  
**Status:** Core Subdomain

This context manages participant registration, digital identity, guarantor relationships, and the trust network that underlies the entire Social Synergy system. Every other context depends on this one.

---

### Participant

**Russian:** Участник  
**Definition:** An individual or legal entity in the Synergy4all network. A participant has a digital signature (EDS), contact information, supply/demand profile, and guarantee capacity derived from their deposit. Participants can be physical persons, pensioners, businesses, or entire settlements acting as a single entity.

**Context:** The root aggregate of the entire system. Every participant must have exactly two guarantors to operate. A participant can simultaneously participate in unlimited synergy cycles without leaving their specialty. Participants are equal peers in a P2P network with no hierarchy.

**Code mapping:**
```python
# contexts/participant_identity/domain/
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Participant:
    participant_id: str
    eds_public_key: str  # Electronic Digital Signature
    contact_info: str
    offer: str           # What they provide
    need: str            # What they require
    can_vouch: str        # Their vouching capacity
    status: ParticipantStatus
    guarantor_chain: list[str]  # Up to root
    joined_at: datetime
    
    def can_transact(self, amount: float, guarantee_capacity: float) -> bool:
        """Check if participant has sufficient guarantee capacity."""
        return guarantee_capacity >= amount

class ParticipantStatus:
    ACTIVE = "active"
    BLOCKED = "blocked"
    EXCLUDED = "excluded"
    PENDING_GUARANTORS = "pending_guarantors"

# contexts/participant_identity/domain/events.py
class ParticipantJoined:
    """Domain event emitted when a participant completes onboarding."""
    pass

class ParticipantExited:
    """Domain event emitted when a participant voluntarily leaves."""
    pass

class ParticipantBlocked:
    """Domain event emitted when a participant is blocked via reclamation."""
    pass
```

**Related terms:** [Guarantor](#guarantor), [Guaranty Chain](#guaranty-chain), [Cluster](#cluster), [Electronic Digital Signature (EDS)](#electronic-digital-signature-eds), [Collective Participant](#collective-participant)

---

### Guarantor

**Russian:** Поручитель  
**Definition:** A participant who vouches for another participant (ward), holds their deposit, and acts as arbiter in disputes. A guarantor bears material (financial) responsibility for the failures of the person they vouch for. This is not moral obligation — it is economic liability backed by the deposit.

**Context:** Any participant can become a guarantor after 14 days of membership. A guarantor cannot have more than 12 wards. They must maintain direct personal contact with all wards. If contact is lost, they must withdraw their guarantorship. A guarantor can charge for their guarantorship services.

**Code mapping:**
```python
# contexts/participant_identity/domain/
@dataclass
class Guarantor:
    guarantor_id: str
    participant_id: str  # Links to Participant
    wards: list[str]     # Max 12
    max_guarantee_sum: float  # Cannot exceed own deposit
    
    def can_guarantee(self, amount: float, own_deposit: float) -> bool:
        """A guarantor cannot guarantee more than their own deposit."""
        return amount <= own_deposit
    
    def is_at_capacity(self) -> bool:
        """Check if guarantor has reached max 12 wards."""
        return len(self.wards) >= 12
    
    def has_direct_contact(self, ward_id: str) -> bool:
        """Guarantor must maintain direct contact with all wards."""
        # Implementation: check last_contact_at within 30 days
        pass
```

**Related terms:** [Ward](#ward), [Guarantee Deposit](#guarantee-deposit), [Max-12-Wards Rule](#max-12-wards-rule), [14-Day Tenure Rule](#14-day-tenure-rule), [Collegium](#collegium)

**Not to be confused with:** Recommender (Рекомендатель) — a historical term from earlier experiments. In Synergy4all, the guarantor role subsumes the recommender function.

---

### Ward

**Russian:** Поручаемый  
**Definition:** A participant who is vouched for by guarantors. Also called "guaranteed person." A ward has their deposit held by their guarantors and relies on their guarantors for dispute resolution.

**Context:** A ward must have exactly two guarantors to operate in the network. The ward's deposit is split across both guarantors. If a guarantor withdraws, the ward must find a new guarantor to continue operating.

**Code mapping:**
```python
# contexts/participant_identity/domain/
@dataclass
class Ward:
    ward_id: str
    participant_id: str
    guarantor_1_id: str
    guarantor_2_id: str
    
    def has_active_guarantors(self) -> bool:
        """A ward must have two active guarantors to operate."""
        return bool(self.guarantor_1_id and self.guarantor_2_id)
    
    def must_find_replacement(self, withdrawing_guarantor_id: str) -> None:
        """Called when a guarantor withdraws. Ward must find replacement."""
        pass
```

**Related terms:** [Guarantor](#guarantor), [Guarantee Deposit](#guarantee-deposit), [Guarantorship Withdrawal](#guarantorship-withdrawal)

---

### Guaranty Chain

**Russian:** Цепочка поручительства  
**Definition:** The hierarchical chain from a participant up through their guarantors, and their guarantors, up to the root. Every participant can trace their path to the origin of the network through this chain.

**Context:** The guaranty chain enables dispute escalation — if local guarantors cannot resolve a claim, it propagates up the chain. The "4th handshake principle" states that any person in a country is reachable within 4-5 links; globally, 9-12 links.

**Code mapping:**
```python
# contexts/participant_identity/domain/
from typing import Protocol

class GuarantyChainRepository(Protocol):
    """Port: storage for guaranty chain operations."""
    def get_chain(self, participant_id: str) -> list[str]: ...
    def get_depth(self, participant_id: str) -> int: ...
    def find_path(self, from_id: str, to_id: str) -> list[str] | None: ...

# contexts/participant_identity/application/
class GuarantyChainService:
    def __init__(self, repo: GuarantyChainRepository):
        self._repo = repo
    
    def get_escalation_path(self, participant_id: str) -> list[str]:
        """Returns list of guarantor IDs for escalation: [parent_guarantor, grandparent, ...]"""
        chain = self._repo.get_chain(participant_id)
        return chain[1:]  # Exclude self, start from immediate guarantor
    
    def is_within_4_handshakes(self, from_id: str, to_id: str) -> bool:
        """Check if two participants are within the 4th handshake principle."""
        path = self._repo.find_path(from_id, to_id)
        return path is not None and len(path) <= 4
```

**Related terms:** [Guarantor](#guarantor), [Reclamation Escalation](#reclamation-escalation), [4th Handshake Principle](#4th-handshake-principle), [Cluster Junction](#cluster-junction)

---

### Electronic Digital Signature (EDS)

**Russian:** ЭЦП (Электронная Цифровая Подпись)  
**Definition:** An electronic digital signature generated by participants and co-signed by their guarantors. The EDS serves as the participant's cryptographic identity in the network.

**Context:** A participant generates an EDS key pair. Both guarantors co-sign the public key. The signed EDS is sent to the Registration Automaton registry. The EDS is used to sign transactions and deals.

**Code mapping:**
```python
# contexts/participant_identity/domain/
@dataclass
class ElectronicDigitalSignature:
    participant_id: str
    public_key: str
    guarantor_1_signature: bytes
    guarantor_2_signature: bytes
    registered_at: datetime
    status: EDSStatus
    
    def is_valid(self) -> bool:
        """Verify both guarantor signatures."""
        pass

class EDSStatus:
    PENDING = "pending"      # Waiting for guarantor co-signature
    ACTIVE = "active"        # Registered and valid
    REVOKED = "revoked"      # Participant exited or was excluded
    SUSPENDED = "suspended"  # Temporarily suspended
```

**Related terms:** [Participant](#participant), [Guarantor](#guarantor), [Registration Automaton](#registration-automaton)

---

### 14-Day Tenure Rule

**Russian:** Правило 14-дневного стажа  
**Definition:** A participant can only become a guarantor after 14 days of membership in the network. This ensures the prospective guarantor has sufficient history before taking on financial responsibility for others.

**Context:** This rule prevents new participants from immediately vouching for others before understanding the system. It also allows time for the new participant's own guarantors to validate their behavior.

**Code mapping:**
```python
# contexts/participant_identity/domain/
class TenureRules:
    MIN_DAYS_TO_BECOME_GUARANTOR = 14
    
    def can_become_guarantor(self, participant: Participant) -> bool:
        tenure = datetime.now() - participant.joined_at
        return tenure.days >= self.MIN_DAYS_TO_BECOME_GUARANTOR
```

**Related terms:** [Participant](#participant), [Guarantor](#guarantor), [Guarantorship](#guarantorship)

---

### Max-12-Wards Rule

**Russian:** Правило максимум 12 поручаемых  
**Definition:** A single guarantor cannot have more than 12 wards (participants they vouch for). This limit ensures each guarantor can maintain direct contact and proper oversight of all their wards.

**Context:** The rule prevents guarantor overload. If a guarantor reaches 12 wards, they cannot accept new wards until some existing wards transfer to other guarantors or exit the network.

**Code mapping:**
```python
# contexts/participant_identity/domain/
class GuarantorLimits:
    MAX_WARDS = 12
    
    def can_accept_ward(self, guarantor: Guarantor) -> bool:
        return len(guarantor.wards) < self.MAX_WARDS
```

**Related terms:** [Guarantor](#guarantor), [Ward](#ward), [Direct Contact Requirement](#direct-contact-requirement)

---

### Direct Contact Requirement

**Russian:** Требование прямого контакта  
**Definition:** A guarantor must maintain direct personal contact with all their wards. This is not just recommended — it is a mandatory invariant. Loss of contact mandates withdrawal of guarantorship.

**Context:** "Direct contact" means the guarantor knows how to reach their ward (phone, email, in-person) and has communicated within a reasonable period. If a guarantor cannot reach a ward for an extended period, they must file to withdraw their guarantorship.

**Code mapping:**
```python
# contexts/participant_identity/domain/
@dataclass
class ContactRecord:
    ward_id: str
    guarantor_id: str
    last_contact_at: datetime
    contact_method: str  # phone, email, in_person
    
    def is_contact_lost(self, days_threshold: int = 30) -> bool:
        elapsed = datetime.now() - self.last_contact_at
        return elapsed.days > days_threshold

class ContactEnforcement:
    MAX_DAYS_WITHOUT_CONTACT = 30
    
    def check_contact_requirement(self, guarantor_id: str) -> list[str]:
        """Returns list of ward IDs with lost contact that require action."""
        # Query contact records, find stale contacts
        pass
    
    def mandate_withdrawal(self, guarantor_id: str, ward_id: str) -> None:
        """Guarantor must withdraw guarantorship for ward with lost contact."""
        pass
```

**Related terms:** [Guarantor](#guarantor), [Ward](#ward), [Guarantorship Withdrawal](#guarantorship-withdrawal)

---

### Cluster

**Russian:** Куст  
**Definition:** An autonomous sub-network of participants served by its own Registration Automaton. Clusters can be small (a neighborhood) or large (an entire region).

**Context:** Each cluster has its own Registration Automaton (private server) that processes requests, maintains the registry, and synchronizes with connected clusters. Clusters link to other clusters at junction points.

**Code mapping:**
```python
# contexts/participant_identity/domain/
@dataclass
class Cluster:
    cluster_id: str
    name: str
    automaton_endpoint: str  # Registration Automaton URL
    participant_count: int
    parent_cluster_id: str | None  # For hierarchy, optional
    
    def get_automaton(self) -> RegistrationAutomaton:
        """Get connection to this cluster's Registration Automaton."""
        pass
    
    def link_to(self, other_cluster: "Cluster", junction_participant_id: str) -> None:
        """Create a junction link to another cluster."""
        pass
```

**Related terms:** [Registration Automaton](#registration-automaton), [Cluster Junction](#cluster-junction), [Participant](#participant)

---

### Registration Automaton

**Russian:** Автомат регистрации  
**Definition:** A private server that serves a cluster. It processes requests, maintains the registry of participants, guarantorships, deposit sums, applications, and claims, and synchronizes with linked clusters.

**Context:** The Registration Automaton is the technical infrastructure for participant management. It accepts plugins for complex contracts (crowdfunding, trust management, commodity tracking). It can be run on modest hardware — one computer per 50-100 people suffices.

**Code mapping:**
```python
# contexts/participant_identity/infrastructure/
from typing import Protocol

class RegistrationAutomaton(Protocol):
    """Port: the registration automaton interface."""
    def register_participant(self, participant: Participant) -> None: ...
    def register_guarantorship(self, guarantor_id: str, ward_id: str) -> None: ...
    def update_deposit_sum(self, participant_id: str, amount: float) -> None: ...
    def file_claim(self, claim: Claim) -> None: ...
    def sync_with_peer(self, peer_endpoint: str) -> None: ...

class AutomatonPlugin(Protocol):
    """Port: plugins for complex contract types."""
    def process(self, contract_data: dict) -> dict: ...

# contexts/participant_identity/infrastructure/postgres_automaton.py
class PostgresRegistrationAutomaton:
    """PostgreSQL implementation of Registration Automaton."""
    def __init__(self, connection: Connection, plugins: list[AutomatonPlugin]):
        self._conn = connection
        self._plugins = plugins
```

**Related terms:** [Cluster](#cluster), [Participant](#participant), [Guarantor](#guarantor), [Claim](#claim)

---

### Cluster Junction

**Russian:** Точка стыка кластеров  
**Definition:** A participant who serves as the connection point between two clusters. The junction participant belongs to both clusters and enables claims and data to traverse cluster boundaries.

**Context:** When two clusters link, they designate a junction participant with metadata for locating the connected Automaton. Claims can traverse cluster boundaries. If one Automaton refuses a claim, the claimant can appeal to any linked higher-level cluster's Automaton.

**Code mapping:**
```python
# contexts/participant_identity/domain/
@dataclass
class ClusterJunction:
    junction_participant_id: str
    cluster_a_id: str
    cluster_b_id: str
    metadata: dict  # Contains endpoints for both Automatons
    
    def route_claim(self, claim_id: str, target_cluster_id: str) -> bool:
        """Route a claim to the target cluster's Automaton."""
        pass
    
    def resolve_appeal(self, rejected_claim_id: str, higher_cluster_id: str) -> None:
        """If local Automaton rejected claim, route to higher-level."""
        pass
```

**Related terms:** [Cluster](#cluster), [Registration Automaton](#registration-automaton), [Reclamation](#reclamation)

---

### Collective Participant

**Russian:** Коллективный участник  
**Definition:** A group entity (project, store, virtual corporation) that participates in the network as a single entity with a shared deposit. A collective participant has its own participants (members) but presents itself as one participant to the network.

**Context:** A collective participant has a shared deposit that backs all its transactions. Reclamation against a collective participant blocks only up to the claimant's deposit sum (not all activity), unless escalated. Special rules exist for individual member blocking within the group.

**Code mapping:**
```python
# contexts/participant_identity/domain/
@dataclass
class CollectiveParticipant:
    collective_id: str
    name: str
    member_participant_ids: list[str]
    shared_deposit: float
    
    def get_representative(self) -> str:
        """Return the primary participant representing the collective."""
        pass
    
    def apply_claim(self, claim_amount: float, claimant_deposit: float) -> float:
        """Reclamation against collective is limited to claimant's deposit."""
        return min(claim_amount, claimant_deposit)
    
    def block_member(self, member_id: str, reason: str) -> None:
        """Block a specific member within the collective."""
        pass
```

**Related terms:** [Participant](#participant), [Deposit](#deposit), [Reclamation](#reclamation), [Virtual Corporation](#virtual-corporation)

---

### Onboarding

**Russian:** Вступление в сеть / Регистрация  
**Definition:** The process of joining the Synergy4all network. A participant generates an EDS, finds two guarantors, deposits funds with each guarantor, guarantors co-sign the EDS, and the EDS is sent to the registry.

**Context:** Onboarding is the critical entry point. The 60-minute launch process is: gather 3-7 acquaintances → each chooses two guarantors → set minimum guarantee deposit → adopt three rules → create shared Demand/Supply board → execute first micro-deal → simulate one reclamation.

**Code mapping:**
```python
# contexts/participant_identity/application/
class OnboardingService:
    def __init__(
        self,
        eds_generator: EDSGenerator,
        guarantor_finder: GuarantorFinder,
        deposit_manager: DepositManager,
        automaton: RegistrationAutomaton,
    ):
        self._eds = eds_generator
        self._guarantor_finder = guarantor_finder
        self._deposit_manager = deposit_manager
        self._automaton = automaton
    
    def register(self, candidate: CandidateParticipant) -> Participant:
        # Step 1: Generate EDS
        eds = self._eds.generate(candidate.email)
        
        # Step 2: Find two guarantors
        guarantors = self._guarantor_finder.find_two(candidate)
        
        # Step 3: Deposit funds with each guarantor
        for guarantor in guarantors:
            self._deposit_manager.create_deposit(
                participant_id=candidate.id,
                guarantor_id=guarantor.id,
                amount=candidate.deposit_amount / 2,
            )
        
        # Step 4: Guarantors co-sign EDS
        for guarantor in guarantors:
            eds.add_guarantor_signature(guarantor.sign(eds.public_key))
        
        # Step 5: Register with Automaton
        self._automaton.register_participant(candidate.to_participant(eds))
        
        return candidate.to_participant(eds)
```

**Related terms:** [Electronic Digital Signature (EDS)](#electronic-digital-signature-eds), [Guarantor](#guarantor), [Guarantee Deposit](#guarantee-deposit), [Registration Automaton](#registration-automaton)

---

### Offboarding

**Russian:** Выход из сети  
**Definition:** The process of voluntarily leaving the Synergy4all network. On exit, a participant reclaims deposits minus outstanding claims. Guarantors provide receipts for any claim deductions.

**Context:** Offboarding requires all outstanding claims to be resolved. The exiting participant receives their deposit back, minus any amounts paid out for valid claims against them. The process involves both guarantors signing off on the exit.

**Code mapping:**
```python
# contexts/participant_identity/application/
class OffboardingService:
    def __init__(self, deposit_manager: DepositManager, claim_repository: ClaimRepository):
        self._deposits = deposit_manager
        self._claims = claim_repository
    
    def exit_network(self, participant_id: str) -> ExitResult:
        # Check for outstanding claims
        open_claims = self._claims.find_open_by_target(participant_id)
        if open_claims:
            raise ExitBlockedError(f"{len(open_claims)} open claims must be resolved")
        
        # Calculate returnable deposit
        total_deposit = self._deposits.get_total(participant_id)
        paid_claims = self._claims.get_total_paid(participant_id)
        returnable = total_deposit - paid_claims
        
        # Release deposits
        for deposit in self._deposits.get_all(participant_id):
            self._deposits.release(deposit, returnable)
        
        return ExitResult(
            participant_id=participant_id,
            deposit_returned=returnable,
            claims_paid=paid_claims,
        )
```

**Related terms:** [Participant](#participant), [Guarantee Deposit](#guarantee-deposit), [Claim](#claim), [Guarantor](#guarantor)

---

### Re-guarantorship

**Russian:** Перепоручительство  
**Definition:** The process of switching from one set of guarantors to another. A participant may need to find new guarantors if their current guarantors withdraw, or for other reasons.

**Context:** Re-guarantorship is initiated by either the ward (seeking new guarantors) or the guarantors (withdrawing). Both guarantors must file for complete removal of guarantorship. The ward must find replacement guarantors to continue operating.

**Code mapping:**
```python
# contexts/participant_identity/application/
class ReGuarantorshipService:
    def transfer_guarantors(
        self,
        participant_id: str,
        new_guarantor_1_id: str,
        new_guarantor_2_id: str,
    ) -> None:
        """Transfer to a new set of guarantors."""
        # Verify new guarantors meet all requirements
        # Update guarantorship records
        # Notify old guarantors
        pass
    
    def partial_withdrawal(self, guarantor_id: str, participant_id: str) -> None:
        """One guarantor withdraws, participant must find replacement."""
        pass
```

**Related terms:** [Guarantor](#guarantor), [Ward](#ward), [Onboarding](#onboarding), [Offboarding](#offboarding)

---

### 4th Handshake Principle

**Russian:** Принцип 4-го рукопожатия  
**Definition:** The principle that any needed person or resource is reachable within 2-4 links in the guarantorship network. In a country: 4-5 hops. Globally: 9-12 hops.

**Context:** This is a core feature enabling the "global search system" for products, services, technologies, and specialists. The principle ensures that participants can find what they need through their network connections.

**Code mapping:**
```python
# contexts/participant_identity/application/
class HandshakeService:
    def find_within_4_handshakes(
        self,
        from_participant_id: str,
        target_profile: ParticipantProfile,
    ) -> list[Participant]:
        """Find participants matching profile within 4-handshake distance."""
        # BFS up to depth 4
        pass
    
    def calculate_distance(self, participant_a: str, participant_b: str) -> int:
        """Return number of hops between two participants."""
        pass
```

**Related terms:** [Guaranty Chain](#guaranty-chain), [Marketplace](#marketplace), [Supply/Demand Matching](#supplydemand-matching)

---

## Cross-Context Boundary Notes

| Term | Used by Context | Relationship |
|------|-----------------|--------------|
| Participant | All 8 contexts | Root entity — every context depends on participant identity |
| Guarantor | [Deposit & Capacity](synergy_deposit_capacity.md), [Dispute Resolution](synergy_dispute_resolution.md) | Manages deposit custody, serves as arbitrator |
| Guarantee Deposit | [Deposit & Capacity](synergy_deposit_capacity.md), [Transaction & Deal](synergy_transaction_deal.md) | Backs guarantee capacity, enables transactions |
| Cluster | [Marketplace](synergy_marketplace.md), [NFT/Tokenomics](synergy_nft_tokenomics.md) | Groups participants, syncs registries |
| Registration Automaton | [Transaction & Deal](synergy_transaction_deal.md), [NFT/Tokenomics](synergy_nft_tokenomics.md) | Records deals, stores NFT contracts |
| Collective Participant | [Synergy Cycle](synergy_cycle.md), [Contribution Evaluation](synergy_contribution_evaluation.md) | Participates in cycles, receives share tokens |
| EDS | [Transaction & Deal](synergy_transaction_deal.md), [NFT/Tokenomics](synergy_nft_tokenomics.md) | Signs deals, creates tokens |