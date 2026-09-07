from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply_obs32_startup_refresh.py <plugin-root>")

root = Path(sys.argv[1])
header = root / "src" / "advanced-masks.h"
source = root / "src" / "advanced-masks-filter.c"

h = header.read_text(encoding="utf-8")
old_h = "\tbool invert;\n\tbool multiPassShader;\n"
new_h = (
    "\tbool invert;\n"
    "\tbool multiPassShader;\n"
    "\tuint32_t settings_target_width;\n"
    "\tuint32_t settings_target_height;\n"
)
if old_h not in h:
    raise SystemExit("advanced-masks.h insertion point not found")
h = h.replace(old_h, new_h, 1)
header.write_text(h, encoding="utf-8")

c = source.read_text(encoding="utf-8")
old_create = "\tfilter->color_adj_data = bzalloc(sizeof(color_adjustments_data_t));\n\tfilter->multiPassShader = true;\n\n\tload_output_effect(filter);\n"
new_create = (
    "\tfilter->color_adj_data = bzalloc(sizeof(color_adjustments_data_t));\n"
    "\tfilter->multiPassShader = true;\n"
    "\tfilter->settings_target_width = 0;\n"
    "\tfilter->settings_target_height = 0;\n\n"
    "\tload_output_effect(filter);\n"
)
if old_create not in c:
    raise SystemExit("advanced_masks_create insertion point not found")
c = c.replace(old_create, new_create, 1)

old_tick = "\tfilter->base->width = (uint32_t)obs_source_get_base_width(target);\n\tfilter->base->height = (uint32_t)obs_source_get_base_height(target);\n\n\tbool multiPass = advanced_masks_multi_pass(filter);\n"
new_tick = r'''	filter->base->width = (uint32_t)obs_source_get_base_width(target);
	filter->base->height = (uint32_t)obs_source_get_base_height(target);

	/* Source Clone deliberately reports 1x1 until its cloned source has been
	 * resolved. OBS 32 can tick Advanced Masks during that temporary state.
	 * Do not treat 1x1 as a usable target. Re-apply the stored filter settings
	 * once real target dimensions become available, and again if the target
	 * dimensions later change. This mirrors the manual property edit that
	 * currently makes Shape masks start working. */
	if (filter->base->width > 1 && filter->base->height > 1 &&
	    (filter->settings_target_width != filter->base->width ||
	     filter->settings_target_height != filter->base->height)) {
		filter->settings_target_width = filter->base->width;
		filter->settings_target_height = filter->base->height;
		blog(LOG_INFO,
		     "[Advanced Masks] Target dimensions ready/changed (%ux%u), refreshing settings",
		     filter->base->width, filter->base->height);
		obs_source_update(filter->base->context, NULL);
	}

	bool multiPass = advanced_masks_multi_pass(filter);
'''
if old_tick not in c:
    raise SystemExit("advanced_masks_video_tick insertion point not found")
c = c.replace(old_tick, new_tick, 1)
source.write_text(c, encoding="utf-8")

print("Applied dynamic post-attachment target-size settings refresh")
