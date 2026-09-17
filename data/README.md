# FarmSight AI — Data Directory

This directory contains dataset metadata, small permitted samples, and documentation for the FarmSight AI data pipeline.

FarmSight AI combines satellite, weather, soil-moisture and agricultural information to build an explainable Digital Farm Twin.

---

## Directory Structure

```text
data/
├── README.md
├── raw/
│   └── water_stress/
├── processed/
└── samples/
```

---

# 1. Data Sources

The primary external sources are:

| Source | Purpose |
|---|---|
| Sentinel-2 | Vegetation and crop-condition monitoring |
| Open-Meteo | Weather and rainfall |
| NASA POWER | Historical climate/weather context |
| ERA5-Land | Soil-moisture context |
| NISAR | Supplementary soil-moisture observations where available |
| TNAU / ICAR | Agricultural knowledge and crop-stage guidance |
| Tamil Nadu government datasets | Regional agricultural context |

Detailed source research is documented in:

```text
docs/01_DATA_SOURCE_RESEARCH.md
```

---

# 2. Raw Data

Raw external datasets should be placed under:

```text
data/raw/
```

The repository should not contain large satellite archives or other large external datasets.

For example:

```text
data/raw/
└── water_stress/
    └── README.md
```

The dataset README should document:

```text
source
provider
URL
license
download date
dataset version
geography
crop
target variable
features
preprocessing
real/synthetic status
limitations
```

---

# 3. Water-Stress Dataset

The ML model ideally requires a real labeled water-stress dataset.

The current research did not identify a sufficiently suitable real dataset matching all of:

```text
Tamil Nadu
Rice / Groundnut / Maize
Water-stress labels
Remote-sensing-compatible features
Weather-compatible features
```

Therefore, the initial implementation may require synthetic development data.

---

# 4. Synthetic Data Policy

Synthetic data may be used for:

- model development
- unit testing
- integration testing
- API testing
- demonstration

Synthetic data must never be represented as real-world observations.

Recommended metadata:

```text
dataset_type: synthetic
```

Example:

```json
{
  "dataset_type": "synthetic",
  "purpose": "development_and_integration_testing"
}
```

Synthetic model metrics must not be presented as real-world accuracy.

---

# 5. Real Data Policy

Real external data should retain provenance.

Each observation should be traceable to:

```text
provider
source
observation time
retrieval time
processing version
quality information
```

Example:

```json
{
  "source": "Sentinel-2",
  "provider": "Copernicus",
  "observation_time": "2026-09-15",
  "quality_status": "valid"
}
```

---

# 6. Satellite Data

Sentinel-2 is the primary satellite source.

Derived features include:

```text
NDVI
NDMI
NDVI temporal change
NDMI temporal change
```

Large satellite files should not be committed to Git.

Instead, store:

- source information
- processing code
- query parameters
- sample data when permitted
- download instructions

---

# 7. Weather Data

Open-Meteo is the primary weather source.

Potential derived variables include:

```text
rainfall_7d
rainfall_30d
rainfall_anomaly
temperature_mean
temperature_anomaly
```

NASA POWER can provide historical climate context and validation.

---

# 8. Soil Moisture

ERA5-Land can provide soil-moisture context.

NISAR may provide supplementary soil-moisture information where accessible.

Important:

> Soil-moisture products must not automatically be treated as field-level ground truth.

The source, spatial resolution and observation date must always be preserved.

---

# 9. Processed Data

Processed datasets should be stored under:

```text
data/processed/
```

Examples:

```text
data/processed/features/
data/processed/observations/
data/processed/zones/
```

Processed data should preserve a connection to the original observation source.

---

# 10. Canonical ML Features

The canonical feature vector is:

```text
ndvi_current
ndvi_7d_change
ndvi_30d_change
ndmi_current
ndmi_change
rainfall_7d
rainfall_30d
rainfall_anomaly
temperature_mean
temperature_anomaly
soil_moisture
soil_moisture_change
crop
crop_stage
historical_deviation
neighboring_deviation
```

The exact feature ordering and schema are defined in:

```text
docs/ml-contract.md
```

Do not create an alternative ML feature schema without updating the canonical contract.

---

# 11. Data Freshness

Every external observation should record its observation time.

The system must distinguish:

