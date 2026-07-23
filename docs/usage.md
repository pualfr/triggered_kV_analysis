# Usage

This document describes how to install and run the retrospective triggered
kilovoltage (kV) image analysis workflow.

> **Research software only.** This workflow is intended for retrospective
> research and offline quality assurance. It has not been validated for
> prospective patient monitoring, clinical decision-making, or real-time beam
> control.

## System requirements

The workflow was developed with Python 3.12.4 on 64-bit Windows and uses CPU
computation. A CUDA-compatible GPU is not required.

The current implementation opens graphical progress, image-display, and summary
windows. A graphical desktop session is therefore required.

## Installation

From the repository root, create and activate an isolated environment.

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

The dependency versions used for the published analysis will be pinned before
the first public release.

### Current local dependency modification

The study environment included a local modification of
torchio.data.Image.get_center() to calculate the planning CT offset from the
RTPLAN isocenter. The development snapshot is described in vendor/README.md.

## Input data

For each patient or treatment course, the workflow requires:

- the planning CT DICOM series;
- the corresponding RT Structure Set;
- the corresponding RT Plan;
- one or more triggered kV RT Image DICOM files.

The DICOM objects must belong to the same treatment dataset. The workflow
checks the relevant Study, Series, SOP Instance, Frame of Reference, RTSTRUCT,
and RTPLAN references before processing.

### Required folder names

Each patient folder must contain:

    01pCT/
    02RTSTRUCT/
    03RTPLAN/

Triggered kV images may be supplied in a single folder:

    04pkV/

or in separate fraction folders:

    04pkV_fr1/
    04pkV_fr2/
    04pkV_fr3/
    04pkV_fr4/
    04pkV_fr5/

Only the fraction folders that exist are processed.

### Batch-processing layout

The current batch entry point scans the current working directory for
subdirectories whose names contain the exact text DICOM Files.

Example:

    analysis_directory/
    |-- DICOM Files_patient001/
    |   |-- 01pCT/
    |   |-- 02RTSTRUCT/
    |   |-- 03RTPLAN/
    |   |-- 04pkV_fr1/
    |   |-- 04pkV_fr2/
    |   +-- 04pkV_fr3/
    |-- DICOM Files_patient002/
    |   |-- 01pCT/
    |   |-- 02RTSTRUCT/
    |   |-- 03RTPLAN/
    |   +-- 04pkV/
    +-- src/
        +-- pkv_motion_workflow.py

Do not create another folder named exactly DICOM Files alongside the patient
folders. That name is used temporarily by the current batch implementation.

## Data protection

Clinical DICOM files are not included in this repository.

The current workflow reads the DICOM PatientID and PatientName attributes and
may reproduce them in generated reports. Input data must be de-identified
before use. Generated reports, logs, images, and CSV files must be treated as
potentially identifiable.

Never commit clinical DICOM files or generated patient outputs to the public
repository.

## Running the workflow

Run the script from the directory containing the patient folders:

    python src/pkv_motion_workflow.py

The script:

1. identifies patient folders containing DICOM Files in their names;
2. processes each available 04pkV or 04pkV_frX folder separately;
3. checks DICOM consistency;
4. extracts triggered kV frames and acquisition geometry;
5. generates or reuses DRRs;
6. preprocesses and registers the images;
7. creates reports, images, transforms, and an execution log;
8. moves the processed patient folder into done/.

### Important: input folders are moved

The current batch implementation moves each processed patient folder into a
done/ directory, including after a failed attempt. Work on a copy of the input
data and keep an independent backup.

This behavior should be replaced by a non-destructive input/output interface
before the public release.

## DRR generation and reuse

The core function accepts a reuse_drr parameter:

- reuse_drr=False generates the DRRs and kV intermediate TIFF images from the
  DICOM inputs, then preprocesses and registers them;
- reuse_drr=True reuses previously generated intermediate images and reruns the
  registration and reporting stages.

The current batch call in process_dicom_folders() is configured as:

    main(reuse_drr=False)

After successful DRR generation, it may be changed back to True to repeat the
registration without regenerating the DRRs.

## Outputs

Outputs are currently written to:

    test/<patient-folder-name>_<fraction-folder-name>/

Example:

    test/DICOM_Files_patient001_04pkV_fr1/
    |-- execution_log.txt
    |-- registration_report.csv
    |-- registration_report.pdf
    |-- output_isocal.tif
    |-- graph/
    |-- imgreport/
    |-- pkslice/
    |-- recap/
    |-- registration/
    +-- tiff_isocal/

Principal outputs:

- registration_report.csv: displacement and acquisition information;
- registration_report.pdf: summary report and registration visualizations;
- execution_log.txt: processing steps, warnings, console output, and errors;
- pkslice/: extracted and preprocessed triggered kV frames;
- tiff_isocal/: generated and preprocessed DRRs;
- recap/: SimpleITK transformation files;
- registration/: registered fusion and checkerboard images;
- imgreport/: PNG images used in the PDF report.

Existing files in recap/, registration/, and imgreport/ are cleared when a
fraction is reprocessed. With reuse_drr=False, pkslice/ and tiff_isocal/ are
also regenerated.

## Interactive windows

The current script displays a progress window during DRR generation, image
windows during registration, and a final batch summary. Image windows must be
closed for processing to continue.

## Troubleshooting

### No patient folders are processed

Confirm that the script is launched from the intended directory, each patient
folder name contains DICOM Files, the 01pCT, 02RTSTRUCT, and 03RTPLAN folders
exist, and either 04pkV or at least one 04pkV_frX folder exists.

### DICOM UID verification fails

Confirm that the planning CT, RTSTRUCT, RTPLAN, and triggered kV images were
exported from the same treatment dataset and that anonymization preserved the
RT references.

### An intermediate TIFF file is missing

reuse_drr=True was probably selected before the intermediate images were
generated. Run the fraction once with reuse_drr=False.

### DRR alignment differs from the study results

The local TorchIO isocenter modification used for the study may not be active
in a clean environment. See the dependency note above and vendor/README.md.

### Processing stops at an image

Check whether a Matplotlib image window is open behind another window. Close it
to continue.

### A patient folder appears to be missing

Check done/. The current implementation moves processed folders there after
each attempt.

## Reporting problems

Do not attach clinical DICOM files or screenshots containing patient
identifiers. Include:

- operating system and Python version;
- installed dependency versions;
- the relevant section of execution_log.txt after removing identifiers;
- the selected reuse_drr value;
- the anonymized input folder structure.
