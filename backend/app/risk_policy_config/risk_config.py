"""Risk engine configuration — configurable weights, thresholds, and scoring parameters.

All risk-assessment parameters are defined here as dataclasses.  The defaults
documented below are sensible starting values; every numeric field can be
overridden via a YAML file or (in Phase 5+) through the admin API.

Version history is tracked so that historical risk assessments remain
reproducible even after configuration changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

# ── Version ──────────────────────────────────────────────────────────────────
RISK_ENGINE_VERSION = "1.0.0"
RISK_CONFIG_VERSION = "1.0.0"


# ── Action types ─────────────────────────────────────────────────────────────
class ActionType(StrEnum):
    READ = "READ"
    OPEN = "OPEN"
    CREATE = "CREATE"
    MODIFY = "MODIFY"
    RENAME = "RENAME"
    MOVE = "MOVE"
    COPY = "COPY"
    DELETE = "DELETE"
    USB_TRANSFER = "USB_TRANSFER"
    EXTERNAL_UPLOAD = "EXTERNAL_UPLOAD"
    CLOUD_SYNC = "CLOUD_SYNC"
    NETWORK_TRANSFER = "NETWORK_TRANSFER"
    ARCHIVE = "ARCHIVE"
    PRINT = "PRINT"
    UNKNOWN = "UNKNOWN"


# ── Destination types ────────────────────────────────────────────────────────
class DestinationType(StrEnum):
    LOCAL_TRUSTED = "LOCAL_TRUSTED"
    LOCAL_UNTRUSTED = "LOCAL_UNTRUSTED"
    PROTECTED_DIRECTORY = "PROTECTED_DIRECTORY"
    APPROVED_NETWORK = "APPROVED_NETWORK"
    APPROVED_CLOUD = "APPROVED_CLOUD"
    UNKNOWN_NETWORK = "UNKNOWN_NETWORK"
    EXTERNAL_NETWORK = "EXTERNAL_NETWORK"
    USB_TRUSTED = "USB_TRUSTED"
    USB_UNTRUSTED = "USB_UNTRUSTED"
    PUBLIC_CLOUD = "PUBLIC_CLOUD"
    EXTERNAL_STORAGE = "EXTERNAL_STORAGE"
    UNKNOWN = "UNKNOWN"


# ── Device trust ─────────────────────────────────────────────────────────────
class DeviceTrustLevel(StrEnum):
    MANAGED = "MANAGED"
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    UNTRUSTED = "UNTRUSTED"


# ── User role risk ───────────────────────────────────────────────────────────
class UserRiskRole(StrEnum):
    ADMIN = "ADMIN"
    SECURITY_ADMIN = "SECURITY_ADMIN"
    EMPLOYEE = "EMPLOYEE"
    CONTRACTOR = "CONTRACTOR"
    GUEST = "GUEST"
    UNKNOWN = "UNKNOWN"


# ── Sensitive-data categories ────────────────────────────────────────────────
class SensitiveCategory(StrEnum):
    PERSONAL_DATA = "PERSONAL_DATA"
    IDENTITY_INFORMATION = "IDENTITY_INFORMATION"
    FINANCIAL_DATA = "FINANCIAL_DATA"
    PAYMENT_CARD_DATA = "PAYMENT_CARD_DATA"
    BANKING_DATA = "BANKING_DATA"
    CREDENTIALS = "CREDENTIALS"
    AUTHENTICATION_SECRETS = "AUTHENTICATION_SECRETS"
    API_KEYS = "API_KEYS"
    TOKENS = "TOKENS"
    SOURCE_CODE = "SOURCE_CODE"
    CUSTOMER_DATA = "CUSTOMER_DATA"
    EMPLOYEE_DATA = "EMPLOYEE_DATA"
    CONFIDENTIAL_DOCUMENT = "CONFIDENTIAL_DOCUMENT"
    HEALTH_DATA = "HEALTH_DATA"
    INTELLECTUAL_PROPERTY = "INTELLECTUAL_PROPERTY"
    SECURITY_DATA = "SECURITY_DATA"


# ── Volume size categories ───────────────────────────────────────────────────
class VolumeSizeCategory(StrEnum):
    SMALL = "SMALL"          # < 1 MB
    MEDIUM = "MEDIUM"        # 1 MB – 50 MB
    LARGE = "LARGE"          # 50 MB – 500 MB
    VERY_LARGE = "VERY_LARGE"  # > 500 MB


# ── Time context ─────────────────────────────────────────────────────────────
class TimeContext(StrEnum):
    BUSINESS_HOURS = "BUSINESS_HOURS"
    OUTSIDE_BUSINESS_HOURS = "OUTSIDE_BUSINESS_HOURS"
    WEEKEND = "WEEKEND"
    HOLIDAY = "HOLIDAY"


# ── Risk level (derived) ────────────────────────────────────────────────────
class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ═════════════════════════════════════════════════════════════════════════════
#  Configuration data-classes
# ═════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class RiskLevelThreshold:
    """A single risk level band."""
    min_score: int
    max_score: int

    def __post_init__(self) -> None:
        if not (0 <= self.min_score <= self.max_score <= 100):
            raise ValueError(
                f"Invalid risk level range: min={self.min_score}, max={self.max_score}"
            )


@dataclass(frozen=True)
class BusinessHoursConfig:
    """Business-hours definition (timezone-aware)."""
    enabled: bool = True
    start_hour: int = 9
    start_minute: int = 0
    end_hour: int = 18
    end_minute: int = 0
    timezone: str = "Asia/Kolkata"
    weekend_days: tuple[int, ...] = (5, 6)  # Saturday=5, Sunday=6


@dataclass(frozen=True)
class VolumeThresholds:
    """Byte-size boundaries for volume categories."""
    small_max: int = 1_048_576          # 1 MB
    medium_max: int = 52_428_800        # 50 MB
    large_max: int = 524_288_000        # 500 MB
    # anything above large_max is VERY_LARGE


@dataclass(frozen=True)
class BehaviorThresholds:
    """Configurable thresholds for behavioural-context scoring."""
    high_frequency_ops: int = 10       # ops within time_window_seconds
    time_window_seconds: int = 300     # 5 minutes
    large_transfer_count: int = 5      # sensitive files in window


@dataclass
class RiskConfig:
    """Complete risk engine configuration.

    Every numeric parameter used to calculate a risk score lives here.
    Changing a field here and bumping ``config_version`` is sufficient to
    alter scoring behaviour system-wide without touching engine code.
    """

    config_version: str = RISK_CONFIG_VERSION

    # ── Component weights (must sum to 1.0 when all enabled) ─────────────
    risk_weights: dict[str, float] = field(default_factory=lambda: {
        "sensitivity": 0.30,
        "action": 0.20,
        "destination": 0.20,
        "user_context": 0.05,
        "device_context": 0.05,
        "behavior": 0.10,
        "time_context": 0.05,
        "volume": 0.05,
    })

    # ── Action risk scores (0–100) ───────────────────────────────────────
    action_risk: dict[str, int] = field(default_factory=lambda: {
        ActionType.READ: 5,
        ActionType.OPEN: 5,
        ActionType.CREATE: 5,
        ActionType.MODIFY: 10,
        ActionType.RENAME: 10,
        ActionType.MOVE: 15,
        ActionType.COPY: 20,
        ActionType.DELETE: 25,
        ActionType.USB_TRANSFER: 70,
        ActionType.EXTERNAL_UPLOAD: 75,
        ActionType.CLOUD_SYNC: 65,
        ActionType.NETWORK_TRANSFER: 60,
        ActionType.ARCHIVE: 25,
        ActionType.PRINT: 15,
        ActionType.UNKNOWN: 50,
    })

    # ── Sensitivity level scores (0–100) ─────────────────────────────────
    sensitivity_risk: dict[str, int] = field(default_factory=lambda: {
        "PUBLIC": 5,
        "INTERNAL": 20,
        "CONFIDENTIAL": 55,
        "HIGHLY_CONFIDENTIAL": 90,
        "UNKNOWN": 30,
    })

    # ── Category modifier: additional risk contribution per category ─────
    # These are *additive bonuses* (capped so total sensitivity ≤ 100)
    category_risk: dict[str, int] = field(default_factory=lambda: {
        SensitiveCategory.PERSONAL_DATA: 5,
        SensitiveCategory.IDENTITY_INFORMATION: 10,
        SensitiveCategory.FINANCIAL_DATA: 10,
        SensitiveCategory.PAYMENT_CARD_DATA: 15,
        SensitiveCategory.BANKING_DATA: 12,
        SensitiveCategory.CREDENTIALS: 20,
        SensitiveCategory.AUTHENTICATION_SECRETS: 20,
        SensitiveCategory.API_KEYS: 18,
        SensitiveCategory.TOKENS: 15,
        SensitiveCategory.SOURCE_CODE: 8,
        SensitiveCategory.CUSTOMER_DATA: 10,
        SensitiveCategory.EMPLOYEE_DATA: 8,
        SensitiveCategory.CONFIDENTIAL_DOCUMENT: 5,
        SensitiveCategory.HEALTH_DATA: 15,
        SensitiveCategory.INTELLECTUAL_PROPERTY: 10,
        SensitiveCategory.SECURITY_DATA: 12,
    })

    # Maximum additional category contribution (to prevent double-counting)
    max_category_bonus: int = 25

    # ── Destination risk scores (0–100) ──────────────────────────────────
    destination_risk: dict[str, int] = field(default_factory=lambda: {
        DestinationType.PROTECTED_DIRECTORY: 0,
        DestinationType.LOCAL_TRUSTED: 5,
        DestinationType.APPROVED_NETWORK: 10,
        DestinationType.APPROVED_CLOUD: 15,
        DestinationType.USB_TRUSTED: 25,
        DestinationType.LOCAL_UNTRUSTED: 35,
        DestinationType.USB_UNTRUSTED: 65,
        DestinationType.UNKNOWN_NETWORK: 60,
        DestinationType.EXTERNAL_NETWORK: 70,
        DestinationType.PUBLIC_CLOUD: 75,
        DestinationType.EXTERNAL_STORAGE: 80,
        DestinationType.UNKNOWN: 50,
    })

    # ── Device trust scores (0–100) ──────────────────────────────────────
    device_trust_risk: dict[str, int] = field(default_factory=lambda: {
        DeviceTrustLevel.MANAGED: 5,
        DeviceTrustLevel.KNOWN: 20,
        DeviceTrustLevel.UNKNOWN: 50,
        DeviceTrustLevel.UNTRUSTED: 80,
    })

    # ── User role risk (0–100) ───────────────────────────────────────────
    user_role_risk: dict[str, int] = field(default_factory=lambda: {
        UserRiskRole.ADMIN: 5,
        UserRiskRole.SECURITY_ADMIN: 5,
        UserRiskRole.EMPLOYEE: 15,
        UserRiskRole.CONTRACTOR: 40,
        UserRiskRole.GUEST: 60,
        UserRiskRole.UNKNOWN: 50,
    })

    # ── Time context scores (0–100) ──────────────────────────────────────
    time_context_risk: dict[str, int] = field(default_factory=lambda: {
        TimeContext.BUSINESS_HOURS: 0,
        TimeContext.OUTSIDE_BUSINESS_HOURS: 40,
        TimeContext.WEEKEND: 55,
        TimeContext.HOLIDAY: 60,
    })

    # ── Volume risk (0–100) ──────────────────────────────────────────────
    volume_risk: dict[str, int] = field(default_factory=lambda: {
        VolumeSizeCategory.SMALL: 5,
        VolumeSizeCategory.MEDIUM: 20,
        VolumeSizeCategory.LARGE: 55,
        VolumeSizeCategory.VERY_LARGE: 85,
    })

    # ── Behavioral risk parameters ───────────────────────────────────────
    behavior_thresholds: BehaviorThresholds = field(
        default_factory=BehaviorThresholds
    )

    # ── Risk level thresholds ────────────────────────────────────────────
    risk_levels: dict[str, RiskLevelThreshold] = field(default_factory=lambda: {
        RiskLevel.LOW: RiskLevelThreshold(min_score=0, max_score=29),
        RiskLevel.MEDIUM: RiskLevelThreshold(min_score=30, max_score=69),
        RiskLevel.HIGH: RiskLevelThreshold(min_score=70, max_score=100),
    })

    # ── Business hours ───────────────────────────────────────────────────
    business_hours: BusinessHoursConfig = field(
        default_factory=BusinessHoursConfig
    )

    # ── Volume thresholds ────────────────────────────────────────────────
    volume_thresholds: VolumeThresholds = field(
        default_factory=VolumeThresholds
    )

    # ── Fail-safe defaults ───────────────────────────────────────────────
    unknown_sensitivity_fallback: str = "UNKNOWN"
    unknown_destination_fallback: str = DestinationType.UNKNOWN
    unknown_action_fallback: str = ActionType.UNKNOWN
    unknown_device_fallback: str = DeviceTrustLevel.UNKNOWN
    unknown_user_fallback: str = UserRiskRole.UNKNOWN

    # ══════════════════════════════════════════════════════════════════════
    #  Validation
    # ══════════════════════════════════════════════════════════════════════
    def validate(self) -> list[str]:
        """Return a list of configuration errors (empty == valid)."""
        errors: list[str] = []

        # Weight sum
        weight_sum = sum(self.risk_weights.values())
        if abs(weight_sum - 1.0) > 0.001:
            errors.append(
                f"risk_weights must sum to 1.0, got {weight_sum:.4f}"
            )

        # Weights non-negative
        for key, val in self.risk_weights.items():
            if val < 0:
                errors.append(f"risk_weights[{key}] must be >= 0, got {val}")

        # Score maps in [0, 100]
        score_maps = {
            "action_risk": self.action_risk,
            "sensitivity_risk": self.sensitivity_risk,
            "destination_risk": self.destination_risk,
            "device_trust_risk": self.device_trust_risk,
            "user_role_risk": self.user_role_risk,
            "time_context_risk": self.time_context_risk,
            "volume_risk": self.volume_risk,
        }
        for map_name, score_map in score_maps.items():
            for key, val in score_map.items():
                if not (0 <= val <= 100):
                    errors.append(f"{map_name}[{key}] must be 0–100, got {val}")

        # Risk-level ranges — must cover 0–100 without gaps/overlaps
        sorted_levels = sorted(
            self.risk_levels.values(), key=lambda r: r.min_score
        )
        if sorted_levels:
            if sorted_levels[0].min_score != 0:
                errors.append("Risk levels must start at 0")
            if sorted_levels[-1].max_score != 100:
                errors.append("Risk levels must end at 100")
            for i in range(1, len(sorted_levels)):
                expected_min = sorted_levels[i - 1].max_score + 1
                if sorted_levels[i].min_score != expected_min:
                    errors.append(
                        f"Risk level gap/overlap between "
                        f"{sorted_levels[i-1].max_score} and {sorted_levels[i].min_score}"
                    )
        else:
            errors.append("At least one risk level must be defined")

        return errors


def get_default_risk_config() -> RiskConfig:
    """Return the default risk configuration, validated at construction time."""
    cfg = RiskConfig()
    errors = cfg.validate()
    if errors:
        raise ValueError(f"Default risk configuration is invalid: {errors}")
    return cfg
