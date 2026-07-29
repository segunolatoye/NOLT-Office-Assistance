from pathlib import Path
from typing import Iterable, List, Optional, Callable, Dict, Any
import gc

import fitz  # PyMuPDF
from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter
from pdf2docx import Converter

from .config import (
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_EXPORT_IMAGE_FORMATS,
    MIN_DPI,
    MAX_DPI,
    DEFAULT_MAX_IMAGE_SIZE,
)
from .exceptions import InvalidFileError, UserInputError


ProgressCallback = Optional[Callable[[int, int], None]]


def get_pdf_page_count(pdf_path: str | Path) -> int:
    """Get number of pages in a PDF file."""
    try:
        pdf_path = validate_pdf(pdf_path)
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception:
        return 0


def get_pdf_info(pdf_path: str | Path) -> Dict[str, Any]:
    """
    Get PDF metadata: page count, file size, filename.
    
    Returns dict with keys: pages, size_bytes, size_mb, filename
    """
    try:
        pdf_path = validate_pdf(pdf_path)
        pages = get_pdf_page_count(pdf_path)
        size_bytes = pdf_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        
        return {
            "pages": pages,
            "size_bytes": size_bytes,
            "size_mb": round(size_mb, 2),
            "filename": pdf_path.name,
        }
    except Exception as e:
        raise InvalidFileError(f"Cannot read PDF: {e}")


