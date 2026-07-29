# Merge PDF Features: Reordering & Preview

## Overview

The Merge PDFs tab now includes professional-grade reordering and preview capabilities for managing PDF merge operations.

## Features

### 1. **Reorder PDFs Before Merge**

- **Move Up (↑)**: Move selected PDF one position up in merge order
- **Move Down (↓)**: Move selected PDF one position down in merge order
- **Drag-friendly interface**: Click to select, then use buttons to arrange
- **Visual feedback**: Current position shown in preview pane (e.g., "Position: 3 of 5")

#### How to Use
1. Add multiple PDFs using "Add PDFs" button
2. Click on a PDF in the list to select it
3. Click "↑ Move Up" or "Move Down ↓" to reorder
4. Repeat until PDFs are in desired merge order
5. Click "Merge" to combine in the displayed order

### 2. **PDF Preview Pane**

Right side preview panel shows details of the selected PDF:

- **File Name**: Full filename of the selected PDF
- **Pages**: Number of pages in the PDF
- **Size**: File size in MB
- **Position**: Current position in merge queue (e.g., "Position: 1 of 5")

#### Preview Updates
- Automatically updates when you select a PDF from the list
- Updates after reordering to show new position
- Shows helpful message when no PDF is selected

### 3. **File Count Display**

Header shows total number of PDFs: "(5 files)" or "(1 file)"
- Updates in real-time when adding/removing PDFs
- Helps prevent accidental operations with wrong file count

### 4. **Enhanced List Controls**

- **Add PDFs**: Select multiple PDFs at once
- **Remove**: Delete selected PDF from merge list
- **Clear All**: Remove all PDFs and start fresh
- **Move Up/Down**: Reorder PDFs (see reordering section)
- **Merge**: Create final merged PDF in specified order

## UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ PDF Order: (5 files)    │  Preview                      │
│                         │  ─────────────────────────    │
│ ┌───────────────────┐  │  📄 FILE INFO                 │
│ │ document1.pdf     │  │                                │
│ │ document2.pdf     │  │  Name:                        │
│ │ document3.pdf     │  │  document2.pdf                │
│ │ document4.pdf     │  │                                │
│ │ document5.pdf     │  │  Pages:                       │
│ └───────────────────┘  │  42                            │
│                        │                                │
│ [Add] [Remove] [Clear] │  Size:                        │
│ [↑ Move Up] [Down ↓]   │  3.25 MB                       │
│             [Merge]    │                                │
│                        │  Position:                    │
│                        │  2 of 5                        │
└─────────────────────────────────────────────────────────┘
```

## Technical Details

### PDF Info Retrieved
- **Pages**: Via PyMuPDF (fitz) PDF reader
- **File Size**: OS file system stat
- **Filename**: Path basename

### Error Handling
- If a PDF becomes inaccessible, preview shows error message
- Reordering maintains file path integrity
- Merge operation validates all PDFs before combining

### Performance
- Preview loads instantly (caches page count)
- Reordering is O(n) with UI redraw
- No file I/O during reordering

## Workflow Example

### Scenario: Merge 3 reports in reverse chronological order

1. **Add PDFs** → Select `report_jan.pdf`, `report_feb.pdf`, `report_mar.pdf`
   - Files appear in order: Jan, Feb, Mar

2. **Reorder** → Want: Mar, Feb, Jan
   - Select `report_mar.pdf` → Click "↑ Move Up" twice
   - Select `report_jan.pdf` → Click "Move Down ↓" twice
   - Order is now: Mar, Feb, Jan

3. **Preview** → Click each to verify
   - Shows page count and size for each
   - Position counter confirms order

4. **Merge** → Click "Merge"
   - Saves combined PDF in specified order

## Related Functions

From `pdf_image_toolkit/operations.py`:
- `get_pdf_page_count(pdf_path)` - Returns number of pages
- `get_pdf_info(pdf_path)` - Returns dict with pages, size_mb, filename

## Keyboard Tips

- Click to select PDF in list
- Use arrow buttons to reorder
- Tab between buttons for keyboard navigation
