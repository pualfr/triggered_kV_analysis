# Retrospective triggered kV image analysis workflow

Python workflow for retrospective intrafraction motion verification from
triggered kilovoltage (kV) images acquired during stereotactic body
radiotherapy (SBRT) for bone metastases.

> **Research software only.** This software is intended for retrospective
> research and offline quality assurance. It has not been validated for
> prospective patient monitoring, real-time beam control, or clinical
> decision-making.

## Associated manuscript

**Retrospective intrafraction motion verification using triggered kilovoltage
images during bone metastases stereotactic body radiotherapy**

This repository contains the image-level processing workflow developed for the
study. The version cited by the manuscript will be archived as a versioned
software release with a persistent DOI.

## Purpose

Triggered kV images acquired during treatment contain information about the
position of internal bony anatomy but are commonly reviewed only visually. This
workflow retrospectively registers each triggered image to an angle-matched
digitally reconstructed radiograph (DRR) generated from the planning CT.

The workflow performs:

1. DICOM consistency checks across the planning CT, RTSTRUCT, RTPLAN, and
   triggered kV images.
2. Extraction of triggered frames, gantry angles, imaging geometry, and beam
   information.
3. Angle-specific DRR generation with DiffDRR.
4. Intensity preprocessing and focal cropping around the treatment isocentre.
5. Rigid in-plane translation registration with SimpleITK.
6. Conversion of image-plane offsets to millimetres.
7. Generation of transforms, CSV and PDF reports, fusion images,
   checkerboards, and execution logs.

## Scope of the current code

The current script produces one two-dimensional displacement estimate per
triggered kV image.

The following study-level steps are not yet included:

- classification and exclusion of aberrant registrations;
- distinction between isolated and systematic registration failures;
- detection of sustained displacement events across consecutive images;
- aggregation by patient, fraction, centre, anatomical site, or gantry angle;
- statistical analyses and manuscript tables or cohort figures.

These downstream steps must be added as a documented analysis module for full
computational reproduction of the manuscript results.

## Repository structure

    .
    |-- README.md
    |-- requirements.txt
    |-- src/
    |   +-- pkv_motion_workflow.py
    |-- docs/
    |   |-- usage.md
    |   |-- workflow.md
    |   +-- data_privacy.md
    +-- vendor/
        |-- README.md
        +-- local_dependency_snapshot.zip

The vendor snapshot is retained temporarily for traceability of the original
development environment. It is not the recommended installation method and
should be replaced by an integrated isocentre calculation or a small documented
patch before the first public release.

## Requirements

The workflow was developed with:

- Python 3.12.4;
- 64-bit Windows;
- CPU-based SimpleITK registration;
- a graphical desktop session.

Main dependencies include:

- numpy==1.26.4
- pandas==2.2.2
- matplotlib==3.9.0
- pydicom==3.0.1
- SimpleITK==2.5.2
- diffdrr==0.5.1
- torch==2.2.2
- torchio==0.20.17
- opencv-python==4.10.0.82
- scikit-image==0.23.2
- Pillow==10.3.0
- tifftools==1.6.1
- reportlab==4.2.0
- loguru==0.7.3

See requirements.txt for the installation list. Direct runtime dependencies are
pinned to the versions recorded in the original study environment.

## Installation

From the repository root, create an isolated environment.

PowerShell:

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

Command Prompt:

    py -3.12 -m venv .venv
    .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

Detailed installation information and current dependency caveats are provided
in docs/usage.md.

## Input data

For each patient or treatment course, the workflow expects:

    DICOM Files_case001/
    |-- 01pCT/
    |-- 02RTSTRUCT/
    |-- 03RTPLAN/
    |-- 04pkV_fr1/
    |-- 04pkV_fr2/
    +-- 04pkV_fr3/

A single 04pkV/ folder is also supported. Only the available fraction folders
are processed.

The folder name must currently contain the exact text DICOM Files because the
batch entry point uses this text to identify datasets.

Clinical DICOM data are not distributed with this repository.

## Running the workflow

Run the script from the directory containing the patient folders:

    python src/pkv_motion_workflow.py

The current development version uses:

    main(reuse_drr=False)

