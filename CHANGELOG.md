# Changelog

All notable changes to the Morphic Backend API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-01-15

### Added
- **Enhanced JWT Security**: JWT tokens now include audience and issuer claims
  - Added `aud: 'morphic-browser-extension'` claim for token audience validation
  - Added `iss: 'morphic-api'` claim for token issuer validation
  - Extracted JWT constants to prevent magic strings and improve maintainability
  - Enhanced security for Chrome extension authentication workflow

### Changed
- **Image Processing**: Implemented best_python download strategy for improved reliability
  - Enhanced image downloading with better error handling
  - Improved success rates for image collection and processing
  - Production-ready download strategy deployment

### Fixed
- **Background Processing**: Enhanced Flask application context handling
  - Fixed context issues for worker threads in background processing
  - Improved stability of image processing operations
  - Better error handling in multi-threaded environments

### Developer Experience
- **Export Functionality**: Added `export_search_results.py` script for data extraction
  - Command-line tool for exporting survey results and search data
  - Improved data analysis and debugging capabilities

## [1.0.0] - 2025-01-11

### Initial Release

The baseline Morphic Backend API providing comprehensive survey and search management capabilities.

#### Core Features

**Survey Management**:
- Complete survey creation, editing, and management system
- Support for multiple field types: text, select, radio, location
- Survey preview and validation functionality
- User authentication and authorization

**Search System**:
- Google Images search integration via Chrome extension
- JWT-based secure upload tokens for search results
- Search result storage and management
- Pagination and filtering for large result sets

**Location Services**:
- Interactive location picker with Leaflet maps
- Nominatim geocoding integration (API-free)
- Click-to-place and drag-to-move marker functionality
- Address and coordinate search capabilities

**Data Export**:
- CSV export functionality for survey results
- Comprehensive data extraction with proper formatting
- Export includes survey responses, search results, and metadata

**Authentication & Security**:
- Session-based user authentication
- JWT token system for Chrome extension communication
- HMAC-SHA256 token signing with configurable expiration
- Cross-origin request handling and validation

#### API Endpoints

**Survey Operations**:
- `GET /api/surveys` - List user surveys
- `POST /api/surveys` - Create new survey
- `GET/PUT/DELETE /api/surveys/{id}` - Survey CRUD operations
- `GET /api/surveys/{id}/fields` - Survey field management

**Search Management**:
- `GET /api/surveys/{id}/searches` - List searches for survey
- `POST /api/surveys/{id}/searches` - Create new search
- `POST /api/searches/{id}/generate-upload-url` - Generate Chrome extension upload token
- `GET /api/surveys/{id}/search_results` - Retrieve search results with pagination

**Data Processing**:
- `POST /api/upload-google-results` - Chrome extension result upload endpoint
- `GET /api/surveys/{id}/export-results` - CSV export functionality
- `GET /api/surveys/{id}/tags` - Available filter tags

**User Management**:
- `POST /api/auth/signin` - User authentication
- `POST /api/auth/signup` - User registration
- `GET /api/auth/user` - Current user information

#### Technical Architecture

**Backend Stack**:
- Python 2.7 with Flask 0.10.1 web framework
- SQLAlchemy ORM for database operations
- PostgreSQL 9.6 database with comprehensive migrations
- JWT token handling for secure API access

**Chrome Extension Integration**:
- Secure token-based authentication for result uploads
- Google Images scraping coordination
- Real-time progress tracking and error handling

**Image Processing**:
- Background worker system for image downloading
- Perceptual hashing for duplicate detection
- Thumbnail generation and storage optimization
- Multi-threaded processing for performance

**Database Schema**:
- Users, surveys, fields, searches, and search_results tables
- Proper foreign key relationships and constraints
- Session management with secure token storage
- Comprehensive indexing for query performance

#### Deployment & Operations

**Docker Support**:
- Development and production Docker configurations
- Multi-service orchestration with docker-compose
- Separated frontend, backend, and database services
- Cloudflare tunnel integration for production

**Database Management**:
- Flask-Migrate for schema versioning
- Automated migration system
- Backup and restore capabilities
- Development fixture system

**Background Processing**:
- Dedicated worker processes for image operations
- Queue-based task management
- Error handling and retry logic
- Performance monitoring and logging

#### Development Tools

**CLI Management**:
- Flask-based management commands
- Database migration utilities
- Background worker control
- Development server configuration

**Testing & Quality**:
- Comprehensive test coverage
- Development fixture data
- API endpoint validation
- Error handling verification

#### Security Features

**Data Protection**:
- Input validation and sanitization
- SQL injection prevention via ORM
- XSS protection in API responses
- Secure session management

**Access Control**:
- User-based resource isolation
- API endpoint authentication requirements
- Token expiration and validation
- CORS policy enforcement

This release establishes the foundation for Morphic's survey and search management platform, providing a robust, scalable backend for research data collection and analysis.