# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-06-21

### Added
- DPoP (Demonstrating Proof of Possession) support for token binding
- Workaround for `requests_oauth2client` DPoP token validation bug

### Changed
- Authorization request is now serialized and stored in the session as `helseid_az_request`

## [1.0.1] - 2026-01-01

### Added
- Initial release
- HelseID OpenID Connect authentication with PKCE and PAR
- `HelseIDBackend` Django auth backend
- `HelseIDProfile` model for storing HelseID subject and HPR number
- Django system checks for required settings
