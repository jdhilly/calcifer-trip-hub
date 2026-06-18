<script lang="ts">
	import { PageHeader, Card, Button, IconBadge } from '@calcifer/ui';
	import { Check, X, Plus, Trash2, Library, Minus, ArrowRight } from '@lucide/svelte/icons';

	let { data } = $props();
	let trip = $derived(data.trip);
	let items = $state(data.trip.items ?? []);
	let allCatalog = $state(data.catalog ?? []);

	let categories = $derived.by(() => {
		const map = new Map<string, typeof items>();
		for (const item of items) {
			const cat = item.category || 'Sans catégorie';
			if (!map.has(cat)) map.set(cat, []);
			map.get(cat)!.push(item);
		}
		return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
	});

	let total = $derived(items.reduce((s: number, i: any) => s + (i.quantity || 1), 0));
	let departCount = $derived(items.reduce((s: number, i: any) => s + (i.checked || 0), 0));
	let departPct = $derived(total > 0 ? Math.round((departCount / total) * 100) : 0);

	// New item form
	let showAddForm = $state(false);
	let newCat = $state('');
	let newLabel = $state('');
	let newQty = $state(1);

	// Catalog import
	let showCatalog = $state(false);
	let selIds = $state<Set<number>>(new Set());
	let selQtys = $state<Record<number, number>>({});

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
		const newVal = Math.max(0, Math.min(item.quantity || 1, (item.checked || 0) + delta));
		item.checked = newVal;
		items = [...items];
		await fetch(`/${trip.id}/checklist?/toggle`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: new URLSearchParams({ itemId: String(itemId) })
		});
	}

	async function removeItem(itemId: number) {
		items = items.filter((i: any) => i.id !== itemId);
		await fetch(`/${trip.id}/checklist?/remove`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: new URLSearchParams({ itemId: String(itemId) })
		});
	}

	async function addItem() {
		if (!newLabel.trim()) return;
		const r = await fetch(`/${trip.id}/checklist?/add`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: new URLSearchParams({ label: newLabel.trim(), category: newCat.trim(), quantity: String(newQty) })
		});
		const result = await r.json();
		if (result.ok) window.location.reload();
	}

	function openCatalog() {
		selIds = new Set();
		selQtys = {};
		for (const item of allCatalog) {
			selQtys[item.id] = item.default_quantity || 1;
		}
		showCatalog = true;
	}

	function toggleSel(id: number) {
		const next = new Set(selIds);
		if (next.has(id)) next.delete(id); else next.add(id);
		selIds = next;
	}

	async function importSelected() {
		const ids = [...selIds];
		if (ids.length === 0) return;
		for (const id of ids) {
			const item = allCatalog.find((c: any) => c.id === id);
			if (!item) continue;
			await fetch(`/${trip.id}/checklist?/add`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
				body: new URLSearchParams({
					label: item.name,
					category: item.category || '',
					quantity: String(selQtys[id] || item.default_quantity || 1)
				})
			});
		}
		showCatalog = false;
		window.location.reload();
	}

	function formatDate(d: string): string {
		return new Date(d + 'T12:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
	}
</script>

<div class="mx-auto max-w-4xl px-4 py-6">
	<PageHeader
		title={trip.destination}
		backHref={`/${trip.id}`}
		description={`Checklist — ${formatDate(trip.start_date)} → ${formatDate(trip.end_date)}`}
	/>

	<!-- Double progress bars -->
	<div class="mb-6 space-y-2">
		<div>
			<div class="flex items-center justify-between text-xs text-coal-400">
				<span>Départ 🧳</span>
				<span>{departCount}/{total} ({departPct}%)</span>
			</div>
			<div class="mt-1 h-2 w-full rounded-full bg-coal-800">
				<div class="h-2 rounded-full bg-ember-500 transition-all" style="width: {departPct}%"></div>
			</div>
		</div>
	</div>

	<!-- Add form -->
	<div class="mb-6">
		<button
			onclick={() => (showAddForm = !showAddForm)}
			class="inline-flex items-center gap-1.5 rounded-lg border border-coal-700 bg-coal-900 px-3 py-1.5 text-xs text-coal-300 transition-colors hover:border-ember-500 hover:text-ember-400"
		>
			<Plus size={14} /> {showAddForm ? 'Annuler' : 'Ajouter un article'}
		</button>
		<button
			onclick={openCatalog}
			class="ml-2 inline-flex items-center gap-1.5 rounded-lg border border-coal-700 bg-coal-900 px-3 py-1.5 text-xs text-coal-300 transition-colors hover:border-ember-500 hover:text-ember-400"
		>
			<Library size={14} /> Catalogue
		</button>

		{#if showAddForm}
			<div class="mt-3 flex flex-wrap items-end gap-2">
				<input bind:value={newCat} placeholder="Catégorie"
					class="rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none placeholder:text-coal-400 focus:border-ember-500 sm:max-w-36" />
				<input bind:value={newLabel} placeholder="Article"
					onkeydown={(e: any) => e.key === 'Enter' && addItem()}
					class="flex-[2] rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none placeholder:text-coal-400 focus:border-ember-500" />
				<div class="flex items-center gap-1">
					<button onclick={() => { if (newQty > 1) newQty--; }}
						class="flex h-8 w-8 items-center justify-center rounded border border-coal-700 text-coal-300 hover:border-ember-500 transition-colors">−</button>
					<span class="w-8 text-center text-sm text-coal-200">{newQty}</span>
					<button onclick={() => newQty++}
						class="flex h-8 w-8 items-center justify-center rounded border border-coal-700 text-coal-300 hover:border-ember-500 transition-colors">+</button>
				</div>
				<Button onclick={addItem} disabled={!newLabel.trim()}>
					<Plus size={16} class="inline" /> Ajouter
				</Button>
			</div>
		{/if}
	</div>

	<!-- Items by category -->
	<div class="space-y-4">
		{#each categories as [category, catItems]}
			<div>
				<h3 class="mb-2 font-display text-base text-coal-300">{category}</h3>
				<div class="space-y-2">
					{#each catItems as item (item.id)}
						<Card variant="static" surface={40} padding="p-3">
							<div class="flex items-center gap-3">
								<!-- Depart counter -->
								<div class="flex items-center gap-0.5">
									<button
										onclick={() => toggle(item.id, -1)}
										disabled={(item.checked || 0) <= 0}
										class="flex h-6 w-6 items-center justify-center rounded-l border border-coal-700 text-coal-400 transition-colors hover:border-ember-500 hover:text-ember-400 disabled:opacity-30 disabled:cursor-not-allowed"
									><Minus size={12} /></button>
									<div
										class="flex h-6 items-center border-y border-coal-700 px-2 text-xs font-medium {(item.checked || 0) > 0 ? 'bg-ember-500/20 text-ember-400' : 'text-coal-400'}"
									>{item.checked || 0}/{item.quantity}</div>
									<button
										onclick={() => toggle(item.id, 1)}
										disabled={(item.checked || 0) >= (item.quantity || 1)}
										class="flex h-6 w-6 items-center justify-center rounded-r border border-coal-700 text-coal-400 transition-colors hover:border-ember-500 hover:text-ember-400 disabled:opacity-30 disabled:cursor-not-allowed"
									><Plus size={12} /></button>
								</div>

								<span class="flex-1 text-sm text-coal-100">{item.label}</span>
								<button onclick={() => removeItem(item.id)}
									class="text-coal-600 hover:text-red-400 transition-colors" title="Supprimer">
									<X size={14} />
								</button>
							</div>
						</Card>
					{/each}
				</div>
			</div>
		{/each}
	</div>

	{#if items.length === 0}
		<p class="mt-8 text-center text-coal-500">Checklist vide. Ajoute des articles ci-dessus.</p>
	{/if}
</div>

<!-- Catalog import overlay -->
{#if showCatalog}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onclick={() => showCatalog = false} role="presentation">
		<div class="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-xl border border-coal-700 bg-coal-950 p-5 shadow-2xl" onclick={(e) => e.stopPropagation()} role="dialog">
			<h2 class="font-display text-lg text-coal-50">Depuis le catalogue</h2>
			<p class="mb-4 text-xs text-coal-400">Sélectionnez les articles à ajouter à ce voyage</p>

			{#if allCatalog.length === 0}
				<p class="py-6 text-center text-sm text-coal-500">Le catalogue est vide.</p>
			{:else}
				<div class="space-y-3">
					{#each Object.entries(catalogByCat) as [cat, catItems]}
						<div>
							<h4 class="mb-1 text-sm font-medium text-coal-400">{cat}</h4>
							<div class="space-y-1.5">
								{#each catItems as item}
									<div class="flex items-center gap-2 rounded-lg border border-coal-800 p-2">
										<input type="checkbox" checked={selIds.has(item.id)} onchange={() => toggleSel(item.id)} class="accent-ember-500 h-4 w-4" />
										<span class="flex-1 text-sm text-coal-100">{item.name}</span>
										<div class="flex items-center gap-1">
											<button onclick={() => { if ((selQtys[item.id] ?? 1) > 1) selQtys[item.id] = (selQtys[item.id] ?? 1) - 1; }}
												class="flex h-6 w-6 items-center justify-center rounded border border-coal-700 text-coal-400 hover:border-ember-500 transition-colors text-sm">−</button>
											<span class="w-6 text-center text-xs text-coal-200">{selQtys[item.id] ?? item.default_quantity ?? 1}</span>
											<button onclick={() => { selQtys[item.id] = (selQtys[item.id] ?? item.default_quantity ?? 1) + 1; }}
												class="flex h-6 w-6 items-center justify-center rounded border border-coal-700 text-coal-400 hover:border-ember-500 transition-colors text-sm">+</button>
										</div>
									</div>
								{/each}
							</div>
						</div>
					{/each}
				</div>

				<div class="mt-4 flex justify-end gap-2">
					<button onclick={() => showCatalog = false}
						class="rounded-lg border border-coal-700 px-4 py-2 text-sm text-coal-300 transition-colors hover:border-ember-500 hover:text-ember-400">
						Annuler
					</button>
					<Button onclick={importSelected} disabled={selIds.size === 0}>Importer ({selIds.size})</Button>
				</div>
			{/if}
		</div>
	</div>
{/if}
