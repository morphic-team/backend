# Entity-Attribute-Value Pattern Implementation

## Overview

Morphic implements a classic Entity-Attribute-Value (EAV) pattern for handling dynamic survey fields. This document details the implementation, trade-offs, and characteristics of this approach.

## EAV Components

### Entity: SearchResult
The "entity" in our EAV model - represents one search result that will have field values collected.

```python
class SearchResult(db.Model, Entity):
    search_id = Column(Integer, ForeignKey('searches.id_'))
    visible_link = Column(String)
    direct_link = Column(String)
    completion_state = Column(String)
```

### Attribute Definition: SurveyField
Defines the schema/metadata for each attribute that can be collected.

```python
class SurveyField(db.Model, Entity):
    survey_id = Column(Integer, ForeignKey('surveys.id_'))
    label = Column(String)           # Human-readable field name
    field_type = Column(String)      # 'text', 'number', 'select', 'location'
    options = Column(String)         # JSON string for select options
```

### Value Storage: ResultField
Stores the actual values, always as strings regardless of type.

```python
class ResultField(db.Model, Entity):
    search_result_id = Column(Integer, ForeignKey('search_results.id_'))
    survey_field_id = Column(Integer, ForeignKey('survey_fields.id_'))
    value = Column(String)           # All values stored as strings
```

## Implementation Characteristics

### Type Handling

**Current Approach:**
- All values stored as `VARCHAR` regardless of actual type
- Type information in `SurveyField.field_type` (not enforced)
- Application-layer type conversion when needed

**Examples:**
```python
# Number field
field_type = "number"
value = "42"                    # Stored as string

# Location field  
field_type = "location"
value = '{"latitude": 40.7, "longitude": -74.0}'  # JSON-in-string

# Select field
field_type = "select"
options = '["Good", "Average", "Poor"]'            # JSON string
value = "Good"                                     # Selected option
```

### Query Patterns

**Retrieving field data for a search result:**
```python
# ORM approach (current)
result_fields = (
    ResultField.query
    .filter(ResultField.search_result_id == result_id)
    .options(joinedload(ResultField.survey_field))
    .all()
)

field_values = {
    rf.survey_field.label: rf.value 
    for rf in result_fields
}
```

**SQL equivalent:**
```sql
SELECT sf.label, rf.value, sf.field_type
FROM result_fields rf
JOIN survey_fields sf ON sf.id_ = rf.survey_field_id  
WHERE rf.search_result_id = ?
```

**Filtering by field values:**
```python
# Find all results with rating = "5"
results = (
    SearchResult.query
    .join(ResultField)
    .join(SurveyField)
    .filter(SurveyField.label == 'rating')
    .filter(ResultField.value == '5')
    .all()
)
```

## Academic Research Context

### Data Collection Workflow

1. **Survey Design**: Researchers define `SurveyField` records
2. **Search Execution**: `Search` records created for queries
3. **Result Collection**: Chrome extension populates `SearchResult` records
4. **Field Data Entry**: Researchers fill `ResultField` values through web interface
5. **Analysis**: Data exported as CSV for statistical analysis

### Published Research Dependencies

The current EAV implementation has been used in academic studies. Key dependencies:

- **CSV Export Format**: Field labels as column headers, values as strings
- **Location Data Format**: Specific JSON structure for geographic coordinates
- **Tag Generation**: Auto-generated tags from field values for filtering
- **Type Conversion**: Consistent string-to-type parsing in application layer

## Trade-offs Analysis

### Benefits of Current EAV Approach

1. **Schema Flexibility**: Can add new field types without database migrations
2. **Research Adaptability**: Surveys can have completely different field sets
3. **Historical Compatibility**: Works with surveys designed over many years
4. **Academic Validation**: System has proven research value with published results

### Costs of EAV Pattern

1. **Query Complexity**: Simple field access requires 3-table joins
2. **Performance Impact**: No efficient indexing on dynamic field values
3. **Type Safety**: No database-level type validation or constraints
4. **Maintenance Overhead**: Complex ORM relationships and marshalling

### Performance Characteristics

**Query Performance:**
- ✅ Single result field lookup: Fast with proper joins
- ⚠️ Filtering by field values: Expensive, requires full table scans
- ❌ Aggregating field values: Very expensive, limited by string storage
- ❌ Cross-survey field analysis: Complex multi-join queries

**Storage Efficiency:**
- ⚠️ String storage for all types: Some space overhead for numbers
- ⚠️ JSON-in-string: Double encoding for complex types
- ✅ Sparse data: Only stores fields that have values

## Alternative Patterns (Historical Context)

### Why EAV Was Chosen (Circa 2013-2014)

**Available Options at the Time:**
1. **Fixed Schema**: Too rigid for research flexibility
2. **XML Storage**: Limited query capabilities in PostgreSQL 9.x
3. **JSON**: Limited support in PostgreSQL < 9.4
4. **EAV**: Well-understood pattern with ORM support

**Decision Factors:**
- PostgreSQL JSONB didn't exist yet (introduced 9.4, late 2014)
- SQLAlchemy had mature support for EAV relationships
- Research requirements demanded maximum flexibility
- Performance was acceptable for expected data volumes

### Modern Alternatives (For Future Reference)

**PostgreSQL JSONB (Post-9.4):**
```sql
-- Hypothetical modern approach
CREATE TABLE search_results (
    id SERIAL PRIMARY KEY,
    search_id INTEGER REFERENCES searches(id),
    field_data JSONB  -- All dynamic fields in single column
);

CREATE INDEX ON search_results USING GIN(field_data);

-- Simple queries become:
SELECT * FROM search_results 
WHERE field_data->>'rating' = '5';
```

**Benefits:**
- Single-table queries for field access
- GIN indexing for efficient filtering
- Proper type storage (numbers as numbers)
- JSON path queries for complex data

**Trade-offs:**
- Requires PostgreSQL 9.4+
- Different data migration complexity
- Would change research reproducibility

## Implementation Guidelines

### Current Best Practices

1. **Always use `joinedload()`** when accessing field relationships:
   ```python
   .options(joinedload(ResultField.survey_field))
   ```

2. **Type conversion at application boundary:**
   ```python
   if field.field_type == 'number':
       return int(result_field.value)
   elif field.field_type == 'location':
       return json.loads(result_field.value)
   ```

3. **Batch field operations** to minimize N+1 queries

4. **Use strategic denormalization** (like tag generation) for performance

### Academic Preservation

**Do NOT modify:**
- Field storage format (string-based)
- JSON parsing behavior for locations
- CSV export column ordering
- Tag generation algorithm

These elements are part of the validated research methodology.

## Conclusion

The EAV pattern serves Morphic's research requirements effectively. While modern PostgreSQL features might offer performance benefits, the academic validation of the current approach takes precedence over technical optimization.

This implementation represents a time-appropriate solution that has proven its research value through published studies.

---

**Historical Note:** This EAV implementation reflects the database technology landscape of 2013-2014 and the specific needs of academic research software.