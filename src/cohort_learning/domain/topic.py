"""Topic entity — a discrete unit of knowledge within a module."""


class Topic:
    """A single concept or skill within a module progression."""

    def __init__(
        self,
        topic_id: str,
        title: str,
        position: int,
        description: str = "",
    ) -> None:
        if not title.strip():
            raise ValueError("Topic title must not be empty")
        if position < 0:
            raise ValueError("Topic position must be non-negative")

        self.topic_id = topic_id
        self.title = title
        self.position = position
        self.description = description
