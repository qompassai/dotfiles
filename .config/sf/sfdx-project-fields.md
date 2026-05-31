# `sfdx-project.json` field guide

This document explains the commonly used and schema-supported fields in `sfdx-project.json` for Salesforce DX projects used with both `sf` and `sfdx` CLIs.[cite:294][cite:312]

`sf` still uses `sfdx-project.json` as the project configuration file; there is no separate `sf-project.json` format.[cite:294][cite:308]

## Full example

```json
{
  "name": "qompass-salesforce",
  "namespace": "",
  "packageAliases": {
    "qompass-base": "0Ho000000000001AAA",
    "qompass-base@1.0.0-1": "04t000000000001AAA"
  },
  "packageDirectories": [
    {
      "path": "force-app",
      "default": true,
      "package": "qompass-base",
      "versionName": "ver 1.0",
      "versionNumber": "1.0.0.NEXT",
      "definitionFile": "config/project-scratch-def.json",
      "branch": "main",
      "ancestorId": "",
      "ancestorVersion": "",
      "dependencies": [],
      "includeProfileUserLicenses": false,
      "postInstallScript": "",
      "uninstallScript": "",
      "releaseNotesUrl": "",
      "versionDescription": "Base package"
    }
  ],
  "plugins": {
    "salesforcedx-vscode-core": {
      "enable-sobject-refresh-on-startup": true
    }
  },
  "pushPackageDirectoriesSequentially": false,
  "replacements": [
    {
      "filename": "force-app/main/default/customMetadata/App_Config.Default.md-meta.xml",
      "replace": "API_BASE_URL_PLACEHOLDER",
      "replaceWith": "https://sandbox.my.salesforce.com"
    }
  ],
  "sfdcLoginUrl": "https://test.salesforce.com",
  "sourceApiVersion": "63.0",
  "sourceBehaviorOptions": [
    "decomposeCustomLabelsBeta2",
    "decomposePermissionSetBeta2"
  ]
}
```

## Top-level fields

<details>
<summary><strong>name</strong></summary>

The project name is a human-readable label for the Salesforce DX project.[cite:294][cite:312]

**Type:** `string`

**Example:**

```json
"name": "qompass-salesforce"
```

**Notes:**
- Commonly used in starter templates and project tooling.[cite:294]
- It does not by itself create or rename Salesforce packages.[cite:307]

</details>

<details>
<summary><strong>namespace</strong></summary>

The namespace identifies the package namespace for managed packaging scenarios, and is usually an empty string for unpackaged or non-namespaced development.[cite:294][cite:307]

**Type:** `string`

**Example:**

```json
"namespace": ""
```

**Options:**
- `""` for no namespace.
- A registered namespace string for managed package development.[cite:307]

</details>

<details>
<summary><strong>packageAliases</strong></summary>

`packageAliases` maps readable names to Salesforce package IDs and package version IDs so CLI commands can use aliases instead of raw IDs.[cite:307][cite:312]

**Type:** `object`

**Example:**

```json
"packageAliases": {
  "qompass-base": "0Ho000000000001AAA",
  "qompass-base@1.0.0-1": "04t000000000001AAA"
}
```

**Notes:**
- Useful for unlocked and second-generation packaging workflows.[cite:307]
- Can be left as `{}` if no packaging aliases are needed.[cite:312]

</details>

<details>
<summary><strong>packageDirectories</strong></summary>

`packageDirectories` defines one or more source roots or package roots inside the project.[cite:294][cite:314]

**Type:** `array`

**Example:**

```json
"packageDirectories": [
  {
    "path": "force-app",
    "default": true
  },
  {
    "path": "unpackaged/config",
    "default": false
  }
]
```

**Notes:**
- One directory is typically marked `"default": true`.[cite:314]
- This section becomes more detailed in unlocked/2GP packaging projects.[cite:307]

</details>

<details>
<summary><strong>plugins</strong></summary>

The `plugins` object stores project-specific plugin settings, including settings used by Salesforce VS Code extensions.[cite:294][cite:312]

