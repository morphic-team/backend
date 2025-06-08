# Field Validation and Completion Logic Documentation

## Overview

This document explores the conceptual design for field validation and completion states within Morphic's research-oriented survey system. The current implementation uses binary completion states that have been validated through academic research.

## Current Completion State Model

### Existing Implementation (Research Validated)

**Completion States:**
- `incomplete`: Default state, data collection in progress
- `complete`: Researcher finished gathering information about this image
- `revisit`: Researcher wants to return to this result later

**Important:** `complete` means "I'm done gathering information about this image" **not** "I've gathered all the required information about this image."

### Academic Research Context

The current binary completion system has been:
- Used in published academic studies
- Validated through research findings
- Proven effective for research workflows
- Essential for reproducibility of published results

**Preservation Requirement:** The existing completion logic must remain unchanged to maintain academic integrity and research reproducibility.

## Conceptual Field Validation Framework

### Problem Statement

Research scenarios often have different validation requirements:

1. **System Required Fields**: Essential for data integrity (image details, IDs)
2. **Research Required Fields**: Needed for specific study completeness
3. **Optional Enrichment Fields**: Valuable but not essential

The current binary model doesn't distinguish between these validation levels.

### Proposed Conceptual Model

#### Field-Level Requirements

```python
class SurveyField(db.Model, Entity):
    # Existing fields...
    validation_level = Column(String)  # 'system', 'study', 'optional'
    is_required_for_completion = Column(Boolean, default=False)
```

**Validation Levels:**
- `system`: Required for basic data integrity (e.g., image ID, timestamp)
- `study`: Required for this specific research study to be considered complete
- `optional`: Enrichment data that adds value but isn't essential

#### Enhanced Completion States

**Proposed States:**
- `incomplete`: Default state, data collection in progress
- `study_complete`: All study-required fields have been filled
- `validated_complete`: Study complete + additional validation checks passed
- `abandoned`: Researcher decided this result isn't viable for the study
- `revisit`: Researcher wants to return to this result later

#### Completion Logic Framework

```python
def calculate_completion_state(search_result, survey_fields):
    """
    Conceptual completion state calculation.
    
    Note: This is a design exploration only.
    Current implementation must remain unchanged.
    """
    system_fields = [f for f in survey_fields if f.validation_level == 'system']
    study_fields = [f for f in survey_fields if f.validation_level == 'study']
    
    # Check system requirements
    if not all_fields_populated(search_result, system_fields):
        return 'incomplete'
    
    # Check study requirements  
    if not all_fields_populated(search_result, study_fields):
        return 'incomplete'
    
    # Manual override states
    if manually_marked_abandoned(search_result):
        return 'abandoned'
    
    if manually_marked_revisit(search_result):
        return 'revisit'
    
    # Study completion achieved
    return 'study_complete'

def all_fields_populated(search_result, required_fields):
    """Check if all required fields have non-empty values."""
    result_field_values = get_field_values(search_result)
    
    for field in required_fields:
        value = result_field_values.get(field.label)
        if not value or value.strip() == '':
            return False
    
    return True
```

### User Experience Implications

#### Visual Indicators

**Field-Level Indicators:**
- 🔴 System required (always enforced)
- 🟡 Study required (needed for completion)
- ⚪ Optional (enrichment data)

**Result-Level Status:**
- 📝 Incomplete (missing required fields)
- ✅ Study Complete (all requirements met)
- 🚫 Abandoned (researcher decision)
- ⏰ Revisit Later (researcher decision)

#### Workflow Enhancements

**Progressive Disclosure:**
1. Show system required fields first
2. Reveal study required fields as system fields are completed
3. Optional fields available but clearly marked as enrichment

**Validation Feedback:**
- Real-time indication of completion progress
- Clear messaging about what's needed vs. what's optional
- Researcher can override completion state based on judgment

## Implementation Considerations

### Database Schema Changes

