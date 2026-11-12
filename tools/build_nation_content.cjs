// Run from any directory: node tools/build_nation_content.cjs [--check]
const fs = require('node:fs');
const path = require('node:path');
const { parse, walk } = require('./audit_content.cjs');

const root = path.resolve(__dirname, '..');
const tags = new Set(['ENG']);
const cultures = new Set(['english']);
const namespaces = new Set(['england', 'england_overseas']);
const ages = ['traditions', 'renaissance', 'discovery', 'reformation', 'absolutism', 'revolutions'];
const categories = ['production', 'military', 'society'];
const conditions = require('./england_event_conditions.json');
const eventKey = id => id.replace('.', '_');
const recordKey = id => `aoc_content_seen_${eventKey(id)}`;
const field = (node, key) => node.value.find(child => child.key === key)?.value;

function files(directory, extension) {
	const folder = path.join(root, directory);
	return fs.readdirSync(folder, { recursive: true, withFileTypes: true })
		.filter(entry => entry.isFile() && entry.name.endsWith(extension))
		.map(entry => path.join(entry.parentPath ?? entry.path, entry.name)).sort();
}

function definitions(directory, include = () => true) {
	return files(directory, '.txt').flatMap(file => {
		const original = fs.readFileSync(file, 'utf8');
		if (!include(original)) return [];
		const script = original.replace(/"(?:\\.|[^"\\])*"/g,
			quoted => quoted.replace(/\t/g, '\\t').replace(/\r/g, '\\r').replace(/\n/g, '\\n'));
		return parse(script, file).filter(node => Array.isArray(node.value));
	});
}

// A positive test must be required. An OR with an unrelated alternative,
// a negative trigger, and a reference in a foreign scope do not qualify.
function nationOnly(nodes, allowedTags = tags) {
	return Array.isArray(nodes) && nodes.some(({ key, op, value }) => {
		if (!['=', '?='].includes(op)) return false;
		if (key === 'OR') return value.length > 0 && value.every(branch => nationOnly([branch], allowedTags));
		if (key === 'AND' || key === 'custom_tooltip') return nationOnly(value, allowedTags);
		if (key.startsWith('c:')) return allowedTags.has(key.slice(2)) && ['this', 'root'].includes(value);
		if (['this', 'root', 'tag', 'country_definition', 'was_formed_from'].includes(key)) {
			return typeof value === 'string' && allowedTags.has(value.replace(/^(c|cd):/, ''));
		}
		return ['has_primary_culture', 'country_has_primary_culture', 'primary_culture'].includes(key)
			&& typeof value === 'string' && cultures.has(value.replace(/^(cu|culture):/, ''));
	});
}

const allTech = definitions('common/technology/technologies');
const nationTechFiles = files('common/technology/technologies', '.txt')
	.filter(file => /^[a-z][a-z0-9_]*_tech\.txt$/.test(path.basename(file)));