def validate_pdf(path: str | Path) -> Path:
    pdf_path = Path(path)

    if not pdf_path.exists():
        raise InvalidFileError(f"PDF file not found: {pdf_path}")

    if not pdf_path.is_file():
        raise InvalidFileError(f"Selected path is not a file: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise InvalidFileError(f"File is not a PDF: {pdf_path.name}")

    return pdf_path


def validate_images(image_paths: Iterable[str | Path]) -> List[Path]:
    paths = [Path(path) for path in image_paths]

    if not paths:
        raise UserInputError("No image files selected.")

    for image_path in paths:
        if not image_path.exists():
            raise InvalidFileError(f"Image file not found: {image_path}")

        if not image_path.is_file():
            raise InvalidFileError(f"Selected path is not a file: {image_path}")

        if image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            raise InvalidFileError(f"Unsupported image format: {image_path.name}")

    return paths


def normalize_image_for_pdf(
    image_path: Path,
    max_size: tuple[int, int] = DEFAULT_MAX_IMAGE_SIZE,
) -> Image.Image:
    """
    Opens an image safely, fixes orientation, resizes if needed, and returns RGB image.

    The returned Image object must be closed by the caller.
    """
    with Image.open(image_path) as original:
        img = ImageOps.exif_transpose(original)

        if max_size:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

        if img.mode in ("RGBA", "LA", "P"):
            rgba_img = img.convert("RGBA")
            background = Image.new("RGB", rgba_img.size, "white")
            background.paste(rgba_img, mask=rgba_img.split()[-1])
            return background

        return img.convert("RGB")


def images_to_pdf(
    image_paths: Iterable[str | Path],
    output_pdf: str | Path,
    progress_callback: ProgressCallback = None,
    max_size: tuple[int, int] = DEFAULT_MAX_IMAGE_SIZE,
) -> Path:
    """
    Convert one or more images into a single PDF.

    Pillow's multi-page PDF writer needs image objects available at save time.
    To reduce memory pressure, images are orientation-fixed and resized before storing.
    """
    images = validate_images(image_paths)
    output_path = Path(output_pdf)

    if output_path.suffix.lower() != ".pdf":
        output_path = output_path.with_suffix(".pdf")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    pil_images: List[Image.Image] = []

    try:
        total = len(images)

        for index, image_path in enumerate(images, start=1):
            pil_images.append(normalize_image_for_pdf(image_path, max_size=max_size))

            if progress_callback:
                progress_callback(index, total)

        first_image = pil_images[0]
        remaining_images = pil_images[1:]

        first_image.save(
            output_path,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=remaining_images,
            optimize=True,
        )

        return output_path

    finally:
        for img in pil_images:
            try:
                img.close()
            except Exception:
                pass

        pil_images.clear()
        gc.collect()


def pdf_to_word(
    input_pdf: str | Path,
    output_docx: str | Path,
    progress_callback: ProgressCallback = None,
) -> Path:
    """
    Convert a PDF file to a Word DOCX document.

    Works best with digital/text-based PDFs. Scanned PDFs may require OCR.
    """
    pdf_path = validate_pdf(input_pdf)
    output_path = Path(output_docx)

    if output_path.suffix.lower() != ".docx":
        output_path = output_path.with_suffix(".docx")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    converter = Converter(str(pdf_path))

    try:
        if progress_callback:
            progress_callback(0, 1)

        converter.convert(str(output_path), start=0, end=None)

        if progress_callback:
            progress_callback(1, 1)

    finally:
        converter.close()
        gc.collect()

    return output_path


def pdf_to_images(
    input_pdf: str | Path,
    output_folder: str | Path,
    image_format: str = "png",
    dpi: int = 200,
    progress_callback: ProgressCallback = None,
) -> List[Path]:
    """
    Export every page of a PDF as an image.

    image_format can be png, jpg, or jpeg.
    """
    pdf_path = validate_pdf(input_pdf)
    output_dir = Path(output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    fmt = image_format.lower().replace(".", "")
    if fmt == "jpeg":
        fmt = "jpg"

    if fmt not in SUPPORTED_EXPORT_IMAGE_FORMATS:
        raise UserInputError("Image format must be PNG or JPG.")

    if dpi < MIN_DPI or dpi > MAX_DPI:
        raise UserInputError(f"DPI must be between {MIN_DPI} and {MAX_DPI}.")

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    exported_files: List[Path] = []

    with fitz.open(pdf_path) as document:
        total_pages = document.page_count

        if total_pages == 0:
            raise UserInputError("The selected PDF has no pages.")

        for page_number in range(total_pages):
            page = document.load_page(page_number)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)

            output_file = output_dir / f"{pdf_path.stem}_page_{page_number + 1}.{fmt}"
            pixmap.save(output_file)
            exported_files.append(output_file)

            pixmap = None
            page = None

            if progress_callback:
                progress_callback(page_number + 1, total_pages)

            gc.collect()

    return exported_files


def resize_image(
    input_image: str | Path,
    output_path: str | Path,
    scale_percent: float = 100.0,
    progress_callback: ProgressCallback = None,
) -> Path:
    """Resize a single image and save it to an image or PDF output file."""
    image_path = validate_images([input_image])[0]
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if scale_percent <= 0:
        raise UserInputError("Scale percentage must be greater than zero.")

    scale = scale_percent / 100.0

    with Image.open(image_path) as original:
        image = ImageOps.exif_transpose(original)
        new_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
        resized = image.resize(new_size, Image.Resampling.LANCZOS)

        if output_file.suffix.lower() == ".pdf":
            if resized.mode in ("RGBA", "LA", "P"):
                rgba = resized.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.split()[-1])
                resized = background
            resized.save(output_file, "PDF", resolution=100.0, save_all=True)
        else:
            image_format = output_file.suffix.lower().lstrip(".")
            if image_format == "jpg":
                image_format = "JPEG"
            elif image_format == "tif":
                image_format = "TIFF"
            else:
                image_format = image_format.upper()

            if resized.mode in ("RGBA", "LA", "P") and image_format in {"JPEG", "JPG"}:
                resized = resized.convert("RGB")

            resized.save(output_file, format=image_format)

        if progress_callback:
            progress_callback(1, 1)

    return output_file


