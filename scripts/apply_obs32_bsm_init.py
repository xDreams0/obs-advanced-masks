from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply_obs32_bsm_init.py <plugin-root>")

root = Path(sys.argv[1])
bsm_c = root / "src" / "mask-bsm.c"
bsm_h = root / "src" / "mask-bsm.h"
filter_c = root / "src" / "advanced-masks-filter.c"


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match in {path}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    bsm_c,
    "mask_bsm_data_t *mask_bsm_create()\n{",
    "mask_bsm_data_t *mask_bsm_create(obs_data_t *settings)\n{",
    "mask_bsm_create signature",
)

replace_once(
    bsm_c,
    '\tdstr_init_copy(&data->mask_source_name, "");\n\n\tload_bsm_effect_files(data);',
    '\tdstr_init_copy(&data->mask_source_name, "");\n\n'
    '\t/* Initialize BSM from persisted settings immediately. The parent filter\n'
    '\t * currently schedules its own obs_source_update() from create(), and the\n'
    '\t * callback may run after the first render during OBS startup. Reading the\n'
    '\t * saved settings here guarantees mask_source_name, fade_time and freeze\n'
    '\t * are available before the first BSM render. If the referenced source is\n'
    '\t * not registered yet, the normal render retry can resolve the saved name. */\n'
    '\tmask_bsm_update(data, settings);\n\n'
    '\tload_bsm_effect_files(data);',
    "mask_bsm_create initialization",
)

replace_once(
    bsm_h,
    "extern mask_bsm_data_t *mask_bsm_create();",
    "extern mask_bsm_data_t *mask_bsm_create(obs_data_t *settings);",
    "mask_bsm_create declaration",
)

replace_once(
    filter_c,
    "filter->bsm_data = mask_bsm_create();",
    "filter->bsm_data = mask_bsm_create(settings);",
    "advanced_masks_create BSM call",
)

print("Applied OBS 32 BSM create-time settings initialization fix")
