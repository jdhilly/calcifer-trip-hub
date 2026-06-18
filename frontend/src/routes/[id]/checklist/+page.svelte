<script lang="ts">
	import { PageHeader, Button } from '@calcifer/ui';
	import { Plus, X, Library, Minus, Check, Square, ListChecks, Luggage, Search, ChevronRight } from '@lucide/svelte/icons';

	let { data } = $props();
	let trip = $derived(data.trip);
	let items = $state(data.trip.items ?? []);
	let allCatalog = $state(data.catalog ?? []);

	let total = $derived(items.reduce((s: number, i: any) => s + (i.quantity || 1), 0));
	let depart = $derived(items.reduce((s: number, i: any) => s + (i.checked || 0), 0));
	let pct = $derived(total > 0 ? Math.round((depart / total) * 100) : 0);

	let showAdd = $state(false);
	let newCat = $state('');
	let newLabel = $state('');
	let newQty = $state(1);

	let showCatalog = $state(false);
	let selIds = $state<Set<number>>(new Set());
	let selQtys = $state<Record<number, number>>({});
	let expandedCats = $state<Set<string>>(new Set());
	let catSearch = $state('');

	// --- Checklist search / filter ---
	let checklistSearch = $state('');
	let checklistFilter = $state<'all' | 'checked' | 'unchecked'>('all');
	let checklistExpanded = $state<Set<string>>(new Set());

	function toggleChecklistCat(cat: string) {
		const next = new Set(checklistExpanded);
		if (next.has(cat)) next.delete(cat); else next.add(cat);
		checklistExpanded = next;
	}

	let filteredItems = $derived.by(() => {
		let out = items;
		const q = checklistSearch.trim().toLowerCase();
		if (q) out = out.filter((i: any) => i.label.toLowerCase().includes(q));
		if (checklistFilter === 'checked') out = out.filter((i: any) => (i.checked || 0) >= (i.quantity || 1));
		if (checklistFilter === 'unchecked') out = out.filter((i: any) => (i.checked || 0) < (i.quantity || 1));
		return out;
	});

	let filteredCategories = $derived.by(() => {
		const map = new Map<string, typeof items>();
		for (const item of filteredItems) {
			const cat = item.category || 'Sans catégorie';
			if (!map.has(cat)) map.set(cat, []);
			map.get(cat)!.push(item);
		}
		return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
	});

	// Progress stats from ALL items (not filtered), so category colors are always correct
	let categoryProgress = $derived.by(() => {
		const map = new Map<string, { done: number; total: number }>();
		for (const item of items) {
			const cat = item.category || 'Sans catégorie';
			const cur = map.get(cat) ?? { done: 0, total: 0 };
			cur.done += item.checked || 0;
			cur.total += item.quantity || 1;
			map.set(cat, cur);
		}
		return map;
	});

	// --- Catalogue modal ---
	function toggleCatExpanded(cat: string) {
		const next = new Set(expandedCats);
		if (next.has(cat)) next.delete(cat); else next.add(cat);
		expandedCats = next;
	}

	let isSearching = $derived(catSearch.trim().length > 0);

	let filteredCatalog = $derived.by(() => {
		if (!isSearching) return catalogByCat;
		const q = catSearch.trim().toLowerCase();
		const out: Record<string, typeof allCatalog> = {};
		for (const [cat, items] of Object.entries(catalogByCat)) {
			const matched = items.filter((i: any) => i.name.toLowerCase().includes(q));
			if (matched.length > 0) out[cat] = matched;
		}
		return out;
	});

	let catalogByCat = $derived.by(() => {
		const g: Record<string, typeof allCatalog> = {};
		for (const item of allCatalog) {
			const cat = item.category || 'Sans catégorie';
			if (!g[cat]) g[cat] = [];
			g[cat].push(item);
		}
		return g;
	});

	async function toggle(itemId: number, delta: number) {
		const item = items.find((i: any) => i.id === itemId);
		if (!item) return;
		const newChecked = Math.max(0, Math.min(item.quantity || 1, (item.checked || 0) + delta));
		item.checked = newChecked;
		items = [...items];
		await fetch(`/${trip.id}/checklist?/toggle`, {
			method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: new URLSearchParams({ itemId: String(itemId), checked: String(newChecked) })
		});
	}

	let editQtyId = $state<number | null>(null);
	let editQtyVal = $state(1);

	function startEdit(itemId: number, current: number) {
		editQtyId = itemId;
		editQtyVal = current;
	}

	async function saveEdit(itemId: number) {
		const qty = Math.max(1, editQtyVal);
		const item = items.find((i: any) => i.id === itemId);
		if (!item) return;
		item.quantity = qty;
		if (item.checked > qty) item.checked = qty;
		items = [...items];
		editQtyId = null;
		await fetch(`/${trip.id}/checklist?/update`, {
			method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: new URLSearchParams({ itemId: String(itemId), quantity: String(qty) })
		});
	}

	function cancelEdit() {
		editQtyId = null;
	}

	async function removeItem(itemId: number) {
		items = items.filter((i: any) => i.id !== itemId);
		await fetch(`/${trip.id}/checklist?/remove`, {
			method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: new URLSearchParams({ itemId: String(itemId) })
		});
	}

	async function addItem() {
		if (!newLabel.trim()) return;
		const r = await fetch(`/${trip.id}/checklist?/add`, {
			method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: new URLSearchParams({ label: newLabel.trim(), category: newCat.trim(), quantity: String(newQty) })
		});
		if ((await r.json()).ok) window.location.reload();
	}

	function openCatalog() {
		catSearch = '';
		selIds = new Set(); selQtys = {};
		for (const item of allCatalog) selQtys[item.id] = item.default_quantity || 1;
		showCatalog = true;
	}
	function toggleSel(id: number) {
		const next = new Set(selIds);
		if (next.has(id)) next.delete(id); else next.add(id);
		selIds = next;
	}
	function toggleCat(catItems: typeof allCatalog) {
		const allInCat = new Set(catItems.map((i: any) => i.id));
		const every = [...allInCat].every((id) => selIds.has(id));
		const next = new Set(selIds);
		for (const id of allInCat) {
			if (every) next.delete(id); else next.add(id);
		}
		selIds = next;
	}
	function catState(items: typeof allCatalog): 'all' | 'some' | 'none' {
		const ids = items.map((i: any) => i.id);
		const checked = ids.filter((id) => selIds.has(id)).length;
		if (checked === 0) return 'none';
		if (checked === ids.length) return 'all';
		return 'some';
	}
	function indeterminate(node: HTMLInputElement, value: boolean) {
		node.indeterminate = value;
		return { update(v: boolean) { node.indeterminate = v; } };
	}
	async function importSelected() {
		const ids = [...selIds];
		if (ids.length === 0) return;
		const items = ids.map((id) => {
			const item = allCatalog.find((c: any) => c.id === id);
			return { label: item?.name, category: item?.category || '', quantity: selQtys[id] || item?.default_quantity || 1 };
		});
		await fetch(`/${trip.id}/checklist?/import`, {
			method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: new URLSearchParams({ items: JSON.stringify(items) })
		});
		showCatalog = false; window.location.reload();
	}

	function focusMe(node: HTMLInputElement) {
		node.focus();
		node.select();
	}
