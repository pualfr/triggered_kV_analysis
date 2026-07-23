# Data privacy and clinical data handling

## Purpose

This repository contains source code only. It does not contain clinical DICOM
data, patient-derived images, registration outputs, or study datasets.

The workflow processes medical imaging data that may contain direct and
indirect patient identifiers. Users are responsible for complying with their
institutional policies, ethics approvals, data-use agreements, and applicable
data-protection regulations.

This document provides technical risk information and is not legal or
regulatory advice.

## No automatic anonymization

The workflow does not anonymize, de-identify, or pseudonymize its inputs or
outputs.

All DICOM data must be appropriately de-identified before being transferred to
an analysis environment that is not approved for identifiable clinical data.
De-identification should be performed with a validated institutional tool and
reviewed according to local policy.

Removing PatientName and PatientID alone is not sufficient.

## Data read by the workflow

Depending on the DICOM object, the script reads or may expose:

- PatientName;
- PatientID;
- AcquisitionDate;
- Study, Series, SOP Instance, and Frame of Reference UIDs;
- RTPLAN and RTSTRUCT references;
- RT Plan Label;
- beam names and beam numbers;
- file and directory names;
- image geometry and acquisition parameters;
- CT and triggered kV pixel data.

Additional DICOM attributes remain present in the original input files even
when the current script does not explicitly read them.

DICOM pixel data may also contain burned-in annotations, embedded overlays,
recognizable anatomy, immobilization devices, or other information that could
contribute to re-identification.

## DICOM relationship integrity

The workflow verifies references between the planning CT, RTSTRUCT, RTPLAN, and
triggered kV objects. De-identification must therefore preserve internal
referential integrity.

If DICOM UIDs are replaced, all corresponding references must be updated
consistently. In particular, de-identification must preserve the relationships
between:

- CT SOP Instance UIDs and RTSTRUCT contour image references;
- CT Series and Study Instance UIDs;
- the Frame of Reference UID;
- RTSTRUCT and RTPLAN references;
- triggered kV images and the referenced RTPLAN.

Randomly changing individual UIDs without updating their references will cause
the workflow's consistency checks to fail and may associate the wrong objects.

Dates, plan labels, beam labels, and institution-specific naming conventions
should also be reviewed because they may act as indirect identifiers.

## Potentially identifiable outputs

Generated files must be treated as potentially identifiable even when the
input DICOM files have been pseudonymized.

### PDF report

registration_report.pdf may contain:

- PatientID;
- PatientName;
- acquisition date;
- RT Plan Label;
- beam names;
- registration images and anatomical information.

The PDF should not be shared publicly unless these fields and images have been
reviewed and cleared for disclosure.

### Execution log

execution_log.txt may contain:

- DICOM UIDs printed during consistency-check failures;
- input and output paths;
- patient-derived folder names;
- exception messages and tracebacks;
- plan or beam information;
- optimizer and processing results.

Logs must be reviewed and sanitized before they are attached to a public issue,
manuscript supplement, or support request.

### CSV files

registration_report.csv contains beam names, gantry angles, and measured
displacements. Beam names or the surrounding folder path may include local or
patient-specific information.

### Derived images and volumes

Generated TIFF, PNG, and NIfTI files no longer provide the same DICOM header
structure, but they remain patient-derived anatomical data. Removing metadata
does not automatically make anatomical images anonymous.

The planning CT NIfTI volume, triggered kV frames, DRRs, fusion images, and
checkerboard images must not be committed to this repository unless a formal
disclosure assessment has confirmed that publication is permitted.

### File and directory names

The current batch workflow constructs output paths from input folder names.
Input folders must not contain patient names, medical record numbers, dates of
birth, or other identifiers.

Use neutral study codes such as:

    DICOM Files_case001

rather than clinical names or identifiers.

## Recommended data-handling workflow

1. Export the required planning CT, RTSTRUCT, RTPLAN, and triggered kV objects
   from the clinical system using an approved process.
