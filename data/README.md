# Data Storage Directory

This directory stores JSON files for the application. In the future, these files will be migrated to Azure Blob Storage.

## Directory Structure

- `maps/` - Contains map location JSON files
  - Each file is named with a UUID: `{uuid}.json`
  - Files contain map location data including coordinates, descriptions, etc.

## Future Migration

This local file storage is temporary. The plan is to:
1. Move all JSON files to Azure Blob Storage
2. Update the backend to read/write from Azure instead of local disk
3. Keep this directory structure for local development/testing

## Note

This directory and its contents should not be committed to version control in production, but is included for development purposes.
