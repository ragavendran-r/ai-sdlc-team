"""Handoff contract schemas for AI SDLC Team."""

from .user_story import UserStory, Priority, Complexity
from .sprint_plan import SprintPlan, Sprint, SprintTask, TaskType, TaskStatus
from .ux_handoff import UXHandoff, ComponentSpec, ComponentType, DesignToken, InteractionSpec
from .api_contract import APIContract, APIEndpoint, HTTPMethod, HTTPStatus, AuthType, JSONSchema, ErrorResponse
from .design_decision import DesignDecision, DecisionCategory, DecisionStatus, DecisionImpact, Alternative, Consequence
from .capacity_report import CapacityReport
from .risk_flag import RiskFlag, RiskSeverity, RiskType
from .dod_item import DoDItem, DefinitionOfDone, DoDCategory
from .sprint_status import SprintStatus, SprintPhase, StoryStatusInSprint
from .blocker import Blocker, BlockerStatus, BlockerType
from .user_persona import UserPersona
from .user_flow import UserFlow, FlowStep, DecisionPoint
from .ia_structure import IAStructure, NavNode
from .wireframe_brief import WireframeBrief, ComponentRequirement, InteractionPattern
from .design_compliance import DesignComplianceReport, ComponentGap, ComplianceStatus
from .accessibility_flag import AccessibilityFlag, WCAGLevel, AccessibilitySeverity
from .component_spec import ComponentSpec as FrontendComponentSpec
from .scaffolded_component import ScaffoldedComponent
from .state_plan import StatePlan, StateGroup, StateManagementType
from .test_file import TestFile, TestCase, TestType
from .review_comment import ReviewComment, ReviewSeverity, ReviewCategory
from .backend_requirement import BackendRequirement, RequirementType
from .domain_model import DomainModel, Entity, Attribute, Relationship, DataType, RelationType
from .database_schema import DatabaseSchema
from .service_scaffold import ServiceScaffold, MethodStub
from .validation_module import ValidationModule, ValidatorFunction
from .security_flag import SecurityFlag, SecuritySeverity, SecurityCategory

__all__ = [
    # UserStory
    "UserStory",
    "Priority",
    "Complexity",
    # SprintPlan
    "SprintPlan",
    "Sprint",
    "SprintTask",
    "TaskType",
    "TaskStatus",
    # UXHandoff
    "UXHandoff",
    "ComponentSpec",
    "ComponentType",
    "DesignToken",
    "InteractionSpec",
    # APIContract
    "APIContract",
    "APIEndpoint",
    "HTTPMethod",
    "HTTPStatus",
    "AuthType",
    "JSONSchema",
    "ErrorResponse",
    # DesignDecision
    "DesignDecision",
    "DecisionCategory",
    "DecisionStatus",
    "DecisionImpact",
    "Alternative",
    "Consequence",
    # CapacityReport
    "CapacityReport",
    # RiskFlag
    "RiskFlag",
    "RiskSeverity",
    "RiskType",
    # DoDItem
    "DoDItem",
    "DefinitionOfDone",
    "DoDCategory",
    # SprintStatus
    "SprintStatus",
    "SprintPhase",
    "StoryStatusInSprint",
    # Blocker
    "Blocker",
    "BlockerStatus",
    "BlockerType",
    # UserPersona
    "UserPersona",
    # UserFlow
    "UserFlow",
    "FlowStep",
    "DecisionPoint",
    # IAStructure
    "IAStructure",
    "NavNode",
    # WireframeBrief
    "WireframeBrief",
    "ComponentRequirement",
    "InteractionPattern",
    # DesignCompliance
    "DesignComplianceReport",
    "ComponentGap",
    "ComplianceStatus",
    # AccessibilityFlag
    "AccessibilityFlag",
    "WCAGLevel",
    "AccessibilitySeverity",
    # Frontend workflow schemas
    "FrontendComponentSpec",
    "ScaffoldedComponent",
    "StatePlan",
    "StateGroup",
    "StateManagementType",
    "TestFile",
    "TestCase",
    "TestType",
    "ReviewComment",
    "ReviewSeverity",
    "ReviewCategory",
    # Backend workflow schemas
    "BackendRequirement",
    "RequirementType",
    "DomainModel",
    "Entity",
    "Attribute",
    "Relationship",
    "DataType",
    "RelationType",
    "DatabaseSchema",
    "ServiceScaffold",
    "MethodStub",
    "ValidationModule",
    "ValidatorFunction",
    "SecurityFlag",
    "SecuritySeverity",
    "SecurityCategory",
]
