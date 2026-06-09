# map-salesforce

This repository is a Salesforce DX project for a template workspace, using `sf`/`sfdx` project configuration, sandbox-first defaults, and a two-package layout consisting of a base package and a dependent feature package.

The current project configuration targets API version `67.0`, uses `https://test.salesforce.com` as the project login default, and sets `oauthLocalPort` to `1718` to avoid common localhost callback conflicts during browser-based auth.

## Project layout

The project defines three package directories: `force-app` as the default base package root, `packages/feature` as a second package that depends on `map-base`, and `unpackaged/config` for unpackaged metadata or environment-specific configuration.

| Path | Purpose | Notes |
|---|---|---|
| `force-app` | Base package source | Default package directory, mapped to `map-base`.[file:290] |
| `packages/feature` | Feature package source | Depends on `map-base@1.0.0.LATEST`.[file:290] |
| `unpackaged/config` | Unpackaged metadata | Not marked as default and not tied to a package alias.[file:290] |

## Packaging model

`packageAliases` maps human-friendly names to package IDs and package version IDs so CLI packaging commands can refer to aliases instead of raw Salesforce IDs.

The current package model is:

| Alias | Type | Value |
|---|---|---|
| `map-base` | Package ID | `0Ho000000000001AAA` |
| `map-base@1.0.0-1` | Package Version ID | `04t000000000001AAA` |
| `map-feature` | Package ID | `0Ho000000000002AAA` |
| `map-feature@1.0.0-1` | Package Version ID | `04t000000000002AAA` |

The feature package declares a dependency on `map-base` version `1.0.0.LATEST`, which means package creation and installation workflows should account for base-first ordering even though `pushPackageDirectoriesSequentially` is currently `false`.

## Environment behavior

The `plugins` block enables `salesforcedx-vscode-core.enable-sobject-refresh-on-startup`, which helps keep local SObject definitions fresh for Salesforce VS Code development workflows.[file:290]

The `replacements` block defines environment substitutions for custom metadata and named credentials, replacing `API_BASE_URL_PLACEHOLDER` with `https://sandbox.my.salesforce.com` and `ENV_NAME_PLACEHOLDER` with `SANDBOX` during supported workflows.[file:290]

The project also enables these `sourceBehaviorOptions`: `decomposeCustomLabelsBeta2`, `decomposeExternalServiceRegistrationBeta`, `decomposePermissionSetBeta2`, `decomposeSharingRulesBeta`, and `decomposeWorkflowBeta`.[file:290]

## Authentication

The project-level `sfdcLoginUrl` is set to `https://test.salesforce.com`, which is appropriate for sandbox-first workflows, but explicit CLI login commands can still override that value with a My Domain URL when needed.

For work, use the org My Domain URL directly when authorizing the CLI:

```bash
sf org login web \
  --instance-url https://replaceme.my.salesforce.com \
  --alias default \
  --set-default
```

If the org is also your Dev Hub, log in and set a Dev Hub alias at the same time:

```bash
sf org login web \
  --instance-url https://replaceme.my.salesforce.com \
  --alias map-dev \
  --set-default-dev-hub
```

Salesforce recommends using `--alias` for readable org names and `--set-default-dev-hub` when authorizing a Dev Hub org for scratch-org creation and packaging workflows.

## `sf.sh` guidance

The setup script should treat the org as the shared work org alias and allow each developer to enter a personal Dev Hub alias, then map that alias to the same authenticated org.

A recommended `sf.sh` looks like this:

```bash
#!/usr/bin/env bash

set -euo pipefail

INSTANCE_URL="https://replaceme.my.salesforce.com"
DEFAULT_ORG_ALIAS="replacme"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Error: required command not found: $1"
    exit 1
  }
}

install_plugin_if_missing() {
  local plugin="$1"

  if sf plugins | grep -Fq "$plugin"; then
    echo "Plugin already installed: $plugin"
  else
    echo "Installing plugin: $plugin"
    sf plugins install "$plugin"
  fi
}

require_cmd sf

sf config set disable-telemetry=true --global
sf config set org-api-version=63.0 --global
sf config set org-capitalize-record-types=false --global
sf config set org-max-query-limit=20000 --global
sf config set rest-deploy=false --global
sf config set org-instance-url="${INSTANCE_URL}" --global
read -r -p "Enter Dev Hub alias (example: map-dev): " DEVHUB_ALIAS
if [[ -z "${DEVHUB_ALIAS}" ]]; then
  echo "Error: Dev Hub alias cannot be empty."
  exit 1
fi
BROWSER=chromium sf org login web \
  --instance-url "${INSTANCE_URL}" \
  --alias "${DEFAULT_ORG_ALIAS}" \
  --set-default \
  --set-default-dev-hub

sf alias set "${DEVHUB_ALIAS}=${DEFAULT_ORG_ALIAS}"

sf config set target-org="${DEFAULT_ORG_ALIAS}" --global
sf config set target-dev-hub="${DEVHUB_ALIAS}" --global

install_plugin_if_missing "@salesforce/plugin-packaging"
install_plugin_if_missing "@salesforce/plugin-devops-center"

sf plugins --core
sf plugins
```

This structure keeps your org as the team-standard org alias, allows a user-defined Dev Hub alias such as `map-dev`, and installs the additional official plugins that are most useful beyond the CLI’s built-in core and just-in-time plugin behavior.

## Recommended commands

Common commands for this repo:

```bash
# log into the org
sf org login web --instance-url https://replaceme.my.salesforce.com --alias default --set-default
# log into the same org as a Dev Hub
sf org login web --instance-url https://replaceme.my.salesforce.com --alias map-dev --set-default-dev-hub
# create a scratch org
sf org create scratch --definition-file config/project-scratch-def.json --alias map-scratch --set-default
# list orgs and aliases
sf org list
sf alias list
# inspect project plugins
sf plugins --core
sf plugins
```

## Notes

- `sf` still uses `sfdx-project.json`/`sfdx-project.jsonc` as the project configuration format; there is no separate `sf-project.json` format.
- `oauthLocalPort: 1718` is useful when default localhost callback ports are unavailable during browser-based auth.
- `sfdcLoginUrl` sets a project default, but `--instance-url` on the command line takes precedence for explicit org login commands
