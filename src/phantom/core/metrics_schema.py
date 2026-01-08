#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PROJECTPHANTOM - METRICS SCHEMA                           ║
║              Enterprise Project Audit Metrics Definitions                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Pydantic schemas for all audit metrics collected by ProjectPhantom.
Provides type-safe data structures for:
- Project metadata
- Code quality metrics
- Activity metrics
- Security metrics
- AI-generated insights
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════════════════════════


class ProjectStatus(str, Enum):
    """Project lifecycle status."""

    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    UNKNOWN = "unknown"


class InvestmentRecommendation(str, Enum):
    """Investment recommendation categories."""

    STRATEGIC_ASSET = "strategic_asset"  # 90-100
    STRONG_PROJECT = "strong_project"  # 80-89
    SOLID_FOUNDATION = "solid_foundation"  # 70-79
    NEEDS_ATTENTION = "needs_attention"  # 60-69
    AT_RISK = "at_risk"  # 50-59
    CRITICAL = "critical"  # 40-49
    LEGACY = "legacy"  # 0-39


class RiskLevel(str, Enum):
    """Risk severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TechCategory(str, Enum):
    """Technology categories."""

    LANGUAGE = "language"
    FRAMEWORK = "framework"
    BUILD_TOOL = "build_tool"
    PACKAGE_MANAGER = "package_manager"
    CONTAINER = "container"
    CI_CD = "ci_cd"
    DATABASE = "database"
    OTHER = "other"


# ══════════════════════════════════════════════════════════════════════════════
# BASE METRICS
# ══════════════════════════════════════════════════════════════════════════════


class HalsteadMetrics(BaseModel):
    """Halstead complexity metrics."""

    vocabulary: int = Field(0, description="Program vocabulary (n)")
    length: int = Field(0, description="Program length (N)")
    calculated_length: float = Field(0.0, description="Calculated length")
    volume: float = Field(0.0, description="Volume (V)")
    difficulty: float = Field(0.0, description="Difficulty (D)")
    effort: float = Field(0.0, description="Effort (E)")
    time: float = Field(0.0, description="Time to program (T)")
    bugs: float = Field(0.0, description="Estimated bugs (B)")


class CodeMetrics(BaseModel):
    """Core code metrics."""

    total_lines: int = Field(0, description="Total lines of code")
    code_lines: int = Field(0, description="Lines of actual code")
    comment_lines: int = Field(0, description="Lines of comments")
    blank_lines: int = Field(0, description="Blank lines")
    file_count: int = Field(0, description="Total number of files")
    avg_file_size: float = Field(0.0, description="Average file size in lines")
    max_file_size: int = Field(0, description="Largest file in lines")
    lines_by_language: dict[str, int] = Field(default_factory=dict)
    files_by_language: dict[str, int] = Field(default_factory=dict)


class ComplexityMetrics(BaseModel):
    """Code complexity metrics."""

    cyclomatic_complexity_avg: float = Field(
        0.0, description="Average cyclomatic complexity"
    )
    cyclomatic_complexity_max: int = Field(
        0, description="Maximum cyclomatic complexity"
    )
    cognitive_complexity_avg: float = Field(
        0.0, description="Average cognitive complexity"
    )
    halstead: HalsteadMetrics = Field(default_factory=HalsteadMetrics)
    maintainability_index: float = Field(
        0.0, description="Maintainability index (0-100)"
    )
    functions_count: int = Field(0, description="Total number of functions")
    classes_count: int = Field(0, description="Total number of classes")
    avg_function_length: float = Field(0.0, description="Average function length")


class ActivityMetrics(BaseModel):
    """Git activity metrics."""

    is_git_repo: bool = Field(False)
    last_commit_date: datetime | None = None
    days_since_last_commit: int = Field(999, description="Days since last commit")
    commits_last_7_days: int = Field(0)
    commits_last_30_days: int = Field(0)
    commits_last_90_days: int = Field(0)
    commits_last_year: int = Field(0)
    commits_total: int = Field(0)
    active_contributors_30d: int = Field(0)
    active_contributors_year: int = Field(0)
    total_contributors: int = Field(0)
    avg_commits_per_day: float = Field(0.0)
    commit_frequency_score: float = Field(0.0, description="0-100 score")


class QualityMetrics(BaseModel):
    """Code quality metrics."""

    documentation_score: float = Field(0.0, description="Documentation quality (0-100)")
    readme_exists: bool = Field(False)
    readme_quality: float = Field(0.0, description="README quality score (0-100)")
    has_changelog: bool = Field(False)
    has_contributing: bool = Field(False)
    has_license: bool = Field(False)
    test_coverage_estimate: float = Field(
        0.0, description="Estimated test coverage (0-100)"
    )
    test_file_ratio: float = Field(
        0.0, description="Ratio of test files to source files"
    )
    code_duplication_ratio: float = Field(
        0.0, description="Code duplication percentage"
    )
    linting_configured: bool = Field(False)
    type_checking_configured: bool = Field(False)


class DependencyInfo(BaseModel):
    """Dependency information."""

    name: str
    version: str | None = None
    latest_version: str | None = None
    is_outdated: bool = False
    days_since_update: int = 0
    has_known_vulnerabilities: bool = False
    vulnerability_count: int = 0
    severity_high: int = 0
    severity_critical: int = 0


class DependencyMetrics(BaseModel):
    """Dependency analysis metrics."""

    total_dependencies: int = Field(0)
    direct_dependencies: int = Field(0)
    dev_dependencies: int = Field(0)
    outdated_dependencies: int = Field(0)
    vulnerable_dependencies: int = Field(0)
    dependency_freshness: float = Field(0.0, description="Freshness score (0-100)")
    security_score: float = Field(0.0, description="Security score (0-100)")
    dependencies: list[DependencyInfo] = Field(default_factory=list)


class SecurityMetrics(BaseModel):
    """Security-related metrics."""

    security_score: float = Field(100.0, description="Overall security score (0-100)")
    vulnerabilities_critical: int = Field(0)
    vulnerabilities_high: int = Field(0)
    vulnerabilities_medium: int = Field(0)
    vulnerabilities_low: int = Field(0)
    secrets_detected: int = Field(0, description="Potential secrets in code")
    security_headers_score: float = Field(0.0)
    has_security_policy: bool = Field(False)
    has_dependabot: bool = Field(False)
    has_code_scanning: bool = Field(False)


class TechStackItem(BaseModel):
    """Technology stack item."""

    name: str
    category: TechCategory
    version: str | None = None
    confidence: float = Field(1.0, description="Detection confidence (0-1)")


class TechStackMetrics(BaseModel):
    """Technology stack analysis."""

    primary_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    build_tools: list[str] = Field(default_factory=list)
    package_managers: list[str] = Field(default_factory=list)
    ci_cd_tools: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    containers: list[str] = Field(default_factory=list)
    all_technologies: list[TechStackItem] = Field(default_factory=list)
    stack_modernity_score: float = Field(
        0.0, description="How modern is the stack (0-100)"
    )


# ══════════════════════════════════════════════════════════════════════════════
# AI-GENERATED INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════


class RiskFactor(BaseModel):
    """Identified risk factor."""

    category: str = Field(..., description="Risk category")
    description: str = Field(..., description="Risk description")
    severity: RiskLevel = Field(RiskLevel.MEDIUM)
    impact: str = Field("", description="Potential impact")
    mitigation: str = Field("", description="Suggested mitigation")
    score_impact: float = Field(0.0, description="Impact on viability score")


class ImprovementSuggestion(BaseModel):
    """AI-generated improvement suggestion."""

    title: str
    description: str
    priority: RiskLevel = Field(RiskLevel.MEDIUM)
    category: str = Field("general", description="Suggestion category")
    effort_estimate: str = Field("medium", description="Implementation effort")
    expected_impact: str = Field("", description="Expected impact on project")
    related_metrics: list[str] = Field(default_factory=list)


class AIInsights(BaseModel):
    """AI-generated project insights."""

    summary: str = Field("", description="AI-generated project summary")
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    threats: list[str] = Field(default_factory=list)
    risk_factors: list[RiskFactor] = Field(default_factory=list)
    suggestions: list[ImprovementSuggestion] = Field(default_factory=list)
    tech_debt_summary: str = Field("")
    market_positioning: str = Field("")


# ══════════════════════════════════════════════════════════════════════════════
# VIABILITY SCORING
# ══════════════════════════════════════════════════════════════════════════════


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown by category."""

    activity_score: float = Field(0.0, description="Activity/engagement score (0-100)")
    activity_weight: float = Field(0.25)
    quality_score: float = Field(0.0, description="Code quality score (0-100)")
    quality_weight: float = Field(0.20)
    complexity_score: float = Field(
        0.0, description="Manageable complexity score (0-100)"
    )
    complexity_weight: float = Field(0.15)
    security_score: float = Field(0.0, description="Security posture score (0-100)")
    security_weight: float = Field(0.15)
    maintenance_score: float = Field(
        0.0, description="Maintenance health score (0-100)"
    )
    maintenance_weight: float = Field(0.15)
    potential_score: float = Field(0.0, description="AI-assessed potential (0-100)")
    potential_weight: float = Field(0.10)

    @property
    def weighted_total(self) -> float:
        """Calculate weighted total score."""
        return (
            self.activity_score * self.activity_weight
            + self.quality_score * self.quality_weight
            + self.complexity_score * self.complexity_weight
            + self.security_score * self.security_weight
            + self.maintenance_score * self.maintenance_weight
            + self.potential_score * self.potential_weight
        )


