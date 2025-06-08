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
            order=1
        ),
        SurveyField(
            label="Observation Location",
            field_type="location",
            order=2
        ),
        SurveyField(
            label="Behavior Observed",
            field_type="select",
            options='["Feeding", "Nesting", "Flying", "Resting", "Other"]',
            order=3
        ),
        SurveyField(
            label="Weather Conditions",
            field_type="radio",
            options='["Sunny", "Cloudy", "Rainy", "Windy"]',
            order=4
        ),
        SurveyField(
            label="Additional Notes",
            field_type="text",
            order=5
        )
    ]
    
    return survey