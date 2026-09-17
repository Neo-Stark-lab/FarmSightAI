# FarmSight AI — Dataset Discovery

## 1. Investigation Goal

The objective was to identify a real, public, labeled dataset containing water-stress (or drought-stress) labels for agriculture—specifically targeting Rice, Groundnut, or Maize in Tamil Nadu, India, or comparable regions. The dataset needed to align with our canonical feature vector containing Sentinel-2 derived indices (NDVI, NDMI), Open-Meteo weather data, and soil moisture context.

## 2. Search Methodology

We investigated several public repositories including Zenodo, Kaggle, Mendeley Data, and IEEE DataPort, searching for combinations of "water stress", "drought stress", "NDVI", and the target crops.

## 3. Candidate Datasets Evaluated

### Candidate A: UAV-Based Multispectral Maize Dataset for Water Stress 2025 (Zenodo)

- **URL/Source**: Zenodo / Recent research publications
- **Target label**: Maize water stress and common rust
- **Features**: UAV multispectral imagery, NDVI, NDRE, CWSI
- **Geography/Scale**: Field-scale, drone-based
- **Suitability**: **B. Useful but incomplete.** While it contains excellent water-stress labels for Maize, the features are based on high-resolution UAV multispectral data rather than the Sentinel-2 and ERA5-Land canonical features our architecture relies on. It cannot be directly used to train our tabular model without significant mismatch.

### Candidate B: Kaggle Agricultural Crop Stress Datasets

- **URL/Source**: Kaggle
- **Target label**: General crop stress, often image classification classes (e.g., Healthy vs. Stressed)
- **Features**: RGB images or generic tabular environmental data
- **Suitability**: **C. Not suitable for water-stress modeling.** Most of these datasets are computer vision datasets (plant leaves) or synthetic tabular data that lack the rigor of field-validated water-stress targets matching our satellite/weather temporal features.

### Candidate C: WRI Aqueduct Global Water Risk

- **URL/Source**: World Resources Institute
- **Target label**: Regional water risk / drought exposure
- **Features**: Macro-level climate and hydrological features
- **Suitability**: **C. Not suitable for water-stress modeling.** This is a regional risk dataset, not a field-level or zone-level crop water-stress dataset.

## 4. Conclusion and Decision

**OPTION C — No suitable public labeled dataset is available.**

We must explicitly state: **"No suitable real labeled dataset was identified for reliable real-world water-stress validation."**

We cannot find a public dataset that provides ground-truth water-stress labels for Rice, Groundnut, or Maize that maps cleanly to our canonical Sentinel-2 + Weather + Soil Moisture feature vector.

### Path Forward:

- We will build the complete ML architecture, preprocessing pipelines, and inference contracts so the system is fully prepared to accept real labeled data when it becomes available (e.g., through field deployment).
- We will generate a **synthetic dataset** strictly for unit testing, integration testing, and verifying the pipeline code.
- **Scientific Guardrail:** We will not report synthetic accuracy as real-world performance, nor will we claim field validation based on this synthetic data. The synthetic data will be explicitly flagged as `synthetic` in its metadata.
