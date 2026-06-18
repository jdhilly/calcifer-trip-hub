<script lang="ts">
	import { PageHeader, Button } from '@calcifer/ui';
	import { Plus, X } from '@lucide/svelte/icons';

	let { data } = $props();
	let trip = $derived(data.trip);
	let ppl = $state(data.participants);
	let tripId = $derived(trip.id);

	let days = $derived.by(() => {
		if (!trip.start_date || !trip.end_date) return [];
		const start = new Date(trip.start_date + 'T12:00:00');
		const end = new Date(trip.end_date + 'T12:00:00');
		const d: Date[] = []; const cur = new Date(start);
		while (cur <= end) { d.push(new Date(cur)); cur.setDate(cur.getDate() + 1); }
		return d;
	});

	function ensurePresence(p: any) {
		if (!p.presence?.length) p.presence = trip.start_date ? [{ start: trip.start_date, end: trip.end_date }] : [];
	}

	function isPresent(p: any, day: Date): boolean {
		const ds = day.toISOString().slice(0, 10);
		ensurePresence(p);
		for (const pr of p.presence) if (ds >= pr.start && ds <= pr.end) return true;
		if (p.return_trips) for (const rt of p.return_trips) if (ds >= rt.start && ds <= rt.end) return false;
		return false;
	}

	function formatDay(d: Date) { return d.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric' }); }
	function ageAt(b: string, t: string): number {
		const bd = new Date(b + 'T12:00:00'), td = new Date(t + 'T12:00:00');
		let a = td.getFullYear() - bd.getFullYear();
		if (td.getMonth() < bd.getMonth() || (td.getMonth() === bd.getMonth() && td.getDate() < bd.getDate())) a--;
		return a;
	}
	function computeAge(p: any): string {
		const dob = p.dob || p.birthDate;
		if (!dob || !trip.start_date) return '';
		const a = ageAt(dob, trip.start_date);
		if (a < 1) return `${Math.floor((new Date(trip.start_date + 'T12:00:00').getTime() - new Date(dob + 'T12:00:00').getTime()) / (1000*60*60*24*30.44))} mois`;
		return `${a} ans`;
	}

	function addDay(d: string) { const dt = new Date(d + 'T12:00:00'); dt.setDate(dt.getDate() + 1); return dt.toISOString().slice(0, 10); }
	function subDay(d: string) { const dt = new Date(d + 'T12:00:00'); dt.setDate(dt.getDate() - 1); return dt.toISOString().slice(0, 10); }

	function onDrop(e: DragEvent, pIdx: number, day: Date) {
		e.preventDefault();
		const p = ppl[pIdx]; if (!p) return;
		ensurePresence(p);
		const ds = day.toISOString().slice(0, 10);
		let found = -1;
		for (let i = 0; i < p.presence.length; i++) { if (ds >= p.presence[i].start && ds <= p.presence[i].end) { found = i; break; } }
		if (found >= 0 && p.presence.length > 1) {
			const b = p.presence[found];
			if (ds === b.start) b.start = addDay(ds);
			else if (ds === b.end) b.end = subDay(ds);
			else { const s2 = addDay(ds); p.presence.splice(found + 1, 0, { start: s2, end: b.end }); b.end = subDay(ds); }
		} else if (found < 0) {
			let merged = false;
			for (const pr of p.presence) { if (ds === addDay(pr.end)) { pr.end = ds; merged = true; break; } if (ds === subDay(pr.start)) { pr.start = ds; merged = true; break; } }
			if (!merged) p.presence.push({ start: ds, end: ds });
		}
		save();
	}
	function save() { fetch('/' + tripId + '/participants?/update', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ participants: JSON.stringify(ppl) }) }); }

	let showAdd = $state(false);
	let newName = $state(''), newRole = $state('adulte'), newDob = $state('');
	function addPerson() {
		if (!newName.trim()) return;
		ppl = [...ppl, { name: newName.trim(), role: newRole, presence: trip.start_date ? [{ start: trip.start_date, end: trip.end_date }] : [] }];
		if (newDob) ppl[ppl.length-1].dob = newDob;
		save(); showAdd = false; newName = ''; newDob = '';
	}
	function removePerson(idx: number) { if (!confirm(`Supprimer ${ppl[idx].name} ?`)) return; ppl = ppl.filter((_: any, i: number) => i !== idx); save(); }
</script>

