#!/usr/bin/env python
"""E-Commerce Platform Example - Complete Pipeline Walkthrough

This example demonstrates the full AI SDLC Team pipeline building a user
authentication system for an e-commerce platform.

Usage:
    python run.py

Expected Output:
    - Complete event flow from PO → EM → UX → Backend → Frontend
    - Generated artifacts in context store
    - Final status report showing all completed workflows
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from team_orchestrator import TeamOrchestrator, Event, EventType


def run_ecommerce_example():
    """Execute the E-Commerce Platform example."""

    print("\n" + "="*80)
    print(" E-COMMERCE PLATFORM - COMPLETE PIPELINE EXAMPLE")
    print("="*80)
    print("\nFeature: User Authentication System")
    print("Scenario: Implementing secure user login for e-commerce platform")
    print("\nThis example shows how the AI SDLC Team collaborates to build a feature")
    print("from requirements through implementation.\n")

    # Initialize orchestrator
    orchestrator = TeamOrchestrator()
    orchestrator.start_pipeline()

    # =========================================================================
    # 1. PO AGENT - Create User Stories
    # =========================================================================
    print("\n" + "-"*80)
    print("STEP 1: PO AGENT - Analyzing market needs and creating user stories")
    print("-"*80)

    po_event = Event(
        event_type=EventType.USER_STORIES_CREATED,
        workflow="po",
        payload={
            "stories": [
                {
                    "id": "US-AUTH-001",
                    "title": "User can log in with email and password",
                    "user_role": "Customer",
                    "user_goal": "access my account securely",
                    "business_value": "customer accounts enable personalization and purchase history",
                    "acceptance_criteria": [
                        "User can enter email and password",
                        "Valid credentials grant access",
                        "Invalid credentials show error message",
                        "Passwords never displayed in plain text",
                        "Failed attempts are logged",
                        "Session expires after 24 hours",
                    ],
                    "priority": "high",
                    "complexity": "medium",
                    "security_considerations": [
                        "HTTPS required",
                        "Password hashing with bcrypt",
                        "Rate limiting on login attempts",
                        "CSRF token protection",
                    ],
                },
                {
                    "id": "US-AUTH-002",
                    "title": "User can create an account",
                    "user_role": "New Customer",
                    "user_goal": "create a new account to make purchases",
                    "business_value": "user registration drives customer growth",
                    "acceptance_criteria": [
                        "Email validation checks for duplicates",
                        "Password strength requirements enforced",
                        "Confirmation email sent",
                        "Account active only after email confirmation",
                    ],
                    "priority": "high",
                    "complexity": "medium",
                },
                {
                    "id": "US-AUTH-003",
                    "title": "User can reset forgotten password",
                    "user_role": "Returning Customer",
                    "user_goal": "regain access to my account",
                    "business_value": "reduces customer frustration and support tickets",
                    "acceptance_criteria": [
                        "Reset link sent to registered email",
                        "Link expires after 1 hour",
                        "New password set requires validation",
                        "User notified of password change",
                    ],
                    "priority": "medium",
                    "complexity": "medium",
                },
            ],
            "context": {
                "project": "ecommerce-platform",
                "sprint": "Q2-2026",
                "stakeholders": ["Product Manager", "CTO", "Security Lead"],
            }
        },
        source_agent="po-agent",
    )
    orchestrator.publish_event(po_event)
    orchestrator.mark_workflow_complete("po")

    # =========================================================================
    # 2. EM AGENT - Create Sprint Plan
    # =========================================================================
    print("\n" + "-"*80)
    print("STEP 2: EM AGENT - Planning sprint and allocating tasks")
    print("-"*80)

    em_event = Event(
        event_type=EventType.SPRINT_CREATED,
        workflow="em",
        payload={
            "sprint": {
                "id": "S-2026-Q2-001",
                "name": "Sprint 1: User Authentication",
                "duration_days": 14,
                "start_date": "2026-06-01",
                "end_date": "2026-06-14",
            },
            "stories": ["US-AUTH-001", "US-AUTH-002", "US-AUTH-003"],
            "tasks": [
                {
                    "id": "T-001",
                    "title": "Design authentication flow",
                    "assigned_to": "ux-agent",
                    "type": "design",
                    "estimated_hours": 4,
                },
                {
                    "id": "T-002",
                    "title": "Design database schema",
                    "assigned_to": "backend-agent",
                    "type": "backend",
                    "estimated_hours": 3,
                },
                {
                    "id": "T-003",
                    "title": "Implement authentication API",
                    "assigned_to": "backend-agent",
                    "type": "backend",
                    "estimated_hours": 8,
                },
                {
                    "id": "T-004",
                    "title": "Implement login form component",
                    "assigned_to": "frontend-agent",
                    "type": "frontend",
                    "estimated_hours": 4,
                },
                {
                    "id": "T-005",
                    "title": "Connect frontend to API",
                    "assigned_to": "frontend-agent",
                    "type": "frontend",
                    "estimated_hours": 3,
                },
                {
                    "id": "T-006",
                    "title": "Security audit and testing",
                    "assigned_to": "backend-agent",
                    "type": "backend",
                    "estimated_hours": 4,
                },
            ],
            "total_points": 26,
            "team_capacity": 32,
            "risks": [
                "Security audit may reveal required changes",
                "API integration complexity",
            ],
        },
        source_agent="em-agent",
    )
    orchestrator.publish_event(em_event)
    orchestrator.mark_workflow_complete("em")

    # =========================================================================
    # 3. UX AGENT - Design User Interface
    # =========================================================================
    print("\n" + "-"*80)
    print("STEP 3: UX AGENT - Designing user interface and flows")
    print("-"*80)

    ux_event = Event(
        event_type=EventType.HANDOFF_CREATED,
        workflow="ux",
        payload={
            "handoff": {
                "id": "UX-AUTH-001",
                "feature": "User Authentication",
                "components": [
                    {
                        "name": "LoginForm",
                        "type": "form",
                        "fields": ["email", "password"],
                        "validations": {
                            "email": "required, valid email format",
                            "password": "required, min 8 chars",
                        },
                        "states": ["default", "loading", "error", "success"],
                        "accessibility": {
                            "aria_labels": True,
                            "keyboard_navigation": True,
                            "error_announcements": True,
                        },
                    },
                    {
                        "name": "SignupForm",
                        "type": "form",
                        "fields": ["email", "password", "confirm_password", "name"],
                        "validations": {
                            "password": "required, min 8 chars, must have uppercase, number, special char",
                        },
                    },
                    {
                        "name": "ForgotPasswordForm",
                        "type": "form",
                        "fields": ["email"],
                    },
                    {
                        "name": "ErrorMessage",
                        "type": "feedback",
                        "props": ["message", "type"],
                    },
                    {
                        "name": "SuccessMessage",
                        "type": "feedback",
                        "props": ["message"],
                    },
                ],
                "flows": [
                    {
                        "name": "Login Flow",
                        "steps": [
                            "User navigates to /login",
                            "User enters email and password",
                            "User clicks 'Log In' button",
                            "If valid: redirect to dashboard",
                            "If invalid: show error message",
                        ],
                    },
                    {
                        "name": "Signup Flow",
                        "steps": [
                            "User clicks 'Create Account'",
                            "User fills signup form",
                            "Confirmation email sent",
                            "User verifies email",
                            "Account activated",
                        ],
                    },
                ],
            },
            "tokens": {
                "colors": {
                    "primary": "#007bff",
                    "danger": "#dc3545",
                    "success": "#28a745",
                    "warning": "#ffc107",
                },
                "spacing": {
                    "xs": "0.25rem",
                    "sm": "0.5rem",
                    "md": "1rem",
                    "lg": "1.5rem",
                    "xl": "2rem",
                },
                "typography": {
                    "heading": "1.5rem, 600 weight",
                    "body": "1rem, 400 weight",
                    "small": "0.875rem, 400 weight",
                },
                "border_radius": {
                    "sm": "2px",
                    "md": "4px",
                    "lg": "8px",
                },
            },
            "accessibility_requirements": [
                "WCAG 2.1 Level AA compliance",
                "Keyboard navigation support",
                "ARIA labels on all interactive elements",
                "Error messages announced to screen readers",
                "Color contrast minimum 4.5:1 for text",
            ],
        },
        source_agent="ux-agent",
    )
    orchestrator.publish_event(ux_event)
    orchestrator.mark_workflow_complete("ux")

    # =========================================================================
    # 4. BACKEND AGENT - Design API and Database
    # =========================================================================
    print("\n" + "-"*80)
    print("STEP 4: BACKEND AGENT - Designing API and database schema")
    print("-"*80)

    backend_event = Event(
        event_type=EventType.API_CONTRACT_PUBLISHED,
        workflow="backend",
        payload={
            "contract": {
                "id": "API-AUTH-001",
                "feature": "User Authentication",
                "base_url": "https://api.ecommerce.example.com/v1",
                "version": "1.0.0",
                "endpoints": [
                    {
                        "method": "POST",
                        "path": "/auth/login",
                        "summary": "User login",
                        "request_body": {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string", "format": "email"},
                                "password": {"type": "string"},
                            },
                            "required": ["email", "password"],
                        },
                        "response": {
                            "type": "object",
                            "properties": {
                                "token": {"type": "string"},
                                "user": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "email": {"type": "string"},
                                        "name": {"type": "string"},
                                    },
                                },
                            },
                        },
                        "status": 200,
                        "errors": [
                            {"status": 400, "code": "INVALID_CREDENTIALS"},
                            {"status": 422, "code": "VALIDATION_ERROR"},
                        ],
                    },
                    {
                        "method": "POST",
                        "path": "/auth/signup",
                        "summary": "User registration",
                        "auth_required": False,
                    },
                    {
                        "method": "POST",
                        "path": "/auth/logout",
                        "summary": "User logout",
                        "auth_required": True,
                    },
                    {
                        "method": "GET",
                        "path": "/auth/me",
                        "summary": "Get current user",
                        "auth_required": True,
                    },
                ],
                "authentication": {
                    "type": "bearer_token",
                    "scheme": "Bearer",
                    "format": "JWT",
                    "expiration": "24h",
                },
                "security": {
                    "https_required": True,
                    "csrf_protection": True,
                    "rate_limiting": "100 requests per hour per IP",
                    "password_policy": {
                        "min_length": 8,
                        "require_uppercase": True,
                        "require_numbers": True,
                        "require_special_chars": True,
                    },
                    "password_hashing": "bcrypt with salt rounds 12",
                },
                "database": {
                    "tables": [
                        {
                            "name": "users",
                            "columns": [
                                {"name": "id", "type": "UUID PRIMARY KEY"},
                                {"name": "email", "type": "VARCHAR UNIQUE NOT NULL"},
                                {"name": "password_hash", "type": "VARCHAR NOT NULL"},
                                {"name": "name", "type": "VARCHAR"},
                                {"name": "created_at", "type": "TIMESTAMP"},
                                {"name": "updated_at", "type": "TIMESTAMP"},
                                {"name": "last_login", "type": "TIMESTAMP"},
                            ],
                            "indexes": [
                                "users(email)",
                                "users(created_at)",
                            ],
                        },
                        {
                            "name": "sessions",
                            "columns": [
                                {"name": "id", "type": "UUID PRIMARY KEY"},
                                {"name": "user_id", "type": "UUID FOREIGN KEY"},
                                {"name": "token", "type": "VARCHAR UNIQUE NOT NULL"},
                                {"name": "expires_at", "type": "TIMESTAMP"},
                                {"name": "created_at", "type": "TIMESTAMP"},
                            ],
                            "indexes": [
                                "sessions(token)",
                                "sessions(user_id)",
                                "sessions(expires_at)",
                            ],
                        },
                        {
                            "name": "login_attempts",
                            "columns": [
                                {"name": "id", "type": "UUID PRIMARY KEY"},
                                {"name": "email", "type": "VARCHAR"},
                                {"name": "ip_address", "type": "VARCHAR"},
                                {"name": "success", "type": "BOOLEAN"},
                                {"name": "attempted_at", "type": "TIMESTAMP"},
                            ],
                            "indexes": [
                                "login_attempts(email, attempted_at)",
                                "login_attempts(ip_address, attempted_at)",
                            ],
                        },
                    ],
                },
            },
            "security_review": {
                "status": "passed",
                "findings": [
                    {"severity": "high", "issue": "Missing rate limiting"},
                    {"severity": "medium", "issue": "Implement refresh token rotation"},
                ],
            },
        },
        source_agent="backend-agent",
    )
    orchestrator.publish_event(backend_event)
    orchestrator.mark_workflow_complete("backend")

    # =========================================================================
    # 5. FRONTEND AGENT - Scaffold Components
    # =========================================================================
    print("\n" + "-"*80)
    print("STEP 5: FRONTEND AGENT - Scaffolding React components")
    print("-"*80)

    frontend_event = Event(
        event_type=EventType.COMPONENTS_SCAFFOLDED,
        workflow="frontend",
        payload={
            "components": [
                {
                    "id": "C-LOGIN-001",
                    "name": "LoginForm",
                    "path": "src/components/auth/LoginForm.tsx",
                    "description": "User login form component",
                    "props": [
                        {
                            "name": "onSuccess",
                            "type": "() => void",
                            "required": False,
                            "description": "Callback on successful login",
                        },
                        {
                            "name": "onError",
                            "type": "(error: string) => void",
                            "required": False,
                            "description": "Callback on login error",
                        },
                    ],
                    "state_management": "Context API (AuthContext)",
                    "api_calls": ["POST /auth/login"],
                    "design_tokens": [
                        "color-primary",
                        "color-danger",
                        "spacing-md",
                        "border-radius-md",
                    ],
                    "accessibility": {
                        "aria_labels": True,
                        "keyboard_support": True,
                        "screen_reader_tested": False,  # TODO
                    },
                    "tests": [
                        "Should render form with email and password fields",
                        "Should validate email format",
                        "Should validate password min length",
                        "Should submit form and call API",
                        "Should display error on failed login",
                        "Should show loading state during submission",
                        "Should be keyboard navigable",
                    ],
                },
                {
                    "id": "C-AUTH-002",
                    "name": "SignupForm",
                    "path": "src/components/auth/SignupForm.tsx",
                    "description": "User registration form",
                    "tests": [
                        "Should validate password strength",
                        "Should confirm password matches",
                        "Should send confirmation email on success",
                    ],
                },
                {
                    "id": "C-AUTH-003",
                    "name": "ForgotPasswordForm",
                    "path": "src/components/auth/ForgotPasswordForm.tsx",
                    "description": "Password reset form",
                },
                {
                    "id": "C-FEEDBACK-001",
                    "name": "ErrorMessage",
                    "path": "src/components/feedback/ErrorMessage.tsx",
                    "description": "Error message display component",
                    "props": [
                        {"name": "message", "type": "string", "required": True},
                        {"name": "onDismiss", "type": "() => void", "required": False},
                    ],
                },
            ],
            "state_management_plan": {
                "strategy": "Context API",
                "providers": [
                    {
                        "name": "AuthContext",
                        "state": {
                            "user": "User | null",
                            "isLoading": "boolean",
                            "error": "string | null",
                        },
                        "actions": [
                            "login(email, password)",
                            "logout()",
                            "signup(email, password, name)",
                            "resetPassword(email)",
                        ],
                    }
                ],
                "redux_needed": False,
            },
            "test_coverage": {
                "total_tests": 24,
                "unit_tests": 20,
                "integration_tests": 4,
                "coverage_target": "80%",
            },
            "accessibility_checklist": {
                "wcag_level": "AA",
                "aria_labels": "✓",
                "keyboard_navigation": "✓",
                "color_contrast": "✓",
                "focus_visible": "TODO",
                "screen_reader_tested": "TODO",
            },
        },
        source_agent="frontend-agent",
    )
    orchestrator.publish_event(frontend_event)
    orchestrator.mark_workflow_complete("frontend")

    # =========================================================================
    # Complete Pipeline
    # =========================================================================
    orchestrator.complete_pipeline()

    # =========================================================================
    # Print Summary
    # =========================================================================
    print("\n" + "="*80)
    print(" PIPELINE COMPLETE - SUMMARY")
    print("="*80)

    orchestrator.print_status_report()
    orchestrator.print_route_diagram()
    orchestrator.print_context_timeline()

    print("\n" + "="*80)
    print(" NEXT STEPS FOR IMPLEMENTATION")
    print("="*80)
    print("""
