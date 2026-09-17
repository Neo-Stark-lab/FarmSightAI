# FarmSight AI — Data Source Research

## 1. Purpose

This document defines the recommended external data sources for FarmSight AI.

FarmSight AI is an explainable Digital Farm Twin for small and marginal farmers in Tamil Nadu. The system combines satellite observations, weather information, soil-moisture information, agricultural knowledge, historical observations, and machine-learning outputs to identify and explain crop stress.

The initial target crops are:

- Rice
- Groundnut
- Maize

The primary deep implementation focus is:

> Water-stress and irrigation intelligence.

The system must distinguish between:

1. Directly observed measurements
2. Derived remote-sensing features
3. Model predictions
4. Agricultural-rule interpretations
5. Recommendations

The system must not present inferred quantities as if they were directly measured.

---

# 2. Recommended Data Sources

## 2.1 Sentinel-2

### Role

Primary source for vegetation and surface-condition observations.

### Recommended use

Sentinel-2 imagery can provide:

- NDVI
- NDMI
- vegetation condition
- vegetation change
- temporal crop-condition trends
- spatial variation across a farm

Sentinel-2 should be the primary remote-sensing source for the Digital Farm Twin.

### Important characteristics

- Optical satellite imagery
- Multispectral bands
- Useful for vegetation monitoring
- Provides spatial information at field scale
- Repeated observations allow temporal analysis

### Recommended processing

For the initial prototype, derive:

```text
NDVI
NDMI
NDVI 7-day change
NDVI 30-day change
NDMI change
```

The exact observation date must be stored with every derived feature.

### Cloud limitations

Optical imagery can be affected by:

- clouds
- cloud shadows
- haze
- missing observations

The pipeline must therefore retain:

```text
observation_date
source
cloud_quality
availability_status
```

If a recent observation is unavailable, the system should use the most recent valid observation while reducing confidence.

### Recommended access

Google Earth Engine is recommended for the hackathon because it simplifies satellite-data discovery, filtering and processing.

The implementation should avoid downloading large raw satellite archives into the Git repository.

---

# 3. Soil Moisture

## 3.1 ERA5-Land

ERA5-Land is recommended as a practical large-scale soil-moisture source for the prototype.

### Role

Use soil moisture as contextual information for water-stress reasoning.

Potential uses:

- current soil-moisture context
- soil-moisture trend
- comparison against historical conditions
- supporting evidence for water-stress detection

### Important limitation

ERA5-Land does not represent direct field-level soil-moisture measurements.

Therefore:

> ERA5-Land soil moisture must be treated as contextual/modelled environmental information rather than ground-truth field measurements.

It should not be presented to the farmer as an exact measurement of soil moisture at a particular point in the field.

---

## 3.2 NISAR

NISAR soil-moisture products are potentially valuable for the project, particularly because they provide soil-moisture information from an Indian/ISRO-supported Earth-observation mission.

However, accessibility, spatial resolution and product availability must be verified during implementation.

NISAR should therefore be treated as:

```text
Preferred supplementary source
```

rather than a hard dependency for the first working prototype.

### Scientific limitation

NISAR soil-moisture information should not automatically be interpreted as field-level ground truth.

It is an additional observation source that can strengthen the evidence chain when available.

---

# 4. Weather Data

## 4.1 Open-Meteo

Open-Meteo is recommended as the primary operational weather source for the prototype.

### Useful variables

The system can obtain:

- rainfall
- temperature
- humidity
- wind
- weather forecasts
- historical weather information

### Features

Useful FarmSight features include:

```text
rainfall_7d
rainfall_30d
rainfall_anomaly
temperature_mean
temperature_anomaly
```

Weather information can be combined with satellite and soil-moisture observations.

Example:

```text
Low rainfall
+
High temperature
+
Declining NDVI
+
Declining NDMI
=
Stronger evidence of water stress
```

The ML model must still determine the actual risk rather than the rule engine assuming that every rainfall deficit means water stress.

---

# 5. NASA POWER

NASA POWER can be used as a secondary historical climate/weather source.

### Recommended use

- historical weather context
- climate baselines
- validation of weather trends
- historical comparisons

It is particularly useful when constructing:

```text
historical_deviation
temperature_anomaly
rainfall_anomaly
```

### Role

NASA POWER should complement Open-Meteo rather than necessarily replace it.

---

# 6. Tamil Nadu Agricultural Data

Tamil Nadu government agricultural statistics and agricultural datasets should be used to provide regional agricultural context.

Potential information includes:

- crop information
- agricultural production
- district-level agricultural statistics
- crop distributions
- seasonal information

These datasets are useful for:

