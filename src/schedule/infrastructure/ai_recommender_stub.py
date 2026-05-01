"""AI recommender stub for the Schedule bounded context.

In the first phase this stub returns curators whose skills contain keywords
from the request text (case-insensitive). When an LLM API is integrated,
this adapter will be replaced without touching the domain or application layers.
"""

from schedule.domain.curator import Curator


class KeywordAiRecommenderStub:
    """Driven adapter: naive keyword-matching recommender.

    Scores each curator by counting how many of their skills appear
    in the request text. Curators with higher scores are ranked first.
    Curators with score 0 are still included (last in the list) so the
    coordinator always has options.
    """

    def recommend(self, request_text: str, curators: list[Curator]) -> list[str]:
        text_lower = request_text.lower()

        def score(curator: Curator) -> int:
            return sum(
                1 for skill in curator.skills if skill.lower() in text_lower
            )

        ranked = sorted(curators, key=score, reverse=True)
        return [c.curator_id for c in ranked]
