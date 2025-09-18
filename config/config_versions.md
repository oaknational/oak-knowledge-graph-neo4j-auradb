# Configuration Version History

## Naming Convention
- `oak_curriculum_schema_v{major}.{minor}.json`
- Example: `oak_curriculum_schema_v1.0.json`

## Version History

### MVP Phase (Pre-Production)
- **v0.1.0-alpha**: Schema design and experimentation
- **v0.2.0-alpha**: Schema building and testing
- **v0.3.0-alpha**: Full schema tested
- **v0.4.0-beta**: Stakeholder review
- **v0.5.0-rc.1**: Approved for production

### Production Phase (Post-Approval)
- **v1.0.0**: First approved production schema
- **v1.1.0**: Add assessment nodes
- **v1.2.0**: Add teacher resources
- **v2.0.0**: Major schema restructure (if needed)

## Usage
```python
# Load specific version
config = config_manager.load_config("oak_curriculum_schema_v1.0.json")

# Load latest (symlink)
config = config_manager.load_config("oak_curriculum_schema_latest.json")
```

---

## Professional Versioning System Notes

### Semantic Versioning (SemVer) 2.0.0

This project follows **Semantic Versioning** as defined at [semver.org](https://semver.org), the industry standard for version numbering.

**Format:** `MAJOR.MINOR.PATCH`

#### Version Number Components:

1. **MAJOR** version: Incremented for incompatible schema changes
   - Breaking changes that require code updates
   - Node/relationship type renames or removals
   - Property type changes that break existing queries
   - Example: `v1.0.0` → `v2.0.0`

2. **MINOR** version: Incremented for backwards-compatible functionality additions
   - New node types or relationship types
   - New optional properties
   - New materialized views
   - Example: `v1.0.0` → `v1.1.0`

3. **PATCH** version: Incremented for backwards-compatible bug fixes
   - Property description clarifications
   - Documentation updates
   - Non-breaking configuration corrections
   - Example: `v1.0.0` → `v1.0.1`

#### Schema Evolution Examples:

**MAJOR (Breaking Changes):**
- Renaming `Unit` node to `CurriculumUnit` → `v2.0.0`
- Changing `lesson_order` from `int` to `string` → `v2.0.0`
- Removing deprecated relationships → `v2.0.0`

**MINOR (Additive Changes):**
- Adding `Assessment` node type → `v1.1.0`
- Adding new `PREREQUISITE` relationship → `v1.2.0`
- Adding optional `difficulty_level` property → `v1.3.0`

**PATCH (Fixes):**
- Fixing typos in property descriptions → `v1.0.1`
- Correcting example values in documentation → `v1.0.2`
- Updating field mappings for clarity → `v1.0.3`

#### Benefits for Oak Curriculum Project:

1. **Clear Communication**: Stakeholders immediately understand impact of changes
2. **Safe Deployments**: Production systems know which updates are safe
3. **Dependency Management**: Different services can specify compatible schema versions
4. **Rollback Strategy**: Easy to identify last working version
5. **API Evolution**: Gradual migration paths for schema changes

#### Implementation Best Practices:

- **Tag releases**: Git tag each schema version (e.g., `schema-v1.0.0`)
- **Changelog**: Document all changes with impact assessment
- **Migration guides**: Provide upgrade instructions for major versions
- **Deprecation warnings**: Mark features for removal in advance
- **Testing**: Validate schema changes against existing data

This approach ensures professional schema management suitable for production educational technology systems.

---

## MVP Pre-Release Versioning Strategy

### Current Phase: MVP Development

#### Pre-Release Identifiers (SemVer Standard):

**`0.x.x-alpha`** - **Experimental/Internal Development**
- Rapid iteration and breaking changes expected
- Internal team testing only
- Schema structure may change significantly
- Example: `oak_curriculum_schema_v0.3.0-alpha.json`

**`0.x.x-beta`** - **Feature-Complete MVP**
- All core features implemented
- Ready for stakeholder review
- Minor adjustments expected from feedback
- Example: `oak_curriculum_schema_v0.4.0-beta.json`

**`0.x.x-rc.1`** - **Release Candidate**
- Final version pending approval
- No new features, only bug fixes
- Ready for production approval process
- Example: `oak_curriculum_schema_v0.5.0-rc.1.json`

**`1.0.0`** - **Production Release**
- Approved schema for production use
- Stability guarantees begin
- Breaking changes require major version increment

#### Benefits for MVP Phase:

1. **Clear Development Stage**: `alpha` signals "expect changes"
2. **Stakeholder Communication**: `beta` means "ready for review"
3. **Approval Process**: `rc` indicates "pending final approval"
4. **No False Stability**: `0.x` version prevents premature production use
