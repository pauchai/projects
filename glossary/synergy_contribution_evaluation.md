# Contribution Evaluation (F/S/E/A)

**Bounded Context:** Contribution Evaluation  
**Domain:** Social Synergy (Социальная Синергия)  
**Status:** Supporting Subdomain

This context manages the fractal method for evaluating proportional contributions (долевой вклад) in collective endeavors. The F/S/E/A methodology decomposes contributions into four dimensions and evaluates them across temporal stages to determine fair shares.

---

### Object of Evaluation

**Russian:** Объект оценки  
**Definition:** The thing being valued — an enterprise, project, innovation, virtual corporation, or any collectively-owned entity whose ownership/share must be distributed among participants.

**Context:** The object of evaluation is the root aggregate for contribution assessment. It can be: a synergy cycle's output, a virtual corporation's collective product, a shared asset, or any joint endeavor. The evaluation produces share percentages for each participant.

**Code mapping:**
```python
# contexts/contribution_evaluation/domain/
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

@dataclass
class ObjectOfEvaluation:
    object_id: str
    object_type: ObjectType
    name: str
    description: str
    evaluation_status: EvaluationStatus
    created_at: datetime
    evaluation_completed_at: Optional[datetime]
    
    def start_evaluation(self) -> EvaluationProcess:
        """Begin the evaluation process."""
        return EvaluationProcess(
            process_id=uuid4(),
            object_id=self.object_id,
            status="in_progress",
            stages=[],
        )

class ObjectType:
    SYNERGY_CYCLE = "synergy_cycle"
    VIRTUAL_CORPORATION = "virtual_corporation"
    SHARED_ASSET = "shared_asset"
    PROJECT = "project"
    INNOVATION = "innovation"

class EvaluationStatus:
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    CONSENSUS_REACHED = "consensus_reached"
    DISPUTED = "disputed"
    FINALIZED = "finalized"

@dataclass
class EvaluationProcess:
    process_id: str
    object_id: str
    status: str
    stages: list[EvaluationStage]
    current_stage_index: int = 0
    
    def get_current_stage(self) -> EvaluationStage:
        return self.stages[self.current_stage_index]
```