2. Create a protected working copy.
3. De-identify the copy with a validated tool.
4. Regenerate or remap DICOM UIDs consistently while preserving all RT
   references.
5. Inspect metadata for residual direct and indirect identifiers.
6. Inspect pixel data for burned-in information or overlays.
7. Replace patient-derived folder and file names with neutral study codes.
8. Run the analysis only in an approved storage and computing environment.
9. Restrict access to authorized personnel.
10. Review all generated reports, logs, tables, and images before sharing.
11. Remove working data according to the approved data-retention policy.

Never use the only available clinical copy as the workflow input. The current
batch implementation moves processed folders into done/, so an independent
backup is required.

## Repository safeguards

The public repository should include a restrictive .gitignore before any
clinical data are placed near the source tree.

At minimum, the following patterns should be excluded:

    *.dcm
    *.dicom
    DICOM Files/
    DICOM Files_*/
    04pkV*/
    01pCT/
    02RTSTRUCT/
    03RTPLAN/
    done/
    test/
    outputs/
    execution_log.txt
    registration_report.csv
    registration_report.pdf
    *.nii
    *.nii.gz
    *.tif
    *.tiff
    __pycache__/
    *.pyc
    .venv/
    venv/

A .gitignore reduces accidental additions but does not replace user review.
Before each commit, inspect the complete list of staged files.

Do not rely only on automated secret scanning: patient identifiers and medical
images are not necessarily detected as secrets.

## Git history and release archives

Deleting a sensitive file in a later commit does not remove it from earlier Git
history, forks, caches, pull requests, or release archives.

Before making the repository public:

- inspect the complete Git history;
- inspect all branches and tags;
- inspect GitHub releases and attached archives;
- inspect large-file storage if it was used;
- confirm that no clinical data or identifiers were ever committed.

If sensitive clinical data have been committed, stop publication and follow the
institutional incident-response procedure. Rewriting Git history may be
necessary but may not remove copies already downloaded or mirrored.

Do not generate a Zenodo archive until this review is complete. A published
archive and DOI are intended to remain persistent.

## Sharing example data

No clinical example data should be included by default.

If an example is needed, prefer:

- a synthetic phantom dataset;
- programmatically generated DICOM objects;
- a public dataset whose license explicitly permits redistribution;
- a minimal non-anatomical test fixture.

A dataset described as anonymized must still undergo institutional review
before redistribution. The ability to download a dataset does not necessarily
grant permission to include it in another repository.

## Publications and supplementary material

The manuscript may provide aggregated study results without distributing the
underlying clinical images.

The code-availability statement should distinguish clearly between:

- publicly available source code;
- non-public clinical DICOM data;
- any aggregated or synthetic example data that are actually distributed.

A suitable data-availability statement is:

> The source code is publicly available in the archived software repository.
> The clinical imaging data are not publicly available because they contain
> sensitive patient information and are subject to institutional and regulatory
> restrictions.

Any process for requesting controlled access to study data should be described
only if such access has been approved and can genuinely be provided.

## Reporting issues

Do not upload clinical DICOM files, patient-derived images, PDF reports, CSV
files, or unsanitized logs to a public GitHub issue.

When reporting a problem, provide only:

- operating system and Python version;
- dependency versions;
- a synthetic or non-identifiable reproduction when possible;
- the minimum relevant log excerpt after manual review;
- neutral placeholder paths and study codes.

If a problem cannot be reproduced without clinical data, use an institutionally
approved secure communication and transfer method.

## Security and clinical disclaimer

This software is provided for retrospective research and offline quality
assurance. It is not a medical device and must not be used as the sole basis
for patient positioning, treatment interruption, beam control, diagnosis, or
another clinical decision.

A local installation should follow institutional cybersecurity requirements,
including access control, storage encryption where required, backup,
workstation maintenance, and secure deletion.
