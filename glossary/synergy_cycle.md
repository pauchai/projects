# Synergy Cycle & Virtual Corporation

**Bounded Context:** Synergy Cycle & Virtual Corporation  
**Domain:** Social Synergy (Социальная Синергия)  
**Status:** Core Domain

This context is the **Core Domain** of Synergy4all — the highest strategic value. It manages the formation and operation of synergetic cycles: closed loops of participants whose cooperation generates emergent value exceeding the sum of individual contributions. Multiple cycles compose into virtual corporations for larger projects.

---

### Synergy Cycle

**Russian:** Синергетический цикл  
**Definition:** A closed loop of participants exchanging goods/services where emergent collective value is created. The cycle produces outcomes no single participant could achieve alone — this is the "new quality" (новое качество) that distinguishes social synergy from simple cooperation.

**Context:** A synergy cycle is the fundamental unit of value creation. Participants with complementary skills/goods/services form a closed loop: A→B→C→A. Each iteration multiplies the group's capabilities. The output value exceeds the sum of inputs — this is the multiplicative effect.

**Code mapping:**
```python
# contexts/synergy_cycle/domain/
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

@dataclass
class SynergyCycle:
    cycle_id: str
    name: str
    participants: list[CycleParticipant]  # Ordered: A→B→C→...→A
    deals: list[str]          # Deal IDs forming the cycle
    stage_discount: float     # 20% per stage
    iteration_count: int
    total_value_created: float
    created_at: datetime
    status: CycleStatus
    
    def get_participant_at(self, position: int) -> str:
        return self.participants[position % len(self.participants)].participant_id
    
    def next_participant(self, current_id: str) -> str:
        """Get next participant in the closed loop."""
        idx = next(i for i, p in enumerate(self.participants) if p.participant_id == current_id)
        return self.participants[(idx + 1) % len(self.participants)].participant_id
    
    def calculate_emergent_value(
        self,
        sum_of_individual_inputs: float,
    ) -> float:
        """New quality > sum of parts due to multiplicative effect."""
        # Each stage adds ~20% discount/efficiency
        stages = len(self.participants)
        multiplier = (1 + self.stage_discount) ** stages
        return sum_of_individual_inputs * multiplier

class CycleStatus:
    FORMING = "forming"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DISSOLVED = "dissolved"

@dataclass
class CycleParticipant:
    participant_id: str
    role: str            # organizer, specialist, consumer
    contribution_type: str  # goods, services, coordination
    contribution_value: float
    share_percentage: float  # Determined by Contribution Evaluation
```

