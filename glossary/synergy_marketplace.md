# Supply/Demand Matching

**Bounded Context:** Supply/Demand Matching  
**Domain:** Social Synergy (Социальная Синергия)  
**Status:** Supporting Subdomain

This context manages the marketplace where participants post what they offer (supply), what they need (demand), and what they can vouch for. The matching system finds chains of complementary needs, enabling synergy cycles to form.

---

### Storefront

**Russian:** Витрина спроса/предложения  
**Definition:** A participant's public profile showing their Offer, Need, and Can-Vouch capacity. The storefront is the primary interface for marketplace matching.

**Context:** Every participant has a storefront on the network. The storefront contains three fields: "Предлагаю" (I offer) — what goods/services they provide, "Требуется" (I need) — what they need, and "Могу поручиться" (I can vouch for) — their guarantor capacity. Storefronts are visible to all participants and form the basis of matching.

**Code mapping:**
```python
# contexts/marketplace/domain/
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

@dataclass
class Storefront:
    participant_id: str
    offer: str           # What they provide (goods/services)
    need: str           # What they require
    can_vouch: str      # Their vouching capacity
    categories: list[str]
    last_updated: datetime
    visibility: StorefrontVisibility
    
    def matches_need(self, need: str, category: str) -> bool:
        """Check if this storefront can fulfill a need."""
        return category in self.categories and need in self.offer
    
    def has_vouch_capacity(self) -> bool:
        """Check if can accept new wards as guarantor."""
        # Reference to participant identity context
        pass

class StorefrontVisibility:
    PUBLIC = "public"           # Visible to all
    NETWORK_ONLY = "network"   # Visible to network participants
    CONNECTED_ONLY = "connected"  # Only connected participants
    PRIVATE = "private"         # Only self

@dataclass
class StorefrontUpdate:
    storefront_id: str
    changed_fields: list[str]
    updated_at: datetime
    approved: bool
```