1. BACKEND ENGINEER
   - Set up PostgreSQL database with schema
   - Implement AuthService with password hashing
   - Create API endpoints with validation and error handling
   - Implement JWT token generation and validation
   - Add rate limiting and CSRF protection
   - Write and run security tests
   - Conduct security audit

2. FRONTEND ENGINEER
   - Create React components from scaffolds
   - Implement form validation
   - Connect to API endpoints
   - Set up AuthContext and state management
   - Implement error handling and loading states
   - Add keyboard navigation
   - Test accessibility compliance
   - Write unit and integration tests

3. QA/TESTING
   - End-to-end testing of login flow
   - Security testing (brute force protection, injection)
   - Performance testing (load testing)
   - Cross-browser compatibility testing
   - Mobile responsiveness testing

4. DEVOPS/DEPLOYMENT
   - Containerize application
   - Set up CI/CD pipeline
   - Deploy to staging environment
   - Conduct load testing
   - Deploy to production

5. MONITORING
   - Set up error tracking (Sentry)
   - Add performance monitoring
   - Track login success/failure rates
   - Monitor security events
""")

    print("\nArtifacts are stored in: team-contracts/context-store/")
    print("View them with: python ../../run_team_pipeline.py context --timeline")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        run_ecommerce_example()
        print("✅ Example completed successfully!")
    except Exception as e:
        print(f"❌ Example failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