class ViabilityScore(BaseModel):
    """Complete viability assessment."""

    score: float = Field(0.0, description="Overall viability score (0-100)")
    grade: str = Field("F", description="Letter grade (A-F)")
    breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    recommendation: InvestmentRecommendation = Field(InvestmentRecommendation.LEGACY)
    recommendation_text: str = Field("")
    confidence: float = Field(0.0, description="Assessment confidence (0-1)")
    assessed_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_score(cls, score: float, breakdown: ScoreBreakdown) -> "ViabilityScore":
        """Create ViabilityScore from numeric score."""
        if score >= 90:
            rec = InvestmentRecommendation.STRATEGIC_ASSET
            grade = "A+"
            text = "Strategic asset - Invest heavily and prioritize"
        elif score >= 80:
            rec = InvestmentRecommendation.STRONG_PROJECT
            grade = "A"
            text = "Strong project - Maintain and grow"
        elif score >= 70:
            rec = InvestmentRecommendation.SOLID_FOUNDATION
            grade = "B"
            text = "Solid foundation - Continue development"
        elif score >= 60:
            rec = InvestmentRecommendation.NEEDS_ATTENTION
            grade = "C"
            text = "Needs attention - Address identified issues"
        elif score >= 50:
            rec = InvestmentRecommendation.AT_RISK
            grade = "D"
            text = "At risk - Major intervention needed"
        elif score >= 40:
            rec = InvestmentRecommendation.CRITICAL
            grade = "D-"
            text = "Critical state - Consider archiving"
        else:
            rec = InvestmentRecommendation.LEGACY
            grade = "F"
            text = "Legacy/Dead - Archive or deprecate"

        return cls(
            score=score,
            grade=grade,
            breakdown=breakdown,
            recommendation=rec,
            recommendation_text=text,
            confidence=0.8 if score > 30 else 0.6,
        )