</script>

<div class="mx-auto max-w-4xl px-4 py-6">
	<PageHeader title={trip.destination} backHref={`/${trip.id}`} description="Checklist" />

	<div class="mb-6">
		<div class="flex items-center justify-between text-xs text-coal-400">
			<span><Luggage size={14} class="inline" /> Départ</span>
			<span>{depart}/{total} ({pct}%)</span>
		</div>
		<div class="mt-1 h-2 w-full rounded-full bg-coal-800">
			<div class="h-2 rounded-full bg-ember-500 transition-all" style="width: {pct}%"></div>
		</div>
	</div>

	<div class="mb-6 flex flex-wrap gap-2">
		<button onclick={() => (showAdd = !showAdd)}
			class="inline-flex items-center gap-1.5 rounded-lg border border-coal-700 bg-coal-900 px-3 py-1.5 text-xs text-coal-300 transition-colors hover:border-ember-500 hover:text-ember-400">
			<Plus size={14} /> {showAdd ? 'Annuler' : 'Article'}
		</button>
		<button onclick={openCatalog}
			class="inline-flex items-center gap-1.5 rounded-lg border border-coal-700 bg-coal-900 px-3 py-1.5 text-xs text-coal-300 transition-colors hover:border-ember-500 hover:text-ember-400">
			<Library size={14} /> Catalogue
		</button>
	</div>

	{#if showAdd}
		<div class="mb-6 flex flex-wrap items-end gap-2 rounded-2xl border border-coal-800 bg-coal-900/55 p-4">
			<input bind:value={newCat} placeholder="Catégorie"
				class="rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none placeholder:text-coal-400 focus:border-ember-500 sm:max-w-36" />
			<input bind:value={newLabel} placeholder="Article"
				onkeydown={(e: any) => e.key === 'Enter' && addItem()}
				class="flex-[2] rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none placeholder:text-coal-400 focus:border-ember-500" />
			<div class="flex items-center gap-1">
				<button onclick={() => { if (newQty > 1) newQty--; }}
					class="flex h-8 w-8 items-center justify-center rounded border border-coal-700 text-coal-300 hover:border-ember-500">−</button>
				<span class="w-8 text-center text-sm text-coal-200">{newQty}</span>
				<button onclick={() => newQty++}
					class="flex h-8 w-8 items-center justify-center rounded border border-coal-700 text-coal-300 hover:border-ember-500">+</button>
			</div>
			<Button onclick={addItem} disabled={!newLabel.trim()}>Ajouter</Button>
		</div>
	{/if}

	<!-- Search + filter bar -->
	<div class="mb-4 flex flex-wrap items-center gap-2">
		<div class="relative flex-1 min-w-0">
			<Search size={14} class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-coal-500" />
			<input
				type="text"
				bind:value={checklistSearch}
				placeholder="Rechercher dans la checklist…"
				class="w-full rounded-lg border border-coal-700 bg-coal-900 py-2 pl-8 pr-3 text-sm text-coal-50 outline-none placeholder:text-coal-500 focus:border-ember-500"
			/>
		</div>
		<div class="flex gap-1">
			<button
				onclick={() => checklistFilter = 'all'}
				class="rounded-lg border px-2.5 py-1.5 text-xs transition-colors
					{checklistFilter === 'all'
						? 'border-ember-500 bg-ember-500/20 text-ember-400'
						: 'border-coal-700 text-coal-400 hover:border-coal-500 hover:text-coal-300'}"
			>Tout</button>
			<button
				onclick={() => checklistFilter = 'checked'}
				class="rounded-lg border px-2.5 py-1.5 text-xs transition-colors
					{checklistFilter === 'checked'
						? 'border-ember-500 bg-ember-500/20 text-ember-400'
						: 'border-coal-700 text-coal-400 hover:border-coal-500 hover:text-coal-300'}"
			>Cochés</button>
			<button
				onclick={() => checklistFilter = 'unchecked'}
				class="rounded-lg border px-2.5 py-1.5 text-xs transition-colors
					{checklistFilter === 'unchecked'
						? 'border-ember-500 bg-ember-500/20 text-ember-400'
						: 'border-coal-700 text-coal-400 hover:border-coal-500 hover:text-coal-300'}"
			>Non cochés</button>
		</div>
	</div>

	{#if checklistSearch || checklistFilter !== 'all'}
		<p class="mb-3 text-xs text-coal-500">
			{filteredItems.length} résultat{filteredItems.length > 1 ? 's' : ''} sur {items.length}
		</p>
	{/if}

	<div class="space-y-1">
		{#each filteredCategories as [category, catItems]}
			{@const prog = categoryProgress.get(category) ?? { done: 0, total: 0 }}
			{@const catPct = prog.total > 0 ? Math.round((prog.done / prog.total) * 100) : 0}
			{@const isExpanded = checklistExpanded.has(category)}
			<div>
				<!-- Category header (clickable to fold/unfold) -->
				<button
					onclick={() => toggleChecklistCat(category)}
					class="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left transition-colors hover:bg-coal-800/40"
				>
					<ChevronRight
						size={14}
						class="shrink-0 text-coal-500 transition-transform {isExpanded ? 'rotate-90' : ''}"
					/>
					<span
					class="font-display text-base"
					style="background: linear-gradient(to right, #f97316 0%, #f97316 {catPct}%, #d4d4d4 {catPct}%, #d4d4d4 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;"
				>{category}</span>
					<span class="ml-auto text-xs text-coal-500">{prog.done}/{prog.total}</span>
				</button>

				<!-- Items (visible only when expanded) -->
				{#if isExpanded}
					<div class="ml-5 space-y-2 pb-3">
						{#each catItems as item (item.id)}
							<div class="rounded-2xl border border-coal-800 bg-coal-900/55 p-3 transition-all duration-200 hover:border-ember-500/30">
								<div class="flex items-center gap-3">
									<div class="flex items-center gap-0.5">
										<button onclick={() => toggle(item.id, -1)} disabled={(item.checked || 0) <= 0}
											class="flex h-6 w-6 items-center justify-center rounded-l border border-coal-700 text-coal-400 transition-colors hover:border-ember-500 hover:text-ember-400 disabled:opacity-30"><Minus size={12} /></button>
																				{#if editQtyId === item.id}
																				<input
																				type="number" min="1" bind:value={editQtyVal}
																				onkeydown={(e: any) => { if (e.key === 'Enter') saveEdit(item.id); if (e.key === 'Escape') cancelEdit(); }}
																				onblur={() => saveEdit(item.id)}
																				use:focusMe
																				class="h-6 w-14 rounded border border-ember-500 bg-coal-800 px-1 text-center text-xs font-medium text-ember-400 outline-none"
																				/>
																				{:else}
																				<button onclick={() => startEdit(item.id, item.quantity)}
																				class="flex h-6 cursor-text items-center border-y border-coal-700 px-2 text-xs font-medium transition-colors hover:border-ember-500 {(item.checked || 0) > 0 ? 'bg-ember-500/20 text-ember-400' : 'text-coal-400'}"
																				>{item.checked || 0}/{item.quantity}</button>
																				{/if}
																				<button onclick={() => toggle(item.id, 1)} disabled={(item.checked || 0) >= (item.quantity || 1)}
											class="flex h-6 w-6 items-center justify-center rounded-r border border-coal-700 text-coal-400 transition-colors hover:border-ember-500 hover:text-ember-400 disabled:opacity-30"><Plus size={12} /></button>
									</div>
									<span class="flex-1 text-sm text-coal-100">{item.label}</span>
									<button onclick={() => removeItem(item.id)} class="text-coal-600 hover:text-red-400 transition-colors"><X size={14} /></button>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	</div>

	{#if items.length === 0}
		<p class="mt-8 text-center text-coal-500">Checklist vide.</p>
	{/if}

	{#if items.length > 0 && filteredItems.length === 0}
		<p class="mt-8 text-center text-coal-500">Aucun article ne correspond à votre recherche.</p>
	{/if}
</div>

{#if showCatalog}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onclick={() => showCatalog = false} role="presentation">
		<div class="flex max-h-[80vh] w-full max-w-lg flex-col rounded-xl border border-coal-700 bg-coal-950 shadow-2xl" onclick={(e) => e.stopPropagation()} role="dialog">
			<div class="shrink-0 space-y-3 px-5 pb-3 pt-5">
				<h2 class="font-display text-lg text-coal-50">Depuis le catalogue</h2>
				<p class="text-xs text-coal-400">Sélectionnez les articles à ajouter</p>
				<div class="relative">
					<svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-coal-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
					</svg>
					<input
						type="text"
						bind:value={catSearch}
						placeholder="Rechercher un article…"
						class="w-full rounded-lg border border-coal-700 bg-coal-900 py-2.5 pl-9 pr-3 text-sm text-coal-50 outline-none placeholder:text-coal-500 focus:border-ember-500"
					/>
				</div>
			</div>

			{#if allCatalog.length > 0}
				<div class="flex-1 overflow-y-auto px-5">
					<div class="space-y-3 pb-4">
						{#each Object.entries(filteredCatalog) as [cat, catItems]}
							{@const state = catState(catItems)}
							{@const catExpanded = isSearching || expandedCats.has(cat)}
							<div>
								<button
									onclick={() => toggleCatExpanded(cat)}
									class="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-coal-800/60"
								>
									{#if !isSearching}
									<input
										type="checkbox"
										checked={state === 'all'}
										onchange={(e) => { e.stopPropagation(); toggleCat(catItems); }}
										use:indeterminate={state === 'some'}
										class="accent-ember-500 h-4 w-4 shrink-0"
										onclick={(e) => e.stopPropagation()}
									/>
									{/if}
									<h4 class="flex-1 text-sm font-medium text-coal-100">{cat}</h4>
									<span class="text-xs text-coal-500">{catItems.length}</span>
									<svg
										class="h-4 w-4 text-coal-500 transition-transform {catExpanded ? 'rotate-90' : ''}"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="2"
										stroke-linecap="round"
										stroke-linejoin="round"
									>
										<polyline points="9 18 15 12 9 6" />
									</svg>
								</button>
								{#if catExpanded}
								<div class="space-y-1.5">
									{#each catItems as item}
										<div class="flex items-center gap-2 rounded-lg border border-coal-800 p-2">
											<input type="checkbox" checked={selIds.has(item.id)} onchange={() => toggleSel(item.id)} class="accent-ember-500 h-4 w-4" />
											<span class="flex-1 text-sm text-coal-100">{item.name}</span>
											<div class="flex items-center gap-1">
												<button onclick={() => { if ((selQtys[item.id] ?? 1) > 1) selQtys[item.id]--; }}
													class="flex h-6 w-6 items-center justify-center rounded border border-coal-700 text-coal-400 hover:border-ember-500">−</button>
												<span class="w-6 text-center text-xs text-coal-200">{selQtys[item.id] ?? item.default_quantity ?? 1}</span>
												<button onclick={() => selQtys[item.id] = (selQtys[item.id] ?? item.default_quantity ?? 1) + 1}
													class="flex h-6 w-6 items-center justify-center rounded border border-coal-700 text-coal-400 hover:border-ember-500">+</button>
											</div>
										</div>
									{/each}
								</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>

				<div class="sticky bottom-0 shrink-0 border-t border-coal-800 bg-coal-950 px-5 py-4">
					<div class="flex justify-end gap-2">
						<button onclick={() => showCatalog = false} class="rounded-lg border border-coal-700 px-4 py-2 text-sm text-coal-300 hover:border-ember-500 hover:text-ember-400">Annuler</button>
						<Button onclick={importSelected} disabled={selIds.size === 0}>Importer ({selIds.size})</Button>
					</div>
				</div>
			{:else}
				<div class="flex-1 px-5 pb-4">
					<p class="py-6 text-center text-sm text-coal-500">Catalogue vide.</p>
				</div>
			{/if}
		</div>
	</div>
{/if}
