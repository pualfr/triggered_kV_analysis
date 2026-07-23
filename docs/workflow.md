# Processing workflow

## Scope

This document describes the scientific and technical processing implemented in
src/pkv_motion_workflow.py.

The program converts planning and triggered-imaging DICOM data into
angle-specific digitally reconstructed radiographs (DRRs), performs focal
two-dimensional image registration, and exports one in-plane displacement
estimate per triggered kV image.

The current source code covers the image-level workflow. Cohort-level quality
control, exclusion of aberrant registrations, sustained-event detection, and
statistical analyses reported in the associated manuscript are downstream
steps and are not currently implemented in this script.

## Workflow overview

For each patient and treatment fraction, the processing sequence is:

    Planning CT + RTSTRUCT + RTPLAN + triggered kV DICOM
                              |
                              v
                    DICOM reference checks
                              |
                              v
             Triggered-frame and geometry extraction
                              |
                              v
               Angle-specific DRR generation
                              |
                              v
              Intensity preprocessing and cropping
                              |
                              v
           Rigid in-plane translation registration
                              |
                              v
        Displacement conversion to millimetres and QC images
                              |
                              v
               CSV, PDF, transforms, images, and log

Each triggered frame is processed independently against the DRR generated at
its corresponding acquisition angle.

## 1. DICOM consistency checks

Before image processing, the workflow reads identifiers and references from the
planning CT, RTSTRUCT, RTPLAN, and triggered kV RT Image objects.

The checks include:

- consistency of the CT Frame of Reference UID;
- consistency of CT Study and Series Instance UIDs;
- correspondence between CT SOP Instance UIDs and the RTSTRUCT contour image
  references;
- correspondence between the RTPLAN and its referenced RTSTRUCT;
- correspondence between each triggered kV object and its referenced RTPLAN.

Processing continues only when these checks return successfully.

These checks confirm DICOM linkage. They do not assess image quality,
anonymization, treatment correctness, or the clinical suitability of the
dataset.

## 2. Triggered kV image extraction

For each triggered kV DICOM object, the workflow reads:

- the Exposure Sequence;
- the gantry angle of each frame;
- the RT Image source-to-detector distance (RTImageSID);
- the referenced treatment beam number;
- the image dimensions and Image Plane Pixel Spacing;
- the acquisition date;
- the patient and plan identifiers used in the report.

Multi-frame pixel data are exported to individual 16-bit TIFF images in
pkslice/. Single-frame RT Image objects are also supported.

Frame order is inherited from the order returned for the DICOM files and from
the order of items in each Exposure Sequence. The current implementation does
not explicitly sort objects using acquisition time or Instance Number.
Datasets should therefore be exported with unambiguous file ordering.

## 3. Imaging geometry and scale

The gantry angle and source-to-detector distance are read from the triggered kV
DICOM metadata. A source-to-isocentre distance of 1000 mm is used in the DRR
camera translation.

Detector sampling is derived from ImagePlanePixelSpacing, Rows, Columns, and
RTImageSID. The current variables used for conversion at isocentre are:

    sx = spacingx_rescaled * 256 / Columns / (SID / 1000)
    sy = spacingy_rescaled * 256 / Rows    / (SID / 1000)

where the rescaled spacing values account for the 256 by 256 DRR rendering
grid.

The SimpleITK transforms are estimated from TIFF images without an explicitly
assigned physical spacing. Their translation parameters are therefore treated
as pixel offsets and multiplied by sx and sy to obtain the reported
millimetre-scale displacements.

## 4. DRR generation

### CT loading and centring

The planning CT DICOM series is converted to a NIfTI volume for local output
and is also loaded through DiffDRR.

The DiffDRR input configuration is:

- orientation: AP;
- centre volume: enabled;
- bone attenuation multiplier: 3;
- source-to-detector distance: the RTImageSID associated with the kV object;
- rendered image size: 256 by 256 pixels;
- final DRR size: resized to the Rows and Columns of the triggered image.

