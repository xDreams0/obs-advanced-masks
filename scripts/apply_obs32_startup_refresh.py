from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply_obs32_startup_refresh.py <plugin-root>")

root = Path(sys.argv[1])
header = root / "src" / "advanced-masks.h"
source = root / "src" / "advanced-masks-filter.c"

h = header.read_text(encoding="utf-8")
old_h = "\tbool invert;\n\tbool multiPassShader;\n"
new_h = "\tbool invert;\n\tbool multiPassShader;\n\tbool startup_update_pending;\n"
if old_h not in h:
    raise SystemExit("advanced-masks.h insertion point not found")
h = h.replace(old_h, new_h, 1)
header.write_text(h, encoding="utf-8")

c = source.read_text(encoding="utf-8")
old_create = "\tfilter->color_adj_data = bzalloc(sizeof(color_adjustments_data_t));\n\tfilter->multiPassShader = true;\n\n\tload_output_effect(filter);\n"
new_create = "\tfilter->color_adj_data = bzalloc(sizeof(color_adjustments_data_t));\n\tfilter->multiPassShader = true;\n\tfilter->startup_update_pending = true;\n\n\tload_output_effect(filter);\n"
if old_create not in c:
    raise SystemExit("advanced_masks_create insertion point not found")
c = c.replace(old_create, new_create, 1)

old_tick = "\tfilter->base->width = (uint32_t)obs_source_get_base_width(target);\n\tfilter->base->height = (uint32_t)obs_source_get_base_height(target);\n\n\tbool multiPass = advanced_masks_multi_pass(filter);\n"
new_tick = "\tfilter->base->width = (uint32_t)obs_source_get_base_width(target);\n\tfilter->base->height = (uint32_t)obs_source_get_base_height(target);\n\n\t/* OBS may create a filter before it is fully attached to its target while\n\t * loading a scene collection.  The create-time obs_source_update() can\n\t * therefore run before Shape has usable target dimensions.  Once the\n\t * target is genuinely ready, queue one fresh update using the already\n\t * stored settings.  This is equivalent to the user changing a property,\n\t * but happens automatically and only once per filter instance. */\n\tif (filter->startup_update_pending && filter->base->width > 0 &&\n\t    filter->base->height > 0) {\n\t\tfilter->startup_update_pending = false;\n\t\tblog(LOG_INFO,\n\t\t     \"[Advanced Masks] Refreshing startup settings after target attachment (%ux%u)\",\n\t\t     filter->base->width, filter->base->height);\n\t\tobs_source_update(filter->base->context, NULL);\n\t}\n\n\tbool multiPass = advanced_masks_multi_pass(filter);\n"
if old_tick not in c:
    raise SystemExit("advanced_masks_video_tick insertion point not found")
c = c.replace(old_tick, new_tick, 1)
source.write_text(c, encoding="utf-8")

print("Applied post-attachment startup settings refresh")