**Related terms:** [Closed Cycle](#closed-cycle), [Emergent Quality](#emergent-quality), [Multiplicative Effect](#multiplicative-effect), [Virtual Corporation](#virtual-corporation), [20% Stage Discount](#20-stage-discount)

---

### Closed Cycle

**Russian:** Замкнутый цикл  
**Definition:** A synergetic cycle where the output flows back to the beginning, creating a closed production-consumption loop. Without closure, you get only arithmetic addition; with closure, you get multiplicative synergy.

**Context:** The "closed cycle principle" is essential. Open chains (A→B→C) are simple cooperation. Closed loops (A→B→C→A) are social synergy. The closure enables repeated iterations where value multiplies each pass. Example: nanny→dentist→cobbler→hairdresser→nanny.

**Code mapping:**
```python
# contexts/synergy_cycle/domain/
class CycleClosure:
    @staticmethod
    def is_closed(participants: list[str]) -> bool:
        """Check if all participants are connected in a loop."""
        return len(participants) >= 3  # Minimum for closed loop
    
    @staticmethod
    def verify_completeness(
        incoming: dict[str, float],
        outgoing: dict[str, float],
    ) -> CycleCompleteness:
        """Check if value flows back to start."""
        start_value = incoming.get(participants[0], 0)
        end_value = outgoing.get(participants[-1], 0)
        
        return CycleCompleteness(
            is_complete=start_value > 0 and end_value > 0,
            flow_balance=start_value - end_value,
        )

@dataclass
class CycleCompleteness:
    is_complete: bool
    flow_balance: float
    deficit_participant: Optional[str]
```

**Related terms:** [Synergy Cycle](#synergy-cycle), [Multiplicative Effect](#multiplicative-effect), [Production-Consumption Loop](#production-consumption-loop)

---

### Emergent Quality

**Russian:** Новое качество  
**Definition:** Capabilities that no individual participant possesses alone but emerge from their synergistic cooperation. The whole becomes greater than the sum of parts — this is the core value proposition of Synergy4all.

**Context:** Emergent quality is the "new quality" produced by synergy cycles. Example: individual tradespeople (bricklayer, carpenter, plumber) working separately can build houses, but through a closed synergy cycle they build houses more efficiently and the collective output exceeds what they could achieve independently.

**Code mapping:**
```python
# contexts/synergy_cycle/domain/
@dataclass
class EmergentQuality:
    cycle_id: str
    description: str         # What emerged
    input_sum: float        # Sum of individual contributions
    output_value: float     # Value of emergent result
    multiplier: float       # output / input
    
    def get_multiplier_effect(self) -> str:
        if self.multiplier >= 2.0:
            return "exponential"  # >100% gain
        elif self.multiplier >= 1.5:
            return "significant"  # 50%+ gain
        elif self.multiplier >= 1.2:
            return "moderate"     # 20%+ gain
        else:
            return "minimal"      # <20% gain

@dataclass
class EmergentProduct:
    """The tangible or intangible result of a synergy cycle."""
    product_id: str
    cycle_id: str
    description: str
    category: str          # physical_goods, services, knowledge, etc.
    value: float
    distributed_to: list[DistributionShare]
    
    def get_share_for(self, participant_id: str) -> float:
        for share in self.distributed_to:
            if share.participant_id == participant_id:
                return share.percentage
        return 0.0

@dataclass
class DistributionShare:
    participant_id: str
    percentage: float
    value: float
```

**Related terms:** [Synergy Cycle](#synergy-cycle), [Multiplicative Effect](#multiplicative-effect), [Virtual Corporation](#virtual-corporation)

---

### Multiplicative Effect

**Russian:** Мультипликация  
**Definition:** The compounding effect where value multiplies with each iteration of a synergy cycle. Unlike simple addition (a+b), multiplicative effect means each completed cycle amplifies the group's capabilities further.

**Context:** The multiplicative effect is why closed cycles matter. Each pass through the cycle returns value to participants, strengthening them and enabling larger next cycles. This creates exponential growth, not linear. The original Almaty experiment achieved 40-60% cost reduction through this effect.

**Code mapping:**
```python
# contexts/synergy_cycle/domain/
class MultiplicativeCalculator:
    BASE_DISCOUNT_PER_STAGE = 0.20  # 20% per stage
    
    @classmethod
    def calculate_stage_discount(
        cls,
        stage_count: int,
        discount_per_stage: float = None,
    ) -> float:
        """Total discount from N stages."""
        if discount_per_stage is None:
            discount_per_stage = cls.BASE_DISCOUNT_PER_STAGE
        
        # Compound: (1 + d)^n - 1
        total_discount = (1 + discount_per_stage) ** stage_count - 1
        return total_discount
    
    @classmethod
    def project_multi_iterations(
        cls,
        initial_input: float,
        stage_count: int,
        iterations: int,
    ) -> IterationProjection:
        """Project value growth over multiple iterations."""
        stage_discount = cls.calculate_stage_discount(stage_count)
        projected = initial_input
        
        projections = []
        for i in range(1, iterations + 1):
            projected *= (1 + stage_discount)
            projections.append(IterationResult(
                iteration=i,
                input_value=initial_input * (1 + stage_discount) ** (i-1),
                output_value=projected,
                multiplier=projected / initial_input,
            ))
        
        return IterationProjection(iterations=projections)

@dataclass
class IterationResult:
    iteration: int
    input_value: float
    output_value: float
    multiplier: float
```

**Related terms:** [Closed Cycle](#closed-cycle), [20% Stage Discount](#20-stage-discount), [Synergy Cycle](#synergy-cycle)

---

### Virtual Corporation

**Russian:** Виртуальная корпорация  
**Definition:** A higher-level entity formed by combining multiple synergy cycles, capable of undertaking large-scale projects (building houses, cities, "spaceships" in the metaphorical sense). A virtual corporation operates by the same SSS rules as individual participants.

**Context:** Virtual corporations emerge when multiple synergy cycles combine. They are not formal firms — they are emergent structures following the same rules: no hierarchy, closed loops, emergent quality. A virtual design bureau might participate as a single node in a city-building virtual corporation.

**Code mapping:**
```python
# contexts/synergy_cycle/domain/
@dataclass
class VirtualCorporation:
    vc_id: str
    name: str
    participating_cycles: list[str]      # SynergyCycle IDs
    participating_participants: list[str]  # Direct participants
    purpose: str                         # What it's building/accomplishing
    created_at: datetime
    status: VCStatus
    
    def get_total_capability(self) -> VCcapability:
        """Aggregate capability from all participating cycles."""
        capabilities = []
        for cycle_id in self.participating_cycles:
            cycle = self._cycle_repo.get(cycle_id)
            capabilities.append(cycle.total_value_created)
        
        return VCcapability(
            vc_id=self.vc_id,
            total_value=sum(c.total_value_created for c in capabilities),
            participant_count=len(self.participating_participants),
            cycle_count=len(self.participating_cycles),
        )
    
    def can_undertake(self, project_requirements: dict) -> bool:
        """Check if VC has capability for a project."""
        cap = self.get_total_capability()
        # Check against requirements
        pass
    
    def nest_into_larger_vc(self, parent_vc_id: str) -> None:
        """This VC can participate as a node in a larger VC."""
        pass

class VCStatus:
    FORMING = "forming"
    ACTIVE = "active"
    COMPLETED = "completed"
    DISSOLVED = "dissolved"
```

**Related terms:** [Synergy Cycle](#synergy-cycle), [Emergent Quality](#emergent-quality), [Participant](#participant), [Cycle Composition](#cycle-composition)

---

### Cycle Composition

**Russian:** Композиция циклов  
**Definition:** The process of combining multiple synergy cycles into a virtual corporation, or nesting virtual corporations into larger structures.

**Context:** Cycles compose hierarchically. Individual cycles combine into virtual corporations. Virtual corporations combine into meta-level virtual corporations. Each level follows the same SSS rules. The composition preserves the closed-loop principle at each level.

**Code mapping:**
```python
# contexts/synergy_cycle/application/
class CycleCompositionService:
    def compose_cycles(
        self,
        cycle_ids: list[str],
        purpose: str,
        name: str,
    ) -> VirtualCorporation:
        """Combine multiple cycles into a VC."""
        cycles = [self._cycle_repo.get(cid) for cid in cycle_ids]
        
        # Collect all participants
        all_participants = set()
        for cycle in cycles:
            all_participants.update(p.participant_id for p in cycle.participants)
        
        return VirtualCorporation(
            vc_id=uuid4(),
            name=name,
            participating_cycles=cycle_ids,
            participating_participants=list(all_participants),
            purpose=purpose,
            created_at=datetime.now(),
            status=VCStatus.FORMING,
        )
    
    def nest_vc(self, child_vc_id: str, parent_vc_id: str) -> None:
        """Add a VC as a node in a larger VC."""
        # Child VC participates as a single unit in parent
        pass
    
    def decompose(self, vc_id: str) -> list[str]:
        """Reverse: break VC back into individual cycles."""
        vc = self._vc_repo.get(vc_id)
        return vc.participating_cycles
```

**Related terms:** [Virtual Corporation](#virtual-corporation), [Synergy Cycle](#synergy-cycle), [Cycle Formation](#cycle-formation)

---

### Cycle Formation

**Russian:** Формирование цикла  
**Definition:** The process of creating a new synergy cycle by finding participants with complementary needs/offerings and organizing them into a closed loop.

**Context:** Cycle formation is triggered when marketplace matching finds compatible participants. An "organizer" (any participant) identifies the opportunity, assembles the cycle, and coordinates the first iteration. The organizer is compensated by cycle participants, not as a boss but as a service provider.

**Code mapping:**
```python
# contexts/synergy_cycle/application/
class CycleFormationService:
    def __init__(
        self,
        matching_service: MarketplaceMatchingService,
        contribution_evaluator: ContributionEvaluationService,
        deal_service: DealService,
    ):
        self._matching = matching_service
        self._evaluator = contribution_evaluator
        self._deals = deal_service
    
    def form_cycle(
        self,
        matching_result: MatchingResult,
        initiator_participant_id: str,
    ) -> SynergyCycle:
        # Verify we have complementary participants (closed loop)
        if not self._verify_closed_loop(matching_result):
            raise InvalidMatchingError("Not a closed cycle")
        
        # Create deals for each link in the cycle
        deals = []
        for link in matching_result.links:
            deal = self._deals.create_deal(
                obligor_id=link.from_participant,
                receiver_id=link.to_participant,
                subject=link.exchange.subject,
                amount=link.exchange.value,
            )
            deals.append(deal.deal_id)
        
        # Create the cycle
        cycle = SynergyCycle(
            cycle_id=uuid4(),
            name=f"Cycle-{datetime.now().strftime('%Y%m%d')}",
            participants=[CycleParticipant(
                participant_id=p.participant_id,
                role="specialist",
                contribution_type=p.specialty,
                contribution_value=p.estimated_value,
            ) for p in matching_result.participants],
            deals=deals,
            stage_discount=0.20,
            iteration_count=1,
            total_value_created=0,
            created_at=datetime.now(),
            status=CycleStatus.ACTIVE,
        )
        
        self._cycle_repo.save(cycle)
        return cycle
```

**Related terms:** [Marketplace](#marketplace), [Supply/Demand Matching](#supplydemand-matching), [Organizer](#organizer), [Deal](#deal)

---

### Organizer

**Russian:** Организатор  
**Definition:** A participant who provides the "end link" service of finding buyers and managing the cycle. The organizer is not a hierarchical boss — they are a service provider compensated by cycle participants.

**Context:** Any participant can be an organizer. The organizer identifies the cycle opportunity, assembles participants, coordinates the flow, and finds the final consumer. They are compensated from the cycle's value — typically the "end link" receives compensation for bringing the buyer.

**Code mapping:**
```python
# contexts/synergy_cycle/domain/
@dataclass
class Organizer:
    participant_id: str
    cycles_organized: list[str]
    compensation_earned: float
    specialty: str  # coordination, matching, logistics
    
    def calculate_compensation(
        self,
        cycle_value: float,
        compensation_rate: float = 0.10,
    ) -> float:
        """Organizer typically gets ~10% of cycle value."""
        return cycle_value * compensation_rate

@dataclass
class OrganizerCompensation:
    cycle_id: str
    organizer_id: str
    amount: float
    source: str  # "from_seller", "from_buyer", "from_cycle_pool"
    paid_at: datetime
```

**Related terms:** [Synergy Cycle](#synergy-cycle), [Cycle Formation](#cycle-formation), [Participant](#participant)

---

### 20% Stage Discount

**Russian:** 20% скидка на этап  
**Definition:** The empirical observation that each stage in a synergetic cycle achieves approximately 20% cost reduction compared to traditional supply chains. This discount compounds across stages.

**Context:** The 20% per stage discount is from the Almaty experiment. Each production stage (raw materials → processing → delivery) achieves ~20% savings. Over multiple stages, the total discount compounds — leading to 40-60% total reduction vs. traditional costs.

**Code mapping:**
```python
# contexts/synergy_cycle/domain/
class StageDiscount:
    DEFAULT_DISCOUNT = 0.20
    MIN_DISCOUNT = 0.15
    MAX_DISCOUNT = 0.25
    
    @classmethod
    def calculate_total_discount(cls, stages: int) -> float:
        """Total discount = (1 + d)^n - 1"""
        return (1 + cls.DEFAULT_DISCOUNT) ** stages - 1
    
    @classmethod
    def project_cost_reduction(
        cls,
        traditional_cost: float,
        stage_count: int,
    ) -> CostProjection:
        total_discount = cls.calculate_total_discount(stage_count)
        synergy_cost = traditional_cost * (1 - total_discount)
        
        return CostProjection(
            traditional=traditional_cost,
            synergy=synergy_cost,
            savings=traditional_cost - synergy_cost,
            savings_percentage=total_discount * 100,
            stage_count=stage_count,
        )

@dataclass
class CostProjection:
    traditional: float
    synergy: float
    savings: float
    savings_percentage: float
    stage_count: int
```

**Related terms:** [Synergy Cycle](#synergy-cycle), [Multiplicative Effect](#multiplicative-effect), [Production-Consumption Loop](#production-consumption-loop)

---

### Production-Consumption Loop

**Russian:** Кругооборот производства-потребления  
**Definition:** The full loop from production to consumption where value circulates back to the beginning. The loop connects producers, processors, logistics, and end consumers in a closed circuit.

**Context:** The production-consumption loop is the economic foundation of synergy cycles. Raw materials → processing → delivery → payment → back to raw materials for next cycle. The closure prevents value leakage and enables multiplicative growth.

**Code mapping:**
```python
# contexts/synergy_cycle/domain/
@dataclass
class ProductionConsumptionLoop:
    loop_id: str
    cycle_id: str
    stages: list[ProductionStage]
    start_participant_id: str
    end_participant_id: str
    
    @property
    def is_closed(self) -> bool:
        return self.start_participant_id == self.end_participant_id

@dataclass
class ProductionStage:
    stage_number: int
    participant_id: str
    role: str            # supplier, processor, logistics, retailer, consumer
    input_value: float
    output_value: float  # input * (1 + discount)
    discount_applied: float

# contexts/synergy_cycle/application/
class LoopTrackingService:
    def track_value_flow(self, loop: ProductionConsumptionLoop) -> ValueFlow:
        """Track how value flows through the loop."""
        cumulative = 0
        flows = []
        
        for stage in loop.stages:
            cumulative += stage.output_value - stage.input_value
            flows.append(StageFlow(
                stage=stage.stage_number,
                participant=stage.participant_id,
                input=stage.input_value,
                output=stage.output_value,
                cumulative_value=cumulative,
            ))
        
        return ValueFlow(
            loop_id=loop.loop_id,
            total_input=sum(s.input_value for s in loop.stages),
            total_output=sum(s.output_value for s in loop.stages),
            net_value=cumulative,
            stage_flows=flows,
        )
```

**Related terms:** [Closed Cycle](#closed-cycle), [Synergy Cycle](#synergy-cycle), [20% Stage Discount](#20-stage-discount)

---

### Collective Participant (in Cycle Context)

**Russian:** Коллективный участник (в контексте цикла)  
**Definition:** A group entity (collective participant) that participates in a synergy cycle as a single node. The collective has internal cycles among its members but presents as one participant to the outer cycle.

**Context:** A virtual corporation or collective participant can join an outer synergy cycle as a single entity. The inner structure (its own cycles and member relationships) is preserved, but the outer interaction treats it as one participant with one share.

**Code mapping:**
```python
# contexts/synergy_cycle/domain/
@dataclass
class CycleParticipantRepresentation:
    """How a collective participant appears in a cycle."""
    participant_id: str          # The collective's ID
    is_collective: bool = True
    member_count: int
    total_contribution_value: float
    
    def get_share_in_cycle(self, cycle: SynergyCycle) -> float:
        """Calculate share based on contribution."""
        return self.total_contribution_value / cycle.total_value_created

@dataclass
class NestedCycle:
    """Cycle inside a collective participant."""
    inner_cycle_id: str
    outer_cycle_id: str
    collective_id: str
    representation: CycleParticipantRepresentation
```

**Related terms:** [Virtual Corporation](#virtual-corporation), [Collective Participant](synergy_participant_identity.md#collective-participant), [Contribution Evaluation](synergy_contribution_evaluation.md)

---

## Cross-Context Boundary Notes

| Term | Used by Context | Relationship |
|------|-----------------|--------------|
| Synergy Cycle | [Transaction & Deal](synergy_transaction_deal.md), [Marketplace](synergy_marketplace.md), [Contribution Evaluation](synergy_contribution_evaluation.md) | Composed of deals; formed from matching; shares evaluated |
| Deal | [Transaction & Deal](synergy_transaction_deal.md) | The link between participants in a cycle |
| Virtual Corporation | [Contribution Evaluation](synergy_contribution_evaluation.md), [Marketplace](synergy_marketplace.md) | Receives share tokens; can participate in larger cycles |
| Participant | [Participant Identity](synergy_participant_identity.md) | Member of cycle |
| Matching Result | [Marketplace](synergy_marketplace.md) | Triggers cycle formation |
| Share | [Contribution Evaluation](synergy_contribution_evaluation.md) | Determines distribution of cycle value |
| NFT Contract | [NFT/Tokenomics](synergy_nft_tokenomics.md) | Can represent cycle participation |