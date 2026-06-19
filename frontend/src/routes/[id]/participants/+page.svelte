<script lang="ts">
	import { PageHeader, Button } from '@calcifer/ui';
	import { Plus, X, User, Baby, ChevronRight } from '@lucide/svelte/icons';

	let { data } = $props();
	let trip = $derived(data.trip);
	let tripId = $derived(trip.id);

	// Pre-populate presence & dob on participants (Svelte 5 can't add new properties after $state)
	let ppl = $state(data.participants.map((p: any) => {
		if (!p.presence?.length) p.presence = data.trip.start_date ? [{ start: data.trip.start_date, end: data.trip.end_date }] : [];
		return p;
	}));

	// Group by role
	let groups = $derived.by(() => {
		const order = ['adulte', 'enfant', 'bebe'];
		const labels: Record<string, string> = { adulte: 'Adultes', enfant: 'Enfants', bebe: 'Bébé' };
		const icons: Record<string, any> = { adulte: User, enfant: Baby, bebe: Baby };
		const map = new Map<string, any[]>();
		for (const p of ppl) {
			const key = p.role || 'adulte';
			if (!map.has(key)) map.set(key, []);
			map.get(key)!.push(p);
		}
		return order.filter(k => map.has(k)).map(k => ({
			key: k,
			label: labels[k] || k,
			icon: icons[k] || User,
			people: map.get(k)!
		}));
	});

	// Set of collapsed groups (by role key)
	let collapsed = $state<Set<string>>(new Set());

	function toggleGroup(key: string) {
		const s = new Set(collapsed);
		if (s.has(key)) s.delete(key); else s.add(key);
		collapsed = s;
	}

	function addDays(dateStr: string, n: number): string {
		const d = new Date(dateStr + 'T12:00:00');
		d.setDate(d.getDate() + n);
		return d.toISOString().slice(0, 10);
	}

	let days = $derived.by(() => {
		if (!trip.start_date || !trip.end_date) return [];
		const s = new Date(trip.start_date + 'T12:00:00'), e = new Date(trip.end_date + 'T12:00:00');
		const d: Date[] = []; const c = new Date(s);
		while (c <= e) { d.push(new Date(c)); c.setDate(c.getDate() + 1); }
		return d;
	});

	function present(p: any, day: Date): boolean {
		const ds = day.toISOString().slice(0, 10);
		for (const pr of p.presence) if (ds >= pr.start && ds <= pr.end) return true;
		if (p.return_trips) for (const rt of p.return_trips) if (ds >= rt.start && ds <= rt.end) return false;
		return false;
	}
	function fmtDay(d: Date) { return d.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric' }); }
	function ageAt(b: string, t: string): number {
		const bd = new Date(b + 'T12:00:00'), td = new Date(t + 'T12:00:00');
		let a = td.getFullYear() - bd.getFullYear();
		if (td.getMonth() < bd.getMonth() || (td.getMonth() === bd.getMonth() && td.getDate() < bd.getDate())) a--;
		return a;
	}
	function age(p: any): string {
		const d = p.dob || p.birthDate; if (!d || !trip.start_date) return '';
		const a = ageAt(d, trip.start_date);
		return a < 1 ? `${Math.floor((new Date(trip.start_date+'T12:00:00').getTime()-new Date(d+'T12:00:00').getTime())/(1000*60*60*24*30.44))} mois` : `${a} ans`;
	}

	function toggleDay(p: any, day: Date) {
		const ds = day.toISOString().slice(0, 10);
		// Find the presence block that contains this day
		let found = -1;
		for (let i = 0; i < p.presence.length; i++) {
			if (ds >= p.presence[i].start && ds <= p.presence[i].end) { found = i; break; }
		}

		if (found >= 0) {
			// Day is present → remove it
			const b = p.presence[found];
			if (b.start === b.end) {
				// Single-day block → remove entirely
				p.presence.splice(found, 1);
			} else if (ds === b.start) {
				// First day of block → shift start forward
				b.start = addDays(ds, 1);
			} else if (ds === b.end) {
				// Last day of block → shift end backward
				b.end = addDays(ds, -1);
			} else {
				// Middle of block → split into two
				const n = { start: addDays(ds, 1), end: b.end };
				b.end = addDays(ds, -1);
				p.presence.splice(found + 1, 0, n);
			}
		} else {
			// Day is absent → add it
			// Try to merge with adjacent blocks
			let merged = false;
			for (const pr of p.presence) {
				if (ds === addDays(pr.end, 1)) { pr.end = ds; merged = true; break; }
				if (ds === addDays(pr.start, -1)) { pr.start = ds; merged = true; break; }
			}
			if (!merged) {
				p.presence.push({ start: ds, end: ds });
			}
		}
		// Sort blocks by start date
		p.presence.sort((a: any, b: any) => a.start.localeCompare(b.start));
		save();
	}
	function save() { fetch('/'+tripId+'/participants?/update', { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: new URLSearchParams({participants: JSON.stringify(ppl)}) }); }

	let showAdd = $state(false);
	let nN = $state(''), nR = $state('adulte'), nD = $state('');
	function add() {
		if (!nN.trim()) return;
		const newP: any = {name:nN.trim(), role:nR, presence:trip.start_date?[{start:trip.start_date,end:trip.end_date}]:[]};
		if (nD) newP.dob = nD;
		ppl = [...ppl, newP];
		save(); showAdd=false; nN=''; nD='';
	}
	function rem(idx: number) { if (!confirm(`Supprimer ${ppl[idx].name} ?`)) return; ppl=ppl.filter((_:any,i:number)=>i!==idx); save(); }
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
					<input bind:value={nN} placeholder="Prénom" class="mt-1 rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none focus:border-ember-500" /></div>
				<div><label class="block text-xs text-coal-500">Rôle</label>
					<select bind:value={nR} class="mt-1 rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none focus:border-ember-500">
						<option value="adulte">Adulte</option><option value="enfant">Enfant</option><option value="bebe">Bébé</option></select></div>
				<div><label class="block text-xs text-coal-500">Naissance</label>
					<input type="date" bind:value={nD} class="mt-1 rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none focus:border-ember-500" /></div>
				<Button onclick={add} disabled={!nN.trim()}>Ajouter</Button>
			</div>
		</div>
	{/if}

	<div class="mb-8 space-y-4">
		{#each groups as g}
			<div class="rounded-2xl border border-coal-800 bg-coal-900/55 overflow-hidden">
				<button onclick={() => toggleGroup(g.key)}
					class="flex w-full items-center gap-2 px-4 py-3 text-left transition-colors hover:bg-coal-800/40">
					<ChevronRight size={16} class="shrink-0 text-coal-500 transition-transform {collapsed.has(g.key) ? '' : 'rotate-90'}" />
					<g.icon size={16} class="text-ember-400" />
					<span class="font-display text-sm text-coal-200">{g.label}</span>
					<span class="ml-auto text-xs text-coal-500">{g.people.length}</span>
				</button>
				{#if !collapsed.has(g.key)}
					<div class="space-y-3 px-4 pb-4">
						{#each g.people as p, idx}
							{@const globalIdx = ppl.indexOf(p)}
							<div class="rounded-xl border border-coal-700/60 bg-coal-900/40 p-3">
								<div class="mb-1.5 flex items-center justify-between">
									<div class="flex items-center gap-1.5">
										<g.icon size={15} class="text-ember-400 shrink-0" />
										<h3 class="text-sm font-semibold text-coal-50">{p.name}</h3>
										{#if age(p)}<span class="rounded-full bg-ember-500/15 px-1.5 py-0.5 text-[10px] text-ember-400">{age(p)}</span>{/if}
										<span class="text-[10px] text-coal-500 capitalize">· {p.role}</span>
									</div>
									<button onclick={() => rem(globalIdx)} class="text-coal-600 hover:text-red-400"><X size={12} /></button>
								</div>
								<div class="flex flex-wrap gap-1.5">
									{#each p.presence as pr, prIdx}
										<div class="flex items-center gap-1 rounded bg-ember-500/10 px-1.5 py-1 text-[11px]">
											<input type="date" bind:value={pr.start} onchange={save} class="w-24 rounded border border-coal-700 bg-coal-900 px-1 py-0.5 text-[11px] text-coal-50" />
											<span class="text-coal-500">→</span>
											<input type="date" bind:value={pr.end} onchange={save} class="w-24 rounded border border-coal-700 bg-coal-900 px-1 py-0.5 text-[11px] text-coal-50" />
											{#if p.presence.length > 1}<button onclick={() => { p.presence.splice(prIdx,1); ppl=[...ppl]; save(); }} class="text-coal-500 hover:text-red-400">✕</button>{/if}
										</div>
									{/each}
									<button onclick={() => { p.presence.push({start:trip.start_date||'',end:trip.end_date||''}); ppl=[...ppl]; save(); }}
										class="rounded border border-coal-700 bg-coal-900 px-1.5 py-1 text-[11px] text-coal-400 hover:border-ember-500 hover:text-ember-400">+ Bloc</button>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	</div>

	{#if days.length > 0 && ppl.length > 0}
		<h2 class="mb-3 font-display text-lg text-coal-300">Timeline</h2>
		<p class="mb-2 text-xs text-coal-500">Clique sur un jour pour ajouter/retirer la présence</p>
		<div class="overflow-x-auto">
			<table class="w-full min-w-[500px] text-sm">
				<thead><tr><th class="sticky left-0 bg-coal-950 pr-3 text-left text-xs text-coal-500">Participant</th>
					{#each days as day}<th class="px-1 py-1 text-center text-xs text-coal-500">{fmtDay(day)}</th>{/each}</tr></thead>
				<tbody>
					{#each ppl as p, pIdx}
						<tr class="border-t border-coal-800">
							<td class="sticky left-0 bg-coal-950 pr-3 py-2 text-sm text-coal-100">{p.name}</td>
							{#each days as day}
								<td class="px-1 py-2 text-center">
									<button onclick={() => toggleDay(p, day)}
										class="inline-block h-6 w-6 rounded-full border-0 transition-transform hover:scale-125 active:scale-95 {present(p, day) ? 'bg-ember-500' : 'bg-coal-700'}"></button>
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
