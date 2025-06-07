# Data Model Documentation

## Overview

The Morphic backend uses a multi-table structure to manage user surveys, search operations, and results collection.

## Core Model Structure

```
User → Survey → Search → SearchResult
     ↓         ↓                ↓
  Session   SurveyField     Tag/ResultField
```

## Diamond Dependency Issue

### Problem Description

The data model contains a "diamond dependency" pattern that allows modeling of theoretically invalid states:

```
Survey
├─→ Search ─→ SearchResult ─→ ResultField
└─→ SurveyField ←──────────────────────┘
```

A `ResultField` references both:
- A `SearchResult` (which belongs to Survey A via Search)
- A `SurveyField` (which belongs to Survey B)

**The issue:** There's no inherent constraint ensuring Survey A == Survey B.

### Theoretical Invalid State Example

```sql
-- Survey 1 has a field "Name"
INSERT INTO surveys (id, name) VALUES (1, 'User Feedback');
INSERT INTO survey_fields (id, survey_id, label) VALUES (1, 1, 'Name');

-- Survey 2 has a search with results  
INSERT INTO surveys (id, name) VALUES (2, 'Product Research');
INSERT INTO searches (id, survey_id, name) VALUES (1, 2, 'Search A');
INSERT INTO search_results (id, search_id) VALUES (1, 1);

-- INVALID: ResultField links Survey 2 result to Survey 1 field
INSERT INTO result_fields (search_result_id, survey_field_id, value) 
VALUES (1, 1, 'John Doe');
```

### Current Status: Unresolved

**The Problem:** No database-level constraint can prevent this invalid state.

- **CHECK constraints:** PostgreSQL doesn't allow subqueries in CHECK constraints
- **Triggers:** Would work but add complexity for a theoretical issue
- **Denormalization:** Could add survey_id to result_fields but changes the model significantly

**Current Approach:** Be careful + documentation

1. **Application Logic:** Always create ResultFields through proper survey context
2. **Code Reviews:** Watch for incorrect cross-survey field assignments  
3. **Documentation:** This file documents the issue
4. **Testing:** Write tests that verify correct survey associations

**Recommendation:** The theoretical nature of this issue doesn't justify complex database triggers or model restructuring at this time. The application logic naturally creates ResultFields in the correct context, making invalid states unlikely in practice.

## Model Relationships

### User ↔ Survey
- **One-to-Many:** A user can have multiple surveys
- **Bidirectional:** `User.surveys` ↔ `Survey.user`

### Survey ↔ Search
- **One-to-Many:** A survey can have multiple searches
- **Bidirectional:** `Survey.searches` ↔ `Search.survey`

### Search ↔ SearchResult  
- **One-to-Many:** A search can have multiple results
- **Bidirectional:** `Search.results` ↔ `SearchResult.search`

### Survey ↔ SurveyField
- **One-to-Many:** A survey defines multiple fields
- **Bidirectional:** `Survey.fields` ↔ `SurveyField.survey`

### SearchResult ↔ ResultField
- **One-to-Many:** A result can have multiple field values
- **Bidirectional:** `SearchResult.result_fields` ↔ `ResultField.search_result`

### SurveyField ↔ ResultField  
- **One-to-Many:** A field definition can have multiple value instances
- **Bidirectional:** `SurveyField.result_fields` ↔ `ResultField.survey_field`

### SearchResult ↔ Tag
- **One-to-Many:** A result can have multiple tags
- **Bidirectional:** `SearchResult.tags` ↔ `Tag.search_result`

## Removed Relationships

### Historical Context
Previously, the model included convenience relationships that created circular dependencies:

- `User.searches` - Indirect access to searches through surveys
- `Survey.search_results` - Indirect access using `secondary='searches'`

These were removed in favor of explicit SQLAlchemy queries for better performance and clarity.

### Accessing Data Across Relationships

Instead of convenience relationships, use explicit joins:

```python
# Get all search results for a survey
search_results = (
    SearchResult.query
    .join(Search)
    .filter(Search.survey_id == survey_id)
    .all()
)

# Get all searches for a user
user_searches = (
    Search.query
    .join(Survey)
    .filter(Survey.user_id == user_id)
    .all()
)
```

## Design Principles

1. **Explicit over Implicit:** Use clear SQLAlchemy queries rather than hidden convenience relationships
2. **Performance Conscious:** Control exactly what data gets loaded with explicit `joinedload()`
3. **Referential Integrity:** Database constraints prevent invalid states where possible
4. **Bidirectional Relationships:** All relationships use `back_populates` for clarity

## Future Considerations

- Consider migrating to a proper IdP for authentication
- The diamond dependency could be resolved by denormalizing or restructuring, but current constraint approach is sufficient for the application's needs
- Session management may need optimization for scale (consider JWT/Redis)