**Related terms:** [Offer](#offer), [Need](#need), [Can-Vouch](#can-vouch), [Category](#category), [Visual Navigator-Organizer](#visual-navigator-organizer)

---

### Offer

**Russian:** Предложение  
**Definition:** What a participant provides to the network — goods, services, skills, or resources. The offer is published in the participant's storefront and forms the supply side of the marketplace.

**Context:** An offer is a description of what a participant can provide. Offers are categorized for efficient matching. Examples: "carpentry services," "organic vegetables," "3D printing," "language tutoring." Offers can be generic or specific.

**Code mapping:**
```python
# contexts/marketplace/domain/
@dataclass
class Offer:
    offer_id: str
    participant_id: str
    title: str
    description: str
    category: str
    subcategory: Optional[str]
    availability: Availability
    pricing_model: PricingModel  # money, barter, equivalent, free
    
    def is_available(self) -> bool:
        return self.availability == Availability.ACTIVE
    
    def matches_search(self, query: str) -> float:
        """Relevance score for search query."""
        # Simple keyword matching, can be enhanced with embeddings
        pass

class Availability:
    ACTIVE = "active"
    BUSY = "busy"
    PAUSED = "paused"
    UNAVAILABLE = "unavailable"

class PricingModel:
    MONEY = "money"
    BARTER = "barter"          # Exchange for other goods/services
    EQUIVALENT = "equivalent"  # Value-equivalent exchange
    FREE = "free"              # Gift/favor
    MIXED = "mixed"            # Combination

@dataclass
class OfferSearchResult:
    offer: Offer
    relevance_score: float
    distance: Optional[int]  # Handshakes to reach
```

**Related terms:** [Need](#need), [Storefront](#storefront), [Category](#category), [Barter](#barter)

---

### Need

**Russian:** Требуется  
**Definition:** What a participant requires from the network — goods, services, skills, or resources they need. The need is published in the participant's storefront and forms the demand side of the marketplace.

**Context:** A need is a description of what a participant wants to receive. Like offers, needs are categorized for matching. The marketplace finds participants whose offers match others' needs, forming potential synergies.

**Code mapping:**
```python
# contexts/marketplace/domain/
@dataclass
class Need:
    need_id: str
    participant_id: str
    title: str
    description: str
    category: str
    subcategory: Optional[str]
    urgency: NeedUrgency
    budget_type: BudgetType
    budget_amount: Optional[float]
    
    def is_urgent(self) -> bool:
        return self.urgency == NeedUrgency.HIGH
    
    def get_matching_offers(self) -> list[OfferSearchResult]:
        """Find offers matching this need."""
        pass

class NeedUrgency:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class BudgetType:
    MONEY = "money"
    BARTER = "barter"
    EQUIVALENT = "equivalent"
    FLEXIBLE = "flexible"

@dataclass
class NeedSearchResult:
    need: Need
    relevance_score: float
    matching_offers: list[OfferSearchResult]
```

**Related terms:** [Offer](#offer), [Storefront](#storefront), [Category](#category), [Matching](#matching)

---

### Can-Vouch

**Russian:** Могу поручиться  
**Definition:** A participant's stated capacity to act as a guarantor for others. This is published in the storefront as part of the demand/supply profile.

**Context:** "Can-vouch" indicates a participant's willingness and capacity to take on guarantor responsibilities. It shows: how many more wards they can accept (up to 12), their specialty areas for vouching, and any terms (compensation expected, etc.). This connects marketplace to the guarantorship system.

**Code mapping:**
```python
# contexts/marketplace/domain/
@dataclass
class CanVouch:
    participant_id: str
    max_wards: int           # Up to 12, less current wards
    current_wards: int
    specialty_areas: list[str]  # Categories they can vouch for
    compensation_expected: Optional[str]  # Terms for guarantorship
    availability: str
    
    def get_available_capacity(self) -> int:
        return self.max_wards - self.current_wards
    
    def can_vouch_for(self, category: str) -> bool:
        """Check if can accept a new ward in this category."""
        return category in self.specialty_areas and self.get_available_capacity() > 0
    
    def to_storefront_field(self) -> str:
        """Convert to storefront 'can_vouch' string."""
        cap = self.get_available_capacity()
        if cap <= 0:
            return "Not accepting new wards"
        return f"Can vouch for {cap} more. Specialties: {', '.join(self.specialty_areas)}"
```

**Related terms:** [Guarantor](synergy_participant_identity.md#guarantor), [Max-12-Wards Rule](synergy_participant_identity.md#max-12-wards-rule), [Storefront](#storefront)

---

### Matching

**Russian:** Сопоставление / Поиск  
**Definition:** The process of finding compatible participants: offers matching needs, and chains of complementary exchanges that form potential synergy cycles.

**Context:** Matching operates at multiple levels: (1) Direct matching — one offer matches one need, (2) Chain matching — multiple participants with complementary needs form a chain (A→B→C), (3) Cycle matching — closed loops where output returns to start. The 4th handshake principle ensures matching can reach any participant.

**Code mapping:**
```python
# contexts/marketplace/domain/
@dataclass
class MatchingResult:
    match_id: str
    match_type: MatchType  # DIRECT, CHAIN, CYCLE
    participants: list[str]
    links: list[MatchLink]  # Who matches with whom
    total_value: float
    estimated_savings: float  # From synergy effect
    created_at: datetime
    
    def is_cycle(self) -> bool:
        return self.match_type == MatchType.CYCLE
    
    def get_organizer_candidates(self) -> list[str]:
        """Participants who could organize this match."""
        return self.participants  # All could potentially organize

class MatchType:
    DIRECT = "direct"        # A -> B
    CHAIN = "chain"          # A -> B -> C
    CYCLE = "cycle"          # A -> B -> C -> A

@dataclass
class MatchLink:
    from_participant_id: str
    to_participant_id: str
    from_offer_id: str
    to_need_id: str
    exchange_value: float

# contexts/marketplace/application/
class MatchingService:
    def match_direct(self, need_id: str) -> list[MatchingResult]:
        """Find direct offer matches for a need."""
        need = self._needs.get(need_id)
        offers = self._offers.search(
            category=need.category,
            keywords=need.title,
        )
        
        results = []
        for offer in offers:
            if self._verify_compatibility(offer, need):
                results.append(self._create_direct_match(offer, need))
        
        return results
    
    def match_cycle(self, start_need_id: str) -> list[MatchingResult]:
        """Find closed cycle matches starting from a need."""
        # Find chains that loop back to start
        # This is the key for synergy cycle formation
        pass
```

**Related terms:** [4th Handshake Principle](#4th-handshake-principle), [Synergy Cycle](synergy_cycle.md), [Supply/Demand Chain](#supplydemand-chain)

---

### Supply/Demand Chain

**Russian:** Цепочка спроса/предложения  
**Definition:** A sequence of participants where each provides what the next needs. The chain can be open (A→B→C) or closed (A→B→C→A). Closed chains become synergy cycles.

**Context:** The supply/demand chain is the matching output. Chains are the building blocks of synergy cycles. The "global search system" for products, services, technologies, and specialists operates by finding these chains.

**Code mapping:**
```python
# contexts/marketplace/domain/
@dataclass
class SupplyDemandChain:
    chain_id: str
    participants: list[ChainNode]
    is_closed: bool
    total_value: float
    chain_discount: float     # Combined discount from all stages
    
    def get_link_at(self, position: int) -> ChainLink:
        return self.links[position]
    
    def to_synergy_cycle(self) -> Optional[SynergyCycle]:
        """If closed, this chain can form a synergy cycle."""
        if self.is_closed:
            return CycleFormationService().form_cycle_from_chain(self)
        return None

@dataclass
class ChainNode:
    participant_id: str
    offer: Offer
    need: Need
    
@dataclass
class ChainLink:
    from_node: ChainNode
    to_node: ChainNode
    matched_need_id: str
    matched_offer_id: str
    value: float

# contexts/marketplace/application/
class ChainSearchService:
    def search_chain(
        self,
        starting_need: Need,
        max_length: int = 5,
    ) -> list[SupplyDemandChain]:
        """Find chains starting from a need, up to max_length."""
        # BFS through participants' needs/offers
        pass
    
    def search_closed_chain(
        self,
        starting_need: Need,
    ) -> list[SupplyDemandChain]:
        """Find closed chains (cycles) starting from a need."""
        chains = self.search_chain(starting_need, max_length=5)
        return [c for c in chains if c.is_closed]
```

**Related terms:** [Matching](#matching), [Synergy Cycle](synergy_cycle.md), [Closed Cycle](synergy_cycle.md#closed-cycle)

---

### 4th Handshake Principle (Marketplace Context)

**Russian:** Принцип 4-го рукопожатия (в контексте рынка)  
**Definition:** The marketplace principle that any needed person, product, service, or technology is reachable within 2-4 links in the participant network. Country: 4-5 hops. Global: 9-12 hops.

**Context:** The 4th handshake principle enables the "global search system." The marketplace doesn't need every participant to directly know everyone — it finds paths through the guaranty chain. This makes the marketplace scalable to any size.

**Code mapping:**
```python
# contexts/marketplace/application/
class GlobalSearchService:
    def __init__(
        self,
        guaranty_chain_service: GuarantyChainService,
        storefront_repo: StorefrontRepository,
    ):
        self._chains = guaranty_chain_service
        self._storefronts = storefront_repo
    
    def find_within_4_handshakes(
        self,
        need: Need,
        requester_id: str,
    ) -> list[MatchingResult]:
        """Find all matches within 4-handshake distance."""
        # Get all storefronts
        all_storefronts = self._storefronts.get_all()
        
        matches = []
        for storefront in all_storefronts:
            if storefront.participant_id == requester_id:
                continue
            
            # Check if within 4 handshakes
            distance = self._chains.calculate_distance(requester_id, storefront.participant_id)
            if distance is None or distance > 4:
                continue
            
            # Check if offer matches need
            if self._compatibility_check(storefront.offer, need):
                matches.append(MatchingResult(
                    participant_id=storefront.participant_id,
                    distance=distance,
                    offer=storefront.offer,
                ))
        
        return matches
    
    def find_global(
        self,
        category: str,
        keywords: list[str],
    ) -> list[GlobalSearchResult]:
        """Search entire network for category/keywords."""
        # Same as above but no distance limit
        pass
```

**Related terms:** [Guaranty Chain](synergy_participant_identity.md#guaranty-chain), [Matching](#matching), [Storefront](#storefront)

---

### Share Token

**Russian:** Доля-токен  
**Definition:** A token representing fractional ownership of expensive items (bicycle, 3D printer, generator) shared among multiple participants. Share tokens enable collective ownership and usage tracking.

**Context:** Share tokens solve the problem of expensive items that would be underutilized by one owner. Multiple participants buy shares in an item, getting ownership tokens. Usage is tracked, and tokens are transferable within the network.

**Code mapping:**
```python
# contexts/marketplace/domain/
@dataclass
class ShareToken:
    token_id: str
    item_id: str
    total_shares: int
    owner_participant_ids: list[str]
    share_distribution: dict[str, int]  # participant -> shares
    usage_schedule: list[UsageSlot]
    created_at: datetime
    transferable: bool

@dataclass
class SharedItem:
    item_id: str
    name: str
    category: str
    total_value: float
    share_count: int
    price_per_share: float
    
    def get_share_token(self) -> ShareToken:
        """Mint share tokens for this item."""
        shares = {}
        for owner_id in self.owners:
            shares[owner_id] = self.share_count // len(self.owners)
        
        return ShareToken(
            token_id=uuid4(),
            item_id=self.item_id,
            total_shares=self.share_count,
            owner_participant_ids=self.owners,
            share_distribution=shares,
            usage_schedule=[],
            created_at=datetime.now(),
            transferable=True,
        )

@dataclass
class UsageSlot:
    participant_id: str
    start_time: datetime
    end_time: datetime
    item_id: str
```

**Related terms:** [Storefront](#storefront), [NFT-Contract](synergy_transaction_deal.md#nft-contract), [Collective Participant](synergy_participant_identity.md#collective-participant)

---

### Tool Library

**Russian:** Библиотека инструментов  
**Definition:** A shared repository of tools, equipment, and resources that participants can borrow or use. Tool libraries leverage share tokens and the guarantor system to enable trust-based sharing.

**Context:** Tool libraries are a common use case in Synergy4all. A group of participants pool expensive tools (lawnmowers, power tools, kitchen equipment) and share access. The deposit system covers potential damage. Usage is tracked via the system.

**Code mapping:**
```python
# contexts/marketplace/domain/
@dataclass
class ToolLibrary:
    library_id: str
    name: str
    organizer_id: str
    tools: list[LibraryTool]
    member_participant_ids: list[str]
    deposit_per_tool: float  # Deposit to borrow
    
    def get_available_tools(self) -> list[LibraryTool]:
        return [t for t in self.tools if t.is_available]
    
    def borrow_tool(self, tool_id: str, participant_id: str, duration: timedelta) -> BorrowRecord:
        """Borrow a tool, requires deposit."""
        pass

@dataclass
class LibraryTool:
    tool_id: str
    name: str
    category: str
    value: float
    deposit_required: float
    available: bool
    
    def borrow(self, borrower_id: str) -> BorrowRecord:
        """Create borrow record with deposit hold."""
        pass
    
    def return_tool(self, record_id: str) -> bool:
        """Verify return, release deposit hold."""
        pass

@dataclass
class BorrowRecord:
    record_id: str
    tool_id: str
    borrower_id: str
    borrowed_at: datetime
    due_at: datetime
    returned_at: Optional[datetime]
    deposit_held: float
    condition_on_return: Optional[str]
```

**Related terms:** [Share Token](#share-token), [Guarantee Deposit](synergy_deposit_capacity.md#guarantee-deposit), [Storefront](#storefront)

---

### Category

**Russian:** Категория  
**Definition:** A classification system for offers and needs that enables efficient matching. Categories organize the marketplace and help participants find relevant opportunities.

**Context:** Categories are hierarchical: broad categories (Goods, Services) → subcategories (Electronics, Construction) → specific types. The matching system uses categories to filter and rank results. Participants assign categories to their offers and needs.

**Code mapping:**
```python
# contexts/marketplace/domain/
@dataclass
class Category:
    category_id: str
    name: str
    parent_id: Optional[str]
    level: int
    
    def get_children(self) -> list["Category"]:
        return self._repo.get_children(self.category_id)
    
    def get_path(self) -> list[str]:
        """Full path: Services > Construction > Carpentry."""
        path = [self.name]
        if self.parent_id:
            parent = self._repo.get(self.parent_id)
            path = parent.get_path() + path
        return path

class CategoryRegistry:
    """Standard categories for Synergy4all marketplace."""
    
    GOODS = "goods"
    SERVICES = "services"
    SKILLS = "skills"
    RESOURCES = "resources"
    
    # Subcategories
    GOODS_ELECTRONICS = "goods/electronics"
    GOODS_FOOD = "goods/food"
    SERVICES_CONSTRUCTION = "services/construction"
    SERVICES_EDUCATION = "services/education"
    SKILLS_CRAFTS = "skills/crafts"
    RESOURCES_TOOLS = "resources/tools"
    RESOURCES_SPACE = "resources/space"

# contexts/marketplace/application/
class CategoryService:
    def normalize(self, category_input: str) -> Category:
        """Convert user input to standard category."""
        # Match against known categories, fuzzy matching
        pass
    
    def get_suggestions(self, partial: str) -> list[Category]:
        """Suggest categories as user types."""
        pass
```

**Related terms:** [Offer](#offer), [Need](#need), [Storefront](#storefront), [Matching](#matching)

---

### Visual Navigator-Organizer

**Russian:** Визуальный навигатор-органайзер  
**Definition:** A user interface tool (originally for social networks) that helps form real operational groups and communities — not just chat groups. It visualizes the network and enables drag-and-drop formation of synergy cycles.

**Context:** The Visual Navigator-Organizer is the user-facing tool for marketplace interaction. It shows participant networks visually, enables finding matches, and helps organize groups into complete synergy cycles with guarantor systems.

**Code mapping:**
```python
# contexts/marketplace/infrastructure/
from typing import Protocol

class NavigatorOrganizerUI(Protocol):
    """Port: visual navigator interface."""
    def render_network(self, center_participant_id: str, depth: int) -> NetworkGraph: ...
    def show_matches(self, need_id: str) -> list[MatchCard]: ...
    def form_group(self, participant_ids: list[str]) -> GroupFormation: ...

@dataclass
class NetworkGraph:
    center_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]  # Connections, including guaranty
    
    def render_html(self) -> str: ...
    def export_json(self) -> dict: ...

@dataclass
class GraphNode:
    participant_id: str
    position: tuple[float, float]
    size: float
    color: str  # Based on status, category

@dataclass
class GraphEdge:
    from_id: str
    to_id: str
    edge_type: str  # guarantor, trade, cycle_link

@dataclass
class MatchCard:
    """Card shown for each matching participant."""
    participant_id: str
    offer_summary: str
    need_summary: str
    distance: int  # Handshakes
    compatibility_score: float

@dataclass
class GroupFormation:
    group_id: str
    participants: list[str]
    purpose: str
    cycle_potential: bool  # Can form closed cycle
```

**Related terms:** [Storefront](#storefront), [Matching](#matching), [Synergy Cycle](synergy_cycle.md), [Guaranty Chain](synergy_participant_identity.md#guaranty-chain)

---

## Cross-Context Boundary Notes

| Term | Used by Context | Relationship |
|------|-----------------|--------------|
| Storefront | [Participant Identity](synergy_participant_identity.md) | Participant publishes offer/need/vouch |
| Offer/Need | [Synergy Cycle](synergy_cycle.md) | Triggers cycle formation |
| Matching Result | [Synergy Cycle](synergy_cycle.md) | Input to cycle formation |
| Can-Vouch | [Participant Identity](synergy_participant_identity.md) | Connects to guarantorship |
| Share Token | [NFT/Tokenomics](synergy_nft_tokenomics.md) | Represented as NFT |
| Category | [Transaction & Deal](synergy_transaction_deal.md) | Used in deal templates |
| 4th Handshake | [Participant Identity](synergy_participant_identity.md) | Network reach for matching |