The original study environment included a local TorchIO modification that
replaced the generic CT-volume centre with a centre corrected using the
RTPLAN isocentre. 

### Projection pose

For each triggered image, the DRR camera pose uses:

- translation: [0, 1000, 0] mm;
- rotation angle: the triggered-image gantry angle converted to radians;
- Euler parameterization;
- ZXY rotation convention.

DRRs are generated with DiffDRR 0.5.1. The code selects CUDA automatically when
available; otherwise DRR generation runs on the CPU. SimpleITK registration is
performed separately and was evaluated using CPU computation in the study.

## 5. Image preprocessing

Preprocessing is applied to the triggered kV image and the corresponding DRR
before registration.

The implemented sequence is:

1. Normalize image arrays for intensity-processing operations.
2. Match the global histogram of the triggered kV image to the DRR.
3. Apply adaptive histogram equalization to both images with:
   - clip limit: 0.01;
   - kernel size: library default.
4. Convert the equalized images to unsigned 16-bit representation.
5. Repeat a light histogram match of the kV image to the DRR.
6. Apply OpenCV CLAHE to both images with:
   - clip limit: 10.0;
   - tile grid size: 4 by 4.
7. Crop both images to a region centred on the image centre corresponding to
   150 mm by 150 mm, or 15 cm by 15 cm.
8. Apply a recursive Gaussian smoothing filter with sigma 1 to the fixed
   triggered kV image immediately before registration.

The crop is intended to focus registration on the treated bony region around
the treatment isocentre and reduce the influence of distant anatomy.

The current PDF report labels the crop value as centimetres although the
internal calculated value corresponds to millimetres. This unit label should be
corrected before the public release.

## 6. Image registration

### Fixed and moving images

The registration convention in the current implementation is:

- fixed image: preprocessed triggered kV image;
- moving image: corresponding preprocessed DRR.

The estimated transform maps the moving DRR toward the fixed triggered image.

### Transformation model

The reported registration uses a two-dimensional SimpleITK TranslationTransform.
Rotations and deformable changes are not included in the reported transform.

### Similarity metric and optimizer

The implemented SimpleITK settings are:

- similarity metric: Mean Squares;
- interpolation: linear;
- multi-resolution shrink factors: [4, 2, 1];
- multi-resolution smoothing sigmas: [5, 4, 1];
- optimizer: Regular Step Gradient Descent;
- initial learning rate: 4.0;
- minimum step: 0.0001;
- maximum iterations: 200;
- relaxation factor: 0.5;
- gradient magnitude tolerance: 1e-10.

Optimizer iterations, final metric values, stopping conditions, and transform
parameters are written to the console and execution log.

The resulting SimpleITK transform is saved in recap/ and is the transform used
to calculate the reported X and Y displacements.

### OpenCV ECC diagnostic

After the SimpleITK registration, the script also computes an OpenCV
findTransformECC estimate using a two-dimensional Euclidean model.

ECC settings are:

- motion model: Euclidean;
- maximum iterations: 5000;
- convergence epsilon: 1e-7.

The ECC translation, rotation, and correlation coefficient are written to the
log for diagnostic purposes. They are not used to replace the SimpleITK
transform and are not included in registration_report.csv.

## 7. Displacement definition

For each image, the SimpleITK transform provides translation parameters dx and
dy. Reported displacements are calculated as:

    X_mm = dx * sx
    Y_mm = dy * sy
    vector_magnitude = sqrt(X_mm^2 + Y_mm^2)

X and Y are detector image-plane coordinates:

- X represents the horizontal direction in the projection image and may
  correspond predominantly to left-right or anterior-posterior patient motion
  depending on gantry angle;
- Y represents the vertical direction in the projection image and corresponds
  predominantly to the superior-inferior direction for the acquisition
  geometry used in the study.

Because the workflow uses a single projection at each angle, X and Y should not
be interpreted as fixed three-dimensional patient-coordinate components across
all gantry angles.

