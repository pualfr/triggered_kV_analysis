# Retrospective triggered kV image analysis workflow

This repository contains the Python workflow used for the retrospective analysis of triggered kilovoltage (kV) images acquired during bone metastases stereotactic body radiotherapy (SBRT).

The workflow was developed for the manuscript:

**Retrospective intrafraction motion verification using triggered kilovoltage images during bone metastases stereotactic body radiotherapy**

## Purpose

The aim of the workflow is to retrospectively estimate intrafraction displacement from routinely acquired triggered kV images by registering each acquired image to a corresponding digitally reconstructed radiograph (DRR) generated from the planning CT.

The workflow includes:

1. DICOM consistency checks between planning CT, RTSTRUCT, RTPLAN, and triggered kV images.
2. Extraction of gantry angles and imaging geometry from triggered kV DICOM headers.
3. DRR generation using DiffDRR.
4. Image preprocessing to improve comparability between kV images and DRRs.
5. Rigid in-plane registration using SimpleITK.
6. Export of displacement values, visual overlays, checkerboard images, logs, and summary reports.

## Expected input folder structure

The script expects the following folder structure:

```text
Fichiers DICOM/
├── 01pCT/
├── 02RTSTRUCT/
├── 03RTPLAN/
└── 04pkV/
```

Where:

* `01pCT/` contains the planning CT DICOM files.
* `02RTSTRUCT/` contains the RT structure set.
* `03RTPLAN/` contains the RT plan.
* `04pkV/` contains the triggered kV images acquired during treatment delivery.

## Main script

The main analysis script is located in:

```text
src/pkv_motion_workflow.py
```

The original development script was written in Python 3.12.4 and executed in a local portable Python/Spyder environment.

## Dependencies

The main Python dependencies are listed in:

```text
requirements.txt
```

They can be installed using:

```bash
pip install -r requirements.txt
```

A full list of packages from the original development environment may also be provided for information if needed.

A local snapshot of selected dependencies is provided in `vendor/` for peer-review inspection. 
This is important because the original workflow used a locally modified TorchIO function to center the CT volume on the RTPLAN isocenter during DRR generation.

## Output

The workflow generates several output folders, including:

```text
pkslice/
tiff_isocal/
recale/
recap/
imgrap/
graph/
```

Typical outputs include:

* Generated DRRs.
* Preprocessed triggered kV images.
* Registration transform files.
* Color fusion overlays.
* Checkerboard images.
* CSV summary of displacement values.
* PDF summary report.
* Execution log file.

## Notes for peer review

This repository is provided to allow peer-review assessment of the processing logic, workflow structure, and documentation.

Clinical DICOM data are not included in this repository for confidentiality reasons.

The workflow was originally developed and executed in a local portable Python environment. Some local package-level adjustments may have been present in the original environment. Therefore, the repository should primarily be considered as the documented research workflow used for the manuscript rather than a fully containerized software release.

A cleaner public release will be prepared upon publication.

## Code availability

The source code of the retrospective analysis workflow will be made publicly available upon publication.

During peer review, this private repository may be shared with the editor and reviewers to allow assessment of code structure, documentation, and usability.

## License

License information will be added before public release.
