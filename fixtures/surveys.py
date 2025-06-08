"""Mock survey data generators."""

from backend.models import Survey, SurveyField, User


def create_mock_survey(user: User) -> Survey:
    """Create a mock survey with fields for the given user."""
    survey = Survey(
        name="Mock Wildlife Survey",
        user=user
    )
    
    # Add survey fields
    survey.fields = [
        SurveyField(
            label="Species Name",
            field_type="text",
            # required=True,  # TODO: Add required field to SurveyField model
            # order=1  # TODO: Add order field to SurveyField model
        ),
        SurveyField(
            label="Observation Location",
            field_type="location",
            # required=True,  # TODO: Add required field to SurveyField model
            # order=2  # TODO: Add order field to SurveyField model
        ),
        SurveyField(
            label="Behavior Observed",
            field_type="select",
            options='["Feeding", "Nesting", "Flying", "Resting", "Other"]',
            # required=False,  # TODO: Add required field to SurveyField model
            # order=3  # TODO: Add order field to SurveyField model
        ),
        SurveyField(
            label="Weather Conditions",
            field_type="radio",
            options='["Sunny", "Cloudy", "Rainy", "Windy"]',
            # required=False,  # TODO: Add required field to SurveyField model
            # order=4  # TODO: Add order field to SurveyField model
        ),
        SurveyField(
            label="Additional Notes",
            field_type="text",
            # required=False,  # TODO: Add required field to SurveyField model
            # order=5  # TODO: Add order field to SurveyField model
        )
    ]
    
    return survey