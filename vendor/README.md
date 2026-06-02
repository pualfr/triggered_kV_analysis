# Local dependency snapshots

This folder contains local snapshots of selected Python dependencies from the original portable Python environment used for the analyses.

These files are provided for peer-review inspection of the execution environment and to document local package-level adjustments that affected the DRR generation workflow.

In particular, the local TorchIO version includes a modification of `torchio.data.Image.get_center()`. This modification calls `calcule_isocentre_test_4_2_opti.py` to extract the treatment isocenter from the RTPLAN and compute the offset between the RTPLAN isocenter and the planning CT center. This corrected center is then used during DRR generation through the DiffDRR/TorchIO workflow.

The recommended installation route remains the dependency list in `requirements.txt`. The `vendor/` folder is not intended to replace a clean package installation for the final public release.

For public release, these local modifications should ideally be converted into a documented patch or integrated directly into the analysis workflow.