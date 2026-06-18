<script lang="ts">
	import { PageHeader, Button } from '@calcifer/ui';
	import { Library, Pencil, Trash2, X, Check } from '@lucide/svelte/icons';

	let { data, form } = $props();
	let items = $state(data.items);

	let categories = $derived.by(() => {
		const map = new Map<string, typeof items>();
		for (const item of items) {
			const cat = item.category || 'Autre';
			if (!map.has(cat)) map.set(cat, []);
			map.get(cat)!.push(item);
		}
		return Array.from(map.entries()).sort();
	});

	// --- Inline editing ---
	let editId = $state<number | null>(null);
	let editName = $state('');
	let editCat = $state('');
	let editQty = $state(1);

	function startEdit(item: any) {
		editId = item.id;
		editName = item.name;
		editCat = item.category || '';
		editQty = item.default_quantity ?? 1;
	}

	function cancelEdit() {
		editId = null;
	}

	async function saveEdit(itemId: number) {
		if (!editName.trim()) return;
		// Optimistic update
		const idx = items.findIndex((i: any) => i.id === itemId);
		if (idx !== -1) {
			items[idx] = { ...items[idx], name: editName.trim(), category: editCat, default_quantity: Math.max(1, editQty) };
			items = [...items];
		}
		editId = null;
		await fetch('/catalog?/update', {
			method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: new URLSearchParams({
				itemId: String(itemId),
				name: editName.trim(),
				category: editCat,
				default_quantity: String(Math.max(1, editQty))
			})
		});
	}

	// --- Delete ---
	async function removeItem(itemId: number) {
		items = items.filter((i: any) => i.id !== itemId);
		await fetch('/catalog?/remove', {
			method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: new URLSearchParams({ itemId: String(itemId) })
		});
	}

	function focusMe(node: HTMLInputElement) {
		node.focus();
		node.select();
	}
</script>

<div class="mx-auto max-w-4xl px-4 py-6">
	<PageHeader title="Catalogue d'articles" description="{items.length} articles — global, partagé entre tous les voyages" />

	{#if editId !== null}
		<div class="mb-6 rounded-2xl border border-ember-500/40 bg-coal-900/70 p-4">
			<h3 class="mb-3 font-display text-sm text-coal-200">Modifier l'article</h3>
			<div class="flex flex-wrap items-end gap-3">
				<div>
					<label class="mb-1 block text-xs text-coal-500">Nom</label>
					<input bind:value={editName}
						onkeydown={(e: any) => e.key === 'Escape' && cancelEdit()}
						use:focusMe
						class="rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none focus:border-ember-500" />
				</div>
				<div>
					<label class="mb-1 block text-xs text-coal-500">Catégorie</label>
					<input bind:value={editCat} placeholder="Bagage, Pharmacie..."
						class="rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none focus:border-ember-500" />
				</div>
				<div>
					<label class="mb-1 block text-xs text-coal-500">Qté par défaut</label>
					<input type="number" min="1" bind:value={editQty}
						class="w-16 rounded-lg border border-coal-700 bg-coal-900 px-2 py-2 text-sm text-coal-50 outline-none focus:border-ember-500" />
				</div>
				<Button onclick={() => saveEdit(editId!)} disabled={!editName.trim()}>
					<Check size={14} /> Enregistrer
				</Button>
				<button onclick={cancelEdit}
					class="flex items-center gap-1 rounded-lg border border-coal-700 px-3 py-2 text-xs text-coal-400 hover:border-coal-500">
					<X size={14} /> Annuler
				</button>
			</div>
		</div>
	{/if}

	<div class="space-y-6">
		{#each categories as [category, catItems]}
			<div>
				<h3 class="mb-2 font-display text-base text-coal-300">{category}</h3>
				<div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
					{#each catItems as item}
						<div class="group rounded-2xl border border-coal-800 bg-coal-900/55 p-3 transition-colors hover:border-coal-700">
							<div class="flex items-center gap-2">
								<Library size={16} class="shrink-0 text-coal-500" />
								<div class="flex-1 min-w-0">
									<p class="truncate text-sm text-coal-100">{item.name}</p>
									<p class="text-xs text-coal-500">×{item.default_quantity}</p>
								</div>
								<div class="flex shrink-0 gap-1 opacity-0 transition-opacity group-hover:opacity-100">
									<button onclick={() => startEdit(item)}
										class="flex h-7 w-7 items-center justify-center rounded text-coal-500 hover:bg-coal-800 hover:text-ember-400"
										title="Modifier">
										<Pencil size={13} />
									</button>
									<button onclick={() => removeItem(item.id)}
										class="flex h-7 w-7 items-center justify-center rounded text-coal-500 hover:bg-coal-800 hover:text-red-400"
										title="Supprimer">
										<Trash2 size={13} />
									</button>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/each}
	</div>
</div>