**Type:** `object`

**Example:**

```json
"plugins": {
  "salesforcedx-vscode-core": {
    "enable-sobject-refresh-on-startup": true
  }
}
```

**Notes:**
- Plugin-specific keys vary by plugin.[cite:294]
- Safe to omit if no plugin requires project-level configuration.[cite:312]

</details>

<details>
<summary><strong>pushPackageDirectoriesSequentially</strong></summary>

This boolean controls whether package directories are pushed sequentially rather than in parallel during source operations.[cite:312]

**Type:** `boolean`

**Options:**
- `true`
- `false`

</details>

<details>
<summary><strong>replacements</strong></summary>

`replacements` defines find-and-replace rules that can adjust source content for environment-specific deployments.[cite:294][cite:312]

**Type:** `array`

**Example:**

```json
"replacements": [
  {
    "filename": "force-app/main/default/customMetadata/App_Config.Default.md-meta.xml",
    "replace": "API_BASE_URL_PLACEHOLDER",
    "replaceWith": "https://sandbox.my.salesforce.com"
  }
]
```

**Replacement object fields:**
- `filename`: relative file path.[cite:312]
- `replace`: text to search for.[cite:312]
- `replaceWith`: replacement value.[cite:312]

</details>

<details>
<summary><strong>sfdcLoginUrl</strong></summary>

`sfdcLoginUrl` sets the default login URL for org authorization in the project context.[cite:294][cite:298]

**Type:** `string`

**Common options:**
- `"https://login.salesforce.com"` for production/developer edition logins.[cite:294]
- `"https://test.salesforce.com"` for sandbox-first workflows.[cite:294]
- A My Domain login URL when needed for org-specific authentication behavior.[cite:294]

**Example:**

```json
"sfdcLoginUrl": "https://test.salesforce.com"
```

</details>

<details>
<summary><strong>sourceApiVersion</strong></summary>

`sourceApiVersion` controls the metadata API version used for source operations such as retrieve, deploy, and convert.[cite:294]

**Type:** `string`

**Example:**

```json
"sourceApiVersion": "63.0"
```

**Notes:**
- This is separate from the CLI org API version config value.[cite:294]
- It should match the target platform version your project is built for.[cite:294]

</details>

<details>
<summary><strong>sourceBehaviorOptions</strong></summary>

`sourceBehaviorOptions` enables optional metadata decomposition behaviors for specific metadata types.[cite:294][cite:312]

**Type:** `array`

**Known examples:**
- `"decomposeCustomLabelsBeta2"`[cite:294]
- `"decomposeExternalServiceRegistrationBeta"`[cite:312]
- `"decomposePermissionSetBeta2"`[cite:294]
- `"decomposeSharingRulesBeta"`[cite:312]
- `"decomposeWorkflowBeta"`[cite:294]

**Example:**

```json
"sourceBehaviorOptions": [
  "decomposeCustomLabelsBeta2",
  "decomposePermissionSetBeta2"
]
```

</details>

## `packageDirectories` object fields

<details>
<summary><strong>path</strong></summary>

`path` is the relative directory path for the package or source directory.[cite:294][cite:314]

**Type:** `string`

**Example:**

```json
"path": "force-app"
```

</details>

<details>
<summary><strong>default</strong></summary>

`default` marks whether the package directory is the default source directory in the project.[cite:314]

**Type:** `boolean`

**Options:**
- `true`
- `false`

</details>

<details>
<summary><strong>package</strong></summary>

`package` names the package associated with that directory in packaging workflows.[cite:307]

**Type:** `string`

**Example:**

```json
"package": "qompass-base"
```

</details>

<details>
<summary><strong>versionName</strong></summary>

`versionName` is a descriptive label for the package version.[cite:307]

**Type:** `string`

**Example:**

```json
"versionName": "ver 1.0"
```

</details>

<details>
<summary><strong>versionNumber</strong></summary>

`versionNumber` defines the semantic package version, often using placeholders like `NEXT` for automated builds.[cite:307]

