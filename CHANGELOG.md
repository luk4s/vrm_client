# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.2] - 2025-04-11
### Changed
- Improved data aggregation in InfluxDBService for calculating summary points | [@lukas](https://github.com/luk4s)

## [1.0.1] - 2025-04-08
### Fixed
- Formula for calculation battery SOC and VOLTAGE | [@lukas](https://github.com/luk4s)

## [1.0.0] - 2025-04-06

### Added
- Initial release
- API client for fetch basic data from VRM cloud
- models for basic data
- SiteService which collect data about installations
- InfluxDB service for storing data
- Scheduler for automatic processing
