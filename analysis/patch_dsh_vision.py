"""Patch the DeepSeek provider plugin so a model can declare image input.

Why the patch is needed
-----------------------
`dsh-llm-deepseek` hardcodes the capability in two places:

    function modelInfo(provider, model) { ... inputModalities: ["text"] }
    resolveModel(...) fallback         { ... inputModalities: ["text"] }

and `settings.yaml` has no field that can override it, so `read_image` refuses while
the API itself accepts images. A measurement settled that the capability is real: a PNG
sent to `deepseek-flash` over the OpenAI-compatible endpoint comes back described in
`reasoning_content`.

Design: configuration-driven, not hardcoded
-------------------------------------------
The obvious patch -- replace `["text"]` with `["text", "image"]` -- would be wrong. It
would declare image input for *every* model in the catalog, including
`deepseek-v4-pro` and any diagnostic model, so the harness would forward an image to a
route that cannot read it and fail later with a confusing provider error instead of an
honest local refusal.

Instead the catalog entry gains an optional `inputModalities` field:

  * schema: `catalogModel` accepts it and `resolveModels` preserves it;
  * `modelInfo` reads it, defaulting to `["text"]` so existing configs are unchanged;
  * `settings.yaml` opts a specific model in.

So the capability is declared per model, by the user, in a file that survives as a
config rather than as a code edit.

Backup and revert
-----------------
The original file is copied to `index.js.dsh-patch-backup` beside it, and
`revert_dsh_patch.py` restores it. An npm update replaces the whole package directory,
so the patch is lost then; re-running this script is the recovery, which is why the
script is idempotent and refuses to double-apply.
"""
import io
import os
import shutil
import sys

PLUGIN = os.path.join(
    os.environ.get('APPDATA', ''),
    'npm', 'node_modules', '@deepseek-ai', 'dsh', 'node_modules',
    '@deepseek-ai', 'dsh-llm-deepseek', 'lib', 'index.js')
BACKUP = PLUGIN + '.dsh-patch-backup'
MARK = 'dsh-patch: inputModalities'

# --- 1. modelInfo honours the catalog field ---------------------------------- #
OLD_MODELINFO = '''function modelInfo(provider, model) {
	return {
		provider,
		id: model.id,
		name: model.name ?? model.id,
		...model.description === void 0 ? {} : { description: model.description },
		inputModalities: ["text"]
	};
}'''

NEW_MODELINFO = '''function modelInfo(provider, model) {
	// dsh-patch: inputModalities -- honour the catalog entry when it declares
	// modalities, and default to text-only otherwise so no existing config
	// silently gains a capability it does not have.
	return {
		provider,
		id: model.id,
		name: model.name ?? model.id,
		...model.description === void 0 ? {} : { description: model.description },
		inputModalities: Array.isArray(model.inputModalities) && model.inputModalities.length > 0 ? model.inputModalities : ["text"]
	};
}'''

# --- 2. schema accepts the field --------------------------------------------- #
OLD_SCHEMA = '''const catalogModel = z.object({
	id: z.string().required(),
	name: z.string(),
	description: z.string(),
	contextWindow: z.number().step(1).min(1),
	maxTokens: z.number().step(1).min(1)
});'''

NEW_SCHEMA = '''const catalogModel = z.object({
	id: z.string().required(),
	name: z.string(),
	description: z.string(),
	contextWindow: z.number().step(1).min(1),
	maxTokens: z.number().step(1).min(1),
	// dsh-patch: inputModalities -- which content parts this model accepts.
	// Opt-in per model; absent means text only.
	inputModalities: z.array(z.union(["text", "image"]))
});'''

# --- 3. resolveModels preserves it, with validation -------------------------- #
OLD_RESOLVE = '''		if (seen.has(model.id)) throw new Error(`llm-deepseek: duplicate catalog model "${model.id}"`);
		seen.add(model.id);
		return {
			id: model.id,
			...model.name === void 0 ? {} : { name: model.name },
			...model.description === void 0 ? {} : { description: model.description },
			...model.contextWindow === void 0 ? {} : { contextWindow: model.contextWindow },
			...model.maxTokens === void 0 ? {} : { maxTokens: model.maxTokens }
		};'''