**Type:** `string`

**Example:**

```json
"versionNumber": "1.0.0.NEXT"
```

</details>

<details>
<summary><strong>definitionFile</strong></summary>

`definitionFile` points to a scratch org definition JSON file used during scratch org creation for that package context.[cite:307][cite:315]

**Type:** `string`

**Example:**

```json
"definitionFile": "config/project-scratch-def.json"
```

</details>

<details>
<summary><strong>branch</strong></summary>

`branch` can be used to associate the package directory with a source control branch name.[cite:307]

**Type:** `string`

</details>

<details>
<summary><strong>ancestorId</strong></summary>

`ancestorId` specifies a package version ID used as an ancestor for packaging operations.[cite:307]

**Type:** `string`

</details>

<details>
<summary><strong>ancestorVersion</strong></summary>

`ancestorVersion` specifies the ancestor version number instead of using an explicit ancestor ID.[cite:307]

**Type:** `string`

</details>

<details>
<summary><strong>dependencies</strong></summary>

`dependencies` lists other package dependencies required by the package directory.[cite:307][cite:309]

**Type:** `array`

**Example:**

```json
"dependencies": [
  {
    "package": "qompass-base",
    "versionNumber": "1.0.0.LATEST"
  }
]
```

</details>

<details>
<summary><strong>includeProfileUserLicenses</strong></summary>

`includeProfileUserLicenses` controls whether profile user licenses are included in packaging metadata behavior.[cite:307][cite:312]

**Type:** `boolean`

**Options:**
- `true`
- `false`

</details>

<details>
<summary><strong>postInstallScript</strong></summary>

`postInstallScript` identifies an Apex script to run after package installation.[cite:307]

**Type:** `string`

</details>

<details>
<summary><strong>uninstallScript</strong></summary>

`uninstallScript` identifies an Apex script to run during package uninstall.[cite:307]

**Type:** `string`

</details>

<details>
<summary><strong>releaseNotesUrl</strong></summary>

`releaseNotesUrl` points to release documentation for a package version.[cite:307]

**Type:** `string`

</details>

<details>
<summary><strong>versionDescription</strong></summary>

`versionDescription` provides additional description text for the package version.[cite:307]

**Type:** `string`

</details>

<details>
<summary><strong>seedMetadata</strong></summary>

`seedMetadata` references metadata seed content used in supported package workflows.[cite:312][cite:315]

**Type:** `object`

**Example:**

```json
"seedMetadata": {
  "path": "seed/base"
}
```

</details>

## `dependencies` object fields

<details>
<summary><strong>package</strong></summary>

The dependency package alias or package ID.[cite:307][cite:309]

</details>

<details>
<summary><strong>versionNumber</strong></summary>

The dependency version number to require, such as `1.0.0.LATEST`.[cite:307]

</details>

## Recommended profiles

<details>
<summary><strong>Sandbox-first project</strong></summary>

Use these values for a typical sandbox-centered metadata repo:[cite:294]

```json
{
  "name": "qompass-salesforce",
  "namespace": "",
  "packageAliases": {},
  "packageDirectories": [
    {
      "path": "force-app",
      "default": true
    },
    {
      "path": "unpackaged/config",
      "default": false
    }
  ],
  "plugins": {
    "salesforcedx-vscode-core": {
      "enable-sobject-refresh-on-startup": true
    }
  },
  "pushPackageDirectoriesSequentially": false,
  "replacements": [],
  "sfdcLoginUrl": "https://test.salesforce.com",
  "sourceApiVersion": "63.0",
  "sourceBehaviorOptions": []
}
```

</details>

<details>
<summary><strong>Packaging project</strong></summary>

Use packaging-specific fields only if the project is actually building unlocked or second-generation packages.[cite:307][cite:313]

Add fields such as `package`, `versionName`, `versionNumber`, `ancestorId`, `ancestorVersion`, `dependencies`, `postInstallScript`, and `uninstallScript` under the relevant `packageDirectories` entries.[cite:307]

</details>