- crop-context understanding
- regional baselines
- validation
- agricultural context

They should not be treated as field-level sensor measurements.

---

# 7. Agricultural Knowledge Sources

The recommendation engine requires agricultural knowledge in addition to raw environmental observations.

Recommended sources include:

- Tamil Nadu Agricultural University (TNAU)
- ICAR
- relevant government agricultural departments

These sources can support:

- crop growth stages
- crop water requirements
- irrigation guidance
- crop-specific stress interpretation
- pest/disease knowledge
- nutrient-management guidance

Agricultural rules must be versioned and traceable to their source.

---

# 8. Real Labeled Water-Stress Dataset

## 8.1 Requirement

The ML model ideally requires real observations with a meaningful water-stress label.

A suitable dataset should contain as many of the following as possible:

```text
crop
location
time
water-stress label
soil moisture
vegetation indicators
weather
growth stage
field information
```

The target label must genuinely represent water stress or a defensible proxy for water stress.

A dataset containing only NDVI, soil moisture or rainfall is not automatically a labeled water-stress dataset.

---

## 8.2 Dataset Investigation Result

No suitable real labeled dataset specifically matching:

```text
Tamil Nadu
+
Rice / Groundnut / Maize
+
Water-stress labels
+
Remote-sensing/weather-compatible features
```

was identified as sufficiently suitable for the initial hackathon implementation.

Therefore, the ML implementation should not claim real-world validation accuracy unless suitable ground-truth labels are obtained.

---

# 9. Synthetic Data

If a suitable real labeled dataset cannot be obtained within the hackathon timeframe, synthetic data may be used for:

- pipeline development
- model-development testing
- unit tests
- integration testing
- demonstration

Synthetic labels must be clearly marked.

For example:

```text
label_source = synthetic
```

Synthetic-data performance must not be reported as real-world model accuracy.

The final system should clearly distinguish:

```text
REAL OBSERVATION
SYNTHETIC TRAINING DATA
MODEL PREDICTION
```

---

# 10. Canonical Feature Mapping

FarmSight AI uses the following canonical feature vector:

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

## Feature-to-source mapping

| Feature | Primary source | Type |
|---|---|---|
| `ndvi_current` | Sentinel-2 | Derived |
| `ndvi_7d_change` | Sentinel-2 | Derived |
| `ndvi_30d_change` | Sentinel-2 | Derived |
| `ndmi_current` | Sentinel-2 | Derived |
| `ndmi_change` | Sentinel-2 | Derived |
| `rainfall_7d` | Open-Meteo | Derived |
| `rainfall_30d` | Open-Meteo | Derived |
| `rainfall_anomaly` | Open-Meteo / NASA POWER | Derived |
| `temperature_mean` | Open-Meteo | Derived |
| `temperature_anomaly` | Open-Meteo / NASA POWER | Derived |
| `soil_moisture` | ERA5-Land / NISAR where available | Observation/context |
| `soil_moisture_change` | ERA5-Land / NISAR | Derived |
| `crop` | Farmer input | Input |
| `crop_stage` | Sowing date + crop rules | Derived |
| `historical_deviation` | Historical farm observations | Derived |
| `neighboring_deviation` | Comparable nearby fields | Derived |

---

# 11. Historical Baselines

Historical observations should be used to establish a farm-specific baseline.

Example:

```text
Current NDVI
vs
Historical NDVI for the same field/crop/stage
```

This is more meaningful than simply comparing a farm against a global average.

Historical comparison should consider:

- crop
- growth stage
- season
- observation quality
- date
- weather context

The system should not compare unrelated crop stages.

---

# 12. Nearby-Field Baselines

Nearby fields may provide useful context.

However:

> Nearby fields are not automatically comparable.

Comparison should consider:

- crop
- approximate crop stage
- season
- location
- observation date
- environmental conditions

If insufficient comparable fields exist, the system should avoid presenting the comparison as strong evidence.

---

# 13. Data Freshness

Every observation should contain provenance and freshness information.

Recommended metadata:

```text
source
provider
observation_time
retrieval_time
processing_time
quality_status
age
```

Example:

```json
{
  "source": "Sentinel-2",
  "observation_time": "2026-09-15",
  "quality_status": "valid"
}
```

The system should distinguish between:

```text
latest available observation
```

and

```text
real-time measurement
```

Satellite observations should not be described as real-time.

---

# 14. Missing Data

Missing data is expected.

Examples:

- cloud-covered satellite image
- unavailable soil-moisture product
- missing weather observation
- old satellite observation
- incomplete historical baseline

The system should not invent missing values.

Possible strategy:

