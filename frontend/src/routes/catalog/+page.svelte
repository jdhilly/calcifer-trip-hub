<script lang="ts">
	import { PageHeader } from '@calcifer/ui';

	let { data } = $props();
	let items = $derived(data.items);

	let categories = $derived.by(() => {
		const map = new Map<string, typeof items>();
		for (const item of items) {
			const cat = item.category || 'Autre';
			if (!map.has(cat)) map.set(cat, []);
			map.get(cat)!.push(item);
		}
		return Array.from(map.entries()).sort();
	});
</script>

<div class="mx-auto max-w-4xl px-4 py-6">
	<PageHeader title="Catalogue d'articles" description="{items.length} articles — global, partagé entre tous les voyages" />
	<div class="space-y-6">
		{#each categories as [category, catItems]}
			<div>
				<h3 class="mb-2 font-display text-base text-coal-300">{category}</h3>
				<div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
					{#each catItems as item}
						<div class="rounded-2xl border border-coal-800 bg-coal-900/55 p-3">
							<div class="flex items-center justify-between">
								<div>
									<p class="text-sm text-coal-100">{item.name}</p>
									<p class="text-xs text-coal-500">×{item.default_quantity}</p>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/each}
	</div>
</div>