**New Columns Needed:**
```sql
-- Add to survey_fields table
ALTER TABLE survey_fields ADD COLUMN validation_level VARCHAR DEFAULT 'optional';
ALTER TABLE survey_fields ADD COLUMN is_required_for_completion BOOLEAN DEFAULT FALSE;

-- Index for performance
CREATE INDEX idx_survey_fields_validation ON survey_fields(validation_level);
```

**Migration Strategy:**
1. Add columns with safe defaults
2. Populate based on field analysis or researcher input
3. Update application logic gradually
4. Maintain backward compatibility

### API Changes

**Enhanced Field Schema:**
```json
{
  "id": 1,
  "label": "Species Name",
  "fieldType": "text",
  "validationLevel": "study",
  "isRequiredForCompletion": true,
  "options": []
}
```

**Completion State Calculation:**
```python
# New endpoint: GET /api/search-results/{id}/completion-status
{
  "completionState": "study_complete",
  "systemFieldsComplete": true,
  "studyFieldsComplete": true,
  "missingRequiredFields": [],
  "canMarkComplete": true
}
```

### Frontend Integration

**Form Enhancements:**
- Progressive validation indicators
- Required field highlighting
- Completion progress tracking
- Override buttons for researcher judgment

**List View Updates:**
- Enhanced status badges
- Filtering by completion level
- Progress indicators for studies

## Research Impact Analysis

### Benefits of Enhanced Model

1. **Clearer Research Protocols**: Distinguish between different validation needs
2. **Improved Data Quality**: Systematic tracking of required vs. optional data
3. **Better User Experience**: Clear expectations about field requirements
4. **Flexible Study Design**: Different studies can have different requirements

### Risks and Mitigations

**Risk: Breaking Academic Reproducibility**
- **Mitigation**: Implement as additive feature, preserve existing completion logic
- **Migration Path**: New studies opt-in, existing studies unchanged

**Risk: Increased Complexity**
- **Mitigation**: Default to current behavior, enhanced features optional
- **User Training**: Clear documentation of when to use enhanced validation

**Risk: Performance Impact**
- **Mitigation**: Efficient completion state calculation, proper indexing
- **Caching**: Cache completion states for frequently accessed results

## Future Research Applications

### Study-Specific Validation Rules

Different research projects could define their own validation frameworks:

**Example: Behavioral Study**
- System: Image ID, timestamp, search query
- Study: Species identification, behavior category
- Optional: Weather conditions, geographic details

**Example: Comparative Analysis**
- System: Image ID, timestamp
- Study: Rating scale, comparison category
- Optional: Detailed notes, secondary classifications

### Advanced Validation Rules

**Conditional Requirements:**
```python
# If species == "bird", then behavior_type is required
# If location is provided, then coordinates are required
```

**Cross-Field Validation:**
```python
# Consistency checks between related fields
# Date ranges, geographic boundaries, categorical relationships
```

## Implementation Roadmap (Conceptual)

### Phase 1: Foundation
- [ ] Add validation_level and is_required_for_completion columns
- [ ] Migrate existing surveys with conservative defaults
- [ ] Update marshallers to include new fields

### Phase 2: Backend Logic
- [ ] Implement completion state calculation
- [ ] Add API endpoints for validation status
- [ ] Create migration tools for study configuration

### Phase 3: Frontend Integration
- [ ] Enhanced form validation indicators
- [ ] Completion progress tracking
- [ ] Study configuration interface

### Phase 4: Advanced Features
- [ ] Conditional validation rules
- [ ] Cross-field validation
- [ ] Study-specific validation templates

## Conclusion

The proposed field validation framework would enhance Morphic's research capabilities while preserving the academic integrity of the current system. The key principle is **additive enhancement** - new features that don't disrupt existing validated workflows.

**Critical Requirement:** Any implementation must maintain backward compatibility with existing completion states and research methodologies. The current binary completion system has proven academic value and must be preserved.

This framework provides a foundation for more sophisticated research validation needs while respecting the validated nature of the current implementation.

---

**Status:** Conceptual design document  
**Implementation:** Not approved - requires research validation  
**Current System:** Must remain unchanged for academic reproducibility  
**Last Updated:** 2025-06-08