```text
Recent satellite unavailable
        ↓
Use latest valid satellite observation
        +
Use latest weather information
        +
Reduce confidence
```

The user interface should clearly indicate data freshness.

---

# 15. Evidence Fusion

The system should combine multiple independent evidence sources.

Example:

```text
Satellite:
NDVI ↓
NDMI ↓

Weather:
Rainfall ↓
Temperature ↑

Soil:
Soil moisture ↓
```

The combination provides stronger evidence than any single feature.

However, the system should not automatically conclude that water stress is present.

Possible alternative explanations include:

- crop-stage variation
- harvest/senescence
- nutrient stress
- pest/disease stress
- cloud/artifact contamination
- recent irrigation
- recent rainfall
- abnormal weather

The ML model and agricultural rules should consider these alternatives.

---

# 16. Recommended Hackathon Priority

## MUST HAVE

### Satellite

- Sentinel-2
- NDVI
- NDMI
- temporal change

### Weather

- Open-Meteo
- rainfall
- temperature

### Soil moisture

- ERA5-Land or another accessible source

### Agricultural context

- crop
- sowing date
- crop stage

### ML

- tabular water-stress model
- explainable feature contributions
- confidence/data-quality information

### Historical context

- same-field historical observations where available

---

# 17. SHOULD HAVE

- NISAR soil moisture
- NASA POWER historical validation
- comparable nearby-field baseline
- stronger crop-stage rules
- additional agricultural datasets
- improved missing-data handling

---

# 18. FUTURE

Potential future extensions:

- physical IoT soil sensors
- drone imagery
- higher-resolution soil moisture
- validated field-level water-stress labels
- larger multi-season datasets
- disease/weed image models
- nutrient-stress models
- automated irrigation control

These are outside the minimum viable hackathon implementation.

---

# 19. Licensing and Repository Policy

The Git repository should contain:

- source metadata
- processing code
- small permitted sample datasets
- dataset documentation
- download instructions

The repository should not contain:

- large satellite archives
- private farmer data
- credentials
- API keys
- restricted datasets
- large generated raster collections

Large datasets should be retrieved during pipeline execution or documented with reproducible download instructions.

---

# 20. Scientific Guardrails

FarmSight AI must follow these rules.

### Rule 1

Do not claim satellite imagery directly measures exact NPK.

Use:

```text
nutrient-stress risk
```

rather than:

```text
exact nitrogen concentration
```

unless ground-validated measurements exist.

### Rule 2

Do not call satellite data real-time.

Use:

```text
latest available observation
```

or:

```text
latest valid satellite observation
```

### Rule 3

Do not claim exact irrigation volume from satellite imagery alone.

The system provides:

```text
water-stress risk
```

and:

```text
context-aware irrigation guidance
```

### Rule 4

Do not report model accuracy without real-world validation data.

### Rule 5

Confidence is not the probability that the prediction is correct.

It represents model/data confidence based on the available evidence and data quality.

### Rule 6

When evidence is insufficient, the system should say:

```text
Insufficient evidence
```

rather than inventing a cause.

---

# 21. Final Data Architecture

```text
                 FARMER INPUT
                      │
          ┌───────────┼───────────┐
          │           │           │
       Location      Crop     Sowing Date
          │           │           │
          └───────────┼───────────┘
                      │
                      ▼
               FARM BOUNDARY
                      │
                      ▼
              DATA COLLECTION
                      │
       ┌──────────────┼──────────────┐
       │              │              │
   Sentinel-2      Weather      Soil Moisture
       │              │              │
       │         Open-Meteo      ERA5-Land
       │         NASA POWER       NISAR
       │              │              │
       └──────────────┼──────────────┘
                      │
                      ▼
              FEATURE ENGINE
                      │
                      ▼
               FEATURE SET
                      │
                      ▼
                ML MODEL
                      │
              ┌───────┴───────┐
              │               │
            Risk         Contributions
              │               │
              └───────┬───────┘
                      │
                      ▼
             AGRICULTURAL RULES
                      │
                      ▼
                EXPLANATION
                      │
                      ▼
              RECOMMENDATION
```

---

# 22. Conclusion

For the hackathon implementation, FarmSight AI should prioritize a reliable multi-source data pipeline rather than attempting to collect every possible agricultural dataset.

The recommended minimum combination is:

```text
Sentinel-2
+
Open-Meteo
+
ERA5-Land
+
Agricultural knowledge
+
Historical field observations
```

This combination can support the Digital Farm Twin and water-stress intelligence concept without requiring physical sensors.

The largest scientific limitation is the lack of suitable real labeled water-stress ground truth for the target crops and region. Therefore, model validation must remain explicitly limited until appropriate field labels are obtained.
