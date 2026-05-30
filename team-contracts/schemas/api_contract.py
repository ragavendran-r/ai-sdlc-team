"""APIContract handoff: Backend → Frontend workflow."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class HTTPMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class AuthType(str, Enum):
    """Authentication types."""
    NONE = "none"
    BEARER_TOKEN = "bearer_token"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    SESSION = "session"


class HTTPStatus(str, Enum):
    """Common HTTP status codes."""
    OK = "200"
    CREATED = "201"
    ACCEPTED = "202"
    BAD_REQUEST = "400"
    UNAUTHORIZED = "401"
    FORBIDDEN = "403"
    NOT_FOUND = "404"
    CONFLICT = "409"
    UNPROCESSABLE = "422"
    INTERNAL_ERROR = "500"
    SERVICE_UNAVAILABLE = "503"


class JSONSchema(BaseModel):
    """Simplified JSON Schema for request/response bodies."""

    type: str = Field(..., description="Data type (object, array, string, number, boolean, etc.)")
    properties: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Object properties"
    )
    required: List[str] = Field(
        default_factory=list,
        description="Required fields"
    )
    description: Optional[str] = Field(default=None)
    example: Optional[Any] = Field(default=None)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "properties": self.properties,
            "required": self.required,
            "description": self.description,
            "example": self.example,
        }

    def to_markdown(self) -> str:
        """Convert to readable Markdown."""
        lines = [f"**Type:** `{self.type}`"]

        if self.description:
            lines.append(f"**Description:** {self.description}")

        if self.properties:
            lines.append("**Properties:**")
            for prop_name, prop_schema in self.properties.items():
                prop_type = prop_schema.get("type", "unknown")
                prop_desc = prop_schema.get("description", "")
                required_marker = "✓" if prop_name in self.required else "○"
                lines.append(f"- [{required_marker}] `{prop_name}` ({prop_type}): {prop_desc}")

        if self.example:
            lines.extend([
                "",
                "**Example:**",
                "```json",
            ])
            import json
            lines.append(json.dumps(self.example, indent=2))
            lines.append("```")

        return "\n".join(lines)


class ErrorResponse(BaseModel):
    """Definition of an error response."""

    status: HTTPStatus = Field(..., description="HTTP status code")
    error_code: str = Field(..., description="Application-specific error code")
    message: str = Field(..., description="Human-readable error message")
    example_response: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Example error response body"
    )

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "error_code": self.error_code,
            "message": self.message,
            "example_response": self.example_response,
        }


class QueryParameter(BaseModel):
    """A query parameter for an endpoint."""

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Data type (string, number, boolean, array)")
    required: bool = Field(default=False, description="Is this parameter required?")
    description: str = Field(..., description="What does this parameter do?")
    example: Optional[str] = Field(default=None, description="Example value")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
            "example": self.example,
        }


class APIEndpoint(BaseModel):
    """Complete specification of a single API endpoint."""

    id: str = Field(..., description="Unique endpoint identifier")
    method: HTTPMethod = Field(..., description="HTTP method")
    path: str = Field(..., description="API path (e.g., '/api/v1/users/login')")
    summary: str = Field(..., description="Short summary of what endpoint does")
    description: str = Field(..., description="Full description")

    # Authentication
    auth_required: bool = Field(default=True, description="Does this require authentication?")
    auth_type: AuthType = Field(default=AuthType.BEARER_TOKEN, description="Type of auth")
    auth_description: Optional[str] = Field(default=None, description="Auth requirements details")

    # Query parameters
    query_parameters: List[QueryParameter] = Field(
        default_factory=list,
        description="Query parameters accepted by this endpoint"
    )

    # Request body
    request_schema: Optional[JSONSchema] = Field(
        default=None,
        description="Request body schema (for POST, PUT, PATCH)"
    )

    # Response
    response_schema: JSONSchema = Field(..., description="Success response body schema")
    success_status: HTTPStatus = Field(
        default=HTTPStatus.OK,
        description="HTTP status code on success"
    )

    # Error responses
    error_responses: List[ErrorResponse] = Field(
        default_factory=list,
        description="Possible error responses"
    )

    # Rate limiting
    rate_limit: Optional[str] = Field(
        default=None,
        description="Rate limit info (e.g., '100 requests per minute')"
    )

    # Implementation notes
    notes: Optional[str] = Field(default=None, description="Implementation notes for frontend")
    idempotent: bool = Field(default=False, description="Is this endpoint idempotent?")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Ensure path starts with /."""
        if not v.startswith('/'):
            raise ValueError("Path must start with /")
        return v

    def get_full_signature(self) -> str:
        """Get full method + path signature."""
        return f"{self.method.value} {self.path}"

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"### {self.get_full_signature()}",
            f"**ID:** `{self.id}`",
            "",
            self.description,
            "",
        ]

        # Authentication
        lines.extend([
            "**Authentication:**",
            f"- Required: {'Yes' if self.auth_required else 'No'}",
        ])
        if self.auth_required:
            lines.append(f"- Type: {self.auth_type.value}")
            if self.auth_description:
                lines.append(f"- Details: {self.auth_description}")

        # Query parameters
        if self.query_parameters:
            lines.extend([
                "",
                "**Query Parameters:**",
            ])
            for param in self.query_parameters:
                required = "✓ Required" if param.required else "○ Optional"
                lines.append(f"- `{param.name}` ({param.type}) [{required}]: {param.description}")
                if param.example:
                    lines.append(f"  Example: `{param.example}`")

        # Request body
        if self.request_schema:
            lines.extend([
                "",
                "**Request Body:**",
                self.request_schema.to_markdown(),
            ])

        # Response
        lines.extend([
            "",
            f"**Response ({self.success_status.value}):**",
            self.response_schema.to_markdown(),
        ])

        # Error responses
        if self.error_responses:
            lines.extend([
                "",
                "**Error Responses:**",
            ])
            for error in self.error_responses:
                lines.append(f"- **{error.status.value} - {error.error_code}:** {error.message}")

        # Additional info
        if self.rate_limit:
            lines.extend([
                "",
                f"**Rate Limit:** {self.rate_limit}",
            ])

        if self.notes:
            lines.extend([
                "",
                "**Implementation Notes:**",
                self.notes,
            ])

        if self.idempotent:
            lines.extend([
                "",
                "**Note:** This endpoint is idempotent.",
            ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "method": self.method.value,
            "path": self.path,
            "summary": self.summary,
            "description": self.description,
            "auth_required": self.auth_required,
            "auth_type": self.auth_type.value,
            "auth_description": self.auth_description,
            "query_parameters": [p.to_dict() for p in self.query_parameters],
            "request_schema": self.request_schema.to_dict() if self.request_schema else None,
            "response_schema": self.response_schema.to_dict(),
            "success_status": self.success_status.value,
            "error_responses": [e.to_dict() for e in self.error_responses],
            "rate_limit": self.rate_limit,
            "notes": self.notes,
            "idempotent": self.idempotent,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class APIContract(BaseModel):
    """
    APIContract is the primary handoff from Backend to Frontend workflow.

    It contains complete API specifications needed for frontend integration,
    including all endpoints, authentication, error handling, and rate limits.
    """

    id: str = Field(..., description="Unique contract identifier")
    feature_name: str = Field(..., description="Feature name")
    user_story_id: str = Field(..., description="Reference to user story")

    # API info
    base_url: str = Field(..., description="Base URL for API (e.g., 'https://api.example.com/v1')")
    api_version: str = Field(default="1.0", description="API version")

    # Endpoints
    endpoints: List[APIEndpoint] = Field(
        ...,
        description="All endpoints for this feature",
        min_items=1
    )

    # Global authentication
    global_auth_requirements: Optional[str] = Field(
        default=None,
        description="Global auth requirements for all endpoints"
    )

    # Global headers
    global_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Headers that must be sent with all requests (e.g., Content-Type)"
    )

    # Error handling
    error_handling_notes: Optional[str] = Field(
        default=None,
        description="Notes on error handling patterns, retry strategies, etc."
    )

    # Data models
    data_models: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Shared data model definitions referenced by multiple endpoints"
    )

    # CORS and security
    cors_policy: Optional[str] = Field(
        default=None,
        description="CORS policy details"
    )

    security_notes: Optional[str] = Field(
        default=None,
        description="Security considerations (HTTPS required, token expiration, etc.)"
    )

    # Testing and validation
    example_flow: Optional[str] = Field(
        default=None,
        description="Example user flow with API calls"
    )

    # Metadata
    approved: bool = Field(default=False, description="Has API been approved?")
    approved_by: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent that created (typically 'backend-agent')")

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"# API Contract: {self.feature_name}",
            f"**ID:** {self.id}",
            f"**User Story:** {self.user_story_id}",
            f"**Base URL:** `{self.base_url}`",
            f"**Version:** {self.api_version}",
            f"**Status:** {'✅ Approved' if self.approved else '⏳ Pending Approval'}",
            "",
        ]

        if self.global_auth_requirements:
            lines.extend([
                "## Authentication",
                self.global_auth_requirements,
                "",
            ])

        if self.global_headers:
            lines.extend([
                "## Global Headers",
            ])
            for header, value in self.global_headers.items():
                lines.append(f"- `{header}: {value}`")
            lines.append("")

        lines.append("## Endpoints")
        for endpoint in self.endpoints:
            lines.append(endpoint.to_markdown())

        if self.data_models:
            lines.extend([
                "",
                "## Data Models",
            ])
            import json
            for model_name, model_schema in self.data_models.items():
                lines.append(f"\n### {model_name}")
                lines.append("```json")
                lines.append(json.dumps(model_schema, indent=2))
                lines.append("```")

        if self.error_handling_notes:
            lines.extend([
                "",
                "## Error Handling",
                self.error_handling_notes,
            ])

        if self.security_notes:
            lines.extend([
                "",
                "## Security",
                self.security_notes,
            ])

        if self.cors_policy:
            lines.extend([
                "",
                "## CORS",
                self.cors_policy,
            ])

        if self.example_flow:
            lines.extend([
                "",
                "## Example Flow",
                "```",
                self.example_flow,
                "```",
            ])

        lines.extend([
            "",
            f"**Created:** {self.created_at.isoformat()}",
            f"**Last Updated:** {self.updated_at.isoformat()}",
            f"**Created By:** {self.created_by}",
        ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "feature_name": self.feature_name,
            "user_story_id": self.user_story_id,
            "base_url": self.base_url,
            "api_version": self.api_version,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "global_auth_requirements": self.global_auth_requirements,
            "global_headers": self.global_headers,
            "error_handling_notes": self.error_handling_notes,
            "data_models": self.data_models,
            "cors_policy": self.cors_policy,
            "security_notes": self.security_notes,
            "example_flow": self.example_flow,
            "approved": self.approved,
            "approved_by": self.approved_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
        }


if __name__ == "__main__":
    endpoint = APIEndpoint(
        id="EP-001",
        method=HTTPMethod.POST,
        path="/api/v1/auth/login",
        summary="User login",
        description="Authenticate user with email and password",
        auth_required=False,
        request_schema=JSONSchema(
            type="object",
            properties={
                "email": {"type": "string", "description": "User email"},
                "password": {"type": "string", "description": "User password"},
            },
            required=["email", "password"],
            example={"email": "user@example.com", "password": "password123"},
        ),
        response_schema=JSONSchema(
            type="object",
            properties={
                "token": {"type": "string", "description": "JWT access token"},
                "user": {
                    "type": "object",
                    "description": "User object",
                },
            },
            required=["token", "user"],
        ),
        error_responses=[
            ErrorResponse(
                status=HTTPStatus.BAD_REQUEST,
                error_code="INVALID_CREDENTIALS",
                message="Email or password is incorrect",
            ),
            ErrorResponse(
                status=HTTPStatus.UNPROCESSABLE,
                error_code="VALIDATION_ERROR",
                message="Request validation failed",
            ),
        ],
    )

    contract = APIContract(
        id="API-001",
        feature_name="User Authentication",
        user_story_id="US-001",
        base_url="https://api.example.com/v1",
        endpoints=[endpoint],
        global_headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        security_notes="All endpoints use HTTPS. Tokens expire after 24 hours.",
        created_by="backend-agent",
    )

    print(contract.to_markdown())
