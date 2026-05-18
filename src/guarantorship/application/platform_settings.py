"""GetPlatformSettingsUseCase / UpdatePlatformSettingsUseCase."""

from __future__ import annotations

from dataclasses import dataclass

from guarantorship.domain.platform_settings import PlatformSettings
from guarantorship.domain.ports import GuarantorshipUnitOfWork


class GetPlatformSettingsUseCase:
    def __init__(self, uow: GuarantorshipUnitOfWork) -> None:
        self._uow = uow

    def execute(self) -> PlatformSettings:
        with self._uow as uow:
            return uow.settings.get()


@dataclass
class UpdatePlatformSettingsCommand:
    required_guarantors_count: int | None = None
    guarantor_ward_limit: int | None = None
    escalation_levels: int | None = None


class UpdatePlatformSettingsUseCase:
    def __init__(self, uow: GuarantorshipUnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: UpdatePlatformSettingsCommand) -> PlatformSettings:
        with self._uow as uow:
            settings = uow.settings.get()

            if cmd.required_guarantors_count is not None:
                if cmd.required_guarantors_count < 1:
                    raise ValueError("required_guarantors_count must be >= 1")
                settings.required_guarantors_count = cmd.required_guarantors_count

            if cmd.guarantor_ward_limit is not None:
                if cmd.guarantor_ward_limit < 1:
                    raise ValueError("guarantor_ward_limit must be >= 1")
                settings.guarantor_ward_limit = cmd.guarantor_ward_limit

            if cmd.escalation_levels is not None:
                if cmd.escalation_levels < 0:
                    raise ValueError("escalation_levels must be >= 0")
                settings.escalation_levels = cmd.escalation_levels

            uow.settings.save(settings)
            uow.commit()
            return settings
