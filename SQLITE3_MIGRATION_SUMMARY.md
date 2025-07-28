# Migration from SQLAlchemy to sqlite3 for SpatiaLite Processing

## Overview
This document summarizes the changes made to migrate from SQLAlchemy to Python's default sqlite3 library for processing SpatiaLite files.

## Key Changes

### 1. Import Changes
- Added `import sqlite3` to the imports in `app.py`
- Removed dependency on SQLAlchemy's engine for SpatiaLite file processing

### 2. Connection Method
**Before (SQLAlchemy):**
```python
spatialite_engine = create_engine(f"sqlite:///{tmp_file.name}")
with spatialite_engine.connect() as conn:
    result = conn.execute(text("SELECT ..."))
```

**After (sqlite3):**
```python
conn = sqlite3.connect(tmp_file.name)
conn.row_factory = sqlite3.Row  # Enables column access by name
cursor = conn.cursor()
cursor.execute("SELECT ...")
```

### 3. Query Execution
**Before (SQLAlchemy):**
```python
query = text(f"SELECT ... FROM {table_name}")
result = conn.execute(query)
for row in result:
    row_dict = dict(row._mapping)
```

**After (sqlite3):**
```python
query = f"SELECT ... FROM {table_name}"
cursor.execute(query)
for row in cursor:
    row_dict = dict(row)
```

### 4. Extension Loading
**Before (SQLAlchemy):**
```python
conn.execute(text(f"SELECT load_extension('{ext_path}')"))
```

**After (sqlite3):**
```python
conn.enable_load_extension(True)
cursor.execute(f"SELECT load_extension('{ext_path}')")
```

### 5. Connection Cleanup
**After (sqlite3):**
Added explicit connection cleanup:
```python
conn.close()
```

## Benefits of Using sqlite3

1. **No External Dependencies**: sqlite3 is part of Python's standard library
2. **Simpler Code**: Direct SQL execution without ORM abstractions
3. **Better Control**: More explicit control over database connections and cursors
4. **Performance**: Potentially better performance for simple read operations
5. **Compatibility**: Works with any Python installation without additional packages

## Demo Script
A demo script (`demo_sqlite3_spatialite.py`) has been created to demonstrate:
- Creating a sample SQLite database with geometry data
- Processing the database using sqlite3
- Handling both regular SQLite and SpatiaLite databases
- Loading SpatiaLite extensions when available
- Parsing GeoJSON geometry data

## Testing
The implementation has been tested with:
- Regular SQLite databases storing geometry as GeoJSON strings
- Fallback handling when SpatiaLite extensions are not available
- Proper row-to-dictionary conversion using `sqlite3.Row`

## Notes
- The main application still uses SQLAlchemy for its primary database operations (storing key-value pairs)
- Only the SpatiaLite file import functionality has been migrated to use sqlite3
- The API interface remains unchanged, ensuring backward compatibility