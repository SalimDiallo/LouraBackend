# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django-based multi-tenant backend application for the "Loura" platform. The project uses Django 5.2.8 with Django REST Framework for building RESTful APIs that serve a Next.js frontend.

## Architecture

### Multi-Tenant Design

The application follows a **hierarchical multi-tenant architecture**:

#### Current Implementation (Phase 1)
1. **AdminUser** → Top-level supervisors who manage organizations
2. **Organization** → Multi-tenant organizations with unique subdomains
3. **OrganizationSettings** → Configuration per organization (currency, country, theme, etc.)
4. **Category** → Categorization system for organizations

Each organization is isolated and managed by a single AdminUser (owner), supporting multiple independent tenant workspaces.

#### Future Architecture (Phase 2 - Planned)

The system is designed to support a dual-authentication model:

1. **AdminUser** (current)
   - Creates and manages organizations
   - Full administrative access to their organizations
   - Authenticates via `/api/core/auth/` endpoints

2. **Employee** (to be implemented in `hr` app)
   - Belongs to a specific organization
   - Limited permissions based on roles
   - Authenticates via separate employee endpoints
   - Scoped to their organization's data only

**Key Design Considerations:**
- Use separate authentication endpoints for AdminUser vs Employee
- Implement role-based permissions for employees (to be defined)
- Ensure data isolation: employees can only access their organization's data
- Consider using different token types or scopes to distinguish user types
- Employee model should reference Organization via ForeignKey
- May inherit from `BaseProfile` in `lourabackend/models.py` for consistency

**Placeholder:** When implementing employees, add models to `hr/models.py` and create separate authentication views to avoid mixing admin and employee authentication flows.

### Base Models Pattern

The codebase uses an **abstract base model pattern** defined in `lourabackend/models.py`:

- **TimeStampedModel**: Provides UUID primary keys, automatic timestamps (`created_at`, `updated_at`), and soft-delete functionality (`deleted_at`)
- **BaseProfile**: Abstract user profile with authentication, extending `AbstractBaseUser` and `PermissionsMixin`

All models should inherit from these base classes to maintain consistency across the application.

### App Structure

- **lourabackend/**: Main Django project configuration
  - Contains `settings.py`, `urls.py`, and shared base models

- **core/**: Core business logic and organization management
  - Models: `AdminUser`, `Organization`, `OrganizationSettings`, `Category`
  - API endpoint: `/api/core/` (includes basic health check)

- **hr/**: Human resources module (in development)

- **auth/**: Authentication module (in development)

### Key Settings

- **Database**: SQLite (development) - located at `db.sqlite3`
- **CORS**: Configured for Next.js frontend at `http://localhost:3000`
- **Authentication**: JWT (JSON Web Tokens) with HTTP-only cookies
  - Access token lifetime: 15 minutes
  - Refresh token lifetime: 7 days
  - Token rotation and blacklist enabled
  - HTTP-only cookies for security (protects against XSS)
- **REST Framework**:
  - Authentication: JWTAuthentication
  - Default permission: AllowAny
  - CORS credentials enabled
- **Language**: French (`fr`) with timezone `Africa/Conakry`
- **Currency**: Default MAD (Moroccan Dirham)

## Development Commands

### Running the Server

```bash
python manage.py runserver
```

### Database Operations

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check for issues without making changes
python manage.py check

# View migration status
python manage.py showmigrations
```

### Django Shell

```bash
# Interactive Python shell with Django context
python manage.py shell
```

### Database Management

```bash
# Access database shell
python manage.py dbshell

# Dump data to JSON
python manage.py dumpdata [app_name] > data.json

# Load data from JSON
python manage.py loaddata data.json

# Reset database (flush all data)
python manage.py flush
```

### Admin/User Management

```bash
# Create superuser
python manage.py createsuperuser
```

### Testing

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test core
python manage.py test hr
python manage.py test auth
```

## Key Implementation Notes

### Soft Delete Pattern

Models inheriting from `TimeStampedModel` support soft deletion:

```python
# Soft delete (sets deleted_at timestamp)
instance.soft_delete()

# Restore soft-deleted record
instance.restore()

# Query non-deleted records
Model.objects.filter(deleted_at__isnull=True)
```

### Organization Context

When implementing features:
- Always consider the multi-tenant context
- Filter queries by organization where applicable
- Use the `admin` foreign key to identify the organization owner
- Access organization settings via `organization.settings` property

### URL Routing

- Main project URLs: `lourabackend/urls.py`
- App-specific URLs: Include patterns like `path('api/core/', include('core.urls'))`
- Admin interface: `/admin/`

### Database Schema

All custom tables use explicit `db_table` names:
- `admin_users`
- `organizations`
- `organization_settings`
- `categories`

## Adding New Features

1. Create or update models in the appropriate app
2. Inherit from `TimeStampedModel` or `BaseProfile` for consistency
3. Run `makemigrations` and `migrate`
4. Define serializers in `serializers.py` (if using DRF)
5. Create views in `views.py`
6. Register URL patterns in the app's `urls.py`
7. Write tests in `tests.py`

## Python Virtual Environment

The project uses a virtual environment located at `../venv/`. Activate it before running commands:

```bash
source ../venv/bin/activate  # Linux/Mac
# or
..\venv\Scripts\activate  # Windows
```
