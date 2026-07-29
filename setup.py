from setuptools import setup, find_packages

setup(
    name="pdf-image-toolkit",
    version="1.0.0",
    description="Lightweight desktop software for PDF and image conversion.",
    author="Segun Olatoye",
    packages=find_packages(),
    install_requires=[
        "Pillow>=10.0.0",
        "pypdf>=4.0.0",
        "PyMuPDF>=1.23.0",
        "pdf2docx>=0.5.8",
    ],
    entry_points={
        "console_scripts": [
            "pdf-image-toolkit=pdf_image_toolkit.app:run_app"
        ]
    },
    python_requires=">=3.9",
)