<div class="mx-auto max-w-4xl px-4 py-6">
	<PageHeader title={`Participants — ${trip.destination}`} backHref={`/${trip.id}`} description="Timeline de présence interactive" />

	<button onclick={() => (showAdd = !showAdd)}
		class="mb-6 inline-flex items-center gap-1.5 rounded-lg border border-coal-700 bg-coal-900 px-3 py-1.5 text-xs text-coal-300 transition-colors hover:border-ember-500 hover:text-ember-400">
		<Plus size={14} /> {showAdd ? 'Annuler' : 'Ajouter'}
	</button>

	{#if showAdd}
		<div class="mb-6 rounded-2xl border border-coal-800 bg-coal-900/55 p-4">
			<div class="flex flex-wrap items-end gap-3">
				<div><label class="block text-xs text-coal-500">Nom</label>
					<input bind:value={newName} placeholder="Prénom" class="mt-1 rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none focus:border-ember-500" /></div>
				<div><label class="block text-xs text-coal-500">Rôle</label>
					<select bind:value={newRole} class="mt-1 rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none focus:border-ember-500">
						<option value="adulte">Adulte</option><option value="enfant">Enfant</option><option value="bebe">Bébé</option></select></div>
				<div><label class="block text-xs text-coal-500">Date naissance</label>
					<input type="date" bind:value={newDob} class="mt-1 rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none focus:border-ember-500" /></div>
				<Button onclick={addPerson} disabled={!newName.trim()}>Ajouter</Button>
			</div>
		</div>
	{/if}

	<div class="mb-8 space-y-3">
		{#each ppl as p, idx}
			<div class="rounded-2xl border border-coal-800 bg-coal-900/55 p-4">
				<div class="mb-2 flex items-center justify-between">
					<div class="flex items-center gap-2">
						<span class="text-xl">{p.role === 'adulte' ? '🧑' : p.role === 'enfant' ? '👶' : '🍼'}</span>
						<h3 class="font-semibold text-coal-50">{p.name}</h3>
						{#if computeAge(p)}<span class="rounded-full bg-ember-500/15 px-2 py-0.5 text-xs text-ember-400">{computeAge(p)}</span>{/if}
						<span class="text-xs text-coal-500 capitalize">· {p.role}</span>
					</div>
					<button onclick={() => removePerson(idx)} class="text-coal-600 hover:text-red-400"><X size={14} /></button>
				</div>
				{ensurePresence(p)}
				<div class="flex flex-wrap gap-2">
					{#each p.presence as pr, prIdx}
						<div class="flex items-center gap-1 rounded bg-ember-500/10 px-2 py-1 text-xs">
							<input type="date" bind:value={pr.start} onchange={save} class="w-28 rounded border border-coal-700 bg-coal-900 px-1 py-0.5 text-xs text-coal-50" />
							<span class="text-coal-500">→</span>
							<input type="date" bind:value={pr.end} onchange={save} class="w-28 rounded border border-coal-700 bg-coal-900 px-1 py-0.5 text-xs text-coal-50" />
							{#if p.presence.length > 1}<button onclick={() => { p.presence.splice(prIdx, 1); ppl = [...ppl]; save(); }} class="text-coal-500 hover:text-red-400">✕</button>{/if}
						</div>
					{/each}
					<button onclick={() => { ensurePresence(p); p.presence.push({ start: trip.start_date || '', end: trip.end_date || '' }); ppl = [...ppl]; save(); }}
						class="rounded border border-coal-700 bg-coal-900 px-2 py-1 text-xs text-coal-400 hover:border-ember-500 hover:text-ember-400">+ Bloc</button>
				</div>
			</div>
		{/each}
	</div>

	{#if days.length > 0 && ppl.length > 0}
		<h2 class="mb-3 font-display text-lg text-coal-300">Timeline</h2>
		<p class="mb-2 text-xs text-coal-500">Glisse un 🟢/🔴 pour ajouter/retirer la présence</p>
		<div class="overflow-x-auto">
			<table class="w-full min-w-[500px] text-sm">
				<thead><tr><th class="sticky left-0 bg-coal-950 pr-3 text-left text-xs text-coal-500">Participant</th>
					{#each days as day}<th class="px-1 py-1 text-center text-xs text-coal-500">{formatDay(day)}</th>{/each}</tr></thead>
				<tbody>
					{#each ppl as p, pIdx}
						<tr class="border-t border-coal-800">
							<td class="sticky left-0 bg-coal-950 pr-3 py-2 text-sm text-coal-100">{p.name}</td>
							{#each days as day}
								<td class="px-1 py-2 text-center" ondragover={(e) => e.preventDefault()} ondrop={(e) => onDrop(e, pIdx, day)}>
									<span draggable="true" ondragstart={(e) => { if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'; }}
										class="inline-block h-6 w-6 cursor-grab rounded-full transition-transform hover:scale-125 active:cursor-grabbing {isPresent(p, day) ? 'bg-ember-500' : 'bg-coal-700'}">
									</span>
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
	{#if ppl.length === 0}<p class="mt-8 text-center text-coal-500">Aucun participant.</p>{/if}
</div>