const allGrants = new Map();
const ageGrants = new Map();
const nationTags = new Set();
const nationData = new Map();
for (const nationFile of nationTechFiles) {
	const nation = path.basename(nationFile, '_tech.txt');
	const source = fs.readFileSync(nationFile, 'utf8');
	const declaredTag = source.match(/^\s*#\s*nation_tag\s*=\s*([A-Z0-9]{3})\s*$/m)?.[1];
	const historyFile = path.join(root, 'common/history/countries', `${nation}.txt`);
	const history = fs.existsSync(historyFile)
		? parse(fs.readFileSync(historyFile, 'utf8'), historyFile).find(node => node.key === 'COUNTRIES') : undefined;
	const historyTags = history?.value.filter(node => /^c:[A-Z0-9]{3}$/.test(node.key))
		.map(node => node.key.slice(2)) || [];
	const tag = declaredTag || (historyTags.length === 1 ? historyTags[0] : undefined);
	if (!tag) throw new Error(`${nationFile}: add # nation_tag = TAG or provide a matching single-country history file`);
	if (declaredTag && historyTags.length === 1 && declaredTag !== historyTags[0]) {
		throw new Error(`${nationFile}: nation_tag ${declaredTag} differs from history tag ${historyTags[0]}`);
	}
	if (nationTags.has(tag)) throw new Error(`More than one nation tech file uses ${tag}`);
	nationTags.add(tag);
	const nationTech = parse(source, nationFile).filter(node => Array.isArray(node.value));
	nationData.set(nation, { tag, tech: nationTech });
	for (const node of nationTech) {
		const era = field(node, 'era');
		const category = field(node, 'category');
		if (!node.key.startsWith(`${nation}_`) || !ages.some((_, index) => era === `era_${index + 1}`)
			|| !categories.includes(category) || field(node, 'can_research') !== 'no') {
			throw new Error(`${node.key}: national tech needs a ${nation}_ key, valid era/category, and can_research = no`);
		}
		if (allGrants.has(node.key)) throw new Error(`Duplicate national technology ${node.key}`);
		const ageKey = `${category}_age_${era.slice(4)}`;
		allGrants.set(node.key, { ageKey, nation, tag });
		if (!ageGrants.has(ageKey)) ageGrants.set(ageKey, new Map());
		if (!ageGrants.get(ageKey).has(tag)) ageGrants.get(ageKey).set(tag, []);
		ageGrants.get(ageKey).get(tag).push(node.key);
	}
}
const grants = new Map([...allGrants].filter(([, grant]) => grant.nation === 'england')
	.map(([key, grant]) => [key, grant.ageKey]));

// Rebuild national grant hooks while keeping each age technology's other settings.
const ageFile = path.join(root, 'common/technology/technologies/age_techs.txt');
const originalAgeSource = fs.readFileSync(ageFile, 'utf8');
const ageBom = originalAgeSource.startsWith('\uFEFF') ? '\uFEFF' : '';
const ageNewline = originalAgeSource.includes('\r\n') ? '\r\n' : '\n';
const ageSource = originalAgeSource.slice(ageBom.length).replace(/\r\n/g, '\n');
let ageBlockCount = 0;
const generatedAgeSource = ageSource.replace(/^((?:society|production|military)_age_[1-6])\s*=\s*\{[\s\S]*?^\}/gm, block => {
	const ageKey = block.match(/^([\w]+)\s*=/)[1];
	ageBlockCount++;
	const existing = field(parse(block, ageFile)[0], 'on_researched');
	if (existing && existing.some(branch => branch.key !== 'if'
		|| !nationOnly(field(branch, 'limit'), new Set([...nationTags, 'GBR']))
		|| branch.value.some(effect => effect.key !== 'limit'
			&& (effect.key !== 'add_technology_researched' || typeof effect.value !== 'string')))) {
		throw new Error(`${ageKey}: on_researched has effects outside national grant hooks; edit it manually before regenerating`);
	}
	let result = block.replace(/\n+\ton_researched = \{[\s\S]*?\n\t\}\n+/, '\n\n');
	const nations = ageGrants.get(ageKey);
	if (nations?.size) {
		const hook = `\ton_researched = {
${[...nations].map(([tag, keys]) => `\t\tif = {
\t\t\tlimit = { OR = { c:${tag} ?= this was_formed_from = ${tag} } }
${keys.map(key => `\t\t\tadd_technology_researched = ${key}`).join('\n')}
\t\t}`).join('\n')}
	}\n\n`;
		if (!result.includes('\n\tai_weight')) throw new Error(`${ageKey}: missing ai_weight insertion point`);
		result = result.replace('\n\tai_weight', `\n${hook}\tai_weight`);
	}
	return result;
});
if (ageBlockCount !== ages.length * categories.length) {
	throw new Error(`Expected 18 age technologies; found ${ageBlockCount}`);
}
const ageOutput = ageBom + generatedAgeSource.replace(/\n/g, ageNewline);
const tech = allTech.filter(node => ['potential', 'possible', 'can_research', 'is_shown'].some(
	key => nationOnly(field(node, key))) || grants.has(node.key));
for (const node of tech) {
	if (!ages.some((_, index) => field(node, 'era') === `era_${index + 1}`)) {
		throw new Error(`Unrecognized era for ${node.key}`);
	}
}

const english = new Map();
for (const file of files('localization/english', '.yml')
	.filter(file => path.basename(file) !== 'aoc_national_technologies_l_english.yml')) {
	for (const match of fs.readFileSync(file, 'utf8').matchAll(/^\s*([^\s:#]+):\d*\s+"(.*)"\s*$/gm)) {
		english.set(match[1], match[2]);
	}
}
const allEventDefinitions = definitions('events');
const events = allEventDefinitions.filter(node => field(node, 'type') === 'country_event'
	&& field(node, 'hidden') !== 'yes' && english.has(field(node, 'title'))
	&& (namespaces.has(node.key.split('.')[0]) || nationOnly(field(node, 'trigger'))));
const nationalEvents = new Map([...nationData].filter(([nation]) => nation !== 'england')
	.map(([nation]) => [nation, allEventDefinitions.filter(node => field(node, 'type') === 'country_event'
		&& field(node, 'hidden') !== 'yes' && english.has(field(node, 'title'))
		&& (node.key.startsWith(`${nation}.`) || node.key.startsWith(`${nation}_`)))]));
const indexedEvents = new Map([...events, ...[...nationalEvents.values()].flat()].map(node => [node.key, node]));
for (const file of files('events', '.txt')) {
	const original = fs.readFileSync(file, 'utf8');
	const updated = original.replace(/^([\w.]+)[ \t]*=[ \t]*\{[^]*?(?=^[\w.]+[ \t]*=|(?![^]))/gm, (block, id) => {
		const event = indexedEvents.get(id);
		if (!event) return block;
		const immediate = field(event, 'immediate');
		const marker = recordKey(id);
		if (Array.isArray(immediate) && immediate.some(node => node.key === 'set_variable' && node.value === marker)) return block;
		if (process.argv.includes('--check')) throw new Error(`Missing event history marker in ${id}`);
		const newline = block.includes('\r\n') ? '\r\n' : '\n';
		if (immediate) {
			const header = /^(\t| )immediate\s*=\s*\{/m;
			if (!header.test(block)) throw new Error(`Cannot locate immediate block in ${id}`);
			return block.replace(header, (start, indent) => `${start}${newline}${indent}${indent}set_variable = ${marker}${newline}`);
		}
		return block.replace('{', `{${newline}\timmediate = { set_variable = ${marker} }${newline}`);
	});
	if (updated !== original) fs.writeFileSync(file, updated);
}
const groups = [
	['reforms', /^england\.10/],
	['hundred_years', /^england\.30[01]$/],
	['roses', /^england\.3(?:0[2-9]|[12][0-9])$/],
	['overseas', /^england(?:_overseas\.|\.20)/],
];
const eventGroup = id => groups.find(([, pattern]) => pattern.test(id))?.[0] ?? 'other';
const storylineAges = { hundred_years: 1, roses: 2, overseas: 3 };
const journalGates = { 'england.316': 'renaissance', 'england.319': 'renaissance' };
const technologyEras = new Map(allTech.map(node => [node.key, Number(field(node, 'era')?.slice(4))]));
// Bureaucracy is referenced by the English event under its vanilla technology key.
if (!technologyEras.has('tech_bureaucracy')) technologyEras.set('tech_bureaucracy', 1);
const ageIcon = era => `gfx/interface/icons/invention_icons/age_${era}_${ages[era - 1]}.dds`;

function eventAge(node) {
	const trigger = field(node, 'trigger');
	const technologies = Array.isArray(trigger) ? trigger
		.filter(condition => condition.key === 'has_technology_researched' && condition.op === '=')
		.map(condition => condition.value) : [];
	if (journalGates[node.key]) technologies.push(journalGates[node.key]);
	const requiredEra = Math.max(0, ...technologies.map(key => technologyEras.get(key) || 0));
	return { era: requiredEra || storylineAges[eventGroup(node.key)], required: Boolean(requiredEra) };
}

const techRows = [];
for (const index of ages.keys()) {
	const era = index + 1;
	const cards = tech.filter(node => field(node, 'era') === `era_${era}`).sort((a, b) =>
		categories.indexOf(field(a, 'category')) - categories.indexOf(field(b, 'category'))
		|| a.key.localeCompare(b.key));
	if (!cards.length) continue;
	const texture = ageIcon(era);
	if (!fs.existsSync(path.join(root, texture))) throw new Error(`Missing age icon ${texture}`);
	techRows.push(`\t\taoc_content_age_header = {
			blockoverride "age_icon" { texture = "${texture}" }
			blockoverride "age_name" { text = "aoc_england_tech_era_${era}" }
		}`);
	for (let start = 0; start < cards.length; start += 3) {
		const row = cards.slice(start, start + 3).map(({ key }) =>
			`\t\t\taoc_england_technology_card = {
				datacontext = "[GetTechnology('${key}')]"${grants.has(key) ? `
				blockoverride "research_hint" { tooltip = "aoc_content_unlock_${key}" }` : ''}${key === 'england_dominions' ? `
				blockoverride "native_unlocks" { visible = no }
				blockoverride "subject_unlock" {
					visible = yes
					texture = "gfx/interface/icons/war_goals/make_dominion.dds"
					tooltip = "aoc_content_unlock_english_dominion"
				}` : ''}
			}`);
		techRows.push(['\t\tflowcontainer = {', '\t\t\tspacing = 9', ...row, '\t\t}'].join('\n'));
	}
}

function eventRow(node) {
	const key = eventKey(node.key);
	const tooltip = `aoc_content_player_${key}`;
	const { era, required } = eventAge(node);
	const badge = era ? `
			blockoverride "event_age" {
				texture = "${ageIcon(era)}"
				tooltip = "aoc_content_${required ? 'required' : 'storyline'}_age_${era}"
			}` : '';
	return `\t\taoc_content_event_row = {
			blockoverride "event_icon" { texture = "${field(node, 'icon') ?? 'gfx/interface/icons/event_icons/waving_flag.dds'}" tooltip = "${tooltip}" }
			blockoverride "event_title" { text = "${field(node, 'title')}" tooltip = "${tooltip}" }
			blockoverride "event_conditions" { text = "${conditions[node.key] ? `aoc_content_when_${key}` : 'aoc_content_when_unlisted'}" tooltip = "${tooltip}" }${badge}
			blockoverride "event_details" { tooltip = "aoc_content_details_${key}" }
			blockoverride "event_seen" {
				visible = "[GetScriptedGui('aoc_content_check_${key}').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"
			}
		}`;
}

// Keep the script operators and scope names visible without interpreting them
// against the journal's UI scope.
function scriptText({ key, op, value }) {
	const literal = text => String(text).replace(/[\[\]$#"\\]/g, character =>
		({ '[': '［', ']': '］', '$': '＄', '#': '＃', '"': '“', '\\': '＼' })[character]);
	if (!op) return literal(key);
	const right = Array.isArray(value) ? `{ ${value.map(scriptText).join(' ')} }` : literal(value);
	return `${literal(key)} ${op} ${right}`;
}

const staticModifiers = new Set(files('common/static_modifiers', '.txt').flatMap(file =>
	[...fs.readFileSync(file, 'utf8').matchAll(/^([\w]+)\s*=\s*\{/gm)].map(match => match[1])));

function eventEffect(entry) {
	if (entry.key === 'add_modifier' && Array.isArray(entry.value)) {
		const modifier = field(entry, 'name');
		if (staticModifiers.has(modifier)) {
			const duration = entry.value.find(argument => ['days', 'weeks', 'months', 'years'].includes(argument.key));
			return `Event country receives [GetStaticModifier('${modifier}').GetName]${duration ? ` (${duration.key}: ${duration.value})` : ''}\n[GetStaticModifier('${modifier}').GetDesc]`;
		}
	}
	return scriptText(entry);
}

const firingSources = new Map([...indexedEvents.keys()].map(key => [key, new Set()]));
function findFiringSources(nodes, owner, ancestors = []) {
	for (const node of nodes) {
		const parent = ancestors.at(-1);
		const references = node.key === 'trigger_event' ? [Array.isArray(node.value) ? field(node, 'id') : node.value]
			: ['events', 'random_events'].includes(node.key) && Array.isArray(node.value)
				? node.value.map(entry => entry.value ?? entry.key) : [];
		for (const id of references) {
			if (!firingSources.has(id)) continue;
			const context = ancestors.flatMap(ancestor => {
				const limits = field(ancestor, 'limit');
				const trigger = field(ancestor, 'trigger');
				const chance = ancestor.key === 'random' && field(ancestor, 'chance');
				return [
					...(Array.isArray(limits) ? limits.map(scriptText) : []),
					...(Array.isArray(trigger) ? trigger.map(scriptText) : []),
					...(chance ? [`chance = ${chance}%`] : []),
				];
			});
			const effects = parent?.key === 'effect' && ancestors.some(ancestor => ancestor.key === 'outcome')
				? parent.value.filter(effect => effect.key !== 'trigger_event').map(scriptText) : [];
			const source = [owner, ...context.map(line => `  • ${line}`),
				...effects.map(line => `  • Outcome effect: ${line}`)].join('\n');
			firingSources.get(id).add(source);
		}
		if (Array.isArray(node.value)) findFiringSources(node.value, owner, [...ancestors, node]);
	}
}
for (const directory of ['common/journal_entries', 'common/on_actions', 'common/scripted_effects', 'common/scripted_buttons', 'events']) {
	const containsIndexedEvent = script => [...firingSources.keys()].some(id => script.includes(id));
	for (const node of definitions(directory, containsIndexedEvent)) findFiringSources(node.value, node.key, [node]);
}

function eventDetails(node) {
	const lines = ['#title Script details#!', `#v ${node.key}#!`];
	if (conditions[node.key]) lines.push(`$aoc_content_when_${eventKey(node.key)}$`);
	const section = (title, entries) => {
		if (entries.length) lines.push('', `#bold ${title}#!`, ...entries);
	};
	const trigger = field(node, 'trigger');
	section('Event trigger', (Array.isArray(trigger) ? trigger : []).map(entry => `• ${scriptText(entry)}`));
	section('Firing sources', [...firingSources.get(node.key)]);
	const cooldown = node.value.find(entry => entry.key === 'cooldown');
	if (cooldown) lines.push('', scriptText(cooldown));
	const immediate = field(node, 'immediate');
	section('Effects when the event opens', (Array.isArray(immediate) ? immediate : [])
		.filter(entry => entry.key !== 'set_variable' || entry.value !== recordKey(node.key))
		.map(entry => `• ${eventEffect(entry)}`));
	for (const option of node.value.filter(entry => entry.key === 'option')) {
		const name = field(option, 'name');
		const label = english.has(name) && !/[\[\]$]/.test(english.get(name)) ? `$${name}$` : name ?? 'Option';
		const effects = option.value.filter(entry => !['name', 'default_option', 'ai_chance'].includes(entry.key))
			.map(entry => entry.key === 'custom_tooltip' && english.has(entry.value) && !/[\[\]$]/.test(english.get(entry.value))
				? `• $${entry.value}$` : `• ${eventEffect(entry)}`);
		section(label, effects.length ? effects : ['No additional scripted effect.']);
	}
	return ` aoc_content_details_${eventKey(node.key)}: "${lines.join('\n').replace(/\n/g, '\\n')}"`;
}

const durationLabels = { long_modifier_time: '10 years', moderately_long_modifier_time: '15 years',
	very_long_modifier_time: '20 years', stupidly_long_modifier_time: '50 years' };
const variableLabels = {
	war_of_roses_tension_offset_var: 'Realm Tension',
	war_of_roses_balance_offset_var: 'Succession',
};
function playerEffect(entry) {
	if (entry.key === 'add_modifier' && Array.isArray(entry.value)) {
		const modifier = field(entry, 'name');
		if (!staticModifiers.has(modifier)) return undefined;
		const duration = entry.value.find(argument => ['days', 'weeks', 'months', 'years'].includes(argument.key));
		const period = duration && (durationLabels[duration.value] || (/^\d+$/.test(duration.value)
			? `${duration.value} ${duration.value === '1' ? duration.key.slice(0, -1) : duration.key}` : null));
		return `[GetStaticModifier('${modifier}').GetName] · Your country${period ? ` · #v ${period}#!` : ''}\n[GetStaticModifier('${modifier}').GetDesc]`;
	}
	if (entry.key === 'change_variable' && Array.isArray(entry.value)) {
		const label = variableLabels[field(entry, 'name')];
		const amount = Number(field(entry, 'add'));
		if (label && Number.isFinite(amount)) return `${label}: #v ${amount > 0 ? '+' : ''}${amount}#!`;
	}
	if (entry.key === 'custom_tooltip' && safeLocalization(entry.value)) return `$${entry.value}$`;
}

function safeLocalization(key) {
	return english.has(key) && !/[\[\]$]/.test(english.get(key));
}

function playerDetails(node) {
	const lines = [`#v #bold $${field(node, 'title')}$#!#!`];
	const description = field(node, 'desc');
	if (safeLocalization(description)) lines.push(`$${description}$`);
	if (conditions[node.key]) lines.push('$TOOLTIP_DELIMITER$', '#bold When it can happen#!', `$aoc_content_when_${eventKey(node.key)}$`);
	const options = node.value.filter(entry => entry.key === 'option');
	if (options.length) lines.push('$TOOLTIP_DELIMITER$', '#bold Event choices#!');
	for (const [index, option] of options.entries()) {
		const name = field(option, 'name');
		const entries = option.value.filter(entry => !['name', 'default_option', 'ai_chance', 'clamp_variable'].includes(entry.key));
		const effects = entries.map(playerEffect);
		if (index > 0) lines.push('');
		lines.push(`#v #bold ${safeLocalization(name) ? `$${name}$` : 'Event option'}#!#!`, ...effects.filter(Boolean));
		if (effects.some(effect => !effect)) lines.push('See the information icon for additional effects and conditions.');
		else if (!effects.length) lines.push('No additional effects.');
	}
	return ` aoc_content_player_${eventKey(node.key)}: "${lines.join('\n').replace(/\n/g, '\\n')}"`;
}
const eventRows = [...groups.map(([group]) => group), 'other'].flatMap(group => {
	const rows = events.filter(node => eventGroup(node.key) === group);
	if (!rows.length) return [];
	const collapsed = `aoc_content_collapsed_${group}`;
	const open = `[Not(GetVariableSystem.Exists('${collapsed}'))]`;
	return [
		`\t\tbutton_standard = {
			size = { 510 36 }
			text = "aoc_content_category_${group}"
			onclick = "[GetVariableSystem.Toggle('${collapsed}')]"
			icon = {
				position = { 16 11 }
				size = { 14 14 }
				texture = "gfx/interface/politics_view/summary_arrow_right.dds"
				visible = "[GetVariableSystem.Exists('${collapsed}')]"
				alwaystransparent = yes
			}
			icon = {
				position = { 16 11 }
				size = { 14 14 }
				texture = "gfx/interface/politics_view/summary_arrow_down.dds"
				visible = "${open}"
				alwaystransparent = yes
			}
		}`,
		`\t\tflowcontainer = {
			visible = "${open}"
			direction = vertical
			spacing = 4
${rows.map(node => eventRow(node).replace(/^/gm, '\t')).join('\n')}
		}`,
	];
});

const template = fs.readFileSync(path.join(__dirname, 'nation_content.gui.template'), 'utf8').replace(/\r\n/g, '\n');
const gui = template.replace('\t\t# TECHNOLOGY_ROWS', techRows.join('\n'))
	.replace('\t\t# EVENT_ROWS', eventRows.join('\n'));
const counts = [
	` aoc_england_content_summary: "#v ${tech.length}#! unique technologies · #v ${events.length}#! events"`,
	` aoc_content_research_progress: "Unlocked #v [GetPlayer.MakeScope.ScriptValue('aoc_content_english_researched')|0] / ${tech.length}#!"`,
	...tech.filter(node => grants.has(node.key)).map(node =>
		` aoc_content_unlock_${node.key}: "Granted when you research [GetTechnology('${grants.get(node.key)}').GetName]."`),
	...events.filter(node => conditions[node.key]).map(node =>
		` aoc_content_when_${eventKey(node.key)}: "${conditions[node.key]}"`),
	...events.map(eventDetails),
	...events.map(playerDetails),
	...ages.flatMap((_, index) => {
		const era = index + 1;
		return [
			` aoc_content_required_age_${era}: "Required technology age: $aoc_england_tech_era_${era}$"`,
			` aoc_content_storyline_age_${era}: "Storyline age: $aoc_england_tech_era_${era}$"`,
		];
	}),
	...[...groups.map(([group]) => group), 'other'].map(group =>
		` aoc_content_category_${group}: "$aoc_content_group_${group}$ · ${events.filter(node => eventGroup(node.key) === group).length}"`),
].join('\n');
const locFile = 'localization/english/england_journal_l_english.yml';
const loc = fs.readFileSync(path.join(root, locFile), 'utf8').replace(/\r\n/g, '\n');
const generatedLoc = loc.replace(/(^ # BEGIN GENERATED CONTENT\n)[\s\S]*?(^ # END GENERATED CONTENT)/m,
	(_, begin, end) => `${begin}${counts}\n${end}`);
// These overseas flags were already set on the same branches as the events.
const overseasHistory = ['aoc_england_india_unlocked', 'aoc_england_cape_completed',
	'aoc_england_east_india_completed', 'aoc_england_australasia_completed',
	'aoc_england_hudson_bay_completed', 'aoc_england_royal_navy_completed',
	'aoc_england_new_world_completed'];
const checks = events.map(({ key }) => {
	const oldFlag = key.startsWith('england_overseas.') ? overseasHistory[Number(key.split('.')[1]) - 1] : undefined;
	const recorded = `has_variable = ${recordKey(key)}`;
	return `aoc_content_check_${eventKey(key)} = {
	scope = country
	is_valid = { ${oldFlag ? `OR = { ${recorded} has_variable = ${oldFlag} }` : recorded} }
}`;
}).join('\n\n') + '\n';
const progress = `aoc_content_english_researched = {
	value = 0
${tech.map(({ key }) => `	if = { limit = { has_technology_researched = ${key} } add = 1 }`).join('\n')}
}\n`;

const otherNations = [...nationData].filter(([nation]) => nation !== 'england');
const nationName = nation => nation.split('_').map(part => part[0].toUpperCase() + part.slice(1)).join(' ');
const nationalWidget = ([nation, { tech: nationTech }]) => {
	const nationEventRows = (nationalEvents.get(nation) || []).map(node => {
		const key = eventKey(node.key);
		return `		aoc_national_event_row = {
			blockoverride "event_icon" { texture = "${field(node, 'icon') || 'gfx/interface/icons/event_icons/waving_flag.dds'}" tooltip = "aoc_content_player_${key}" }
			blockoverride "event_title" { text = "${field(node, 'title')}" tooltip = "aoc_content_player_${key}" }
			blockoverride "event_conditions" { text = "aoc_national_event_conditions" tooltip = "aoc_content_player_${key}" }
			blockoverride "event_details" { tooltip = "aoc_content_details_${key}" }
			blockoverride "event_seen" {
				visible = "[GetScriptedGui('aoc_content_check_${key}').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"
			}
		}`;
	});
	if (!nationEventRows.length) nationEventRows.push('		textbox = { size = { 510 32 } text = "aoc_national_no_events" align = center|nobaseline }');
	const rows = [];
	for (const index of ages.keys()) {
		const era = index + 1;
		const cards = nationTech.filter(node => field(node, 'era') === `era_${era}`).sort((a, b) =>
			categories.indexOf(field(a, 'category')) - categories.indexOf(field(b, 'category'))
			|| a.key.localeCompare(b.key));
		if (!cards.length) continue;
		rows.push(`		aoc_national_age_header = {
			blockoverride "age_icon" { texture = "${ageIcon(era)}" }
			blockoverride "age_name" { text = "aoc_national_tech_era_${era}" }
		}`);
		for (let start = 0; start < cards.length; start += 3) {
			rows.push(`		flowcontainer = {
			spacing = 9
${cards.slice(start, start + 3).map(({ key }) => `			aoc_national_technology_card = {
				datacontext = "[GetTechnology('${key}')]"
				blockoverride "research_hint" { tooltip = "aoc_${nation}_unlock_${key}" }
			}`).join('\n')}
		}`);
		}
	}
	if (!rows.length) rows.push('		textbox = { size = { 510 32 } text = "aoc_national_no_technologies" align = center|nobaseline }');
	return `flowcontainer = {
	name = "widget_${nation}_technologies"
	parentanchor = hcenter
	direction = vertical
	spacing = 8
	ignoreinvisible = yes
	textbox = { size = { 510 38 } text = "aoc_${nation}_tech_summary" align = center|nobaseline }
	flowcontainer = {
		parentanchor = hcenter
		spacing = 4
		button_tab = {
			size = { 253 35 }
			text = "aoc_content_technologies_tab"
			down = "[Not(GetVariableSystem.Exists('aoc_${nation}_events_tab'))]"
			onclick = "[GetVariableSystem.Clear('aoc_${nation}_events_tab')]"
		}
		button_tab = {
			size = { 253 35 }
			text = "aoc_content_events_tab"
			down = "[GetVariableSystem.Exists('aoc_${nation}_events_tab')]"
			onclick = "[GetVariableSystem.Set('aoc_${nation}_events_tab', 'true')]"
		}
	}
	flowcontainer = {
		visible = "[Not(GetVariableSystem.Exists('aoc_${nation}_events_tab'))]"
		direction = vertical
		spacing = 7
		textbox = { size = { 510 24 } text = "aoc_${nation}_tech_progress" align = center|nobaseline }
${rows.join('\n')}
	}
	flowcontainer = {
		visible = "[GetVariableSystem.Exists('aoc_${nation}_events_tab')]"
		direction = vertical
		spacing = 4
		ignoreinvisible = yes
		textbox = { size = { 510 40 } text = "aoc_content_event_history_note" multiline = yes align = center|nobaseline using = fontsize_small }
${nationEventRows.join('\n')}
	}
}`;
};
const nationalTemplate = fs.readFileSync(path.join(__dirname, 'national_technologies.gui.template'), 'utf8').replace(/\r\n/g, '\n');
const nationalGui = nationalTemplate.replace('# NATION_WIDGETS', otherNations.map(nationalWidget).join('\n\n'));
const nationalLoc = '\uFEFFl_english:\n'
	+ ' aoc_national_no_technologies: "No national technologies have been defined yet."\n'
	+ ' aoc_national_no_events: "No national events have been added yet."\n'
	+ ' aoc_national_event_conditions: "See the information icon for conditions and effects."\n'
	+ ages.map((age, index) => ` aoc_national_tech_era_${index + 1}: "Age of ${age[0].toUpperCase() + age.slice(1)}"`).join('\n') + '\n'
	+ otherNations.flatMap(([nation, { tech: nationTech }]) => {
		const name = nationName(nation);
		const nationEventList = nationalEvents.get(nation) || [];
		return [
			` je_${nation}_technologies: "${name} Content"`,
			` je_${nation}_technologies_lobby: "${name} has technologies and events shaped by its own history. Advance through the ages to explore them."`,
			` je_${nation}_technologies_reason: "Browse this nation's unique technologies and historical events."`,
			` aoc_${nation}_tech_summary: "#v ${nationTech.length}#! unique technologies · #v ${nationEventList.length}#! events"`,
			` aoc_${nation}_tech_progress: "Unlocked #v [GetPlayer.MakeScope.ScriptValue('aoc_${nation}_researched')|0] / ${nationTech.length}#!"`,
			...nationTech.map(({ key }) => ` aoc_${nation}_unlock_${key}: "Granted when you research [GetTechnology('${allGrants.get(key).ageKey}').GetName]."`),
			...nationTech.flatMap(({ key }) => [key, `${key}_desc`].filter(locKey => !english.has(locKey))
				.map(locKey => ` ${locKey}: "${locKey.endsWith('_desc') ? `A national technology of ${name}.` : nationName(key.slice(nation.length + 1))}"`)),
			...nationEventList.flatMap(node => [eventDetails(node), playerDetails(node)]),
		];
	}).join('\n') + '\n';
const nationalProgress = otherNations.map(([nation, { tech: nationTech }]) => `aoc_${nation}_researched = {
	value = 0
${nationTech.map(({ key }) => `	if = { limit = { has_technology_researched = ${key} } add = 1 }`).join('\n')}
}`).join('\n\n') + '\n';
const nationalChecks = [...nationalEvents.values()].flat().map(node => `aoc_content_check_${eventKey(node.key)} = {
	scope = country
	is_valid = { has_variable = ${recordKey(node.key)} }
}`).join('\n\n') + '\n';
const missingJournals = otherNations.flatMap(([nation, { tag, tech: nationTech }]) => {
	const file = `common/journal_entries/${nation}_technologies.txt`;
	if (fs.existsSync(path.join(root, file))) return [];
	const icon = field(nationTech[0] || { value: [] }, 'texture') || 'gfx/interface/icons/invention_icons/crown.dds';
	return [[file, `# Generated by tools/build_nation_content.cjs. You can edit this journal entry after creation.\n
je_${nation}_technologies = {
	icon = "${icon}"
	group = je_group_aoc_national_content
	should_be_pinned_by_default_involved = yes
	is_shown_in_lobby = { OR = { c:${tag} ?= this was_formed_from = ${tag} } }
	is_shown_when_inactive = { OR = { c:${tag} ?= this was_formed_from = ${tag} } }
	possible = { OR = { c:${tag} ?= this was_formed_from = ${tag} } }
	activation_description = { always = yes }
	widget = {
		gui = "gui/journal_entry_widgets/aoc_national_technologies.gui"
		name = "widget_${nation}_technologies"
		container = "custom_widget_container_1"
	}
}\n`]];
});

for (const [file, output] of [
	['common/technology/technologies/age_techs.txt', ageOutput],
	['gui/journal_entry_widgets/england_technologies.gui', gui],
	[locFile, generatedLoc],
	['common/scripted_guis/aoc_england_content.txt', checks],
	['common/script_values/aoc_england_content.txt', progress],
	['gui/journal_entry_widgets/aoc_national_technologies.gui', nationalGui],
	['localization/english/aoc_national_technologies_l_english.yml', nationalLoc],
	['common/script_values/aoc_national_technologies.txt', nationalProgress],
	['common/scripted_guis/aoc_national_content.txt', nationalChecks],
	...missingJournals,
]) {
	const target = path.join(root, file);
	if (process.argv.includes('--check')) {
		if (!fs.existsSync(target) || fs.readFileSync(target, 'utf8').replace(/\r\n/g, '\n') !== output) {
			throw new Error(`Regenerate ${file} with node tools/build_nation_content.cjs`);
		}
	} else {
		fs.writeFileSync(target, output);
	}
}
console.log(`Assigned ${allGrants.size} national technologies across ${nationTags.size} ${nationTags.size === 1 ? 'country' : 'countries'}. Indexed ${tech.length} English technologies and ${events.length} events.`);
