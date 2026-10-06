// A small JSON Schema (draft 2020-12) checker for the keywords the shared
// schemas use, so Node commands can check what they emit against the schema
// file itself without a dependency (the smoke re-validates with Python
// jsonschema, the reference). An unsupported keyword throws: it is never
// silently treated as satisfied.
const IGNORED = new Set(['$schema', '$id', 'title', 'description', '$defs']);
const typeOf = v => v === null ? 'null' : Array.isArray(v) ? 'array' : Number.isInteger(v) ? 'integer' : typeof v;
const isType = (v, t) => t === 'number' ? typeof v === 'number' && Number.isFinite(v) : typeOf(v) === t;

// Errors ([] when valid) of `value` against `schema`, $refs resolved in `root`.
export function schemaErrors(value, schema, root = schema, at = '$') {
  const errors = [], fail = message => errors.push(`${at}: ${message}`);
  if (schema.$ref) {
    const m = /^#\/\$defs\/([^/]+)$/.exec(schema.$ref);
    if (!m || !root.$defs?.[m[1]]) throw new Error(`Unsupported $ref ${schema.$ref}`);
    return schemaErrors(value, root.$defs[m[1]], root, at);
  }
  for (const [key, rule] of Object.entries(schema)) {
    if (IGNORED.has(key)) continue;
    if (key === 'type') { const types = [rule].flat(); if (!types.some(t => isType(value, t))) fail(`must be ${types.join(' or ')}`); }
    else if (key === 'const') { if (JSON.stringify(value) !== JSON.stringify(rule)) fail(`must be ${JSON.stringify(rule)}`); }
    else if (key === 'enum') { if (!rule.some(v => JSON.stringify(v) === JSON.stringify(value))) fail(`must be one of ${rule.join(', ')}`); }
    else if (key === 'required') { if (typeOf(value) === 'object') for (const k of rule) if (!(k in value)) fail(`missing ${k}`); }
    else if (key === 'properties') { if (typeOf(value) === 'object') for (const [k, sub] of Object.entries(rule)) if (k in value) errors.push(...schemaErrors(value[k], sub, root, `${at}.${k}`)); }
    else if (key === 'additionalProperties') {
      if (rule !== false) throw new Error('Only additionalProperties: false is supported');
      if (typeOf(value) === 'object') for (const k of Object.keys(value)) if (!(k in (schema.properties ?? {}))) fail(`unexpected property ${k}`);
    }
    else if (key === 'items') { if (Array.isArray(value)) value.forEach((v, i) => errors.push(...schemaErrors(v, rule, root, `${at}[${i}]`))); }
    else if (key === 'minItems') { if (Array.isArray(value) && value.length < rule) fail(`needs at least ${rule} item(s)`); }
    else if (key === 'maxItems') { if (Array.isArray(value) && value.length > rule) fail(`allows at most ${rule} item(s)`); }
    else if (key === 'minLength') { if (typeof value === 'string' && [...value].length < rule) fail(`needs at least ${rule} character(s)`); }
    else if (key === 'pattern') { if (typeof value === 'string' && !new RegExp(rule, 'u').test(value)) fail(`must match ${rule}`); }
    else if (key === 'minimum') { if (typeof value === 'number' && value < rule) fail(`must be ≥ ${rule}`); }
    else if (key === 'maximum') { if (typeof value === 'number' && value > rule) fail(`must be ≤ ${rule}`); }
    else if (key === 'exclusiveMinimum') { if (typeof value === 'number' && value <= rule) fail(`must be > ${rule}`); }
    else throw new Error(`Unsupported JSON Schema keyword ${key}`);
  }
  return errors;
}
