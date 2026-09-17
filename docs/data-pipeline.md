# Data pipeline

LAP 4 converts source-attributed zone observations into the canonical version
`1.0` `WaterStressScoringRequest`. It does not train a model or make a farm
recommendation.

## Providers and data status

`OpenMeteoProvider` is a real-data adapter for daily precipitation and mean
temperature when a representative point is supplied. It has no hard-coded key.
`GoogleEarthEngineProvider` and `ERA5LandProvider` are intentionally explicit
configuration boundaries: authenticated/approved adapters must be injected by
deployment. They cannot manufacture observations when unavailable.

`FixtureProvider` supplies deterministic local observations exclusively for
tests and demo development. Fixtures are mock data, not real observations.
The existing ML training data remains synthetic and is not field validation.

## Processing

Satellite adapters return cloud-screened zone observations or `sentinel_bands`.
The pipeline calculates NDVI `(NIR-red)/(NIR+red)` and NDMI `(NIR-SWIR)/(NIR+SWIR)`
before aggregation. It selects the newest valid observation within 30 days of
analysis and comparison observations nearest the 7/30-day target within three
days; it stores the actual timestamps. It never calls satellite data real-time.

Weather windows are `(reference_time - N days, reference_time]`: rainfall is
summed and temperature is averaged. Anomalies only exist when a provider gives
an explicit historical baseline. Soil moisture is modelled context, never
field-scale ground truth; its spatial resolution is retained.

For operational weather, `OpenMeteoProvider` requests the inclusive 30-day
daily range ending on `reference_time` (reference date minus 29 days through
the reference date). This supplies both 7-day and 30-day aggregations; it does
not create a historical anomaly baseline.

Historical deviation uses a `comparable: true` same-field baseline; neighbouring
deviation additionally requires a privacy-filtered, comparable baseline from
upstream. Absent comparability leaves the value null.

The rules define accepted crop-stage names but no crop/day ranges. To avoid
inventing a crop calendar, crop stage deterministically remains `unknown` with
its missingness documented.

## Missingness, freshness, provenance

Unavailable values are `null`, never zero/imputed, and include an allowed
missing reason. Defaults are 120h satellite, 48h weather, and 168h soil
moisture, configurable through `DataPipeline(freshness_hours=...)`. Metadata
keeps source observation IDs, source, observed/retrieved timestamps, spatial
aggregation/resolution, calculation, and freshness. Stale observations remain
traceable; they are not current data.

## Local use

Run `pytest`. Tests use only `FixtureProvider` and no external API. A deployment
can instantiate `OpenMeteoProvider` and inject authenticated Sentinel-2/ERA5
providers with the same `fetch(context)` interface.