def resize_pdf(
    input_pdf: str | Path,
    output_pdf: str | Path,
    scale_percent: float = 100.0,
    progress_callback: ProgressCallback = None,
) -> Path:
    """Resize a PDF by rendering its pages at a scaled resolution."""
    pdf_path = validate_pdf(input_pdf)
    output_file = Path(output_pdf)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file.suffix.lower() != ".pdf":
        output_file = output_file.with_suffix(".pdf")

    if scale_percent <= 0:
        raise UserInputError("Scale percentage must be greater than zero.")

    scale = scale_percent / 100.0
    matrix = fitz.Matrix(scale, scale)
    pages: list[Image.Image] = []

    try:
        with fitz.open(pdf_path) as document:
            total_pages = document.page_count
            if total_pages == 0:
                raise UserInputError("The selected PDF has no pages.")

            for index, page in enumerate(document, start=1):
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                pages.append(image)

                if progress_callback:
                    progress_callback(index, total_pages)

        first_page = pages[0]
        remaining_pages = pages[1:]
        first_page.save(
            output_file,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=remaining_pages,
            optimize=True,
        )
    finally:
        for image in pages:
            try:
                image.close()
            except Exception:
                pass
        pages.clear()
        gc.collect()

    return output_file


def merge_pdfs(
    pdf_paths: Iterable[str | Path],
    output_pdf: str | Path,
    progress_callback: ProgressCallback = None,
) -> Path:
    """
    Merge multiple PDF files into one PDF.
    """
    paths = [validate_pdf(path) for path in pdf_paths]

    if len(paths) < 2:
        raise UserInputError("Select at least two PDF files to merge.")

    output_path = Path(output_pdf)

    if output_path.suffix.lower() != ".pdf":
        output_path = output_path.with_suffix(".pdf")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    writer = PdfWriter()

    try:
        total = len(paths)

        for index, pdf_path in enumerate(paths, start=1):
            reader = PdfReader(str(pdf_path))

            for page in reader.pages:
                writer.add_page(page)

            if progress_callback:
                progress_callback(index, total)

        with output_path.open("wb") as file:
            writer.write(file)

    finally:
        writer.close()
        gc.collect()

    return output_path


def split_pdf(
    input_pdf: str | Path,
    output_folder: str | Path,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
    progress_callback: ProgressCallback = None,
) -> List[Path]:
    """
    Split a PDF.

    If start_page and end_page are empty, each page is exported as a separate PDF.
    If start_page and end_page are provided, only that page range is exported as one PDF.

    Page numbers are 1-based for users.
    """
    pdf_path = validate_pdf(input_pdf)
    output_dir = Path(output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)

    if total_pages == 0:
        raise UserInputError("The selected PDF has no pages.")

    exported_files: List[Path] = []

    if start_page is None and end_page is None:
        for index, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)

            output_file = output_dir / f"{pdf_path.stem}_page_{index}.pdf"

            with output_file.open("wb") as file:
                writer.write(file)

            writer.close()
            exported_files.append(output_file)

            if progress_callback:
                progress_callback(index, total_pages)

            gc.collect()

        return exported_files

    if start_page is None or end_page is None:
        raise UserInputError("Both start page and end page are required for range split.")

    if start_page < 1 or end_page < 1:
        raise UserInputError("Page numbers must start from 1.")

    if start_page > end_page:
        raise UserInputError("Start page cannot be greater than end page.")

    if end_page > total_pages:
        raise UserInputError(f"End page cannot exceed total pages: {total_pages}")

    writer = PdfWriter()
    selected_pages = end_page - start_page + 1

    try:
        for current, page_index in enumerate(range(start_page - 1, end_page), start=1):
            writer.add_page(reader.pages[page_index])

            if progress_callback:
                progress_callback(current, selected_pages)

        output_file = output_dir / f"{pdf_path.stem}_pages_{start_page}_to_{end_page}.pdf"

        with output_file.open("wb") as file:
            writer.write(file)

        exported_files.append(output_file)

    finally:
        writer.close()
        gc.collect()

    return exported_files