The displacement sign follows the SimpleITK moving-to-fixed transform
convention. Any comparison with couch shifts or another tracking system must
verify the expected sign and axis orientation using a phantom dataset.

## 8. Registration visualizations

The DRR is resampled using the final SimpleITK transform. The workflow then
generates:

- a colour fusion image;
- a 4 by 4 checkerboard comparison;
- individual PNG images for the PDF report;
- a concatenated TIFF stack of registered images.

These visualizations support human assessment of registration plausibility.
They are not an automated registration confidence score.

## 9. Image-level reports

The CSV report contains, for each triggered image:

- treatment beam name;
- gantry angle;
- shift along X in millimetres;
- shift along Y in millimetres.

The PDF report includes:

- patient and plan metadata;
- maximum absolute X and Y shifts;
- maximum vector magnitude;
- mean and standard deviation of signed and absolute X and Y shifts;
- mean and standard deviation of vector magnitude;
- angle-dependent displacement plots;
- fusion and checkerboard images;
- the crop and bone attenuation settings.

The execution log records processing messages, optimizer information,
diagnostic ECC output, warnings, and tracebacks.

PatientID and PatientName may be included in the generated PDF. Reports and
logs must therefore be considered potentially identifiable.

## 10. Quality control and cohort analysis

The current script does not automatically determine whether a registration is
clinically or technically acceptable. In the study, fusion and checkerboard
images were used for visual quality control, and unreliable registrations were
excluded before cohort-level motion analysis.

The following manuscript-level steps are not currently implemented in this
repository:

- automated or manual classification labels for valid and aberrant
  registrations;
- separation of isolated discrepancies and systematic registration failures;
- detection of displacements exceeding the study threshold;
- identification of sustained events across three consecutive images;
- aggregation by fraction, patient, centre, anatomical site, or gantry-angle
  bin;
- statistical tests and regression analyses;
- generation of the manuscript tables and cohort figures.

## 11. Main fixed parameters

| Parameter | Current value |
|---|---:|
| DiffDRR version | 0.5.1 |
| DRR render size | 256 by 256 pixels |
| Source-to-isocentre translation | 1000 mm |
| Bone attenuation multiplier | 3 |
| Focal crop | 150 mm by 150 mm |
| Adaptive histogram equalization clip limit | 0.01 |
| CLAHE clip limit | 10.0 |
| CLAHE tile grid | 4 by 4 |
| Gaussian smoothing sigma | 1 |
| Registration model | 2D translation |
| Similarity metric | Mean Squares |
| Shrink factors | 4, 2, 1 |
| Smoothing sigmas | 5, 4, 1 |
| Optimizer learning rate | 4.0 |
| Optimizer minimum step | 0.0001 |
| Optimizer maximum iterations | 200 |
| Optimizer relaxation factor | 0.5 |
| Optimizer gradient tolerance | 1e-10 |

These parameters were selected during development and are hard-coded in the
current script.

## 12. Known methodological limitations

The main limitations of the implemented image-level workflow are:

- monoscopic two-dimensional registration cannot recover complete
  three-dimensional motion from a single projection;
- registration sensitivity varies with gantry angle and anatomical
  superposition;
- rotations and deformation are not represented by the reported translation;
- performance depends on kV image contrast, artifacts, exposed anatomy, and DRR
  quality;
- the CT-to-isocentre correction currently depends on a local package
  modification;
- acquisition ordering is not explicitly reconstructed from temporal DICOM
  tags;
- important parameters are hard-coded rather than exposed through a stable
  command-line interface;
- visual quality control is required;
- the code is intended for retrospective analysis and not real-time use.

## 13. Relationship to the manuscript

This repository accompanies the manuscript:

**Retrospective intrafraction motion verification using triggered kilovoltage
images during bone metastases stereotactic body radiotherapy**

The archived software release cited by the manuscript should identify the exact
version of this workflow used for the reported analysis. Any later changes to
registration parameters, preprocessing, coordinate conventions, exclusion
rules, or cohort-level analyses should be documented in the release notes.
