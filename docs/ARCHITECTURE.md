# Architecture Documentation

## Important Notice: Academic Research System

**This system has been validated through academic study and published research. The current implementation should be preserved exactly as-is for reproducibility purposes. Any architectural changes, even improvements, could potentially invalidate published results.**

This document serves as architectural analysis for future reference only.

## System Overview

Morphic is a research platform for conducting structured surveys on search engine results. The architecture was designed circa 2013-2014 using patterns common to that era.

## Current Architecture Decisions

### Entity-Attribute-Value (EAV) Pattern

**Implementation:**
- `SurveyField` table: Defines field schema (label, type, options)
- `ResultField` table: Stores field values (always as strings)
- Connected via foreign keys: `SearchResult → ResultField → SurveyField`

**Historical Context:**
This pattern was chosen when:
- PostgreSQL JSONB didn't exist (introduced in 9.4, 2014)
- Dynamic schemas required EAV or XML approaches
- NoSQL was less mature and pg_json was limited

**Current Characteristics:**
- ✅ Flexible: Can add new field types without schema changes
- ✅ Validated: System has proven academic research value
- ⚠️ Complex queries: Requires multiple joins for field access
- ⚠️ Type safety: All values stored as strings regardless of `field_type`
- ⚠️ Performance: Not optimized for filtering/aggregation on field values

### Data Flow Architecture

```
User
├── Survey (research study definition)
│   ├── SurveyField (field schema: name, email, rating, etc.)
│   └── Search (search query execution)
│       └── SearchResult (individual result from search)
│           ├── ResultField (field values for this result)
│           ├── Tag (auto-generated filterable tags)
│           └── Image (scraped screenshot)
```

### Current Query Patterns

**Getting search result with field data:**
```sql
SELECT sr.*, rf.value, sf.label, sf.field_type
FROM search_results sr
JOIN result_fields rf ON rf.search_result_id = sr.id_
JOIN survey_fields sf ON sf.id_ = rf.survey_field_id
WHERE sr.id_ = ?
```

**Filtering results by field value:**
```sql
SELECT sr.*
FROM search_results sr
JOIN result_fields rf ON rf.search_result_id = sr.id_
JOIN survey_fields sf ON sf.id_ = rf.survey_field_id
WHERE sf.label = 'rating' AND rf.value = '5'
```

## Type System Characteristics

### Current Implementation

**SurveyField.field_type** (stored but not enforced):
- `text`: Free text input
- `number`: Numeric input (stored as string)
- `select`: Dropdown options (options stored as JSON string)
- `location`: Geographic coordinates (stored as JSON-in-string)

**Type Handling:**
- All values stored as `VARCHAR` in `ResultField.value`
- Type conversion happens at application layer
- Location data: `JSON.parse(string_value)` in application
- Options data: `JSON.parse(survey_field.options)` in API

### Academic Validation

The current type system has been used to collect and analyze research data. Published results depend on:
- Consistent string-based storage
- Specific JSON parsing behavior for locations
- Current tag generation algorithm
- Existing CSV export format

## Performance Characteristics

### Current Bottlenecks (Documented for Reference)

1. **Field Value Queries**: Require 3-table joins
2. **Survey Export**: Nested loops over result_fields
3. **Tag Generation**: Recreated on every result update
4. **Location Data**: Double-parsed JSON strings

### Current Mitigations

- Strategic use of SQLAlchemy `joinedload()` 
- Pagination on result lists
- CSV streaming for large exports
- Query optimization in critical paths

## Integration Points

### Chrome Extension
- Sends search results via POST to `/api/searches/{id}/results`
- Requires specific JSON format matching current schema

### Frontend (Angular)
- Expects current REST API contract
- Form builders depend on `SurveyField.field_type` enumeration
- Export functionality expects CSV format as implemented

### Background Processing
- Image scraping relies on current `SearchResult.image_scraped_state` workflow
- Tag generation algorithm integrated into result updates

## Future Considerations (Post-Research)

**Note: These are documented for future reference only. Current system should remain unchanged for academic integrity.**

### PostgreSQL JSONB Migration Path
```sql
-- Hypothetical future migration (DO NOT IMPLEMENT)
ALTER TABLE search_results ADD COLUMN field_data JSONB;
-- Migrate: INSERT field_data = json_object(label: value, ...)
-- Benefits: Simpler queries, proper indexing, type safety
```

### Modern Alternatives
- **JSONB columns**: Native PostgreSQL JSON with GIN indexing
- **Schema registry**: Versioned survey schemas with typed validation
- **Hybrid approach**: Common fields as columns, dynamic fields as JSON

### Performance Improvements
- **Materialized views**: Pre-computed field value queries
- **Denormalization**: Survey-scoped caching tables
- **Async processing**: Background tag generation

## Conclusion

The current architecture serves its purpose as a validated research system. While modern approaches might offer performance and maintainability benefits, the academic value of preserving the exact implementation that generated published results takes precedence.

This documentation preserves institutional knowledge about architectural decisions and provides a foundation for potential future iterations of the research platform.

---

**Last Updated:** 2025-06-08  
**System Version:** Validated research implementation  
**Status:** Preserved for academic reproducibility