NEW_RESOLVE = '''		if (seen.has(model.id)) throw new Error(`llm-deepseek: duplicate catalog model "${model.id}"`);
		// dsh-patch: inputModalities -- validate before preserving. An unknown
		// modality is rejected loudly rather than forwarded, because a typo would
		// otherwise read as "no image support" and be debugged as a capability bug.
		if (model.inputModalities !== void 0 && (!Array.isArray(model.inputModalities) || model.inputModalities.some((m) => m !== "text" && m !== "image"))) throw new Error(`llm-deepseek: catalog model "${model.id}" inputModalities must be an array of "text" and/or "image"`);
		seen.add(model.id);
		return {
			id: model.id,
			...model.name === void 0 ? {} : { name: model.name },
			...model.description === void 0 ? {} : { description: model.description },
			...model.contextWindow === void 0 ? {} : { contextWindow: model.contextWindow },
			...model.maxTokens === void 0 ? {} : { maxTokens: model.maxTokens },
			...model.inputModalities === void 0 ? {} : { inputModalities: model.inputModalities }
		};'''

# --- 4. the resolveModel fallback path --------------------------------------- #
OLD_FALLBACK = '''			...configured === void 0 ? {
				provider,
				id: model,
				name: model,
				inputModalities: ["text"]
			} : modelInfo(provider, configured),'''

NEW_FALLBACK = '''			// dsh-patch: an unconfigured model id keeps the text-only default;
			// a configured one goes through modelInfo, which reads its declaration.
			...configured === void 0 ? {
				provider,
				id: model,
				name: model,
				inputModalities: ["text"]
			} : modelInfo(provider, configured),'''

PATCHES = [
    ('modelInfo', OLD_MODELINFO, NEW_MODELINFO),
    ('catalogModel schema', OLD_SCHEMA, NEW_SCHEMA),
    ('resolveModels', OLD_RESOLVE, NEW_RESOLVE),
    ('resolveModel fallback comment', OLD_FALLBACK, NEW_FALLBACK),
]


def main():
    if not os.path.exists(PLUGIN):
        print('plugin not found: %s' % PLUGIN)
        print('is @deepseek-ai/dsh installed under %%APPDATA%%\\npm?')
        return 1

    src = io.open(PLUGIN, encoding='utf-8').read()

    if MARK in src:
        print('already patched (marker present); nothing to do')
        print('backup exists: %s' % os.path.exists(BACKUP))
        return 0

    # verify every anchor before writing anything, so a partial patch is impossible
    missing = [name for name, old, _ in PATCHES if src.count(old) != 1]
    if missing:
        print('ABORT: these anchors did not match exactly once:')
        for name in missing:
            print('   %s' % name)
        print('the plugin version may differ from the one this patch was written for')
        return 1

    shutil.copy2(PLUGIN, BACKUP)
    print('backup written: %s' % BACKUP)
    print('  (%d bytes)' % os.path.getsize(BACKUP))

    out = src
    for name, old, new in PATCHES:
        out = out.replace(old, new, 1)
        print('  patched: %s' % name)

    io.open(PLUGIN, 'w', encoding='utf-8', newline='\n').write(out)
    print('plugin written: %d -> %d bytes' % (len(src), len(out)))
    print()
    print('next: declare the modality for a specific model in settings.yaml, e.g.')
    print('    llm-deepseek:')
    print('      models:')
    print('        - id: deepseek-flash')
    print('          name: DeepSeek-V4.1-Flash')
    print('          contextWindow: 1000000')
    print('          inputModalities: ["text", "image"]')
    print()
    print('then restart DSH: the plugin is loaded at startup.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
