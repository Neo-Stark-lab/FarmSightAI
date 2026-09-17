# Agricultural decision rules

## Purpose and boundary

This versioned policy turns a valid ML **water-stress risk** prediction plus
traceable observations and farm context into a conservative, conditional
recommendation. It does not change the model prediction, calculate irrigation
volume, or establish a field diagnosis. The policy is designed for rice,
groundnut, and maize farms in Tamil Nadu.

Its output is a reviewable recommendation with triggered rule IDs, feature and
observation references, freshness, alternative possible causes, and explicit
limitations. It is a decision-support layer, not an agronomist or irrigation
controller.

## Inputs and outputs

Inputs use the canonical `WaterStressScoringRequest` and response in
[`ml-contract.md`](ml-contract.md): crop, upstream crop stage, feature values,
per-feature metadata/missingness/freshness, quality status, and ML prediction.
It can also accept optional upstream `evidence_flags` such as
`soil_moisture_low` or `recent_rainfall`. Flags must be source-attributed and
are never manufactured by this module.

Outputs contain an action type (`MONITOR`, `PRIORITIZE_FIELD_CHECK`,
`CONSIDER_IRRIGATION`, `REASSESS_AFTER_RAINFALL`, `CHECK_IRRIGATION_SYSTEM`,
`CHECK_CROP_CONDITION`, or `SEEK_FIELD_INSPECTION`), a conditional action,
priority, deterministic explanation, possible causes, evidence references,
freshness summary, triggered conditions, rule-set version, and limitations.

## Interpreting crop context

The accepted stages are `initial`, `vegetative`, `reproductive`, `maturity`,
and `unknown`. The upstream pipeline derives a stage from sowing date only when
its crop calendar is documented; this policy consumes that result rather than
imposing a universal stage schedule. Stage is included in every result. A
missing stage limits stage-specific wording but does not stop general safety
advice.

For all three crops, `reproductive` is handled as a stage where a multi-signal
water-stress risk merits prompt field checking. This is a **project heuristic**
for prioritising verification, not a crop-water prescription. The policy does
not assume crop-specific days after sowing or irrigation quantities.

## Water-stress and recovery reasoning

The strongest irrigation consideration requires a valid high ML risk plus at
least two fresh, independent supporting indications: declining vegetation or
moisture indicators, rainfall anomaly below its documented baseline, or a
declining/low source-attributed soil-moisture indicator. This is a **project
heuristic** based on the data-source research's evidence-fusion guidance.

Recent rainfall, stable/improving vegetation/moisture indicators, or stale
satellite observations are conflicting evidence. They reduce recommendation
strength and favour `REASSESS_AFTER_RAINFALL` or `PRIORITIZE_FIELD_CHECK` over
an irrigation consideration. A low soil-moisture value has no global numeric
cut-off here; it must arrive as a validated, source-specific upstream flag.

An irrigation-system check is suggested only when a water-stress pattern
persists despite recent rain or a documented irrigation event. It is an
inspection prompt, not a claim that the system has failed.

## Vegetation, nutrient, pest, and historical context

Declining NDVI/NDMI can support a vegetation-stress pattern, but may reflect
crop stage, cloud artefacts, nutrient stress, pests/disease, or other causes.
When vegetation declines without enough water evidence, the engine reports
possible nutrient stress or possible pest/disease-related stress and asks for a
field inspection; it never diagnoses either condition.

Historical deviation is considered only when metadata says the comparison is
same-field, same-crop, and comparable stage. Nearby-field deviation is used
only when metadata declares crop, stage, season, timing, and environmental
comparability. Neither comparison proves stress. Missing or invalid comparison
metadata produces a limitation rather than a substitute baseline.

## Missing, stale, conflicting, and multiple evidence

Null features are never imputed. Their documented `missing_reason` is surfaced
as a limitation. Stale evidence remains traceable but is not counted as fresh
support; stale satellite data adds a limitation. Missing weather prevents
rainfall-based reasoning, while missing soil moisture prevents soil-moisture
claims.

The engine preserves multiple possible causes rather than forcing one. Water,
heat, nutrient, and pest/disease-related stress can appear together, each with
qualitative evidence strength. With no usable evidence it returns `unknown`
and an `SEEK_FIELD_INSPECTION` recommendation.

## Prioritisation and explainability

Priority reflects attention needed, not probability or model confidence.
Actions follow this order: insufficient/invalid prediction -> field inspection;
fresh multi-signal high risk -> consider irrigation; rainfall conflict ->
reassess after rainfall; stale/conflicting evidence -> field check; otherwise
monitor. Deterministic templates mention only recorded signals.

Every response must preserve `rule_id`, conditions, supporting features,
source-observation IDs, crop, stage, freshness and limitations. The YAML file
is the policy source; implementation-specific signal detection only evaluates
relative changes, upstream flags, and metadata validity.

## Scientific limitations and sources

**Source-supported facts:** Sentinel-2-derived NDVI/NDMI are temporal
vegetation/surface-condition indicators; weather, soil-moisture context, and
multiple sources may strengthen an interpretation; satellite observations can
be cloud-limited and are not real-time; ERA5-Land/NISAR context is not direct
field-level ground truth. These statements follow
[`01_DATA_SOURCE_RESEARCH.md`](01_DATA_SOURCE_RESEARCH.md).

**Project heuristics:** requiring converging signals, using relative direction
instead of global thresholds, qualitative evidence levels, and the action
priority above. They require future review with TNAU/ICAR guidance and field
validation.

The engine never claims exact NPK, an exact water amount, a disease diagnosis,
or model correctness. Confidence remains ML/data confidence, not the chance a
recommendation is correct. Synthetic data supports development only.

## Examples

* A rice reproductive zone has a high valid risk, negative rainfall anomaly,
  declining NDMI, and declining soil-moisture context. The engine records
  `WS001`, reports high water-stress evidence, and says to check the field and
  consider irrigation based on local conditions.
* A groundnut zone has a low-soil-moisture flag but recent rainfall and stable
  vegetation. The engine records the conflict and says to reassess after
  rainfall; it does not produce a strong irrigation recommendation.
* A maize zone has declining NDVI but no weather or soil-moisture evidence.
  It reports possible nutrient or pest/disease-related stress, lists the data
  gaps, and asks for field inspection.
