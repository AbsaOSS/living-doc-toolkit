# Architecture Overview

**Version:** 1.0  
**Last Updated:** 2026-02-18

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Data Flow Pipeline](#data-flow-pipeline)
3. [Monorepo Package Structure](#monorepo-package-structure)
4. [Service Architecture](#service-architecture)
5. [Adapter Pattern](#adapter-pattern)
6. [Audit Trail Flow](#audit-trail-flow)

---

## System Overview

The Living Documentation Toolkit is a **generic builder** that transforms machine-readable artifacts from upstream collectors into canonical datasets for downstream generators. It is designed as a modular, extensible monorepo with clear separation of concerns.

**Core Principles:**
- **Adapter-driven input detection**: Auto-detect producer format
- **Versioned contracts**: JSON Schema + Pydantic models
- **Enterprise-grade audit**: Preserve provenance throughout the pipeline
- **Fail-safe compatibility**: Warn and attempt processing for version mismatches
- **Deterministic output**: Same input always produces same output

---

## Data Flow Pipeline

### High-Level Pipeline (SPEC.md §5.1)

```mermaid
graph LR
    A[Collector Action] -->|doc-issues.json| B[Adapter]
    B -->|AdapterResult| C[Service]
    C -->|pdf_ready.json| D[Dataset]
    D -->|Validated JSON| E[Generator Action]
    
    style A fill:#e1f5ff,stroke:#0288d1
    style B fill:#fff9c4,stroke:#f57f17
    style C fill:#f3e5f5,stroke:#7b1fa2
    style D fill:#e8f5e9,stroke:#388e3c
    style E fill:#ffe0b2,stroke:#e64a19
```

**Pipeline Stages:**

1. **Collector Action** (`AbsaOSS/living-doc-collector-gh`)
   - Collects issues from GitHub
   - Outputs: `doc-issues.json`

2. **Adapter** (`packages/adapters/collector_gh`)
   - Detects producer format
   - Parses input into internal representation
   - Outputs: `AdapterResult`

3. **Service** (`packages/services/normalize_issues`)
   - Normalizes markdown sections
   - Builds canonical JSON structure
   - Outputs: `pdf_ready.json`

4. **Dataset** (`packages/datasets_pdf`)
   - Validates output against schema
   - Ensures compliance with generator contract

5. **Generator Action** (`AbsaOSS/living-doc-generator-pdf`)
   - Generates PDF document
   - Outputs: `living-documentation.pdf`

---

### Detailed Service Pipeline

```mermaid
flowchart TD
    Start([Start]) --> Load[Load Input JSON]
    Load --> Detect{Auto-detect<br/>Adapter?}
    
    Detect -->|Yes| AutoDetect[Scan metadata.generator.name]
    Detect -->|No| ExplicitAdapter[Use --source adapter]
    
    AutoDetect --> CheckAdapter{Adapter<br/>Found?}
    ExplicitAdapter --> CheckAdapter
    
    CheckAdapter -->|No| Error1[Exit 2: Adapter Error]
    CheckAdapter -->|Yes| CheckVersion[Check Version Compatibility]
    
    CheckVersion --> Warn{Version<br/>in Range?}
    Warn -->|No| LogWarn[Log Warning + Add to Audit]
    Warn -->|Yes| Parse[Parse Input]
    LogWarn --> Parse
    
    Parse --> Normalize[Normalize Markdown Sections]
    Normalize --> Build[Build PDF-Ready JSON]
    Build --> Augment[Augment Audit Envelope]
    Augment --> Validate[Validate Output Schema]
    
    Validate --> ValidCheck{Valid?}
    ValidCheck -->|No| Error3[Exit 3: Schema Validation Failed]
    ValidCheck -->|Yes| Write[Write Output File]
    
    Write --> WriteCheck{Success?}
    WriteCheck -->|No| Error5[Exit 5: File I/O Error]
    WriteCheck -->|Yes| Log[Log Summary]
    
    Log --> End([Exit 0: Success])
    
    style Start fill:#e8f5e9,stroke:#388e3c
    style End fill:#e8f5e9,stroke:#388e3c
    style Error1 fill:#ffebee,stroke:#c62828
    style Error3 fill:#ffebee,stroke:#c62828
    style Error5 fill:#ffebee,stroke:#c62828
    style Normalize fill:#e3f2fd,stroke:#1976d2
    style Build fill:#f3e5f5,stroke:#7b1fa2
```

---

## Monorepo Package Structure

### Directory Layout (SPEC.md §4.1)

```mermaid
graph TD
    Root[living-doc-toolkit/]
    
    Root --> Packages[packages/]
    Root --> Apps[apps/]
    Root --> Docs[docs/]
    Root --> Tests[tests/]
    
    Packages --> Core[core/]
    Packages --> Datasets[datasets_pdf/]
    Packages --> Adapters[adapters/]
    Packages --> Services[services/]
    
    Adapters --> CollectorGH[collector_gh/]
    Services --> NormalizeIssues[normalize_issues/]
    
    Apps --> CLI[cli/]
    
    Docs --> Cookbooks[cookbooks/]
    Docs --> Recipes[recipes/]
    
    Core --> CoreSrc[src/living_doc_core/]
    CoreSrc --> JsonUtils[json_utils.py]
    CoreSrc --> MarkdownUtils[markdown_utils.py]
    CoreSrc --> LoggingConfig[logging_config.py]
    CoreSrc --> Errors[errors.py]
    
    Datasets --> DatasetsSrc[src/living_doc_datasets_pdf/]
    DatasetsSrc --> PdfReady[pdf_ready/v1/models.py]
    DatasetsSrc --> Audit[audit/v1/models.py]
    
    CollectorGH --> AdapterSrc[src/living_doc_adapter_collector_gh/]
    AdapterSrc --> Detector[detector.py]
    AdapterSrc --> Parser[parser.py]
    AdapterSrc --> AdapterModels[models.py]
    
    NormalizeIssues --> ServiceSrc[src/living_doc_service_normalize_issues/]
    ServiceSrc --> Service[service.py]
    ServiceSrc --> Normalizer[normalizer.py]
    ServiceSrc --> Builder[builder.py]
    
    CLI --> CLISrc[src/living_doc_cli/]
    CLISrc --> Main[main.py]
    CLISrc --> Commands[commands/normalize_issues.py]
    
    style Root fill:#e1f5ff,stroke:#0288d1
    style Core fill:#fff9c4,stroke:#f57f17
    style Datasets fill:#f3e5f5,stroke:#7b1fa2
    style Adapters fill:#e8f5e9,stroke:#388e3c
    style Services fill:#ffe0b2,stroke:#e64a19
    style CLI fill:#fce4ec,stroke:#c2185b
```

### Package Dependencies

```mermaid
graph TD
    CLI[apps/cli] --> NormalizeService[packages/services/normalize_issues]
    NormalizeService --> Core[packages/core]
    NormalizeService --> Datasets[packages/datasets_pdf]
    NormalizeService --> CollectorGH[packages/adapters/collector_gh]
    
    CollectorGH --> Core
    Datasets --> Core
    
    style CLI fill:#fce4ec,stroke:#c2185b
    style NormalizeService fill:#ffe0b2,stroke:#e64a19
    style Core fill:#fff9c4,stroke:#f57f17
    style Datasets fill:#f3e5f5,stroke:#7b1fa2
    style CollectorGH fill:#e8f5e9,stroke:#388e3c
```

**Dependency Rules:**
- **Core** has no dependencies (lowest level)
- **Datasets** depends only on Core
- **Adapters** depend on Core
- **Services** depend on Core, Datasets, and specific Adapters
- **CLI** depends on Core and specific Services

---

## Service Architecture

### Normalize-Issues Service Components

```mermaid
graph TB
    subgraph "Service Package (packages/services/normalize_issues)"
        ServiceEntry[service.py<br/>Main Orchestration]
        Normalizer[normalizer.py<br/>Markdown Processing]
        Builder[builder.py<br/>JSON Construction]
    end
    
    subgraph "Core Package (packages/core)"
        JsonUtils[json_utils.py]
        MarkdownUtils[markdown_utils.py]
        LoggingConfig[logging_config.py]
        Errors[errors.py]
    end
    
    subgraph "Adapter Package (packages/adapters/collector_gh)"
        Detector[detector.py<br/>Producer Detection]
        Parser[parser.py<br/>Input Parsing]
        AdapterModels[models.py<br/>AdapterResult]
    end
    
    subgraph "Dataset Package (packages/datasets_pdf)"
        PdfReadyModels[pdf_ready/v1/models.py<br/>PdfReadyV1]
        AuditModels[audit/v1/models.py<br/>AuditEnvelopeV1]
    end
    
    ServiceEntry --> Normalizer
    ServiceEntry --> Builder
    ServiceEntry --> Detector
    ServiceEntry --> Parser
    
    Normalizer --> MarkdownUtils
    Builder --> PdfReadyModels
    Builder --> AuditModels
    
    ServiceEntry --> JsonUtils
    ServiceEntry --> LoggingConfig
    ServiceEntry --> Errors
    
    Parser --> AdapterModels
    
    style ServiceEntry fill:#ffe0b2,stroke:#e64a19,stroke-width:3px
    style Normalizer fill:#e3f2fd,stroke:#1976d2
    style Builder fill:#f3e5f5,stroke:#7b1fa2
```

**Component Responsibilities:**

- **service.py**: Main orchestration logic, pipeline coordination
- **normalizer.py**: Markdown parsing and section mapping
- **builder.py**: PDF-ready JSON structure construction
- **Core utilities**: Reusable helpers (JSON I/O, logging, markdown parsing)
- **Adapter**: Input detection and parsing
- **Dataset models**: Schema validation and type safety

---

## Adapter Pattern

### Adapter Selection and Execution

```mermaid
sequenceDiagram
    participant CLI as CLI Command
    participant Service as normalize_issues<br/>Service
    participant Registry as Adapter<br/>Registry
    participant Adapter as collector_gh<br/>Adapter
    participant Parser as Adapter<br/>Parser
    
    CLI->>Service: run_service(input, output, options)
    Service->>Service: Load input JSON
    
    alt Auto-detect mode
        Service->>Registry: Find compatible adapter
        Registry->>Adapter: can_handle(payload)?
        Adapter->>Registry: Yes (metadata.generator.name matches)
        Registry->>Service: Return CollectorGhAdapter
    else Explicit mode
        Service->>Registry: Get adapter by name
        Registry->>Service: Return CollectorGhAdapter
    end
    
    Service->>Adapter: Check version compatibility
    
    alt Version in range
        Adapter->>Service: OK (no warning)
    else Version out of range
        Adapter->>Service: Warning (log + add to audit)
    end
    
    Service->>Parser: parse(payload)
    Parser->>Parser: Map metadata → audit fields
    Parser->>Parser: Map issues → AdapterItems
    Parser->>Service: Return AdapterResult
    
    Service->>Service: Normalize sections
    Service->>Service: Build PDF-ready JSON
    Service->>Service: Validate output
    Service->>CLI: Success
```

**Key Concepts:**

1. **Detection**: Adapters implement `can_handle(payload)` to identify compatible inputs
2. **Version Checking**: Adapters define confirmed compatible ranges
3. **Parsing**: Adapters translate external format to internal `AdapterResult`
4. **Extensibility**: New adapters can be added without modifying services

---

## Audit Trail Flow

### Audit Envelope Augmentation

```mermaid
flowchart LR
    subgraph Collector["Collector (living-doc-collector-gh)"]
        CollectorMeta[metadata:<br/>generator, run, source]
    end
    
    subgraph Adapter["Adapter (collector_gh)"]
        AdapterMapping[Map to audit envelope:<br/>producer, run, source]
        AdapterExt[Store original in<br/>extensions.collector-gh]
    end
    
    subgraph Service["Service (normalize_issues)"]
        ServiceTrace[Append trace step:<br/>normalization]
        ServiceWarnings[Add warnings if any]
    end
    
    subgraph Output["Output (pdf_ready.json)"]
        OutputAudit[Complete audit envelope:<br/>producer + run + source<br/>+ trace + extensions]
    end
    
    CollectorMeta --> AdapterMapping
    CollectorMeta --> AdapterExt
    AdapterMapping --> ServiceTrace
    AdapterExt --> ServiceTrace
    ServiceTrace --> ServiceWarnings
    ServiceWarnings --> OutputAudit
    
    style Collector fill:#e1f5ff,stroke:#0288d1
    style Adapter fill:#fff9c4,stroke:#f57f17
    style Service fill:#ffe0b2,stroke:#e64a19
    style Output fill:#e8f5e9,stroke:#388e3c
```

**Audit Trail Example:**

```json
{
  "meta": {
    "audit": {
      "schema_version": "1.0",
      "producer": {
        "name": "AbsaOSS/living-doc-collector-gh",
        "version": "1.2.0",
        "build": "abc123"
      },
      "run": {
        "run_id": "123456",
        "run_attempt": "1",
        "actor": "user@example.com",
        "workflow": "collect-docs",
        "ref": "refs/heads/main",
        "sha": "abc123def456"
      },
      "source": {
        "systems": ["GitHub"],
        "repositories": ["AbsaOSS/project"],
        "organization": "AbsaOSS",
        "enterprise": null
      },
      "trace": [
        {
          "step": "collection",
          "tool": "living-doc-collector-gh",
          "tool_version": "1.2.0",
          "started_at": "2026-02-18T10:25:00Z",
          "finished_at": "2026-02-18T10:28:00Z",
          "warnings": []
        },
        {
          "step": "normalization",
          "tool": "living-doc-toolkit",
          "tool_version": "0.1.0",
          "started_at": "2026-02-18T10:30:00Z",
          "finished_at": "2026-02-18T10:30:05Z",
          "warnings": [
            {
              "code": "VERSION_MISMATCH",
              "message": "Producer version 2.1.0 is outside confirmed range",
              "context": "metadata.generator.version"
            }
          ]
        }
      ],
      "extensions": {
        "collector-gh": {
          "original_metadata": {
            "generator": {...},
            "run": {...},
            "source": {...}
          }
        }
      }
    }
  }
}
```

**Audit Benefits:**
- **Provenance**: Track data origin and transformations
- **Reproducibility**: Recreate output with same input and tools
- **Debugging**: Identify which step introduced issues
- **Compliance**: Enterprise audit requirements
- **Extensibility**: Custom metadata via extensions

---

## Extension Points

### Adding a New Service

```mermaid
graph TB
    subgraph "New Service Package"
        NewService[packages/services/new_service/]
        NewServiceSrc[src/living_doc_service_new_service/]
        NewServiceService[service.py]
        NewServiceLogic[custom_logic.py]
    end
    
    subgraph "Dependencies"
        Core[packages/core]
        Datasets[packages/datasets_*]
        Adapters[packages/adapters/*]
    end
    
    subgraph "CLI Integration"
        CLICmd[apps/cli/commands/new_service.py]
        CLIMain[apps/cli/main.py]
    end
    
    NewServiceService --> NewServiceLogic
    NewServiceService --> Core
    NewServiceService --> Datasets
    NewServiceService --> Adapters
    
    CLICmd --> NewServiceService
    CLIMain --> CLICmd
    
    style NewService fill:#e1f5ff,stroke:#0288d1,stroke-width:3px
```

**Steps to Add a New Service:**

1. Create service package: `packages/services/{service_name}/`
2. Define service logic in `service.py`
3. Add dependencies (core, datasets, adapters)
4. Write unit tests
5. Create CLI command in `apps/cli/commands/{service_name}.py`
6. Register command in `apps/cli/main.py`
7. Add cookbook and recipes to `docs/`

---

### Adding a New Adapter

```mermaid
graph TB
    subgraph "New Adapter Package"
        NewAdapter[packages/adapters/new_adapter/]
        NewAdapterSrc[src/living_doc_adapter_new_adapter/]
        NewDetector[detector.py]
        NewParser[parser.py]
        NewModels[models.py]
    end
    
    subgraph "Adapter Interface"
        CanHandle[can_handle: payload → bool]
        CheckVersion[check_compatibility: version → warnings]
        Parse[parse: payload → AdapterResult]
    end
    
    NewDetector --> CanHandle
    NewDetector --> CheckVersion
    NewParser --> Parse
    NewModels --> Parse
    
    style NewAdapter fill:#e8f5e9,stroke:#388e3c,stroke-width:3px
```

**Steps to Add a New Adapter:**

1. Create adapter package: `packages/adapters/{adapter_name}/`
2. Implement `detector.py` with `can_handle()` and `check_compatibility()`
3. Implement `parser.py` with `parse()` returning `AdapterResult`
4. Define `models.py` for adapter-specific types
5. Write unit tests with fixture files
6. Register adapter in service adapter registry
7. Update documentation with supported formats

---

## Performance Considerations

### Expected Performance (SPEC.md §5.5)

| Input Size | Target Time | Maximum Time |
|------------|-------------|--------------|
| 10 issues | < 1 second | 3 seconds |
| 100 issues | < 10 seconds | 30 seconds |
| 1000 issues | < 60 seconds | 180 seconds |

**Performance Bottlenecks:**
- JSON parsing (large files)
- Markdown normalization (complex content)
- Schema validation (large datasets)

**Optimization Strategies:**
- Streaming JSON parsing for large files
- Parallel markdown processing
- Caching compiled schemas

---

## Security Considerations

### Input Validation

```mermaid
flowchart TD
    Input[User Input] --> Validate{Validate<br/>Input}
    
    Validate -->|Invalid JSON| Error1[Exit 1: Invalid Input]
    Validate -->|Missing Fields| Error1
    Validate -->|Valid| Adapter[Adapter Detection]
    
    Adapter --> Parse{Parse<br/>Input}
    Parse -->|Adapter Error| Error2[Exit 2: Adapter Error]
    Parse -->|Success| Normalize[Normalize]
    
    Normalize --> Build[Build Output]
    Build --> ValidateOutput{Validate<br/>Output}
    
    ValidateOutput -->|Invalid| Error3[Exit 3: Schema Validation Failed]
    ValidateOutput -->|Valid| Success[Success]
    
    style Input fill:#e1f5ff,stroke:#0288d1
    style Error1 fill:#ffebee,stroke:#c62828
    style Error2 fill:#ffebee,stroke:#c62828
    style Error3 fill:#ffebee,stroke:#c62828
    style Success fill:#e8f5e9,stroke:#388e3c
```

**Security Measures:**
- Input validation at adapter level
- Schema validation at output level
- No code execution from input data
- No network requests during processing
- Deterministic output (no side effects)

---

## Additional Resources

- **SPEC.md**: Full system specification
- **TASKS.md**: Implementation roadmap
- **Cookbook**: `docs/cookbooks/normalize-issues.md`
- **Recipes**: `docs/recipes/`
- **Troubleshooting**: `docs/troubleshooting.md`
