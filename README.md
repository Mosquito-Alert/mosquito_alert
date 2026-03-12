# Mosquito Alert

[![CI status](https://github.com/Mosquito-Alert/mosquito_alert/actions/workflows/ci.yml/badge.svg)](https://github.com/Mosquito-Alert/mosquito_alert/actions/workflows/ci.yml)
[![Code coverage](https://img.shields.io/codecov/c/github/Mosquito-Alert/mosquito_alert/master.svg)](https://app.codecov.io/github/Mosquito-Alert/mosquito_alert?branch=master)
[![Django Version](https://img.shields.io/badge/django-4.2-green.svg)](https://www.djangoproject.com/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE.md)

In this repository there is the backend infrastructure powering the Mosquito Alert citizen science platform. It manages data collection, validation, and dissemination for mosquito surveillance reports submitted through mobile applications.

**Live Server**: [https://api.mosquitoalert.com/v1/](https://api.mosquitoalert.com/v1/) | [https://webserver.mosquitoalert.com](https://webserver.mosquitoalert.com)

**Project Website**: [https://mosquitoalert.com](https://mosquitoalert.com)

## 📋 Table of Contents

- [Mosquito Alert](#mosquito-alert)
  - [📋 Table of Contents](#-table-of-contents)
  - [🦟 About the Project](#-about-the-project)
  - [✨ Features](#-features)
  - [🚀 Getting Started](#-getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Configuration](#configuration)
  - [💻 Usage](#-usage)
    - [Running the Application](#running-the-application)
    - [Available Commands](#available-commands)
      - [SSL Support](#ssl-support)
  - [📚 API Documentation \& SDKs](#-api-documentation--sdks)
    - [API Documentation](#api-documentation)
    - [Official SDKs](#official-sdks)
  - [🧪 Testing](#-testing)
    - [Running Tests](#running-tests)
    - [Test Configuration](#test-configuration)
  - [🤝 Contributing](#-contributing)
    - [Contribution Guidelines](#contribution-guidelines)
    - [Reporting Issues](#reporting-issues)
    - [Development Workflow](#development-workflow)
  - [📄 License](#-license)
  - [👥 Contact](#-contact)
  - [🙏 Acknowledgments](#-acknowledgments)

## 🦟 About the Project

Mosquito Alert harnesses the power of citizen scientists and modern technology to investigate the spread of mosquito species, particularly tiger mosquitoes, across different regions. This Django-based server application:

- Receives and processes mosquito sighting reports from mobile apps
- Manages photo validation and expert classification workflows
- Provides RESTful APIs for mobile applications
- Handles geospatial data processing with PostGIS
- Supports multi-language localization
- Implements robust authentication and authorization
- Generates statistical reports and visualizations

## ✨ Features

- **RESTful API**: Comprehensive API built with Django REST Framework
- **Geospatial Support**: PostGIS integration for geographic data processing
- **Expert Validation**: Workflow system for report validation and scoring
- **Multi-language**: Internationalization support for multiple languages
- **Push Notifications**: FCM integration for mobile notifications
- **Image Processing**: Automated image handling and validation
- **Authentication**: JWT-based authentication with Django Simple JWT
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation with drf-spectacular
- **Admin Interface**: Enhanced Django admin with custom filters and views
- **Asynchronous Tasks**: Celery integration for background processing

## 🚀 Getting Started

### Prerequisites

- **Docker** and **Docker Compose**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Mosquito-Alert/mosquito_alert.git
   cd mosquito_alert
   ```

2. **Build and start containers**
   ```bash
   make start
   ```

   This will:
   - Build the Docker images
   - Start PostgreSQL with PostGIS
   - Start the Django application on port 8000
   - Run database migrations

3. **Create a superuser** (optional)
   ```bash
   make shell
   python3 manage.py createsuperuser
   ```

### Configuration

The project uses Django settings modules:
- `config.settings.prod` - Production settings
- `config.settings.local` - Development settings
- `config.settings.local_ssl` - Development with SSL

Environment variables can be set for:
- Database connection
- Secret keys
- Email configuration
- Storage backends

## 💻 Usage

### Running the Application

```bash
# Start all services
make start

# View logs
make logs

# Stop services
make stop

# Restart services
make restart
```

Access the application:
- **API**: http://localhost:8000/api/v1/
- **Admin**: http://localhost:8000/admin/

### Available Commands

The `Makefile` provides convenient commands for development:

| Command | Description |
|---------|-------------|
| `make start` | Create and start all containers |
| `make stop` | Stop all containers |
| `make restart` | Restart all services |
| `make down` | Stop and remove containers |
| `make logs` | Show container logs (follow mode) |
| `make shell` | Open bash shell in Django container |
| `make psql` | Start PostgreSQL command-line client |
| `make ps` | List running containers |
| `make db_restore file=<path>` | Restore database from backup |
| `make clean_data` | Remove all data volumes |

#### SSL Support
To run with SSL in development:
```bash
SSL=1 make start
```

## 📚 API Documentation & SDKs

### API Documentation

The API uses drf-spectacular for automatic OpenAPI schema generation:

- **ReDoc**: http://localhost:8000/api/v1/
- **OpenAPI Schema**: http://localhost:8000/api/v1/openapi.yml

### Official SDKs

We provide official SDKs for multiple programming languages to make integration easier:

| Language | Repository | Description |
|----------|------------|-------------|
| 🐍 **Python** | [mosquito-alert-python-sdk](https://github.com/Mosquito-Alert/mosquito-alert-python-sdk) | Python client for Mosquito Alert API |
| 📘 **TypeScript** | [mosquito-alert-typescript-sdk](https://github.com/Mosquito-Alert/mosquito-alert-typescript-sdk) | TypeScript/JavaScript SDK |
| 🎯 **Dart** | [mosquito-alert-dart-sdk](https://github.com/Mosquito-Alert/mosquito-alert-dart-sdk) | Dart SDK for Flutter applications |
| 📊 **R** | [mosquito-alert-R-sdk](https://github.com/Mosquito-Alert/mosquito-alert-R-sdk) | R package for data analysis |

These SDKs provide type-safe interfaces, authentication handling, and convenient methods for interacting with the Mosquito Alert API.

## 🧪 Testing

The project uses pytest for testing with Django integration.

### Running Tests

```bash
# Using Docker
docker compose -f docker-compose-local.yml run --rm django pytest

# Or with the shell
make shell
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest api/tests/test_views.py

# Run specific test
pytest api/tests/test_views.py::TestReportViewSet::test_create_report
```

### Test Configuration

Tests are configured in `pytest.ini`:
- Uses `config.settings.local` for testing
- Database reuse enabled (`--reuse-db`)
- Integration tests with Tavern

## 🤝 Contributing

We welcome contributions to the Mosquito Alert project! Here's how you can help:

### Contribution Guidelines

1. **Fork the repository**
   ```bash
   git fork https://github.com/Mosquito-Alert/mosquito_alert.git
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make your changes**
   - Write clean, documented code
   - Add tests for new features
   - Update documentation as needed

4. **Run tests**
   ```bash
   pytest
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

7. **Open a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure all tests pass

### Reporting Issues

- Use GitHub Issues to report bugs
- Include detailed reproduction steps
- Provide system information and logs
- Tag issues appropriately (bug, enhancement, question)

### Development Workflow

1. Discuss major changes by opening an issue first
2. Keep pull requests focused on single features/fixes
3. Update tests and documentation
4. Follow the existing code style
5. Be responsive to feedback during code review

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE.md](LICENSE.md) file for details.

Mosquito Alert is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

## 👥 Contact

**Mosquito Alert Team**
- Website: [https://mosquitoalert.com](https://mosquitoalert.com)
- Email: it@mosquitoalert.com
- GitHub: [@Mosquito-Alert](https://github.com/Mosquito-Alert)

## 🙏 Acknowledgments

This project is part of a citizen science initiative to monitor and study mosquito populations. Special thanks to all contributors and citizen scientists who make this project possible.

---

**Related Projects**:
- 🌍 **Map**: [map](https://github.com/Mosquito-Alert/map)
- 💻 **Frontend**: [mosquito_alert_frontend](https://github.com/Mosquito-Alert/mosquito_alert_frontend)
- 📱 **Mobile App**: [mosquito_alert_mobile_app](https://github.com/Mosquito-Alert/mosquito_alert_mobile_app)