The current batch implementation moves processed patient folders into
done/. Always work from a protected copy of the input data.

See docs/usage.md for the complete procedure and troubleshooting guidance.

## Processing summary

### DRR generation

DRRs are generated from the planning CT using the triggered-image gantry angle
and source-to-detector distance extracted from DICOM metadata. The current
configuration uses:

- DiffDRR 0.5.1;
- a 256 by 256 rendering grid;
- a bone attenuation multiplier of 3;
- a 1000 mm source-to-isocentre translation;
- an RTPLAN-isocentre correction from the original modified environment.

### Preprocessing

The triggered image and corresponding DRR undergo histogram matching, adaptive
histogram equalization, CLAHE, 16-bit conversion, and central cropping to a
150 mm by 150 mm region around the treatment isocentre. Gaussian smoothing is
applied to the triggered image before registration.

### Registration

The reported transform is a two-dimensional SimpleITK translation estimated
with the Mean Squares metric, a multi-resolution pyramid, and Regular Step
Gradient Descent optimization.

The DRR is the moving image and the triggered kV image is the fixed image.

X and Y are image-plane components and must not be interpreted as fixed
three-dimensional patient-coordinate directions across all gantry angles.

Full parameter definitions and coordinate conventions are provided in
docs/workflow.md.

## Outputs

Outputs are currently written below:

    test/<patient-folder-name>_<fraction-folder-name>/

Principal outputs include:

- registration_report.csv: image-level X and Y displacement estimates;
- registration_report.pdf: metadata, summary statistics, plots, and
  registration visualizations;
- execution_log.txt: processing messages, optimizer output, warnings, and
  errors;
- recap/: SimpleITK transforms;
- registration/: fusion and checkerboard TIFF images;
- imgreport/: PNG images used in the PDF report;
- pkslice/: extracted and preprocessed triggered kV images;
- tiff_isocal/: generated and preprocessed DRRs.

Generated reports and images may contain patient identifiers or
patient-derived anatomy.

## Documentation

- docs/usage.md: installation, input layout, execution, outputs, and
  troubleshooting.
- docs/workflow.md: scientific processing steps, fixed parameters, coordinate
  conventions, and methodological limitations.
- docs/data_privacy.md: DICOM de-identification, output risks, repository
  safeguards, and safe issue reporting.

## Reproducibility notes

The study environment contained a local modification of
torchio.data.Image.get_center() that used the RTPLAN isocentre when centring the
planning CT for DRR generation. The current vendor archive documents this
environment but is not an appropriate long-term distribution mechanism.

Before the archived release, the project should:

- integrate the isocentre calculation into the project source;
- remove full third-party package snapshots and compiled cache files;
- pin all relevant dependency versions;
- expose input, output, and reuse options through a command-line interface;
- make input handling non-destructive;
- add a synthetic smoke test;
- add the cohort-level analysis module used for the manuscript.

## Data availability and privacy

No clinical imaging data are included in this repository. The clinical DICOM
data underlying the study are not publicly available because they contain
sensitive patient information and are subject to institutional and regulatory
restrictions.

The workflow does not anonymize DICOM data. It reads PatientID and PatientName
and may include them in generated PDF reports. Users must de-identify inputs,
preserve DICOM referential integrity, and review all outputs before sharing.

See docs/data_privacy.md before processing any clinical data.

## Citation

Citation metadata for the versioned software release will be provided in
CITATION.cff. The archived release DOI should be cited together with the
associated manuscript when this software is used in published work.

Until the manuscript and software DOI are available, cite the manuscript title
and the exact repository version or commit used.

## License

License terms will be provided in the root LICENSE file before the public
release. Third-party dependencies remain subject to their respective licenses.

## Reporting issues

Do not attach clinical DICOM files, patient-derived images, unsanitized reports,
or logs containing identifiers to public issues.

Provide a synthetic reproduction where possible and follow the guidance in
docs/data_privacy.md.

## Disclaimer

This software is provided without clinical performance guarantees. It is not a
medical device and must not be used as the sole basis for patient positioning,
treatment interruption, beam control, diagnosis, or another clinical decision.
