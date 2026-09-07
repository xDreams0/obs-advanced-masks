from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply_obs32_bsm_rebind.py <mask-bsm.c>")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

old_update = '''\tdstr_copy(&data->mask_source_name, mask_source_name);\n\n\tobs_source_t *mask_source =\n\t\t(mask_source_name && strlen(mask_source_name))\n\t\t\t? obs_get_source_by_name(mask_source_name)\n\t\t\t: NULL;\n\n\tif (mask_source) {\n\t\tobs_weak_source_release(data->mask_source_source);\n\t\tdata->mask_source_source =\n\t\t\tobs_source_get_weak_source(mask_source);\n\t\tobs_source_release(mask_source);\n\t} else {\n\t\tdata->mask_source_source = NULL;\n\t}\n'''

new_update = '''\tdstr_copy(&data->mask_source_name, mask_source_name);\n\n\t/* The referenced OBS source can be recreated while a scene collection is\n\t * loading. Always discard the previous weak handle before resolving the\n\t * current source name again. */\n\tif (data->mask_source_source) {\n\t\tobs_weak_source_release(data->mask_source_source);\n\t\tdata->mask_source_source = NULL;\n\t}\n\n\tobs_source_t *mask_source =\n\t\t(mask_source_name && strlen(mask_source_name))\n\t\t\t? obs_get_source_by_name(mask_source_name)\n\t\t\t: NULL;\n\n\tif (mask_source) {\n\t\tdata->mask_source_source =\n\t\t\tobs_source_get_weak_source(mask_source);\n\t\tobs_source_release(mask_source);\n\t}\n'''

if old_update not in text:
    raise SystemExit("mask_bsm_update block not found; source changed")
text = text.replace(old_update, new_update, 1)

old_render = '''\t// Groups can take a few frames to register, so check to see if there is\n\t// a mask source selected by the user (mask_source_name) but no registered\n\t// mask source (mask_source_source).  If so, attempt to register the\n\t// mask_source_source.\n\tif (!data->mask_source_source &&\n\t    !dstr_is_empty(&data->mask_source_name)) {\n\t\tobs_source_t *mask_source =\n\t\t\tobs_get_source_by_name(data->mask_source_name.array);\n\t\tif (mask_source) {\n\t\t\tobs_weak_source_release(data->mask_source_source);\n\t\t\tdata->mask_source_source =\n\t\t\t\tobs_source_get_weak_source(mask_source);\n\t\t\tobs_source_release(mask_source);\n\t\t} else {\n\t\t\tdata->mask_source_source = NULL;\n\t\t}\n\t}\n\n\tgs_texrender_t *mask_source_render = NULL;\n\tobs_source_t *source =\n\t\tdata->mask_source_source\n\t\t\t? obs_weak_source_get_source(data->mask_source_source)\n\t\t\t: NULL;\n'''

new_render = '''\tgs_texrender_t *mask_source_render = NULL;\n\tobs_source_t *source =\n\t\tdata->mask_source_source\n\t\t\t? obs_weak_source_get_source(data->mask_source_source)\n\t\t\t: NULL;\n\n\t/* A weak source handle may stay allocated after OBS has destroyed and\n\t * recreated the concrete source during startup. A non-NULL weak handle is\n\t * therefore not proof that the source is still usable. If it no longer\n\t * resolves, release it and retry the saved name. This retry happens on\n\t * subsequent render frames until OBS has finished registering the source. */\n\tif (!source && data->mask_source_source) {\n\t\tobs_weak_source_release(data->mask_source_source);\n\t\tdata->mask_source_source = NULL;\n\t}\n\n\tif (!source && !dstr_is_empty(&data->mask_source_name)) {\n\t\tsource = obs_get_source_by_name(data->mask_source_name.array);\n\t\tif (source) {\n\t\t\tdata->mask_source_source = obs_source_get_weak_source(source);\n\t\t}\n\t}\n'''

if old_render not in text:
    raise SystemExit("get_mask_source_render source-resolution block not found; source changed")
text = text.replace(old_render, new_render, 1)

path.write_text(text, encoding="utf-8")
print(f"Applied OBS startup BSM source rebind fix to {path}")
