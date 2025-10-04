# FITS Image Slicer

A simple tool for creating and labeling image patches from FITS files, complete with WCS coordinates.

## Requirements

To run this application, you will need Python 3 and the packages listed in `requirements.txt`. You can install them with:

```bash
pip install -r requirements.txt
```

## Data Labeling Workflow

This tool is designed for data labeling tasks, such as creating training data for machine learning models. The workflow is as follows:

1.  **Create or Open a Project:** Use the project wizard to start a new project or open an existing one.
2.  **Define Labels:** Use the "Labels" menu to define the classes you want to use (e.g., "galaxy", "star", "artifact").
3.  **Select and Label Patches:** Select a region of the image, and a dialog will prompt you to assign a label.
4.  **Review and Edit:** Use the patch table to review and edit the labels of your saved patches.
5.  **Export:** The labeled data, including the patch images and a CSV with metadata, is saved in your project directory.

## Astronomical Image Labeling Considerations

When labeling astronomical images, keep the following in mind:

*   **WCS Information:** The World Coordinate System (WCS) is preserved for each patch, allowing you to know its exact position on the sky.
*   **Image Scaling:** Astronomical images have a high dynamic range. Use the "View" -> "Z-Scale" option to adjust the image scaling and reveal faint features.
*   **Data Augmentation:** For training machine learning models, you may need to augment your data by rotating, flipping, or scaling the patches. This tool provides the raw patches, which you can then use in an augmentation pipeline.
*   **Metadata:** In addition to the label, the tool saves metadata like the object's position. You can extend the tool to save other metadata, such as brightness or size, if needed.
*   **Collaboration:** If multiple people are labeling the same dataset, you can share the project file and the patches directory to merge your work.