```text
observation_time
```

from:

```text
retrieval_time
```

and:

```text
processing_time
```

Satellite imagery must not be described as real-time.

When the latest observation is unavailable, the system may use the latest valid observation while reducing confidence.

---

# 12. Missing Data

Missing values must not be silently replaced with fabricated measurements.

Possible situations include:

```text
cloud-covered satellite image
missing weather observation
unavailable soil-moisture product
old satellite observation
insufficient historical baseline
```

The pipeline should record missingness and data quality.

Example:

```json
{
  "value": null,
  "status": "unavailable",
  "reason": "cloud_cover"
}
```

---

# 13. Historical Data

Historical observations are used to establish farm-specific baselines.

Example:

```text
Current NDVI
        ↓
Compare with
        ↓
Historical NDVI for same farm/crop/stage
```

Historical comparisons should account for:

- crop
- crop stage
- season
- observation date
- data quality

---

# 14. Nearby Farms

Nearby farms can provide additional contextual evidence.

However, they should only be used when sufficiently comparable.

Comparison should consider:

```text
crop
crop stage
season
location
observation date
environmental conditions
```

A nearby field must not automatically be considered a valid baseline.

---

# 15. Licensing

Before committing any external dataset, verify:

- license
- redistribution permissions
- attribution requirements
- access restrictions
- dataset size

Do not commit:

```text
private farmer data
API keys
credentials
restricted datasets
large satellite archives
```

---

# 16. Large Datasets

Large datasets should remain external.

Use:

```text
download instructions
source URL
dataset version
checksum where appropriate
```

instead of committing the complete dataset to Git.

If a dataset is small and its license permits redistribution, a sample may be committed under:

```text
data/samples/
```

---

# 17. Data Naming Convention

Use descriptive names.

Examples:

```text
sentinel2_<location>_<date>.tif
weather_<location>_<start>_<end>.csv
soil_moisture_<location>_<date>.csv
water_stress_<version>.csv
```

Do not use ambiguous names such as:

```text
data1.csv
final.csv
new.csv
test.csv
```

---

# 18. Data Provenance

Every processed observation should be traceable through:

```text
Source
   ↓
Raw observation
   ↓
Processing
   ↓
Derived feature
   ↓
Feature set
   ↓
ML prediction
   ↓
Evidence
   ↓
Recommendation
```

This provenance chain is important for explainability.

---

# 19. Scientific Guardrails

FarmSight AI must not claim:

### Exact NPK measurement

Satellite imagery does not directly provide exact NPK concentrations.

Use:

```text
nutrient-stress risk
```

when appropriate.

### Real-time satellite monitoring

Use:

```text
latest available satellite observation
```

instead.

### Exact irrigation volume

The system provides:

```text
water-stress risk
```

and:

```text
context-aware irrigation guidance
```

rather than claiming exact irrigation requirements from satellite data alone.

### Real-world model accuracy

Do not report real-world accuracy unless the model has been validated against appropriate real ground-truth labels.

---

# 20. Current Recommended Data Stack

For the initial hackathon implementation:

```text
Sentinel-2
     +
Open-Meteo
     +
ERA5-Land
     +
Agricultural knowledge
     +
Historical observations
```

Optional:

```text
NISAR
NASA POWER
Nearby comparable fields
Tamil Nadu agricultural datasets
```

---

# 21. Data Status

| Dataset / Source | Status | Purpose |
|---|---|---|
| Sentinel-2 | Required | Vegetation monitoring |
| Open-Meteo | Required | Weather |
| ERA5-Land | Required/Preferred | Soil-moisture context |
| NISAR | Optional | Additional soil-moisture evidence |
| NASA POWER | Optional | Historical climate context |
| TNAU / ICAR | Required knowledge source | Agricultural rules |
| Tamil Nadu government data | Optional | Regional context |
| Real labeled water-stress dataset | Not currently available | ML validation |
| Synthetic water-stress data | Development only | ML testing |

---

# 22. Important Rule

The data directory is not a place to store arbitrary downloaded datasets.

Every dataset added to this directory must have:

1. A documented source
2. A documented license
3. A defined purpose
4. Provenance information
5. A real/synthetic classification
6. Known limitations

This prevents undocumented data from entering the FarmSight AI ML pipeline.
