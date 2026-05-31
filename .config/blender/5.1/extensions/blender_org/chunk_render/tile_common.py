import math
from dataclasses import dataclass


_CR_REGION_FIELD_CASTS = {
    "index": int,
    "regionName": str,
    "baseName": str,
    "fullName": str,
    "task_output_dir": str,
    "nrow": int,
    "ncol": int,
    "render": bool,
    "minx": float,
    "maxx": float,
    "miny": float,
    "maxy": float,
    "bleed_frac_left": float,
    "bleed_frac_right": float,
    "bleed_frac_top": float,
    "bleed_frac_bottom": float,
}


@dataclass
class CRRegion:
    index: int = -1
    regionName: str = ""
    baseName: str = ""
    fullName: str = ""
    task_output_dir: str = ""
    nrow: int = 0
    ncol: int = 0
    render: bool = False
    minx: float = 0.0
    maxx: float = 0.0
    miny: float = 0.0
    maxy: float = 0.0
    bleed_frac_left: float = 0.0
    bleed_frac_right: float = 0.0
    bleed_frac_top: float = 0.0
    bleed_frac_bottom: float = 0.0

    def to_manifest_record(self):
        return {
            name: _cr_cast_value(getattr(self, name, None), caster)
            for name, caster in _CR_REGION_FIELD_CASTS.items()
        }

    @classmethod
    def from_manifest_record(cls, record):
        region = cls()
        for name, caster in _CR_REGION_FIELD_CASTS.items():
            value = record.get(name, getattr(region, name)) if isinstance(record, dict) else getattr(region, name)
            setattr(region, name, _cr_cast_value(value, caster, getattr(region, name)))
        return region

    @classmethod
    def from_object(cls, obj):
        region = cls()
        for name, caster in _CR_REGION_FIELD_CASTS.items():
            value = getattr(obj, name, getattr(region, name))
            setattr(region, name, _cr_cast_value(value, caster, getattr(region, name)))
        return region


def _cr_cast_value(value, caster, default=None):
    if value is None:
        value = default
    try:
        return caster(value)
    except (TypeError, ValueError):
        return caster(default) if default is not None else caster()


def cr_index_to_row_col(index, cols):
    cols = max(1, int(cols))
    row = int(index) // cols
    col = int(index) - (row * cols)
    return row, col


def cr_row_col_to_index(row, col, cols):
    return int(row) * max(1, int(cols)) + int(col)


def cr_make_region_name_parts(num_cols, num_rows, index):
    num_cols = max(1, int(num_cols))
    num_rows = max(1, int(num_rows))
    row, col = cr_index_to_row_col(index, num_cols)
    dec = max(
        math.ceil(math.log10(num_cols)) if num_cols > 1 else 1,
        math.ceil(math.log10(num_rows)) if num_rows > 1 else 1,
    )
    row_text = f"{row:0{dec}d}"
    col_text = f"{col:0{dec}d}"
    return [f"{num_cols}x{num_rows}_{row_text}_{col_text}", row_text, col_text]


def cr_compute_grid_offsets(row_sizes, col_sizes, *, top_to_bottom=False):
    if not row_sizes or not col_sizes:
        return {}, {}, 0, 0

    rows_total = max(row_sizes.keys()) + 1
    cols_total = max(col_sizes.keys()) + 1

    row_offsets = {}
    current_y = 0
    row_range = range(rows_total) if top_to_bottom else range(rows_total - 1, -1, -1)
    for row in row_range:
        row_offsets[row] = current_y
        current_y += row_sizes.get(row, 0)

    col_offsets = {}
    current_x = 0
    for col in range(cols_total):
        col_offsets[col] = current_x
        current_x += col_sizes.get(col, 0)

    return row_offsets, col_offsets, current_x, current_y


def cr_cell_rect(left, right, bottom, top, cols, rows, index):
    cols = max(1, int(cols))
    rows = max(1, int(rows))
    row, col = cr_index_to_row_col(index, cols)
    if row < 0 or row >= rows or col < 0 or col >= cols:
        return None
    cell_w = (right - left) / cols
    cell_h = (top - bottom) / rows
    x1 = left + col * cell_w
    x2 = left + (col + 1) * cell_w
    y_top = top - row * cell_h
    y_bottom = top - (row + 1) * cell_h
    return x1, x2, y_top, y_bottom