# ══════════════════════════════════════════════════════════════════════════════
# COMPLETE PROJECT METRICS
# ══════════════════════════════════════════════════════════════════════════════


class ProjectMetrics(BaseModel):
    """Complete project metrics collection."""

    # Identification
    project_id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    path: str = Field(..., description="Absolute path to project")

    # Timestamps
    scan_timestamp: datetime = Field(default_factory=datetime.now)
    scan_duration_ms: float = Field(0.0)

    # Status
    status: ProjectStatus = Field(ProjectStatus.UNKNOWN)

    # Metrics Collections
    code: CodeMetrics = Field(default_factory=CodeMetrics)
    complexity: ComplexityMetrics = Field(default_factory=ComplexityMetrics)
    activity: ActivityMetrics = Field(default_factory=ActivityMetrics)
    quality: QualityMetrics = Field(default_factory=QualityMetrics)
    dependencies: DependencyMetrics = Field(default_factory=DependencyMetrics)
    security: SecurityMetrics = Field(default_factory=SecurityMetrics)
    tech_stack: TechStackMetrics = Field(default_factory=TechStackMetrics)

    # AI Insights (optional, requires AI)
    ai_insights: AIInsights | None = None

    # Viability Assessment
    viability: ViabilityScore | None = None

    # Metadata
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AuditReport(BaseModel):
    """Complete audit report for a project or collection."""

    # Report Metadata
    report_id: str
    generated_at: datetime = Field(default_factory=datetime.now)
    report_version: str = Field("1.0.0")

    # Scope
    projects_audited: int = Field(0)
    total_duration_ms: float = Field(0.0)

    # Results
    projects: list[ProjectMetrics] = Field(default_factory=list)

    # Aggregated Insights
    summary: str = Field("")
    top_recommendations: list[ImprovementSuggestion] = Field(default_factory=list)
    risk_overview: dict[str, int] = Field(default_factory=dict)

    # Comparative Metrics (for multi-project audits)
    avg_viability_score: float = Field(0.0)
    best_project: str | None = None
    worst_project: str | None = None
    trends: dict[str, Any] = Field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════════════════
# DOCKER STACK METRICS (for docker-hub integration)
# ══════════════════════════════════════════════════════════════════════════════


class DockerStackMetrics(BaseModel):
    """Metrics for Docker Compose stacks."""

    stack_name: str
    path: str
    services_count: int = Field(0)
    services: list[str] = Field(default_factory=list)
    has_gpu_support: bool = Field(False)
    volumes_count: int = Field(0)
    networks_count: int = Field(0)
    exposed_ports: list[int] = Field(default_factory=list)
    images_used: list[str] = Field(default_factory=list)
    health_status: str = Field("unknown")
    last_updated: datetime | None = None
