import allure
import pytest
from click.testing import CliRunner
from pydantic import BaseModel, Field
from typing import List, Optional
import json


@allure.feature("Runpy BaseModel Documentation")
class TestRunpyBaseModelDocs:
    """BDD tests for BaseModel handling in documentation"""

    @allure.story("BaseModel in function parameters")
    @allure.title(
        "Given functions with BaseModel params, When showing docs, Then displays model schema"
    )
    def test_basemodel_parameter_documentation(self):
        with allure.step("Given functions using BaseModel"):

            class UserInput(BaseModel):
                """User creation input model"""

                name: str = Field(..., description="User's full name")
                email: str = Field(..., description="Valid email address")
                age: Optional[int] = Field(None, description="User's age", ge=0, le=150)
                roles: List[str] = Field(default_factory=list, description="User roles")

            class UserOutput(BaseModel):
                """User response model"""

                id: int = Field(..., description="Unique user ID")
                name: str = Field(..., description="User's full name")
                email: str = Field(..., description="User's email")
                created_at: str = Field(..., description="ISO timestamp of creation")

            def create_user(user_data: UserInput) -> UserOutput:
                """Create a new user account

                This endpoint creates a new user with the provided data.
                Validates email uniqueness and role permissions.
                """
                pass

            def update_user(user_id: int, user_data: UserInput) -> UserOutput:
                """Update existing user

                Updates user information. Email changes require verification.
                """
                pass

        with allure.step("When I view documentation"):
            from runpycli import Runpy

            cli = Runpy()
            cli.register(create_user)
            cli.register(update_user)

            runner = CliRunner()
            # First check general docs shows commands
            general_result = runner.invoke(cli.app, ["docs"])
            # Then check specific command docs for BaseModel details
            specific_result = runner.invoke(cli.app, ["docs", "create-user"])

        with allure.step("Then BaseModel schemas are shown in Components section"):
            # General docs should show command tree
            assert general_result.exit_code == 0
            assert "create-user" in general_result.output
            assert "Create a new user account" in general_result.output

            # Specific command docs should show Components section
            assert specific_result.exit_code == 0
            assert (
                "Components" in specific_result.output
                or "Models" in specific_result.output
            )

            # UserInput model details
            assert "UserInput" in specific_result.output
            assert "User creation input model" in specific_result.output
            assert (
                "name" in specific_result.output
                and "str, required" in specific_result.output
                and "User's full name" in specific_result.output
            )
            assert (
                "email" in specific_result.output
                and "str, required" in specific_result.output
                and "Valid email address" in specific_result.output
            )
            assert (
                "age" in specific_result.output
                and "optional" in specific_result.output
                and "User's age" in specific_result.output
            )
            assert (
                "roles" in specific_result.output
                and "optional" in specific_result.output
                and "User roles" in specific_result.output
            )

            # UserOutput model details
            assert "UserOutput" in specific_result.output
            assert "User response model" in specific_result.output
            assert (
                "id" in specific_result.output
                and "int, required" in specific_result.output
                and "Unique user ID" in specific_result.output
            )

    @allure.story("Nested BaseModel structures")
    @allure.title(
        "Given nested models, When generating docs, Then shows full hierarchy"
    )
    def test_nested_basemodel_documentation(self):
        with allure.step("Given nested BaseModel structures"):

            class Address(BaseModel):
                """Physical address"""

                street: str = Field(..., description="Street address")
                city: str = Field(..., description="City name")
                country: str = Field(..., description="Country code")
                postal_code: Optional[str] = Field(None, description="Postal/ZIP code")

            class ContactInfo(BaseModel):
                """Contact information"""

                email: str = Field(..., description="Primary email")
                phone: Optional[str] = Field(None, description="Phone number")
                address: Optional[Address] = Field(None, description="Physical address")

            class Organization(BaseModel):
                """Organization details"""

                name: str = Field(..., description="Organization name")
                contact: ContactInfo = Field(..., description="Primary contact")
                billing_address: Optional[Address] = Field(
                    None, description="Billing address"
                )

            def create_organization(org: Organization) -> dict:
                """Create a new organization

                Creates organization with full contact and address information.
                """
                pass

        with allure.step("When I request detailed docs"):
            from runpycli import Runpy

            cli = Runpy()
            cli.register(create_organization)

            runner = CliRunner()
            result = runner.invoke(cli.app, ["create-organization", "--help"])

        with allure.step("Then nested model structure is clear"):
            assert result.exit_code == 0

            # Command help shows parameter
            assert "--org Organization" in result.output

            # Models section shows hierarchy
            assert "Models:" in result.output

            # Organization model
            assert "Organization:" in result.output
            assert "Organization details" in result.output
            assert "- name (str, required): Organization name" in result.output
            assert "- contact (ContactInfo, required): Primary contact" in result.output
            assert (
                "- billing_address (Optional[Address], optional): Billing address"
                in result.output
            )

            # ContactInfo model (nested)
            assert "ContactInfo:" in result.output
            assert "Contact information" in result.output
            assert "- email (str, required): Primary email" in result.output
            assert "- phone (Optional[str], optional): Phone number" in result.output
            assert (
                "- address (Optional[Address], optional): Physical address"
                in result.output
            )

            # Address model (double nested)
            assert "Address:" in result.output
            assert "Physical address" in result.output
            assert "- street (str, required): Street address" in result.output
            assert "- city (str, required): City name" in result.output
            assert "- country (str, required): Country code" in result.output
            assert (
                "- postal_code (Optional[str], optional): Postal/ZIP code"
                in result.output
            )

    @allure.story("BaseModel with validation rules")
    @allure.title(
        "Given models with validators, When showing docs, Then includes constraints"
    )
    def test_basemodel_validation_documentation(self):
        with allure.step("Given BaseModel with validation"):
            from pydantic import validator
            from datetime import date

            class ProjectInput(BaseModel):
                """Project creation model"""

                name: str = Field(
                    ..., min_length=3, max_length=50, description="Project name"
                )
                budget: float = Field(
                    ..., gt=0, le=1000000, description="Budget in USD"
                )
                start_date: date = Field(..., description="Project start date")
                end_date: date = Field(..., description="Project end date")
                priority: int = Field(..., ge=1, le=5, description="Priority level")
                tags: List[str] = Field(..., max_length=10, description="Project tags")

                @validator("end_date")
                def end_after_start(cls, v, values):
                    """End date must be after start date"""
                    if "start_date" in values and v <= values["start_date"]:
                        raise ValueError("end_date must be after start_date")
                    return v

                @validator("name")
                def name_alphanumeric(cls, v):
                    """Name must be alphanumeric with spaces"""
                    if not v.replace(" ", "").isalnum():
                        raise ValueError(
                            "Name must contain only letters, numbers, and spaces"
                        )
                    return v

            def create_project(project: ProjectInput) -> dict:
                """Create a new project with validation"""
                pass

        with allure.step("When I view model documentation"):
            from runpycli import Runpy

            cli = Runpy()
            cli.register(create_project)

            runner = CliRunner()
            result = runner.invoke(cli.app, ["create-project", "--help"])

        with allure.step("Then validation rules are included"):
            assert result.exit_code == 0

            # Models section
            assert "Models:" in result.output
            assert "ProjectInput:" in result.output
            assert "Project creation model" in result.output

            # Field constraints in the format: - field_name (type, required/optional): description [constraints]
            assert (
                "- name (str, required): Project name [min length: 3, max length: 50]"
                in result.output
            )
            assert (
                "- budget (float, required): Budget in USD [> 0, <= 1000000]"
                in result.output
            )
            assert "- start_date (date, required): Project start date" in result.output
            assert "- end_date (date, required): Project end date" in result.output
            assert (
                "- priority (int, required): Priority level [>= 1, <= 5]"
                in result.output
            )
            assert (
                "- tags (list[str], required): Project tags [max length: 10]"
                in result.output
            )

            # Note: Custom validators are not currently displayed in the help
            # This is a limitation we should document or implement later

    @allure.story("BaseModel as input and output")
    @allure.title(
        "Given function with BaseModel input/output, When calling, Then handles properly"
    )
    def test_basemodel_input_output(self):
        with allure.step("Given function with Pydantic models for input and output"):
            from typing import Literal

            class TaskInput(BaseModel):
                """Task creation input"""

                title: str = Field(
                    ..., min_length=1, max_length=100, description="Task title"
                )
                description: Optional[str] = Field(
                    None, description="Detailed description"
                )
                priority: Literal["low", "medium", "high"] = Field(
                    "medium", description="Task priority"
                )
                assigned_to: Optional[str] = Field(
                    None, description="Assignee username"
                )
                tags: List[str] = Field(default_factory=list, description="Task tags")

            class TaskOutput(BaseModel):
                """Task response model"""

                id: int = Field(..., description="Task ID")
                title: str = Field(..., description="Task title")
                description: Optional[str] = Field(None, description="Task description")
                priority: Literal["low", "medium", "high"] = Field(
                    ..., description="Task priority"
                )
                status: Literal["pending", "in_progress", "completed"] = Field(
                    "pending", description="Task status"
                )
                assigned_to: Optional[str] = Field(None, description="Assignee")
                created_at: str = Field(..., description="Creation timestamp")
                updated_at: str = Field(..., description="Last update timestamp")

            def create_task(task: TaskInput) -> TaskOutput:
                """Create a new task and return the created task details"""
                pass

            def get_task(task_id: int) -> TaskOutput:
                """Retrieve a task by ID"""
                pass

            def list_tasks(
                status: Optional[Literal["pending", "in_progress", "completed"]] = None,
                priority: Optional[Literal["low", "medium", "high"]] = None,
                limit: int = 10,
            ) -> List[TaskOutput]:
                """List tasks with optional filters"""
                pass

        with allure.step("When I register and use these functions"):
            from runpycli import Runpy

            cli = Runpy("taskmanager")
            cli.register(create_task)
            cli.register(get_task)
            cli.register(list_tasks)

            runner = CliRunner()

            # Test schema generation
            schema_result = runner.invoke(cli.app, ["schema"])

            # Test help for BaseModel input
            help_result = runner.invoke(cli.app, ["create-task", "--help"])

        with allure.step("Then BaseModel handling works correctly"):
            # Schema should show proper types
            assert schema_result.exit_code == 0
            schema = json.loads(schema_result.output)

            # Check create_task command
            create_params = schema["commands"]["create-task"]["parameters"]
            assert "task" in create_params
            assert (
                create_params["task"]["type"] == "basemodel"
                or create_params["task"]["type"] == "object"
            )

            # Help should show how to use BaseModel input
            assert help_result.exit_code == 0
            assert "--task" in help_result.output or "JSON" in help_result.output