**Related terms:** [Participant](#participant), [Synergy Cycle](synergy_cycle.md), [Virtual Corporation](synergy_cycle.md#virtual-corporation), [Share](#share)

---

### Information Contribution (F)

**Russian:** Информационный вклад (F)  
**Definition:** The contribution dimension covering ideas, know-how, blueprints, research, and other intellectual/informational inputs. F represents the "information" aspect of contribution.

**Context:** Information contribution includes: original ideas, technical knowledge, R&D, patents, designs, recipes, methods, and any intellectual property contributed to the collective endeavor. F is one of four dimensions in the F/S/E/A framework.

**Code mapping:**
```python
# contexts/contribution_evaluation/domain/
@dataclass
class InformationContribution:
    contribution_id: str
    participant_id: str
    object_id: str
    contribution_type: str  # idea, knowhow, blueprint, research, patent
    
    description: str
    value_estimate: float  # Participant's own estimate (percentage)
    evidence: list[str]    # URLs, documents, references
    
    def to_component(self) -> ContributionComponent:
        return ContributionComponent(
            component_type="F",
            participant_id=self.participant_id,
            description=self.description,
            participant_estimate=self.value_estimate,
        )

class InformationContributionTypes:
    IDEA = "idea"
    KNOWHOW = "knowhow"
    BLUEPRINT = "blueprint"
    RESEARCH = "research"
    PATENT = "patent"
    METHOD = "method"
    TRADE_SECRET = "trade_secret"

@dataclass
class FComponentSummary:
    """Aggregate F contributions for an object."""
    total_f_value: float
    contributions: list[InformationContribution]
    consensus_weight: float  # Agreed weight of F in total
```

**Related terms:** [Material Contribution (S)](#material-contribution-s), [Labor Contribution (E)](#labor-contribution-e), [Intangible Contribution (A)](#intangible-contribution-a), [Object of Evaluation](#object-of-evaluation)

---

### Material Contribution (S)

**Russian:** Материальный вклад (S)  
**Definition:** The contribution dimension covering money, physical assets, tangible property, equipment, and other material resources. S represents the "material/financial" aspect of contribution.

**Context:** Material contribution includes: capital investments, equipment, raw materials, workspace, vehicles, and any physical assets contributed to the collective endeavor. S is one of four dimensions in the F/S/E/A framework.

**Code mapping:**
```python
# contexts/contribution_evaluation/domain/
@dataclass
class MaterialContribution:
    contribution_id: str
    participant_id: str
    object_id: str
    contribution_type: str  # capital, equipment, materials, workspace
    
    description: str
    market_value: float     # Current market value
    participant_estimate: float  # Participant's estimate (percentage)
    evidence: list[str]     # Invoices, asset registry
    
    def to_component(self) -> ContributionComponent:
        return ContributionComponent(
            component_type="S",
            participant_id=self.participant_id,
            description=self.description,
            participant_estimate=self.participant_estimate,
            objective_value=self.market_value,
        )

class MaterialContributionTypes:
    CAPITAL = "capital"
    EQUIPMENT = "equipment"
    MATERIALS = "materials"
    WORKSPACE = "workspace"
    VEHICLE = "vehicle"
    REAL_ESTATE = "real_estate"

@dataclass
class SComponentSummary:
    """Aggregate S contributions for an object."""
    total_s_value: float
    contributions: list[MaterialContribution]
    consensus_weight: float  # Agreed weight of S in total
```

**Related terms:** [Information Contribution (F)](#information-contribution-f), [Labor Contribution (E)](#labor-contribution-e), [Intangible Contribution (A)](#intangible-contribution-a), [Object of Evaluation](#object-of-evaluation)

---

### Labor Contribution (E)

**Russian:** Трудовой вклад (E)  
**Definition:** The contribution dimension covering work, time, effort, and services performed. E represents the "labor/effort" aspect of contribution.

**Context:** Labor contribution includes: physical work, service provision, management, coordination, and any time/effort spent on the collective endeavor. E is one of four dimensions in the F/S/E/A framework.

**Code mapping:**
```python
# contexts/contribution_evaluation/domain/
@dataclass
class LaborContribution:
    contribution_id: str
    participant_id: str
    object_id: str
    contribution_type: str  # physical_work, service, management, coordination
    
    description: str
    hours_contributed: float
    hourly_rate_estimate: float  # Participant's valuation
    participant_estimate: float  # Participant's overall estimate (%)
    evidence: list[str]  # Timesheets, deliverables
    
    def calculate_value(self) -> float:
        return self.hours_contributed * self.hourly_rate_estimate
    
    def to_component(self) -> ContributionComponent:
        return ContributionComponent(
            component_type="E",
            participant_id=self.participant_id,
            description=self.description,
            participant_estimate=self.participant_estimate,
            objective_value=self.calculate_value(),
        )

class LaborContributionTypes:
    PHYSICAL_WORK = "physical_work"
    SERVICE = "service"
    MANAGEMENT = "management"
    COORDINATION = "coordination"
    CONSULTING = "consulting"

@dataclass
class EComponentSummary:
    """Aggregate E contributions for an object."""
    total_e_value: float
    total_hours: float
    contributions: list[LaborContribution]
    consensus_weight: float
```

**Related terms:** [Information Contribution (F)](#information-contribution-f), [Material Contribution (S)](#material-contribution-s), [Intangible Contribution (A)](#intangible-contribution-a), [Object of Evaluation](#object-of-evaluation)

---

### Intangible Contribution (A)

**Russian:** Опосредованный вклад (A)  
**Definition:** The contribution dimension covering intangible assets: initiative, inspiration, reputation, image, connections, "good name," guarantees, status, and informal relationships. A represents the "intangible/indirect" aspect of contribution.

**Context:** Intangible contribution is the most subjective dimension. It includes: reputation ("good name"), network connections, initiative in starting the project, inspiration/motivation of others, guarantor reputation (from guarantorship system), and informal influence. A is one of four dimensions in the F/S/E/A framework.

**Code mapping:**
```python
# contexts/contribution_evaluation/domain/
@dataclass
class IntangibleContribution:
    contribution_id: str
    participant_id: str
    object_id: str
    contribution_type: str  # reputation, connections, initiative, inspiration
    
    description: str
    participant_estimate: float  # Participant's estimate (%)
    
    def to_component(self) -> ContributionComponent:
        return ContributionComponent(
            component_type="A",
            participant_id=self.participant_id,
            description=self.description,
            participant_estimate=self.participant_estimate,
        )

class IntangibleContributionTypes:
    REPUTATION = "reputation"        # "Good name"
    CONNECTIONS = "connections"       # Network/relationships
    INITIATIVE = "initiative"          # Started the project
    INSPIRATION = "inspiration"       # Motivated others
    GUARANTOR_REPUTATION = "guarantor_rep"  # From guarantorship
    STATUS = "status"                 # Social standing
    INFORMAL_INFLUENCE = "influence"  # Informal authority

@dataclass
class AComponentSummary:
    """Aggregate A contributions for an object."""
    contributions: list[IntangibleContribution]
    consensus_weight: float
```

**Related terms:** [Information Contribution (F)](#information-contribution-f), [Material Contribution (S)](#material-contribution-s), [Labor Contribution (E)](#labor-contribution-e), [Guarantor](synergy_participant_identity.md#guarantor), [Deposit Status Level](synergy_deposit_capacity.md#deposit-status-level)

---

### Temporal Stage

**Russian:** Этап (прошлое/настоящее/будущее)  
**Definition:** The time dimension of contribution evaluation. The history of the object is divided into three stages: Past (1), Present (2), and Future (3), each with different relative significance.

**Context:** The temporal stage reflects that contributions have different weights based on when they occurred: (1) Past = priority/legacy — foundational contributions that made the project possible, (2) Present = current contribution — ongoing work and inputs, (3) Future = obligations/commitments — planned contributions and commitments.

**Code mapping:**
```python
# contexts/contribution_evaluation/domain/
class TemporalStage:
    PAST = 1
    PRESENT = 2
    FUTURE = 3
    
    @classmethod
    def get_default_weights(cls) -> dict[int, float]:
        """Default relative significance by stage."""
        return {
            cls.PAST: 0.30,     # Legacy/priority
            cls.PRESENT: 0.50,  # Current contribution
            cls.FUTURE: 0.20,   # Obligations/commitments
        }
    
    @classmethod
    def get_name(cls, stage: int) -> str:
        names = {cls.PAST: "Past", cls.PRESENT: "Present", cls.FUTURE: "Future"}
        return names.get(stage, "Unknown")

@dataclass
class StageWeight:
    stage: int
    weight: float
    determined_by: list[str]  # Participant IDs who agreed

@dataclass
class TemporalEvaluation:
    object_id: str
    stage_weights: dict[int, float]  # Stage -> weight
    determined_at: datetime
    determined_by: list[str]
    
    def get_weight(self, stage: int) -> float:
        return self.stage_weights.get(stage, 0.0)
```

**Related terms:** [Object of Evaluation](#object-of-evaluation), [Evaluation Table](#evaluation-table)

---

### Self-Similarity Principle

**Russian:** Принцип самоподобия  
**Definition:** The recursive decomposition rule where disputed components can be subdivided following the same F/S/E/A structure until disagreements become negligible.

**Context:** If parties cannot agree on a component's value (e.g., what "reputation" is worth), that component is recursively subdivided into sub-components following the same four-dimensional structure (F, S, E, A). The process repeats until the impact on the final share is negligible.

**Code mapping:**
```python
# contexts/contribution_evaluation/domain/
class SelfSimilarityDecomposition:
    @staticmethod
    def decompose(
        component: str,
        current_value: float,
        threshold: float,
    ) -> list[SubComponent]:
        """Decompose a component until below threshold impact."""
        if current_value * 0.10 <= threshold:  # If impact < threshold, stop
            return [SubComponent(
                component_id=uuid4(),
                parent_component=component,
                f_value=current_value * 0.25,
                s_value=current_value * 0.25,
                e_value=current_value * 0.25,
                a_value=current_value * 0.25,
            )]
        
        # Otherwise decompose
        return [
            SelfSimilarityDecomposition.decompose(
                f"{component}_F", current_value * 0.25, threshold
            ),
            SelfSimilarityDecomposition.decompose(
                f"{component}_S", current_value * 0.25, threshold
            ),
            SelfSimilarityDecomposition.decompose(
                f"{component}_E", current_value * 0.25, threshold
            ),
            SelfSimilarityDecomposition.decompose(
                f"{component}_A", current_value * 0.25, threshold
            ),
        ]

@dataclass
class SubComponent:
    component_id: str
    parent_component: str
    f_value: float
    s_value: float
    e_value: float
    a_value: float
```

**Related terms:** [Evaluation Table](#evaluation-table), [Consensus](#consensus)

---

### Evaluation Table

**Russian:** Таблица оценки  
**Definition:** The matrix of participants × components × stages used to calculate proportional shares. The table is filled with percentage estimates and aggregated via weighted summation.

**Context:** The evaluation table is the primary artifact of the contribution evaluation process. It has dimensions: (1) Participants (rows), (2) Components F/S/E/A (columns), (3) Temporal stages (depth). Each cell contains a percentage estimate agreed by participants.

**Code mapping:**
```python
# contexts/contribution_evaluation/domain/
@dataclass
class EvaluationTable:
    table_id: str
    object_id: str
    stage_weights: dict[int, float]
    component_weights: dict[str, float]  # F, S, E, A weights
    
    # Data structure: participant -> component -> stage -> percentage
    estimates: dict[str, dict[str, dict[int, float]]]
    
    def add_estimate(
        self,
        participant_id: str,
        component: str,
        stage: int,
        percentage: float,
    ) -> None:
        if participant_id not in self.estimates:
            self.estimates[participant_id] = {}
        if component not in self.estimates[participant_id]:
            self.estimates[participant_id][component] = {}
        self.estimates[participant_id][component][stage] = percentage
    
    def calculate_share(self, participant_id: str) -> float:
        """Calculate total percentage share for a participant."""
        total = 0.0
        
        for component, stage_weights in self.component_weights.items():
            for stage, stage_weight in self.stage_weights.items():
                percentage = self.estimates.get(participant_id, {}) \
                    .get(component, {}) \
                    .get(stage, 0.0)
                total += percentage * stage_weight * stage_weights
        
        return total
    
    def calculate_all_shares(self) -> dict[str, float]:
        """Calculate shares for all participants."""
        return {
            pid: self.calculate_share(pid)
            for pid in self.estimates.keys()
        }

@dataclass
class EvaluationResult:
    object_id: str
    shares: dict[str, float]  # participant_id -> percentage
    evaluated_at: datetime
    consensus_reached: bool
    disputed_components: list[str]
```

**Related terms:** [Object of Evaluation](#object-of-evaluation), [Temporal Stage](#temporal-stage), [F/S/E/A Components](#contribution-components)

---

### Consensus

**Russian:** Согласие сторон / Соглашение сторон  
**Definition:** The requirement that all evaluations are by mutual agreement of the parties. No external authority sets values — participants negotiate and agree on contributions.

**Context:** Contribution evaluation is not determined by external appraisers or algorithms. All participants in the object of evaluation must agree on the component weights, stage weights, and individual estimates. Disagreements trigger the recursive subdivision process.

**Code mapping:**
```python
# contexts/contribution_evaluation/application/
class ConsensusService:
    def check_consensus(
        self,
        table: EvaluationTable,
        required_participants: list[str],
        threshold: float = 0.05,  # 5% tolerance
    ) -> ConsensusResult:
        """Check if all required participants have agreed."""
        agreed = []
        disputed = []
        
        for participant_id in required_participants:
            if participant_id in table.estimates:
                # Check if estimate is final (not draft)
                if self._is_finalized(table.estimates[participant_id]):
                    agreed.append(participant_id)
                else:
                    disputed.append(participant_id)
            else:
                disputed.append(participant_id)
        
        return ConsensusResult(
            consensus_reached=len(disputed) == 0,
            agreed_participants=agreed,
            disputed_participants=disputed,
        )
    
    def resolve_dispute(
        self,
        table: EvaluationTable,
        disputed_component: str,
    ) -> SubDivisionResult:
        """If consensus not reached, trigger recursive subdivision."""
        current_value = self._get_component_total(table, disputed_component)
        threshold = current_value * 0.05  # 5% of component value
        
        subcomponents = SelfSimilarityDecomposition.decompose(
            disputed_component, current_value, threshold
        )
        
        return SubDivisionResult(
            original_component=disputed_component,
            subcomponents=subcomponents,
            new_table=self._create_subdivided_table(table, subcomponents),
        )

@dataclass
class ConsensusResult:
    consensus_reached: bool
    agreed_participants: list[str]
    disputed_participants: list[str]
```

**Related terms:** [Evaluation Table](#evaluation-table), [Self-Similarity Principle](#self-similarity-principle), [Share](#share)

---

### Share

**Russian:** Доля  
**Definition:** The final output of contribution evaluation — a percentage ownership share assigned to each participant. Shares are derived from the evaluation table and represent proportional entitlement to the object.

**Context:** Shares are calculated from the evaluation table. Once consensus is reached, each participant receives a share percentage. Shares can be converted to any single dimension (e.g., monetary equivalent via the S component). Share tokens (for shared assets) are issued based on these shares.

**Code mapping:**
```python
# contexts/contribution_evaluation/domain/
@dataclass
class Share:
    share_id: str
    object_id: str
    participant_id: str
    percentage: float
    
    def convert_to_component_value(
        self,
        object_total_value: float,
        component_type: str,
    ) -> float:
        """Convert share to specific component value."""
        return object_total_value * (self.percentage / 100.0)
    
    def to_share_token(
        self,
        token_type: str,
        blockchain_id: Optional[str] = None,
    ) -> "ShareToken":
        """Mint a share token if the object is tokenizable."""
        return ShareToken(
            token_id=uuid4(),
            object_id=self.object_id,
            owner_id=self.participant_id,
            share_percentage=self.percentage,
            token_type=token_type,
            blockchain_id=blockchain_id,
        )

@dataclass
class ShareDistribution:
    object_id: str
    shares: list[Share]
    total_percentage: float  # Should sum to 100%
    finalized_at: datetime
    
    def get_share_for(self, participant_id: str) -> Optional[Share]:
        for share in self.shares:
            if share.participant_id == participant_id:
                return share
        return None
    
    def validate(self) -> bool:
        """Verify shares sum to 100%."""
        return abs(self.total_percentage - 100.0) < 0.01
```

**Related terms:** [Object of Evaluation](#object-of-evaluation), [Evaluation Table](#evaluation-table), [Share Token](synergy_marketplace.md#share-token), [Virtual Corporation](synergy_cycle.md#virtual-corporation)

---

## Cross-Context Boundary Notes

| Term | Used by Context | Relationship |
|------|-----------------|--------------|
| Object of Evaluation | [Synergy Cycle](synergy_cycle.md), [Marketplace](synergy_marketplace.md) | What is being valued in cycles/Virtual Corporations |
| Share | [Synergy Cycle](synergy_cycle.md), [NFT/Tokenomics](synergy_nft_tokenomics.md) | Output of evaluation; can be tokenized |
| F/S/E/A Components | [Deposit & Capacity](synergy_deposit_capacity.md), [Participant Identity](synergy_participant_identity.md) | A-component includes guarantor reputation, deposit status |
| Share Token | [Marketplace](synergy_marketplace.md) | Share represented as NFT token |
| Consensus | [Dispute Resolution](synergy_dispute_resolution.md) | Disagreements escalate to dispute resolution |
| Virtual Corporation | [Synergy Cycle](synergy_cycle.md) | Common object for evaluation |